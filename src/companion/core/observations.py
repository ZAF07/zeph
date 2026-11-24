import json
import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from companion.core.life_threads import describe_thread, read_text
from companion.core.memory_retrieval import format_day
from companion.core.model_call_log import ModelCallLog
from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    EvidenceKind,
    Feature,
    LifeThread,
    MessageDirection,
    MessageKind,
    ModelStep,
    Observation,
    ObservationDirection,
    PatternSign,
    PatternType,
    Power,
    Relationship,
    SituationMatch,
    SituationSetting,
    SituationTags,
    Stance,
    TaggingShape,
    UserSnapshot,
)
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.platform_settings import (
    PATTERN_TAGGING_MODEL,
    PATTERN_TAGGING_PROMPT,
    PATTERN_TAGGING_THINKING,
)
from companion.core.ports import Clock, Repositories
from companion.core.timing import users_today
from companion.core.transcripts import to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

MOST_PATTERN_TYPES_PER_OBSERVATION = 2
EVENED_OUT_CHARACTERS = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})
SPACES = re.compile(r"\s+")


@dataclass(frozen=True)
class UserText:
    """Something the User wrote in their own words, and when.

    Attributes:
        text: Their words.
        sent_at: When they sent it.
    """

    text: str
    sent_at: datetime


@dataclass(frozen=True)
class TaggingContext:
    """What the Observations a tagging answer wrote are checked against.

    Attributes:
        user_id: The User they are about.
        conversation_id: The Conversation they were tagged from.
        pattern_types: The Pattern Types in the catalog now, by ID.
        threads: The Life Threads the model was shown, by number.
        user_texts: What the User wrote in that Conversation, oldest first.
        time_zone: The User's IANA time zone, for the day of each quote.
        now: When they were tagged.
    """

    user_id: UUID
    conversation_id: UUID
    pattern_types: Mapping[str, PatternType]
    threads: Mapping[int, LifeThread]
    user_texts: Sequence[UserText]
    time_zone: str | None
    now: datetime


@dataclass(frozen=True)
class PlannedObservations:
    """The Observations code keeps from a tagging answer, and how many it dropped.

    Attributes:
        kept: The Observations that passed every check, in the order written.
        dropped: How many the model wrote that didn't.
    """

    kept: list[Observation]
    dropped: int


def users_own_texts(messages: Sequence[ConversationMessage]) -> list[UserText]:
    """List what the User wrote in their own words, oldest first.

    A photo's caption is theirs, but its description is the Companion's, so
    only the caption counts. Stickers and other messages have no words of
    theirs.

    Args:
        messages: The Conversation's messages, oldest first.

    Returns:
        Each of their texts and photo captions, with when it was sent.
    """
    texts = []
    for message in messages:
        if message.direction != MessageDirection.INCOMING:
            continue
        if message.kind == MessageKind.TEXT:
            texts.append(UserText(text=message.content, sent_at=message.sent_at))
        elif message.kind == MessageKind.PHOTO:
            texts.extend(
                UserText(text=photo.caption, sent_at=message.sent_at)
                for photo in message.photos
                if photo.caption
            )
    return texts


def even_out(text: str) -> str:
    """Even out spaces and curly quotes, so a quote can be matched word for word.

    Args:
        text: The text.

    Returns:
        It with each run of spaces as one space and curly quotes made
        straight, without spaces around it.
    """
    return SPACES.sub(" ", text.translate(EVENED_OUT_CHARACTERS)).strip()


def find_quoted_text(quote: str, user_texts: Sequence[UserText]) -> UserText | None:
    """Find the User's text a quote is taken from, word for word.

    Args:
        quote: The quote.
        user_texts: What the User wrote, oldest first.

    Returns:
        The first of their texts that holds the whole quote; None if none
        does.
    """
    wanted = even_out(quote)
    return next(
        (user_text for user_text in user_texts if wanted in even_out(user_text.text)),
        None,
    )


def is_situational(tags: SituationTags, matches: Sequence[SituationMatch]) -> bool:
    """Say whether anyone would act the same in an Observation's situation.

    Args:
        tags: The Observation's tags.
        matches: Its Pattern Type's situations where anyone would act the
            same.

    Returns:
        True when the tags fit one of them: for each tag it gives, the
        Observation's value is one of those listed.
    """
    return any(
        all(
            not allowed or value in allowed
            for value, allowed in (
                (tags.relationship, match.relationships),
                (tags.power, match.powers),
                (tags.setting, match.settings),
                (tags.stance, match.stances),
            )
        )
        for match in matches
    )


