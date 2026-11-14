import logging
from uuid import UUID, uuid4

from companion.core.features import FeatureService
from companion.core.models import (
    ConversationSummary,
    Feature,
    MemoryCategory,
    MemoryGroup,
    MemoryItem,
    MemorySource,
    PlatformSettings,
    User,
)
from companion.core.platform_settings import (
    MEMORY_NOT_AVAILABLE_NOTE,
    MEMORY_PAUSED_NOTE,
    ONBOARDING_NAME_MEMORY_CATEGORY,
    ONBOARDING_REASONS_MEMORY_CATEGORY,
)
from companion.core.ports import Clock, Repositories

logger = logging.getLogger(__name__)


class MemoryNotFoundError(LookupError):
    """Raised when a User has no Memory Item or Conversation Summary with that ID."""


class UserMemoryService:
    """Lets a User see and delete their User Memory, and seeds it at onboarding.

    While User Memory is off the Companion stops learning but keeps using what
    it has, so only saving is stopped here.
    """

    def __init__(
        self, repositories: Repositories, features: FeatureService, clock: Clock
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where User Memory, Memory Categories and settings
                are stored.
            features: Says whether User Memory works for the User.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._features = features
        self._clock = clock

    def memory_note(self, user: User, settings: PlatformSettings) -> str:
        """Pick the Dashboard note that says User Memory is off, and why.

        The Admin's switch has the final say, so its note wins over the
        User's own.

        Args:
            user: The User.
            settings: The platform settings, read once per request.

        Returns:
            The Admin-managed "isn't available" note when the Admin side has
            User Memory off, the "paused" note when the User has it off, and
            "" when it works.
        """
        if not self._features.available_for(user.id, Feature.USER_MEMORY):
            note = MEMORY_NOT_AVAILABLE_NOTE
        elif not user.user_memory_enabled:
            note = MEMORY_PAUSED_NOTE
        else:
            return ""
        return settings.get(note)

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

    def delete_all_items(self, user_id: UUID) -> None:
        """Delete every one of a User's Memory Items; Summaries stay.

        Args:
            user_id: The User's ID.
        """
        self._repositories.user_memory.delete_all_items(user_id)

    def list_summaries(self, user_id: UUID) -> list[ConversationSummary]:
        """List a User's Conversation Summaries, newest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Conversation Summaries.
        """
        return self._repositories.user_memory.list_summaries(user_id)

    def delete_summary(self, user_id: UUID, summary_id: UUID) -> None:
        """Delete one of a User's Conversation Summaries.

        Args:
            user_id: The User's ID.
            summary_id: The Conversation Summary's ID.

        Raises:
            MemoryNotFoundError: If the User has no such Conversation Summary.
        """
        if not self._repositories.user_memory.delete_summary(user_id, summary_id):
            raise MemoryNotFoundError

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
