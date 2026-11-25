import json
import logging
from collections.abc import Hashable, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from companion.core.agenda import observations_of
from companion.core.memory_retrieval import format_calendar_day
from companion.core.models import (
    CatalogPattern,
    ChatLine,
    ChatRole,
    EvidenceKind,
    Feature,
    ModelStep,
    NarrowingTag,
    Observation,
    ObservationDirection,
    PatternMoveCause,
    PatternNarrowing,
    PatternReaction,
    PatternState,
    PatternType,
    Power,
    Prediction,
    ShareVia,
    UserSnapshot,
)
from companion.core.observations import is_situational
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.pattern_scoring import (
    PatternScore,
    logged_move,
    reaction_points,
    score_observations,
    scoring_numbers,
    sign_strengths_of,
    situation_of,
    without_narrowing,
)
from companion.core.platform_settings import (
    CHECK_IN_MODEL,
    PATTERN_SHARE_WAIT,
    PATTERNS_SHARED_PER_WEEK,
    thinking_for_model,
)
from companion.core.ports import Clock, Repositories
from companion.core.ready_gate import ReadyKeeper
from companion.core.timing import users_today
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

FEWEST_QUOTES = 2
FIRST_PREDICTION_WORDING = 1
MOST_QUOTES = 3
SHARES_COUNTED_OVER = timedelta(days=7)
EVIDENCE_KINDS_FROM_THEIR_LIFE = (
    EvidenceKind.REAL_STORY,
    EvidenceKind.REPORTED_HABIT,
    EvidenceKind.OWN_OPINION,
)
POWER_WORDS = {
    Power.ABOVE.value: "people above them",
    Power.EQUAL.value: "their equals",
    Power.BELOW.value: "people below them",
}
CAUSE_OF_SHARING = {
    ShareVia.CHAT: PatternMoveCause.SHARED_IN_CHAT,
    ShareVia.CHECK_IN: PatternMoveCause.SHARED_IN_CHECK_IN,
}
SHARED_CHECK_PROMPT = (
    "You check whether a message told someone a Pattern about themselves. "
    "You are given the Pattern and the message as it will be sent. Answer "
    'with JSON only: {"shared": true or false, "prediction": "..."}. '
    '"shared" is true only if the message tells them the Pattern, in any '
    "words, as something noticed about them; a hint, a question or one of "
    'their quotes alone is not enough. "prediction" is the one thing the '
    "message asks them to notice or watch for in their own life, in the "
    'message\'s own words; "" if it asks for none.'
)


@dataclass(frozen=True)
class PatternToShare:
    """A ready Pattern code offers to be shared, with what it is shared with.

    Attributes:
        pattern: The Pattern, ready.
        pattern_type: Its Pattern Type, with the approved wording.
        quotes: Two or three of the User's Observations to quote, each from
            a different situation.
        scored: Its score as scoring counts it, for the log.
    """

    pattern: CatalogPattern
    pattern_type: PatternType
    quotes: tuple[Observation, ...]
    scored: PatternScore


@dataclass(frozen=True)
class ContestedPattern:
    """A Pattern the User disagreed with, numbered for the Reply Plan.

    Attributes:
        number: Its number in the list the model is shown, from 1.
        pattern: The Pattern.
        pattern_type: Its Pattern Type, with the approved wording.
    """

    number: int
    pattern: CatalogPattern
    pattern_type: PatternType


@dataclass(frozen=True)
class SharedCheck:
    """What the check after a message found.

    Attributes:
        shared: Whether the message told the User the Pattern.
        prediction: The Prediction as the message worded it; "" for none.
    """

    shared: bool
    prediction: str


