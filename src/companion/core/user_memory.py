import logging
from collections.abc import Callable
from uuid import UUID, uuid4

from companion.core.errors import NotFoundError
from companion.core.features import FeatureService
from companion.core.models import (
    DaySummary,
    Feature,
    LifeThread,
    MemoryCategory,
    MemoryGroup,
    MemoryItem,
    MemorySource,
    MoveOutcome,
    Observation,
    PatternMoveCause,
    PatternState,
    User,
    UserPortrait,
)
from companion.core.observations import deleted_quotes_of, users_own_texts
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.pattern_scoring import PatternScorer
from companion.core.platform_settings import (
    ONBOARDING_NAME_MEMORY_CATEGORY,
    ONBOARDING_REASONS_MEMORY_CATEGORY,
)
from companion.core.ports import Clock, Repositories
from companion.core.ready_gate import ReadyKeeper
from companion.core.told_patterns import ToldPattern, told_patterns, was_told

logger = logging.getLogger(__name__)

STATES_NEVER_NOTED_AGAIN_ONCE_DELETED = frozenset(
    {PatternState.CONTESTED, PatternState.CLOSED}
)


class MemoryNotFoundError(NotFoundError):
    """Raised when a User has no Memory Item with that ID."""

    shown_message = "Memory not found"


class DaySummaryNotFoundError(MemoryNotFoundError):
    """Raised when a User has no Day Summary with that ID."""

    shown_message = "Day Summary not found"


class LifeThreadNotFoundError(MemoryNotFoundError):
    """Raised when a User has no Life Thread with that ID."""

    shown_message = "Life Thread not found"


class MoveOutcomeNotFoundError(MemoryNotFoundError):
    """Raised when a User has no Move Outcome with that ID."""

    shown_message = "Move Outcome not found"


class PatternNotFoundError(MemoryNotFoundError):
    """Raised when a User has no Pattern they were told with that ID."""

    shown_message = "Pattern not found"


class KeptQuoteNotFoundError(MemoryNotFoundError):
    """Raised when a User has no kept quote (Observation) with that ID."""

    shown_message = "Quote not found"


class UserPortraitNotFoundError(MemoryNotFoundError):
    """Raised when a User has no User Portrait."""

    shown_message = "User Portrait not found"


def newest_first(observations: list[Observation]) -> list[Observation]:
    """Order Observations by their day, newest first, the latest tagged first on a day.

    Args:
        observations: The Observations, oldest tagged first.

    Returns:
        The same Observations, newest first.
    """
    return sorted(
        reversed(observations), key=lambda observation: observation.day, reverse=True
    )