def read_tagging_answer(answer: str) -> list[Any] | None:
    """Read the Observations the tagging model wrote from its JSON answer.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        The Observations, as the model wrote them; None if it can't be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("observations"), list):
        return None
    observations: list[Any] = parsed["observations"]
    return observations


def read_tag[Tag: StrEnum](
    entry: dict[str, Any], key: str, tags: type[Tag]
) -> tuple[bool, Tag | None]:
    """Read one value the model wrote that must come from a fixed list.

    Args:
        entry: The Observation, as the model wrote it.
        key: The tag's name.
        tags: Its fixed list.

    Returns:
        Whether it is valid, and the tag; None when left empty.
    """
    value = entry.get(key)
    if value is None:
        return True, None
    allowed = {tag.value: tag for tag in tags}
    if not isinstance(value, str) or value not in allowed:
        return False, None
    return True, allowed[value]


def read_tags(entry: dict[str, Any]) -> SituationTags | None:
    """Read the situation tags of one Observation the model wrote.

    Args:
        entry: The Observation, as the model wrote it.

    Returns:
        The tags; None if any of them is not from its list.
    """
    relationship = read_tag(entry, "relationship", Relationship)
    power = read_tag(entry, "power", Power)
    setting = read_tag(entry, "setting", SituationSetting)
    stance = read_tag(entry, "stance", Stance)
    if not all(valid for valid, _ in (relationship, power, setting, stance)):
        return None
    return SituationTags(
        relationship=relationship[1],
        power=power[1],
        setting=setting[1],
        stance=stance[1],
    )


def read_named_pattern_types(
    entry: dict[str, Any], pattern_types: Mapping[str, PatternType]
) -> list[PatternType] | None:
    """Read the one Pattern Type, or two look-alikes, an Observation names.

    Args:
        entry: The Observation, as the model wrote it.
        pattern_types: The Pattern Types in the catalog now, by ID.

    Returns:
        The Pattern Types, the one whose sign it matched first; None unless
        it names one or two different ones that are in the catalog.
    """
    value = entry.get("pattern_types")
    if not isinstance(value, list) or not (
        1 <= len(value) <= MOST_PATTERN_TYPES_PER_OBSERVATION
    ):
        return None
    if len(set(map(str, value))) != len(value):
        return None
    named = [
        pattern_types.get(pattern_type_id)
        for pattern_type_id in value
        if isinstance(pattern_type_id, str)
    ]
    found = [pattern_type for pattern_type in named if pattern_type is not None]
    return found if len(found) == len(value) else None


def read_sign(
    entry: dict[str, Any], pattern_type: PatternType
) -> tuple[ObservationDirection, PatternSign] | None:
    """Read the sign an Observation matched, and whether it counts for or against.

    Args:
        entry: The Observation, as the model wrote it.
        pattern_type: The Pattern Type whose sign it matched.

    Returns:
        The direction and the sign; None unless the sign is one of the
        Pattern Type's signs for, when it is for, or signs against, when it
        is against.
    """
    _, direction = read_tag(entry, "direction", ObservationDirection)
    if direction is None:
        return None
    signs = (
        pattern_type.signs
        if direction == ObservationDirection.FOR
        else pattern_type.signs_against
    )
    sign_id = entry.get("sign")
    sign = next((sign for sign in signs if sign.id == sign_id), None)
    return None if sign is None else (direction, sign)


def read_thread(
    entry: dict[str, Any], threads: Mapping[int, LifeThread]
) -> UUID | None:
    """Read the Life Thread an Observation belongs to.

    Args:
        entry: The Observation, as the model wrote it.
        threads: The Threads it was shown, by number.

    Returns:
        The Thread's ID; None when it names none, or one it wasn't shown.
    """
    number = entry.get("thread")
    if not isinstance(number, int) or isinstance(number, bool):
        return None
    thread = threads.get(number)
    return thread.id if thread else None


def check_observation(entry: Any, context: TaggingContext) -> Observation | None:
    """Check one Observation the model wrote, and turn it into one to keep.

    Args:
        entry: The Observation, as the model wrote it.
        context: What it is checked against.

    Returns:
        The Observation; None if its Pattern Types or sign aren't in the
        catalog, its quote isn't word for word in the User's own texts, a
        tag isn't from its list, or it has no context or who it is about.
    """
    if not isinstance(entry, dict):
        return None
    pattern_types = read_named_pattern_types(entry, context.pattern_types)
    if pattern_types is None:
        return None
    matched = read_sign(entry, pattern_types[0])
    quote = read_text(entry, "quote")
    quoted_text = find_quoted_text(quote, context.user_texts) if quote else None
    tags = read_tags(entry)
    context_line = read_text(entry, "context")
    about = read_text(entry, "about")
    _, evidence_kind = read_tag(entry, "evidence", EvidenceKind)
    if (
        matched is None
        or evidence_kind is None
        or quote is None
        or quoted_text is None
        or tags is None
        or context_line is None
        or about is None
    ):
        return None
    direction, sign = matched
    second = pattern_types[1] if len(pattern_types) > 1 else None
    return Observation(
        id=uuid4(),
        user_id=context.user_id,
        conversation_id=context.conversation_id,
        pattern_type_id=pattern_types[0].id,
        pattern_type_version=pattern_types[0].version,
        sign_id=sign.id,
        direction=direction,
        quote=quote,
        context=context_line,
        day=users_today(context.time_zone, quoted_text.sent_at),
        thread_id=read_thread(entry, context.threads),
        about=about,
        tags=tags,
        evidence_kind=evidence_kind,
        second_pattern_type_id=second.id if second else None,
        second_pattern_type_version=second.version if second else None,
        situational=is_situational(tags, pattern_types[0].anyone_would_when),
        tagged_at=context.now,
    )


def plan_observations(
    entries: list[Any], context: TaggingContext
) -> PlannedObservations:
    """Keep the Observations a tagging answer wrote that pass every check.

    One that repeats an Observation already kept (the same Pattern Type,
    sign and quote) is dropped too.

    Args:
        entries: The Observations, as the model wrote them.
        context: What they are checked against.

    Returns:
        The Observations kept and how many were dropped.
    """
    kept: list[Observation] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in entries:
        observation = check_observation(entry, context)
        if observation is None:
            continue
        key = (
            observation.pattern_type_id,
            observation.sign_id,
            even_out(observation.quote),
        )
        if key in seen:
            continue
        seen.add(key)
        kept.append(observation)
    return PlannedObservations(kept=kept, dropped=len(entries) - len(kept))


def describe_signs(signs: Sequence[PatternSign]) -> str:
    """Write a Pattern Type's signs, one per line.

    Args:
        signs: The signs.

    Returns:
        E.g. "- I2 (strong): Reports agreeing in the moment, then resenting
        it later".
    """
    return "\n".join(
        f"- {sign.id} ({sign.strength.value}): {sign.text}" for sign in signs
    )


def describe_pattern_type(pattern_type: PatternType) -> str:
    """Write one Pattern Type as the tagging model reads it.

    Args:
        pattern_type: The Pattern Type.

    Returns:
        Its ID and name, what it is, its if / then / function, its signs
        for and against, its look-alikes and what anyone would do.
    """
    look_alikes = "\n".join(
        f"- {look_alike.pattern_type_id or look_alike.name}: {look_alike.tells_apart}"
        for look_alike in pattern_type.look_alikes
    )
    return (
        f"{pattern_type.id}: {pattern_type.name}\n"
        f"What it is: {pattern_type.definition}\n"
        f"If: {pattern_type.if_situation}. Then: {pattern_type.then_behaviour}. "
        f"Function: {pattern_type.function}.\n"
        f"Signs for:\n{describe_signs(pattern_type.signs)}\n"
        f"Signs against:\n{describe_signs(pattern_type.signs_against)}\n"
        f"Look-alikes:\n{look_alikes or 'None.'}\n"
        f"What anyone would do: {pattern_type.anyone_would}"
    )


def describe_tag_lists() -> str:
    """Write the fixed lists each tag must come from.

    Returns:
        One line per tag, e.g. "power: above, equal, below".
    """
    lists = (
        ("relationship", Relationship),
        ("power", Power),
        ("setting", SituationSetting),
        ("stance", Stance),
        ("evidence", EvidenceKind),
    )
    return "\n".join(
        f"{name}: {', '.join(tag.value for tag in tags)}" for name, tags in lists
    )


def describe_conversation_to_tag(
    threads: Mapping[int, LifeThread],
    pattern_types: Sequence[PatternType],
    messages: list[ConversationMessage],
    now: datetime,
    time_zone: str | None,
) -> str:
    """Write what the tagging model is given.

    Args:
        threads: The Life Threads the Conversation touched, by number.
        pattern_types: Every Pattern Type in the catalog now.
        messages: The Conversation's messages, oldest first.
        now: The current time.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        Today's date, the Threads, the Pattern Catalog, the tag lists and
        the Conversation.
    """
    thread_lines = "\n".join(
        f"[{number}] {describe_thread(thread, time_zone)}"
        for number, thread in threads.items()
    )
    catalog = "\n\n".join(
        describe_pattern_type(pattern_type) for pattern_type in pattern_types
    )
    return (
        f"Today: {format_day(now, time_zone)}\n\n"
        f"Life Threads this Conversation touched:\n{thread_lines or 'None.'}\n\n"
        f"The Pattern Catalog:\n{catalog}\n\n"
        f"The lists each tag comes from:\n{describe_tag_lists()}\n\n"
        f"The Conversation:\n{to_transcript_lines(messages, time_zone)}"
    )


class PatternTagger:
    """Tags a User's Observations when a Conversation ends, after its Life Threads.

    The model reads the Conversation into the Pattern Catalog; code keeps
    only the Observations that pass its checks. Nothing reaches a reply.
    """

    def __init__(
        self,
        repositories: Repositories,
        chat_model: UsageRecordingChatModel,
        model_call_log: ModelCallLog,
        clock: Clock,
    ) -> None:
        """Set up the tagger.

        Args:
            repositories: Where the Pattern Catalog and Observations are
                stored.
            chat_model: Writes the Observations and records the tokens used.
            model_call_log: Records how many were tagged and dropped.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._model_call_log = model_call_log
        self._clock = clock

    def tag_from(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        messages: list[ConversationMessage],
        touched: Sequence[LifeThread],
    ) -> None:
        """Tag and keep the Observations in an ended Conversation.

        Runs only while Pattern noticing works for the User and they wrote
        something in their own words. An unreadable answer is asked again
        once; if it is still unreadable nothing is kept. How many were
        tagged and dropped goes into the Model Call Log, never their words.

        Args:
            snapshot: The User whose Conversation it was; User Memory works
                for them.
            conversation_id: The ended Conversation.
            messages: Its messages, oldest first.
            touched: The Life Threads the Conversation started, changed or
                brought up.
        """
        if not snapshot.works(Feature.PATTERN_NOTICING):
            return
        user_texts = users_own_texts(messages)
        pattern_types = [
            entry.pattern_type
            for entry in PatternCatalogService(
                self._repositories.pattern_catalog
            ).catalog()
        ]
        if not user_texts or not pattern_types:
            return
        threads = dict(enumerate(touched, start=1))
        now = self._clock.now()
        time_zone = snapshot.user.time_zone
        entries = self._ask(
            snapshot,
            describe_conversation_to_tag(
                threads, pattern_types, messages, now, time_zone
            ),
        )
        if entries is None:
            logger.warning("Pattern tagging gave no readable answer")
            return
        planned = plan_observations(
            entries,
            TaggingContext(
                user_id=snapshot.user.id,
                conversation_id=conversation_id,
                pattern_types={
                    pattern_type.id: pattern_type for pattern_type in pattern_types
                },
                threads=threads,
                user_texts=user_texts,
                time_zone=time_zone,
                now=now,
            ),
        )
        self._model_call_log.record_tagging_shape(
            snapshot, TaggingShape(tagged=len(entries), dropped=planned.dropped)
        )
        self._repositories.observations.add_many(planned.kept)

    def _ask(self, snapshot: UserSnapshot, description: str) -> list[Any] | None:
        """Ask the model for the Observations, once more if it can't be read.

        Args:
            snapshot: The User whose Conversation it was.
            description: The Threads, catalog, tag lists and Conversation.

        Returns:
            The Observations it wrote, or None if both answers were
            unreadable.
        """
        settings = snapshot.settings
        for _ in range(2):
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.PATTERN_TAGGING,
                model=settings.get(PATTERN_TAGGING_MODEL),
                thinking=settings.get(PATTERN_TAGGING_THINKING),
                instructions=settings.get(PATTERN_TAGGING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
            entries = read_tagging_answer(answer)
            if entries is not None:
                return entries
        return None