def is_weighty_evidence_for(observation: Observation, pattern_type_id: str) -> bool:
    """Say whether an Observation is clear evidence for a Pattern that carries weight.

    Args:
        observation: The Observation.
        pattern_type_id: The Pattern's Pattern Type.

    Returns:
        True for clear evidence for the Pattern from their own life: not
        said while an exclusion applied, not marked as what anyone would
        do when it was tagged, and not on a ruled-out topic unless they
        raised it themselves.
    """
    on_topic_not_raised = (
        observation.ruled_out_topic is not None and not observation.raised_by_user
    )
    return (
        observation.direction == ObservationDirection.FOR
        and observation.pattern_type_id == pattern_type_id
        and observation.evidence_kind in EVIDENCE_KINDS_FROM_THEIR_LIFE
        and not observation.unclear
        and not observation.excluded
        and not observation.situational
        and not on_topic_not_raised
    )


def may_be_quoted(observation: Observation, pattern_type: PatternType) -> bool:
    """Say whether an Observation may be quoted back when its Pattern is shared.

    Args:
        observation: The Observation.
        pattern_type: The Pattern's Pattern Type, in the catalog now.

    Returns:
        True for clear evidence for the Pattern from their own life that
        carries weight, and not where anyone would act the same by the
        catalog now.
    """
    return is_weighty_evidence_for(observation, pattern_type.id) and not is_situational(
        observation.tags, pattern_type.anyone_would_when
    )


def pick_quotes(
    observations: Sequence[Observation], pattern_type: PatternType
) -> tuple[Observation, ...]:
    """Pick the User's quotes a shared Pattern comes with.

    One per situation (a Life Thread; with none, the same person and
    setting), so they come from different parts of their life. Real
    stories come before habits they reported and their own opinion of
    themselves, and newer ones before older.

    Args:
        observations: The Observations of the Pattern.
        pattern_type: Its Pattern Type, in the catalog now.

    Returns:
        Up to three Observations that may be quoted; fewer than two means
        the Pattern can't be shared yet.
    """
    kind_rank = {kind: rank for rank, kind in enumerate(EvidenceKind)}
    candidates = sorted(
        (
            observation
            for observation in observations
            if may_be_quoted(observation, pattern_type)
        ),
        key=lambda observation: (
            kind_rank[observation.evidence_kind],
            -observation.day.toordinal(),
            -observation.tagged_at.timestamp(),
        ),
    )
    picked: dict[Hashable, Observation] = {}
    for observation in candidates:
        picked.setdefault(situation_of(observation), observation)
    return tuple(picked.values())[:MOST_QUOTES]


def within_weekly_limit(shared_this_week: int, per_week: int) -> bool:
    """Say whether one more new Pattern may be shared with a User this week.

    Args:
        shared_this_week: How many were shared with them in the last 7 days.
        per_week: The most Admins allow in 7 days.

    Returns:
        True while fewer were shared than allowed.
    """
    return shared_this_week < per_week


def describe_where_it_shows(narrowings: Sequence[PatternNarrowing]) -> str:
    """Write where a Pattern shows and where it doesn't, in plain words.

    Args:
        narrowings: Where counter-tests showed it doesn't happen.

    Returns:
        E.g. " It shows with family, friend; not with partner."; "" when
        it isn't narrowed.
    """
    parts = []
    for narrowing in narrowings:
        words = POWER_WORDS if narrowing.tag == NarrowingTag.POWER else {}
        holds_with = ", ".join(
            words.get(value, value) for value in narrowing.holds_with
        )
        not_with = ", ".join(words.get(value, value) for value in narrowing.not_with)
        parts.append(f" It shows with {holds_with}; not with {not_with}.")
    return "".join(parts)


def describe_quotes(quotes: Sequence[Observation]) -> str:
    """Write the quotes a shared Pattern comes with, one per line.

    Args:
        quotes: The Observations to quote.

    Returns:
        E.g. "- 3 Nov 2026, about their mum. They let it go. They said:
        “it's fine honestly”".
    """
    return "\n".join(
        f"- {format_calendar_day(quote.day)}, about {quote.about}. "
        f"{quote.context} They said: “{quote.quote}”"
        for quote in quotes
    )