class UserMemoryService:
    """Lets a User see and delete their User Memory, and seeds it at onboarding.

    While User Memory is off the Companion stops learning but keeps using what
    it has, so only saving is stopped here. Deleting a Memory Item, Life
    Thread, Pattern, Move Outcome or Day Summary asks for the User Portrait
    to be written again without it, whatever User Memory says, since that
    only forgets.
    """

    def __init__(
        self,
        repositories: Repositories,
        features: FeatureService,
        pattern_catalog: PatternCatalogService,
        pattern_scorer: PatternScorer,
        ready_keeper: ReadyKeeper,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where User Memory, Memory Categories and settings
                are stored.
            features: Says whether User Memory works for the User.
            pattern_catalog: Reads the words a Pattern is told in.
            pattern_scorer: Scores the User's Patterns again once
                Observations are deleted.
            ready_keeper: Takes back a ready Pattern that no longer passes
                once Observations are deleted.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._features = features
        self._pattern_catalog = pattern_catalog
        self._pattern_scorer = pattern_scorer
        self._ready_keeper = ready_keeper
        self._clock = clock

    def list_groups(self, user_id: UUID) -> list[MemoryGroup]:
        """List a User's Memory Items by Memory Category, in category order.

        Archived categories are included so their Memory Items stay visible;
        categories with no items for the User are left out.

        Args:
            user_id: The User's ID.

        Returns:
            One group per category that has items.
        """
        items = self._repositories.user_memory.list_items(user_id)
        groups = [
            MemoryGroup(
                category=category,
                items=[item for item in items if item.category_id == category.id],
            )
            for category in self._repositories.memory_categories.list_all()
        ]
        return [group for group in groups if group.items]

    def delete_item(self, user_id: UUID, item_id: UUID) -> None:
        """Delete one of a User's Memory Items.

        Args:
            user_id: The User's ID.
            item_id: The Memory Item's ID.

        Raises:
            MemoryNotFoundError: If the User has no such Memory Item.
        """
        if not self._repositories.user_memory.delete_item(user_id, item_id):
            raise MemoryNotFoundError
        self._rewrite_portrait(user_id)

    def delete_all_items(self, user_id: UUID) -> None:
        """Delete every one of a User's Memory Items; Summaries stay.

        Args:
            user_id: The User's ID.
        """
        self._repositories.user_memory.delete_all_items(user_id)
        self._rewrite_portrait(user_id)

    def list_summaries(self, user_id: UUID) -> list[DaySummary]:
        """List a User's Day Summaries, newest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Day Summaries.
        """
        return self._repositories.user_memory.list_summaries(user_id)

    def delete_summary(self, user_id: UUID, summary_id: UUID) -> None:
        """Delete one of a User's Day Summaries.

        Args:
            user_id: The User's ID.
            summary_id: The Day Summary's ID.

        Raises:
            DaySummaryNotFoundError: If the User has no such
                Day Summary.
        """
        if not self._repositories.user_memory.delete_summary(user_id, summary_id):
            raise DaySummaryNotFoundError
        self._rewrite_portrait(user_id)

    def list_threads(self, user_id: UUID) -> list[LifeThread]:
        """List a User's Life Threads, open first, then the latest updated.

        Args:
            user_id: The User's ID.

        Returns:
            The Life Threads.
        """
        return self._repositories.life_threads.list_for_user(user_id)

    def delete_thread(self, user_id: UUID, thread_id: UUID) -> None:
        """Delete one of a User's Life Threads, so it is never brought up again.

        Its evidence in Patterns goes with it, and so does a Pattern left
        with no evidence. So do its Observations, whose quotes are never
        kept again, and the User's Patterns of Pattern Types are scored
        again at once. The User is locked while it is deleted, as scoring
        locks them.

        Args:
            user_id: The User's ID.
            thread_id: The Life Thread's ID.

        Raises:
            LifeThreadNotFoundError: If the User has no such Life Thread.
        """
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user_id)
            in_transaction = transaction.repositories
            self._note_deleted_quotes(
                in_transaction,
                user_id,
                lambda observation: observation.thread_id == thread_id,
            )
            if not in_transaction.life_threads.delete(user_id, thread_id):
                raise LifeThreadNotFoundError
            in_transaction.patterns.delete_without_evidence(user_id)
        self._score_patterns_again(user_id)
        self._rewrite_portrait(user_id)

    def list_told_patterns(self, user_id: UUID) -> list[ToldPattern]:
        """List the Patterns Zeph has told a User about, as they see them.

        Patterns Zeph hasn't told them, and unmatched ones, are never shown.

        Args:
            user_id: The User's ID.

        Returns:
            The Patterns being tested, then confirmed, disagreed with and
            closed after being told, each with its quotes by Life Thread
            and its Predictions.
        """
        patterns = self._repositories.patterns.list_of_pattern_types(user_id)
        if not any(was_told(pattern) for pattern in patterns):
            return []
        return told_patterns(
            patterns,
            {
                entry.pattern_type.id: entry.pattern_type
                for entry in self._pattern_catalog.catalog()
            },
            self._repositories.observations.list_for_user(user_id),
            self._repositories.patterns.list_predictions(user_id),
            self._repositories.life_threads.list_for_user(user_id),
        )

    def delete_pattern(self, user_id: UUID, pattern_id: UUID) -> None:
        """Delete a Pattern Zeph told a User about, so it is gone at once.

        The Observations whose first Pattern Type is its own go with it,
        so the quotes it showed never bring it back, and those quotes are
        never kept again. Deleting one they disagreed with, or that
        didn't hold up, also marks its Pattern Type so it is never noted
        or shared for them again; its Predictions and
        the User's reactions to it go too. The
        User is locked while it is deleted, as scoring locks them, and
        their other Patterns are scored again at once.

        Args:
            user_id: The User's ID.
            pattern_id: The Pattern's ID.

        Raises:
            PatternNotFoundError: If the User has no such Pattern they were
                told.
        """
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user_id)
            in_transaction = transaction.repositories
            told = [
                pattern
                for pattern in in_transaction.patterns.list_of_pattern_types(user_id)
                if pattern.id == pattern_id and was_told(pattern)
            ]
            if not told:
                raise PatternNotFoundError
            self._note_deleted_quotes(
                in_transaction,
                user_id,
                lambda observation: (
                    observation.pattern_type_id == told[0].pattern_type_id
                ),
            )
            in_transaction.observations.delete_of_pattern_type(
                user_id, told[0].pattern_type_id
            )
            if told[0].state in STATES_NEVER_NOTED_AGAIN_ONCE_DELETED:
                in_transaction.patterns.mark_never_again(
                    user_id, told[0].pattern_type_id, self._clock.now()
                )
            in_transaction.patterns.save_moves([], [], [pattern_id], [])
        self._score_patterns_again(user_id)
        self._rewrite_portrait(user_id)

    def list_kept_quotes(self, user_id: UUID) -> list[Observation]:
        """List the quotes Zeph keeps as evidence for a User, newest day first.

        Listed whatever User Memory says, so a User can always see their own
        words; the Dashboard shows only each quote, its context line and day.

        Args:
            user_id: The User's ID.

        Returns:
            The User's Observations, newest first.
        """
        return newest_first(self._repositories.observations.list_for_user(user_id))

    def delete_kept_quote(self, user_id: UUID, observation_id: UUID) -> None:
        """Delete one of a User's kept quotes, and score their Patterns again at once.

        The User is locked while it is deleted, as scoring locks them, so a
        Conversation end already scoring finishes first and the scoring after
        the deletion never counts it. A record that it was deleted is kept,
        without its words, so tagging its day again never keeps it again.

        Args:
            user_id: The User's ID.
            observation_id: The kept quote's (Observation's) ID.

        Raises:
            KeptQuoteNotFoundError: If the User has no such kept quote.
        """
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user_id)
            in_transaction = transaction.repositories
            self._note_deleted_quotes(
                in_transaction,
                user_id,
                lambda observation: observation.id == observation_id,
            )
            if not in_transaction.observations.delete(user_id, observation_id):
                raise KeptQuoteNotFoundError
        self._score_patterns_again(user_id)

    def list_move_outcomes(self, user_id: UUID) -> list[MoveOutcome]:
        """List a User's Move Outcomes, newest made first.

        Args:
            user_id: The User's ID.

        Returns:
            The Move Outcomes.
        """
        return self._repositories.move_outcomes.list_for_user(user_id)

    def delete_move_outcome(self, user_id: UUID, outcome_id: UUID) -> None:
        """Delete one of a User's Move Outcomes, so it is never used again.

        Args:
            user_id: The User's ID.
            outcome_id: The Move Outcome's ID.

        Raises:
            MoveOutcomeNotFoundError: If the User has no such Move Outcome.
        """
        if not self._repositories.move_outcomes.delete(user_id, outcome_id):
            raise MoveOutcomeNotFoundError
        self._rewrite_portrait(user_id)

    def find_portrait(self, user_id: UUID) -> UserPortrait | None:
        """Find a User's User Portrait.

        Args:
            user_id: The User's ID.

        Returns:
            The Portrait; None if they have none.
        """
        return self._repositories.user_portraits.find(user_id)

    def delete_portrait(self, user_id: UUID) -> None:
        """Clear a User's User Portrait.

        It is written again only at a later Conversation end while User
        Memory works; a Portrait being written as it is cleared never lands.

        Args:
            user_id: The User's ID.

        Raises:
            UserPortraitNotFoundError: If the User has no Portrait.
        """
        if not self._repositories.user_portraits.clear(user_id, self._clock.now()):
            raise UserPortraitNotFoundError

    def _note_deleted_quotes(
        self,
        repositories: Repositories,
        user_id: UUID,
        is_being_deleted: Callable[[Observation], bool],
    ) -> None:
        """Keep a record that the User deleted some kept quotes.

        Args:
            repositories: The repositories, inside the deleting transaction.
            user_id: The User's ID.
            is_being_deleted: Says which of their Observations are about
                to be deleted.
        """
        going = [
            observation
            for observation in repositories.observations.list_for_user(user_id)
            if is_being_deleted(observation)
        ]
        texts_by_conversation = {
            conversation_id: users_own_texts(
                repositories.conversations.list_messages(conversation_id)
            )
            for conversation_id in {
                observation.conversation_id for observation in going
            }
        }
        repositories.observations.note_deleted_quotes(
            deleted_quotes_of(going, texts_by_conversation, self._clock.now())
        )

    def _score_patterns_again(self, user_id: UUID) -> None:
        """Score the User's Patterns of Pattern Types again, after Observations went.

        A ready Pattern that no longer passes its checks goes back too.

        A failure is logged instead of raised: the deletion already happened.

        Args:
            user_id: The User's ID.
        """
        user = self._repositories.users.get(user_id)
        if user is None:
            return
        try:
            settings = self._repositories.platform_settings.load()
            cause = PatternMoveCause.OBSERVATIONS_DELETED
            self._pattern_scorer.score(user, settings, cause)
            self._ready_keeper.look(user, settings, cause)
        except Exception:
            logger.exception("Could not score Patterns after a deletion")

    def _rewrite_portrait(self, user_id: UUID) -> None:
        """Ask for the User's Portrait to be written again, after a deletion.

        The scheduler's next tick writes it, if they have one.

        Args:
            user_id: The User's ID.
        """
        self._repositories.user_portraits.request_rewrite(user_id, self._clock.now())

    def remember_onboarding(self, user: User) -> None:
        """Save the User's onboarding answers as Memory Items.

        Their name and "What brings you here?" answers go into the Memory
        Categories named in platform settings, replacing any earlier
        onboarding items so answering again never duplicates them. Nothing
        changes when User Memory doesn't work for the User.

        Args:
            user: The User who just finished onboarding.
        """
        if not self._features.works_for(user.id, Feature.USER_MEMORY):
            return
        settings = self._repositories.platform_settings.load()
        active_categories = {
            category.name: category
            for category in self._repositories.memory_categories.list_all()
            if not category.archived
        }
        name_category = active_categories.get(
            settings.get(ONBOARDING_NAME_MEMORY_CATEGORY)
        )
        reasons_category = active_categories.get(
            settings.get(ONBOARDING_REASONS_MEMORY_CATEGORY)
        )
        facts: list[tuple[MemoryCategory | None, str]] = []
        if user.name:
            facts.append((name_category, f"Goes by {user.name}"))
        if user.onboarding_reasons:
            facts.append(
                (
                    reasons_category,
                    "Came to Zeph for: " + ", ".join(user.onboarding_reasons),
                )
            )
        if user.onboarding_note:
            facts.append(
                (
                    reasons_category,
                    f"In their own words, what brings them here: "
                    f"{user.onboarding_note}",
                )
            )
        now = self._clock.now()
        items: list[MemoryItem] = []
        for category, content in facts:
            if category is None:
                logger.warning("No active Memory Category for an onboarding answer")
                continue
            items.append(
                MemoryItem(
                    id=uuid4(),
                    user_id=user.id,
                    category_id=category.id,
                    content=content,
                    source=MemorySource.ONBOARDING,
                    source_conversation_id=None,
                    created_at=now,
                    updated_at=now,
                )
            )
        self._repositories.user_memory.replace_onboarding_items(user.id, items)