def describe_pattern_to_share(to_share: PatternToShare | None) -> str:
    """Write the ready Pattern as the Reply Plan model is offered it.

    Args:
        to_share: The Pattern code offers; None for none.

    Returns:
        The Pattern's approved wording, where it shows and the quotes, with
        how to pick it; "" when none is offered.
    """
    if to_share is None:
        return ""
    pattern_type = to_share.pattern_type
    return (
        "\n\nA Pattern you may tell them now. Code tested it against their own "
        "words and it is ready: it is the only Pattern you may say as a "
        "pattern. You pick the moment: tell them when they have room to take "
        "it in, never while they are venting, in a hurry or in the middle of "
        'something else. To tell them in this reply set "share_pattern" to '
        "true; otherwise it waits for a better moment:\n"
        f"{pattern_type.approved_wording}"
        f"{describe_where_it_shows(to_share.pattern.narrowings)}\n"
        f"Their own words behind it:\n{describe_quotes(to_share.quotes)}"
    )


def describe_three_parts(to_share: PatternToShare) -> str:
    """Write the three parts a shared Pattern is told in.

    Args:
        to_share: The Pattern to share.

    Returns:
        The rules of wording, the Pattern, the quotes and the Prediction,
        ending with asking what would prove it wrong.
    """
    pattern_type = to_share.pattern_type
    return (
        "It is your view of them, never a fact: say it as something you've "
        "noticed and could be wrong about. Use plain, warm words: no clinical "
        "or diagnostic words and no labels.\n"
        "1. The Pattern, in your own warm words, fitted to the people in "
        f"their life: {pattern_type.approved_wording}"
        f"{describe_where_it_shows(to_share.pattern.narrowings)}\n"
        "2. Their own words: quote two or three of these word for word, "
        "saying what each was about:\n"
        f"{describe_quotes(to_share.quotes)}\n"
        "3. One Prediction, one thing for them to notice in their own life: "
        f"{pattern_type.prediction_wordings[0]} Where it has a word in curly "
        "brackets, put their own person or thing.\n"
        "Then ask them what would prove it wrong."
    )


def format_pattern_to_share_for_reply(to_share: PatternToShare) -> str:
    """Write the reply's section on the Pattern it shares.

    Args:
        to_share: The Pattern the Reply Plan chose to share.

    Returns:
        The section, which is part of the plan and not an optional extra.
    """
    return (
        "Tell them this Pattern in this reply. It is part of the plan, not an "
        f"extra to leave out. {describe_three_parts(to_share)}"
    )


def format_pattern_to_share_for_check_in(
    to_share: PatternToShare, kind_names: Sequence[str]
) -> str:
    """Write the Check-in model's section on the Pattern its message shares.

    Args:
        to_share: The ready Pattern that waited too long for a moment in chat.
        kind_names: The names of the Check-in Kinds that share a Pattern.

    Returns:
        The section.
    """
    names = " or ".join(f'"{name}"' for name in kind_names)
    return (
        "Something you've noticed about them and have been waiting for a good "
        f"moment to say. If you choose {names}, your message tells them this "
        "Pattern: it may be longer than a usual Check-in and it quotes their "
        f"own words. {describe_three_parts(to_share)}"
    )


def format_raised_pattern_for_reply(contested: ContestedPattern) -> str:
    """Write the reply's section on a Pattern the User disagreed with and now raises.

    Args:
        contested: The Pattern.

    Returns:
        The section.
    """
    return (
        "They disagreed with this when you told them, and have now brought it "
        f"up themselves: {contested.pattern_type.approved_wording} Talk about "
        "it openly, as your view and never as fact. Don't press it: they lead."
    )


def describe_contested(contested: Sequence[ContestedPattern]) -> str:
    """Write the Patterns the User disagreed with as the Reply Plan reads them.

    Args:
        contested: The Patterns, numbered.

    Returns:
        The list with the rule for it; "" when there are none.
    """
    if not contested:
        return ""
    lines = "\n".join(
        f"[{item.number}] {item.pattern_type.approved_wording}" for item in contested
    )
    return (
        "\n\nPatterns you told them that they disagreed with. Never bring one "
        "up or hint at it. Only if they raise one themselves in their latest "
        'message, set "raised_pattern" to its number and the reply may talk '
        f"about it:\n{lines}"
    )


def describe_message_for_shared_check(
    to_share: PatternToShare, texts: Sequence[str]
) -> str:
    """Write what the check after a message is given.

    Args:
        to_share: The Pattern the message was to share.
        texts: The message's texts, in order.

    Returns:
        The Pattern, the Prediction it was to give and the message.
    """
    message = "\n".join(texts)
    return (
        f"The Pattern: {to_share.pattern_type.approved_wording}\n"
        "The Prediction it was to give: "
        f"{to_share.pattern_type.prediction_wordings[0]}"
        f"\n\nThe message:\n{message}"
    )


def read_shared_check(answer: str) -> SharedCheck | None:
    """Read the check's JSON answer.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        Whether the Pattern was shared and the Prediction as worded; None
        if "shared" can't be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("shared"), bool):
        return None
    prediction = parsed.get("prediction")
    return SharedCheck(
        shared=parsed["shared"],
        prediction=prediction.strip() if isinstance(prediction, str) else "",
    )


class PatternSharing:
    """Offers a ready Pattern to be shared, and records when it was.

    Code decides what may be shared and when it counts as shared; the
    Reply Plan picks the moment and the reply words it. Nothing is offered
    unless Pattern sharing works for the User.
    """

    def __init__(
        self,
        repositories: Repositories,
        ready_keeper: ReadyKeeper,
        pattern_catalog: PatternCatalogService,
        chat_model: UsageRecordingChatModel,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Patterns, their log, Predictions and
                reactions are stored.
            ready_keeper: Looks again at the ready Patterns before one is
                offered.
            pattern_catalog: Reads the Pattern Types in the catalog now.
            chat_model: Makes the check after a message and records the
                tokens used.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._ready_keeper = ready_keeper
        self._pattern_catalog = pattern_catalog
        self._chat_model = chat_model
        self._clock = clock

    def pattern_to_offer(
        self, snapshot: UserSnapshot, struggling: bool
    ) -> PatternToShare | None:
        """Find the ready Pattern a reply may share, if any.

        Args:
            snapshot: The User being answered.
            struggling: Whether the Understanding found them struggling.

        Returns:
            Their Pattern ready the longest that still passes every stored
            check and has quotes to share; None while they are struggling,
            Pattern sharing doesn't work for them or the weekly limit is
            reached.
        """
        if struggling or not snapshot.works(Feature.PATTERN_SHARING):
            return None
        return self._ready_longest(snapshot, ready_by=None)

    def pattern_to_offer_in_check_in(
        self, snapshot: UserSnapshot
    ) -> PatternToShare | None:
        """Find the ready Pattern a Check-in may share, if any.

        Args:
            snapshot: The User whose Check-in is due.

        Returns:
            Their Pattern ready the longest, once it has waited the
            Admin-set days for a moment in chat; None while Pattern sharing
            doesn't work for them, their last Message read as struggling
            or the weekly limit is reached.
        """
        if not snapshot.works(Feature.PATTERN_SHARING):
            return None
        if self._last_message_read_as_struggling(snapshot.user.id):
            return None
        waited_since = self._clock.now() - snapshot.settings.get(PATTERN_SHARE_WAIT)
        return self._ready_longest(snapshot, ready_by=waited_since)

    def contested_patterns(self, snapshot: UserSnapshot) -> list[ContestedPattern]:
        """List the Patterns the User disagreed with, for the Reply Plan.

        Args:
            snapshot: The User being answered.

        Returns:
            The Patterns, numbered from 1; none while Pattern sharing
            doesn't work for them.
        """
        if not snapshot.works(Feature.PATTERN_SHARING):
            return []
        patterns = [
            pattern
            for pattern in self._repositories.patterns.list_of_pattern_types(
                snapshot.user.id
            )
            if pattern.state == PatternState.CONTESTED
        ]
        if not patterns:
            return []
        pattern_types = {
            entry.pattern_type.id: entry.pattern_type
            for entry in self._pattern_catalog.catalog()
        }
        known = [
            pattern for pattern in patterns if pattern.pattern_type_id in pattern_types
        ]
        return [
            ContestedPattern(number, pattern, pattern_types[pattern.pattern_type_id])
            for number, pattern in enumerate(known, start=1)
        ]

    def record_if_shared(
        self,
        snapshot: UserSnapshot,
        to_share: PatternToShare,
        texts: Sequence[str],
        via: ShareVia,
        conversation_id: UUID | None,
    ) -> bool:
        """Check whether a sent message shared the Pattern, and record it if so.

        One small model call, on the Check-in model, without thinking where
        the model can do without, reads
        the message. Only when it says the Pattern was told does the Pattern
        move to shared, with the move logged and its Prediction kept. It
        never raises: a failed or unreadable check counts as not shared, so
        the Pattern stays ready.

        Args:
            snapshot: The User the message went to.
            to_share: The Pattern the message was to share.
            texts: The message's texts, in order.
            via: Whether it went as a reply in chat or as a Check-in.
            conversation_id: The Conversation it was said in; None for a
                Check-in.

        Returns:
            True if the Pattern is now shared.
        """
        model = snapshot.settings.get(CHECK_IN_MODEL)
        try:
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.PATTERN_SHARED_CHECK,
                model=model,
                thinking=thinking_for_model(snapshot.settings, model, wanted=False),
                instructions=SHARED_CHECK_PROMPT,
                history=[
                    ChatLine(
                        role=ChatRole.USER,
                        text=describe_message_for_shared_check(to_share, texts),
                    )
                ],
            )
            check = read_shared_check(answer)
            if check is None or not check.shared:
                return False
            return self._record_shared(snapshot, to_share, check, via, conversation_id)
        except Exception:
            logger.exception("Could not check or record a shared Pattern")
            return False

    def settle_reactions(self, snapshot: UserSnapshot, conversation_id: UUID) -> None:
        """Make contested each shared Pattern the User pushed back on.

        Runs when a Conversation ends, after the tagging step saved how the
        User took the Patterns they were told. Every shared Pattern with a
        push-back kept is looked at, whichever Conversation it was read
        from, so one missed by a failed run is caught by the next. The
        User is locked, like scoring, and the move is logged with the
        Pattern's score, which counts its reactions.

        Args:
            snapshot: The User whose Conversation it was.
            conversation_id: The ended Conversation.
        """
        user, settings = snapshot.user, snapshot.settings
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user.id)
            repositories = transaction.repositories
            reactions = repositories.patterns.list_reactions(user.id)
            pushed_back_ids = {
                reaction.pattern_id
                for reaction in reactions
                if reaction.reaction == PatternReaction.PUSHED_BACK
            }
            rejected = [
                pattern
                for pattern in repositories.patterns.list_of_pattern_types(user.id)
                if pattern.id in pushed_back_ids
                and pattern.state == PatternState.SHARED
            ]
            if not rejected:
                return
            now = self._clock.now()
            today = users_today(user.time_zone, now)
            numbers = scoring_numbers(settings)
            sign_strengths = sign_strengths_of(
                entry.pattern_type for entry in self._pattern_catalog.catalog()
            )
            observations = repositories.observations.list_for_user(user.id)
            changed, moves = [], []
            for pattern in rejected:
                scored = score_observations(
                    without_narrowing(
                        observations_of(pattern.pattern_type_id, observations)
                    ),
                    sign_strengths,
                    numbers,
                    today,
                )
                its_reactions = [
                    reaction
                    for reaction in reactions
                    if reaction.pattern_id == pattern.id
                ]
                with_reactions = replace(
                    scored,
                    points=scored.points
                    + reaction_points(its_reactions, numbers, today, user.time_zone),
                )
                moves.append(
                    logged_move(
                        pattern,
                        pattern.state,
                        PatternState.CONTESTED,
                        with_reactions,
                        PatternMoveCause.USER_REACTED,
                        conversation_id,
                        now,
                    )
                )
                changed.append(
                    replace(pattern, state=PatternState.CONTESTED, updated_at=now)
                )
            repositories.patterns.save_moves([], changed, [], moves)

    def _ready_longest(
        self, snapshot: UserSnapshot, ready_by: datetime | None
    ) -> PatternToShare | None:
        """Find the User's Pattern ready the longest that may be shared now.

        Nothing more is read for a User with no ready Pattern. The ready
        ones are looked at again first, since they are otherwise judged
        only when a Conversation ends.

        Args:
            snapshot: The User.
            ready_by: Only a Pattern that became ready at or before this
                counts; None for any.

        Returns:
            The Pattern with its quotes; None when none is ready, the
            weekly limit is reached, or none has two quotes from different
            situations.
        """
        user, settings = snapshot.user, snapshot.settings
        patterns = self._repositories.patterns
        if not any(
            pattern.state == PatternState.READY
            for pattern in patterns.list_of_pattern_types(user.id)
        ):
            return None
        shared_this_week = patterns.count_shared_since(
            [user.id], self._clock.now() - SHARES_COUNTED_OVER
        ).get(user.id, 0)
        if not within_weekly_limit(
            shared_this_week, settings.get(PATTERNS_SHARED_PER_WEEK)
        ):
            return None
        still_ready = sorted(
            self._ready_keeper.still_ready(user, settings),
            key=lambda judged: judged.pattern.updated_at,
        )
        for judged in still_ready:
            if ready_by is not None and judged.pattern.updated_at > ready_by:
                continue
            quotes = pick_quotes(judged.observations, judged.pattern_type)
            if len(quotes) >= FEWEST_QUOTES:
                return PatternToShare(
                    pattern=judged.pattern,
                    pattern_type=judged.pattern_type,
                    quotes=quotes,
                    scored=judged.scored,
                )
        return None

    def _last_message_read_as_struggling(self, user_id: UUID) -> bool:
        """Say whether the User's last Message read as struggling.

        Args:
            user_id: The User's ID.

        Returns:
            True when the newest Understanding of their latest Conversation
            found them struggling; False with no Conversation or
            Understanding.
        """
        conversation = self._repositories.conversations.list_latest_for_users(
            [user_id]
        ).get(user_id)
        if conversation is None:
            return False
        understandings = self._repositories.understandings.list_for_conversation(
            conversation.id
        )
        return bool(understandings) and understandings[-1].form.struggling

    def _record_shared(
        self,
        snapshot: UserSnapshot,
        to_share: PatternToShare,
        check: SharedCheck,
        via: ShareVia,
        conversation_id: UUID | None,
    ) -> bool:
        """Move a ready Pattern to shared, with its log entry and Prediction.

        The User is locked and the Pattern read again, so one that stopped
        being ready meanwhile (or was shared by another message) is left
        as it is.

        Args:
            snapshot: The User it was shared with.
            to_share: The Pattern as it was offered.
            check: What the check after the message found.
            via: Whether it went as a reply in chat or as a Check-in.
            conversation_id: The Conversation it was said in; None for a
                Check-in.

        Returns:
            True if it moved to shared.
        """
        user_id = snapshot.user.id
        with self._repositories.transaction() as transaction:
            transaction.lock_user(user_id)
            repositories = transaction.repositories
            pattern = next(
                (
                    pattern
                    for pattern in repositories.patterns.list_of_pattern_types(user_id)
                    if pattern.id == to_share.pattern.id
                    and pattern.state == PatternState.READY
                ),
                None,
            )
            if pattern is None:
                return False
            now = self._clock.now()
            move = logged_move(
                pattern,
                pattern.state,
                PatternState.SHARED,
                to_share.scored,
                CAUSE_OF_SHARING[via],
                conversation_id,
                now,
            )
            shared = replace(
                pattern,
                state=PatternState.SHARED,
                updated_at=now,
                shared_at=now,
                shared_wording=to_share.pattern_type.approved_wording,
            )
            repositories.patterns.save_moves([], [shared], [], [move])
            if check.prediction:
                repositories.patterns.add_prediction(
                    Prediction(
                        id=uuid4(),
                        user_id=user_id,
                        pattern_id=pattern.id,
                        wording=check.prediction,
                        made_at=now,
                        wording_number=FIRST_PREDICTION_WORDING,
                    )
                )
        return True
