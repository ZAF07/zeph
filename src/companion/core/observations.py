import hashlib
import json
import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from companion.core.curiosities import format_date
from companion.core.life_threads import describe_thread, read_text
from companion.core.memory_retrieval import format_day, summary_line
from companion.core.model_call_log import ModelCallLog
from companion.core.models import (
    AIMS_WRITTEN_BY_CODE,
    OUTCOMES_READ_BY_THE_MODEL,
    CatalogPattern,
    ChatLine,
    ChatRole,
    ConversationMessage,
    CuriosityAim,
    DaySummary,
    DeletedQuote,
    EvidenceKind,
    ExcludedEvidence,
    ExclusionFlag,
    Feature,
    LifeThread,
    MessageDirection,
    MessageKind,
    ModelStep,
    Observation,
    ObservationDirection,
    PatternReaction,
    PatternSign,
    PatternState,
    PatternType,
    Power,
    Prediction,
    PredictionOutcome,
    ReactionToPattern,
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
    PATTERN_EXCLUSION_SUMMARY_DAYS,
    PATTERN_RULED_OUT_TOPICS,
    PATTERN_TAGGING_MODEL,
    PATTERN_TAGGING_PROMPT,
    PATTERN_TAGGING_THINKING,
    thinking_to_use,
)
from companion.core.ports import Clock, Repositories
from companion.core.timing import users_today
from companion.core.transcripts import to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

MOST_PATTERN_TYPES_PER_OBSERVATION = 2
EVENED_OUT_CHARACTERS = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})
WHITESPACE_RUNS = re.compile(r"\s+")
STATES_OF_A_PATTERN_TOLD = frozenset(
    {PatternState.SHARED, PatternState.CONFIRMED, PatternState.CONTESTED}
)


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
        thought_experiment_numbers: The numbers of the Thought Experiments
            put to the User in that Conversation, as the model was shown
            them; an Observation answering one is a "what if" answer.
        ruled_out_topics: The Admin-set ruled-out topics, in lower case.
        ignored_pattern_type_ids: The Pattern Types with an exclusion that
            applies to the User now and whose evidence is ignored.
        not_gathered_pattern_type_ids: The Pattern Types of the Patterns
            the User disagreed with, while they have gathering on those
            turned off; no Observation naming one is kept.
        deleted_quotes: The records of the quotes the User deleted from
            that Conversation; none is kept again.
        never_again_pattern_type_ids: The Pattern Types of the Patterns
            the User deleted after disagreeing or after they didn't hold
            up; no Observation naming one is kept.
    """

    user_id: UUID
    conversation_id: UUID
    pattern_types: Mapping[str, PatternType]
    threads: Mapping[int, LifeThread]
    user_texts: Sequence[UserText]
    time_zone: str | None
    now: datetime
    thought_experiment_numbers: frozenset[int] = frozenset()
    ruled_out_topics: frozenset[str] = frozenset()
    ignored_pattern_type_ids: frozenset[str] = frozenset()
    not_gathered_pattern_type_ids: frozenset[str] = frozenset()
    deleted_quotes: Sequence[DeletedQuote] = ()
    never_again_pattern_type_ids: frozenset[str] = frozenset()


class DropReason(StrEnum):
    """Why code dropped an Observation the tagging model wrote."""

    NOT_AN_OBSERVATION = "not an Observation"
    UNKNOWN_PATTERN_TYPE = "Pattern Type not in the catalog"
    UNKNOWN_SIGN = "sign not among that Pattern Type's signs for or against"
    QUOTE_NOT_WORD_FOR_WORD = "quote not word for word in the User's own texts"
    TAG_OFF_ITS_LIST = "a tag or the kind of evidence not from its list"
    MISSING_DETAILS = "no context line or no one it is about"
    REPEAT = "repeats one already kept"
    NOT_GATHERED = "a Pattern they disagreed with, with gathering turned off"
    DELETED_BY_USER = "a quote the User deleted"
    NEVER_AGAIN = "a Pattern they deleted after disagreeing or it didn't hold up"


@dataclass(frozen=True)
class DroppedEntry:
    """An Observation the tagging model wrote that code dropped, and why.

    Attributes:
        entry: The Observation, as the model wrote it.
        reason: Why it was dropped.
    """

    entry: Any
    reason: DropReason


@dataclass(frozen=True)
class LifeNow:
    """What is going on in a User's life now, for telling which exclusions apply.

    Attributes:
        open_threads: Their open Life Threads.
        summaries: Their latest Day Summaries, newest first.
    """

    open_threads: Sequence[LifeThread] = ()
    summaries: Sequence[DaySummary] = ()


@dataclass(frozen=True)
class PlannedObservations:
    """The Observations code keeps from a tagging answer, and those it dropped.

    Attributes:
        kept: The Observations that passed every check, in the order written.
        dropped_entries: Those the model wrote that didn't, with why.
    """

    kept: list[Observation]
    dropped_entries: list[DroppedEntry]

    @property
    def dropped(self) -> int:
        """Count the Observations dropped.

        Returns:
            How many the model wrote that didn't pass.
        """
        return len(self.dropped_entries)


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
    return WHITESPACE_RUNS.sub(" ", text.translate(EVENED_OUT_CHARACTERS)).strip()


@dataclass(frozen=True)
class QuoteSpan:
    """Where a quote sits in one of the User's own texts.

    Attributes:
        text: The text it is in.
        text_hash: A hash of that text, evened out.
        start: Where the quote starts in the text, evened out.
        end: Where it ends.
    """

    text: UserText
    text_hash: str
    start: int
    end: int


def find_quote_span(quote: str, user_texts: Sequence[UserText]) -> QuoteSpan | None:
    """Find where a quote sits in the User's own texts, word for word.

    Args:
        quote: The quote.
        user_texts: What the User wrote, oldest first.

    Returns:
        The first of their texts that holds the whole quote, starting and
        ending on whole words, with where the quote sits in it; None if
        none does.
    """
    whole_words = re.compile(rf"(?<!\w){re.escape(even_out(quote))}(?!\w)")
    for user_text in user_texts:
        evened_out = even_out(user_text.text)
        found = whole_words.search(evened_out)
        if found:
            return QuoteSpan(
                text=user_text,
                text_hash=hashlib.sha256(evened_out.encode()).hexdigest(),
                start=found.start(),
                end=found.end(),
            )
    return None


def was_deleted(span: QuoteSpan, deleted: Sequence[DeletedQuote]) -> bool:
    """Say whether a quote takes in words the User deleted before.

    Args:
        span: Where the quote sits in the User's text.
        deleted: The records of quotes they deleted from that Conversation.

    Returns:
        True when it is in the same text as a deleted quote and shares
        any of its words, so a longer or shorter quote counts too.
    """
    return any(
        record.text_hash == span.text_hash
        and record.span_start < span.end
        and span.start < record.span_end
        for record in deleted
    )


def deleted_quotes_of(
    observations: Sequence[Observation],
    texts_by_conversation: Mapping[UUID, Sequence[UserText]],
    now: datetime,
) -> list[DeletedQuote]:
    """Write the records that say a User deleted some kept quotes.

    Args:
        observations: The Observations being deleted.
        texts_by_conversation: What the User wrote in each of their
            Conversations whose messages are still kept, oldest first.
        now: When they are deleted.

    Returns:
        One record per Observation whose quote is still in a kept text,
        with where it sits in place of its words. A quote whose messages
        Message Retention deleted needs none: its Conversation can't be
        tagged again.
    """
    records = []
    for observation in observations:
        span = find_quote_span(
            observation.quote,
            texts_by_conversation.get(observation.conversation_id, ()),
        )
        if span is None:
            continue
        records.append(
            DeletedQuote(
                user_id=observation.user_id,
                conversation_id=observation.conversation_id,
                text_hash=span.text_hash,
                span_start=span.start,
                span_end=span.end,
                deleted_at=now,
            )
        )
    return records


def find_quoted_text(quote: str, user_texts: Sequence[UserText]) -> UserText | None:
    """Find the User's text a quote is taken from, word for word.

    Args:
        quote: The quote.
        user_texts: What the User wrote, oldest first.

    Returns:
        The first of their texts that holds the whole quote, starting and
        ending on whole words; None if none does.
    """
    span = find_quote_span(quote, user_texts)
    return span.text if span else None


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


def read_settled_answer(answer: str) -> list[Any]:
    """Read the unclear stories the tagging model settled from its JSON answer.

    Args:
        answer: The model's answer, already readable for its Observations.

    Returns:
        What it settled, as the model wrote it; empty when it settled none.
    """
    start, end = answer.find("{"), answer.rfind("}")
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return []
    settled = parsed.get("settled") if isinstance(parsed, dict) else None
    return settled if isinstance(settled, list) else []


def read_reactions_answer(answer: str) -> list[Any]:
    """Read how the tagging model says the User took Patterns they were told.

    Args:
        answer: The model's answer, already readable for its Observations.

    Returns:
        The reactions, as the model wrote them; empty when it named none.
    """
    start, end = answer.find("{"), answer.rfind("}")
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return []
    reactions = parsed.get("reactions") if isinstance(parsed, dict) else None
    return reactions if isinstance(reactions, list) else []


def plan_reactions(
    entries: Sequence[Any],
    told: Mapping[int, CatalogPattern],
    conversation_id: UUID,
    now: datetime,
) -> list[ReactionToPattern]:
    """Keep the reactions the tagging model read that name a Pattern it was shown.

    Args:
        entries: The reactions, as the model wrote them.
        told: The Patterns the User was told, by the number the model was
            shown.
        conversation_id: The Conversation they were read from.
        now: When they were read.

    Returns:
        One reaction per Pattern, the first the model wrote for it; an
        unknown number or a reaction off its list is left out.
    """
    kept: dict[UUID, ReactionToPattern] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        number = entry.get("pattern")
        pattern = (
            told.get(number)
            if isinstance(number, int) and not isinstance(number, bool)
            else None
        )
        reaction = read_choice(entry, "reaction", PatternReaction)
        if pattern is None or reaction is None or pattern.id in kept:
            continue
        kept[pattern.id] = ReactionToPattern(
            id=uuid4(),
            user_id=pattern.user_id,
            pattern_id=pattern.id,
            reaction=reaction,
            conversation_id=conversation_id,
            reacted_at=now,
        )
    return list(kept.values())


def read_prediction_outcomes_answer(answer: str) -> list[Any]:
    """Read how the tagging model says the User's Predictions went.

    Args:
        answer: The model's answer, already readable for its Observations.

    Returns:
        The outcomes, as the model wrote them; empty when it named none.
    """
    start, end = answer.find("{"), answer.rfind("}")
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return []
    outcomes = parsed.get("prediction_outcomes") if isinstance(parsed, dict) else None
    return outcomes if isinstance(outcomes, list) else []


def plan_prediction_outcomes(
    entries: Sequence[Any],
    open_predictions: Mapping[int, Prediction],
    conversation_id: UUID,
    now: datetime,
) -> list[Prediction]:
    """Keep the outcomes the tagging model read for a Prediction it was shown.

    Args:
        entries: The outcomes, as the model wrote them.
        open_predictions: The Predictions still open, by the number the
            model was shown.
        conversation_id: The Conversation the User said them in.
        now: When they were read.

    Returns:
        Each Prediction once with its outcome, the first the model wrote
        for it; an unknown number or an outcome off the model's list is
        left out.
    """
    kept: dict[UUID, Prediction] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        number = entry.get("prediction")
        prediction = (
            open_predictions.get(number)
            if isinstance(number, int) and not isinstance(number, bool)
            else None
        )
        outcome = read_choice(entry, "outcome", PredictionOutcome)
        if (
            prediction is None
            or outcome not in OUTCOMES_READ_BY_THE_MODEL
            or prediction.id in kept
        ):
            continue
        kept[prediction.id] = replace(
            prediction,
            outcome=outcome,
            outcome_at=now,
            outcome_conversation_id=conversation_id,
        )
    return list(kept.values())


def describe_predictions_given(
    predictions: Mapping[int, Prediction], time_zone: str | None
) -> str:
    """Write the open Predictions, as the tagging model reads them.

    Args:
        predictions: The Predictions, by number.
        time_zone: The User's IANA time zone, for the day each was given.

    Returns:
        One numbered line per Prediction with the day it was given and its
        words; "None." with none.
    """
    return (
        "\n".join(
            f"[{number}] (given {format_day(prediction.made_at, time_zone)}) "
            f"{prediction.wording}"
            for number, prediction in predictions.items()
        )
        or "None."
    )


def not_gathered_pattern_types(
    told: Sequence[CatalogPattern],
    reactions: Sequence[ReactionToPattern],
    gathering_enabled: bool,
) -> frozenset[str]:
    """Find the Pattern Types no new Observation is kept for.

    Args:
        told: The Patterns the User was told.
        reactions: How they took them in the Conversation being tagged.
        gathering_enabled: The User's own switch for noting evidence on a
            Pattern they disagreed with.

    Returns:
        Empty while their switch is on; with it off, the Pattern Types of
        the Patterns they disagreed with, before or in this Conversation.
    """
    if gathering_enabled:
        return frozenset()
    pushed_back_ids = {
        reaction.pattern_id
        for reaction in reactions
        if reaction.reaction == PatternReaction.PUSHED_BACK
    }
    return frozenset(
        pattern.pattern_type_id
        for pattern in told
        if pattern.state == PatternState.CONTESTED or pattern.id in pushed_back_ids
    )


def reactions_to_keep(
    reactions: Sequence[ReactionToPattern],
    told: Sequence[CatalogPattern],
    gathering_enabled: bool,
) -> list[ReactionToPattern]:
    """Leave out what would be gathering on a Pattern the User disagreed with.

    Args:
        reactions: How they took the Patterns in the Conversation being
            tagged.
        told: The Patterns the User was told.
        gathering_enabled: The User's own switch for noting evidence on a
            Pattern they disagreed with.

    Returns:
        Every reaction while their switch is on; with it off, a reaction to
        a contested Pattern is kept only when they pushed back again.
    """
    if gathering_enabled:
        return list(reactions)
    contested_ids = {
        pattern.id for pattern in told if pattern.state == PatternState.CONTESTED
    }
    return [
        reaction
        for reaction in reactions
        if reaction.pattern_id not in contested_ids
        or reaction.reaction == PatternReaction.PUSHED_BACK
    ]


def names_one_of(observation: Observation, pattern_type_ids: frozenset[str]) -> bool:
    """Say whether an Observation names one of some Pattern Types.

    Args:
        observation: The Observation.
        pattern_type_ids: The Pattern Types' IDs.

    Returns:
        True when its first or second Pattern Type is among them.
    """
    return (
        observation.pattern_type_id in pattern_type_ids
        or observation.second_pattern_type_id in pattern_type_ids
    )


def describe_patterns_told(
    told: Mapping[int, CatalogPattern], pattern_types: Mapping[str, PatternType]
) -> str:
    """Write the Patterns the User was told, as the tagging model reads them.

    Args:
        told: The Patterns, by number.
        pattern_types: The Pattern Types in the catalog now, by ID.

    Returns:
        One numbered line per Pattern with the words it was told in;
        "None." with none.
    """
    return (
        "\n".join(
            f"[{number}] {pattern_types[pattern.pattern_type_id].approved_wording}"
            for number, pattern in told.items()
        )
        or "None."
    )


def plan_settled(
    entries: Sequence[Any],
    unclear: Mapping[int, Observation],
    pattern_types: Mapping[str, PatternType],
) -> list[Observation]:
    """Make clear the unclear Observations the tagging model settled.

    Code keeps a settling only when it names one of the Observation's two
    Pattern Types and a sign of that Pattern Type in the Observation's
    direction. Whether anyone would act the same is worked out again for
    the Pattern Type named.

    Args:
        entries: What the model settled, as it wrote it.
        unclear: The unclear Observations it was shown, by number.
        pattern_types: The Pattern Types in the catalog now, by ID.

    Returns:
        The Observations made clear, each once.
    """
    settled: dict[UUID, Observation] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        number = entry.get("unclear")
        observation = (
            unclear.get(number)
            if isinstance(number, int) and not isinstance(number, bool)
            else None
        )
        pattern_type = pattern_types.get(entry.get("pattern_type") or "")
        if (
            observation is None
            or observation.id in settled
            or pattern_type is None
            or pattern_type.id
            not in (observation.pattern_type_id, observation.second_pattern_type_id)
        ):
            continue
        signs = (
            pattern_type.signs
            if observation.direction == ObservationDirection.FOR
            else pattern_type.signs_against
        )
        if entry.get("sign") not in {sign.id for sign in signs}:
            continue
        settled[observation.id] = replace(
            observation,
            pattern_type_id=pattern_type.id,
            pattern_type_version=pattern_type.version,
            sign_id=entry["sign"],
            second_pattern_type_id=None,
            second_pattern_type_version=None,
            situational=is_situational(
                observation.tags, pattern_type.anyone_would_when
            ),
        )
    return list(settled.values())


def describe_unclear_asked(unclear: Mapping[int, Observation]) -> str:
    """Write the unclear stories Zeph asked about, as the tagging model reads them.

    Args:
        unclear: The unclear Observations, by number.

    Returns:
        One line per story with its quote, who it was about, its day, its
        context line and its two Pattern Types; "None." with none.
    """
    return (
        "\n".join(
            f'[{number}] "{observation.quote}" ({observation.about}, '
            f"{format_date(observation.day)}; {observation.context}): "
            f"{observation.pattern_type_id} or {observation.second_pattern_type_id}"
            for number, observation in unclear.items()
        )
        or "None."
    )


def describe_thought_experiments_asked(questions: Mapping[int, str]) -> str:
    """Write the Thought Experiments put to the User, as the tagging model reads them.

    Args:
        questions: The questions that put each one to the User, as asked,
            by number.

    Returns:
        One numbered line per question; "None." with none.
    """
    return (
        "\n".join(f"[{number}] {question}" for number, question in questions.items())
        or "None."
    )


def read_choice[Choice: StrEnum](
    entry: dict[str, Any], key: str, choices: type[Choice]
) -> Choice | None:
    """Read one value the model wrote that must come from a fixed list.

    Args:
        entry: The Observation, as the model wrote it.
        key: The value's name.
        choices: Its fixed list.

    Returns:
        The value; None when it is left empty or not from the list.
    """
    value = entry.get(key)
    allowed = {choice.value: choice for choice in choices}
    return allowed.get(value) if isinstance(value, str) else None


def read_tags(entry: dict[str, Any]) -> SituationTags | None:
    """Read the situation tags of one Observation the model wrote.

    A tag may be left empty when there is no one else or it isn't clear.

    Args:
        entry: The Observation, as the model wrote it.

    Returns:
        The tags; None if any of them is given but not from its list.
    """
    tag_lists: tuple[tuple[str, type[StrEnum]], ...] = (
        ("relationship", Relationship),
        ("power", Power),
        ("setting", SituationSetting),
        ("stance", Stance),
    )
    if any(
        entry.get(key) is not None and read_choice(entry, key, tags) is None
        for key, tags in tag_lists
    ):
        return None
    return SituationTags(
        relationship=read_choice(entry, "relationship", Relationship),
        power=read_choice(entry, "power", Power),
        setting=read_choice(entry, "setting", SituationSetting),
        stance=read_choice(entry, "stance", Stance),
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
    direction = read_choice(entry, "direction", ObservationDirection)
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


def read_ruled_out_topic(
    entry: dict[str, Any], ruled_out_topics: frozenset[str]
) -> str | None:
    """Read the ruled-out topic an Observation the model wrote is about.

    Args:
        entry: The Observation, as the model wrote it.
        ruled_out_topics: The Admin-set ruled-out topics, in lower case.

    Returns:
        The topic, in lower case, when it is on the list; None otherwise.
    """
    topic = read_text(entry, "ruled_out_topic")
    if topic is None or topic.casefold() not in ruled_out_topics:
        return None
    return topic.casefold()


def read_exclusions_answer(answer: str) -> list[Any]:
    """Read the exclusions the tagging model says apply from its JSON answer.

    Args:
        answer: The model's answer, already readable for its Observations.

    Returns:
        The exclusions, as the model wrote them; empty when it named none.
    """
    start, end = answer.find("{"), answer.rfind("}")
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return []
    exclusions = parsed.get("exclusions") if isinstance(parsed, dict) else None
    return exclusions if isinstance(exclusions, list) else []


def plan_exclusion_flags(
    entries: Sequence[Any],
    pattern_types: Mapping[str, PatternType],
    user_id: UUID,
    now: datetime,
) -> list[ExclusionFlag]:
    """Keep the exclusions the tagging model named that the catalog holds.

    Args:
        entries: The exclusions, as the model wrote them.
        pattern_types: The Pattern Types in the catalog now, by ID.
        user_id: The User they apply to.
        now: When they were flagged.

    Returns:
        One flag per Pattern Type and exclusion named, when that Pattern
        Type lists that exclusion (any case); the rest are left out.
    """
    flags: dict[tuple[str, str], ExclusionFlag] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        pattern_type = pattern_types.get(entry.get("pattern_type") or "")
        named = read_text(entry, "exclusion")
        if pattern_type is None or named is None:
            continue
        for exclusion in pattern_type.exclusions:
            if exclusion.text.casefold() == named.casefold():
                flags[(pattern_type.id, exclusion.text)] = ExclusionFlag(
                    user_id=user_id,
                    pattern_type_id=pattern_type.id,
                    exclusion=exclusion.text,
                    evidence=exclusion.evidence,
                    flagged_at=now,
                )
    return list(flags.values())


def ignored_pattern_types(flags: Sequence[ExclusionFlag]) -> frozenset[str]:
    """Find the Pattern Types whose evidence is ignored while a flag applies.

    Args:
        flags: The exclusions that apply to a User now.

    Returns:
        The IDs of the Pattern Types with a flag whose evidence is ignored.
    """
    return frozenset(
        flag.pattern_type_id
        for flag in flags
        if flag.evidence == ExcludedEvidence.IGNORED
    )


def check_observation(entry: Any, context: TaggingContext) -> Observation | DropReason:
    """Check one Observation the model wrote, and turn it into one to keep.

    Args:
        entry: The Observation, as the model wrote it.
        context: What it is checked against.

    Returns:
        The Observation; or why it is dropped: its Pattern Types or sign
        aren't in the catalog, its quote isn't word for word in the User's
        own texts, a tag or its kind of evidence isn't from its list, or it
        has no context or who it is about, or it names a Pattern Type the
        User disagreed with while they have gathering turned off, or one
        of a Pattern they deleted after disagreeing or after it didn't
        hold up, or its quote takes in words the User deleted. One that
        names a Thought
        Experiment put to the User in the Conversation is a "what if"
        answer, whatever kind the model wrote. A ruled-out topic is kept
        only when it is on the Admin-set list. It is excluded when an
        exclusion whose evidence is ignored applies to one of its Pattern
        Types now.
    """
    if not isinstance(entry, dict):
        return DropReason.NOT_AN_OBSERVATION
    pattern_types = read_named_pattern_types(entry, context.pattern_types)
    if pattern_types is None:
        return DropReason.UNKNOWN_PATTERN_TYPE
    if any(
        pattern_type.id in context.never_again_pattern_type_ids
        for pattern_type in pattern_types
    ):
        return DropReason.NEVER_AGAIN
    if any(
        pattern_type.id in context.not_gathered_pattern_type_ids
        for pattern_type in pattern_types
    ):
        return DropReason.NOT_GATHERED
    matched = read_sign(entry, pattern_types[0])
    if matched is None:
        return DropReason.UNKNOWN_SIGN
    quote = read_text(entry, "quote")
    span = find_quote_span(quote, context.user_texts) if quote else None
    if quote is None or span is None:
        return DropReason.QUOTE_NOT_WORD_FOR_WORD
    if was_deleted(span, context.deleted_quotes):
        return DropReason.DELETED_BY_USER
    tags = read_tags(entry)
    evidence_kind = read_choice(entry, "evidence", EvidenceKind)
    if tags is None or evidence_kind is None:
        return DropReason.TAG_OFF_ITS_LIST
    context_line = read_text(entry, "context")
    about = read_text(entry, "about")
    if context_line is None or about is None:
        return DropReason.MISSING_DETAILS
    answered = entry.get("thought_experiment")
    if (
        isinstance(answered, int)
        and not isinstance(answered, bool)
        and answered in context.thought_experiment_numbers
    ):
        evidence_kind = EvidenceKind.WHAT_IF_ANSWER
    direction, sign = matched
    second = pattern_types[1] if len(pattern_types) > 1 else None
    ruled_out_topic = read_ruled_out_topic(entry, context.ruled_out_topics)
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
        day=users_today(context.time_zone, span.text.sent_at),
        thread_id=read_thread(entry, context.threads),
        about=about,
        tags=tags,
        evidence_kind=evidence_kind,
        second_pattern_type_id=second.id if second else None,
        second_pattern_type_version=second.version if second else None,
        situational=is_situational(tags, pattern_types[0].anyone_would_when),
        tagged_at=context.now,
        excluded=any(
            pattern_type.id in context.ignored_pattern_type_ids
            for pattern_type in pattern_types
        ),
        ruled_out_topic=ruled_out_topic,
        raised_by_user=ruled_out_topic is not None
        and entry.get("raised_by_user") is True,
    )


def repeat_key(observation: Observation) -> tuple[str, str, str]:
    """Say what makes an Observation a repeat of another from its Conversation.

    Args:
        observation: The Observation.

    Returns:
        Its Pattern Type, sign and quote, evened out.
    """
    return (
        observation.pattern_type_id,
        observation.sign_id,
        even_out(observation.quote),
    )


def may_keep_observations(snapshot: UserSnapshot) -> bool:
    """Say whether Zeph may keep a User's words as Observations.

    Args:
        snapshot: The User.

    Returns:
        True while Pattern noticing works for them and they have pressed
        "Got it" on the notice saying so.
    """
    return (
        snapshot.works(Feature.PATTERN_NOTICING)
        and snapshot.user.pattern_noticing_told_at is not None
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
        The Observations kept and those dropped, with why.
    """
    kept: list[Observation] = []
    dropped: list[DroppedEntry] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in entries:
        observation = check_observation(entry, context)
        if isinstance(observation, DropReason):
            dropped.append(DroppedEntry(entry, observation))
            continue
        key = repeat_key(observation)
        if key in seen:
            dropped.append(DroppedEntry(entry, DropReason.REPEAT))
            continue
        seen.add(key)
        kept.append(observation)
    return PlannedObservations(kept=kept, dropped_entries=dropped)


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


def describe_exclusions(pattern_type: PatternType) -> str:
    """Write a Pattern Type's exclusions on one line, as the tagging model reads them.

    Args:
        pattern_type: The Pattern Type.

    Returns:
        E.g. "Exclusions: Active relationship crisis; Grief".
    """
    exclusions = "; ".join(exclusion.text for exclusion in pattern_type.exclusions)
    return f"Exclusions: {exclusions or 'none'}"


def describe_life_now(life_now: LifeNow, time_zone: str | None) -> str:
    """Write what is going on in a User's life now.

    Args:
        life_now: Their open Life Threads and latest Day Summaries.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        The open Threads, one per line, then the Day Summaries, newest
        first.
    """
    threads = "\n".join(
        f"- {describe_thread(thread, time_zone)}" for thread in life_now.open_threads
    )
    summaries = "\n".join(summary_line(summary) for summary in life_now.summaries)
    return (
        f"Their open Life Threads:\n{threads or 'None.'}\n\n"
        f"Their latest Day Summaries, newest first:\n{summaries or 'None.'}"
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
    unclear: Mapping[int, Observation] | None = None,
    thought_experiments: Mapping[int, str] | None = None,
    life_now: LifeNow | None = None,
    ruled_out_topics: Sequence[str] = (),
    told: Mapping[int, CatalogPattern] | None = None,
    predictions: Mapping[int, Prediction] | None = None,
) -> str:
    """Write what the tagging model is given.

    Args:
        threads: The Life Threads the Conversation touched, by number.
        pattern_types: Every Pattern Type in the catalog now.
        messages: The Conversation's messages, oldest first.
        now: The current time.
        time_zone: The User's IANA time zone, for the days.
        unclear: The unclear stories Zeph asked about in this Conversation,
            by number; None or empty with none.
        thought_experiments: The questions that put a Thought Experiment to
            the User in this Conversation, as asked, by number; None or
            empty with none.
        life_now: Their open Life Threads and latest Day Summaries; None
            when a past Conversation is tagged again.
        ruled_out_topics: The Admin-set ruled-out topics.
        told: The Patterns Zeph has told the User, by number; None or
            empty with none.
        predictions: The Predictions Zeph gave them that are still open,
            by number; None or empty with none.

    Returns:
        Today's date, the Threads, the Pattern Catalog with each Pattern
        Type's exclusions, the tag lists, the unclear stories asked about,
        the Thought Experiments put to them, what is going on in their life
        now, the ruled-out topics, the Patterns they were told, the open
        Predictions and the Conversation.
    """
    thread_lines = "\n".join(
        f"[{number}] {describe_thread(thread, time_zone)}"
        for number, thread in threads.items()
    )
    catalog = "\n\n".join(
        f"{describe_pattern_type(pattern_type)}\n{describe_exclusions(pattern_type)}"
        for pattern_type in pattern_types
    )
    types_by_id = {pattern_type.id: pattern_type for pattern_type in pattern_types}
    return (
        f"Today: {format_day(now, time_zone)}\n\n"
        f"Life Threads this Conversation touched:\n{thread_lines or 'None.'}\n\n"
        f"The Pattern Catalog:\n{catalog}\n\n"
        f"The lists each tag comes from:\n{describe_tag_lists()}\n\n"
        f"Unclear stories Zeph asked about in this Conversation:\n"
        f"{describe_unclear_asked(unclear or {})}\n\n"
        f"Thought Experiments Zeph put to them in this Conversation:\n"
        f"{describe_thought_experiments_asked(thought_experiments or {})}\n\n"
        f"{describe_life_now(life_now or LifeNow(), time_zone)}\n\n"
        f"Ruled-out topics: {', '.join(ruled_out_topics) or 'none'}\n\n"
        f"Patterns Zeph has told them:\n"
        f"{describe_patterns_told(told or {}, types_by_id)}\n\n"
        f"Predictions Zeph gave them, still open:\n"
        f"{describe_predictions_given(predictions or {}, time_zone)}\n\n"
        f"The Conversation:\n{to_transcript_lines(messages, time_zone)}"
    )


@dataclass(frozen=True)
class Tagged:
    """What one tagging answer came to, once code checked it.

    Attributes:
        planned: The Observations kept and those dropped.
        settled: The unclear stories the model settled, as it wrote them.
        exclusion_flags: The exclusions that apply to the User now.
        reactions: How the User took the Patterns they were told.
        prediction_outcomes: The open Predictions the User said the
            outcome of, each with it.
    """

    planned: PlannedObservations
    settled: list[Any]
    exclusion_flags: list[ExclusionFlag]
    reactions: list[ReactionToPattern]
    prediction_outcomes: list[Prediction]


class PatternTagger:
    """Tags a User's Observations when a Conversation ends, after its Life Threads.

    The model reads the Conversation into the Pattern Catalog; code keeps
    only the Observations that pass its checks. Nothing reaches a reply.
    """

    def __init__(
        self,
        repositories: Repositories,
        pattern_catalog: PatternCatalogService,
        chat_model: UsageRecordingChatModel,
        model_call_log: ModelCallLog,
        clock: Clock,
    ) -> None:
        """Set up the tagger.

        Args:
            repositories: Where Observations are stored.
            pattern_catalog: Reads the Pattern Types in the catalog now.
            chat_model: Writes the Observations and records the tokens used.
            model_call_log: Records how many were tagged and dropped.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._pattern_catalog = pattern_catalog
        self._chat_model = chat_model
        self._model_call_log = model_call_log
        self._clock = clock

    def tag_from(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        messages: list[ConversationMessage],
        touched: Sequence[LifeThread],
    ) -> PlannedObservations | None:
        """Tag and keep the Observations in an ended Conversation.

        Runs only while Pattern noticing works for the User, once they have
        pressed "Got it" on the notice saying so, and only when they wrote
        something in their own words. An unreadable answer is asked again
        once; if it is still unreadable nothing is kept. How many were
        tagged and dropped goes into the Model Call Log, never their words.
        The exclusions the model says apply to the User now replace those
        flagged before. How the model says they took a Pattern Zeph told
        them is kept, one reaction per Pattern and Conversation, and so is
        how they say an open Prediction went.

        Args:
            snapshot: The User whose Conversation it was; User Memory works
                for them.
            conversation_id: The ended Conversation.
            messages: Its messages, oldest first.
            touched: The Life Threads the Conversation started, changed or
                brought up.

        Returns:
            The Observations kept and those dropped; None when the step
            didn't run or its answer couldn't be read.
        """
        if not may_keep_observations(snapshot):
            return None
        pattern_types = [
            entry.pattern_type for entry in self._pattern_catalog.catalog()
        ]
        unclear = self._unclear_asked_in(snapshot, conversation_id)
        told = self._patterns_told(snapshot, pattern_types)
        tagged = self._tag(
            snapshot,
            conversation_id,
            messages,
            touched,
            pattern_types,
            unclear,
            self._thought_experiments_asked_in(snapshot, conversation_id),
            self._life_now(snapshot),
            told,
            self._open_predictions(snapshot, told),
        )
        if tagged is None:
            return None
        self._repositories.observations.add_many(tagged.planned.kept)
        self._repositories.patterns.add_reactions(tagged.reactions)
        self._repositories.patterns.save_prediction_outcomes(tagged.prediction_outcomes)
        self._repositories.observations.settle(
            plan_settled(
                tagged.settled,
                unclear,
                {pattern_type.id: pattern_type for pattern_type in pattern_types},
            )
        )
        self._repositories.observations.replace_exclusion_flags(
            snapshot.user.id, tagged.exclusion_flags
        )
        return tagged.planned

    def tag_again(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        messages: list[ConversationMessage],
        threads: Sequence[LifeThread],
        pattern_types: Sequence[PatternType],
    ) -> list[Observation]:
        """Tag a past Conversation again, against some Pattern Types only.

        Used when stored evidence is found to fit a Pattern Type after its
        Conversation ended. The same rules and checks as `tag_from` apply.
        An Observation already kept from that Conversation (the same
        Pattern Type, sign and quote) is not kept twice, and none is kept
        for a Pattern the User disagreed with while they have gathering on
        those turned off. Exclusions are left as they are: they say what
        applies now, not back then, and no reaction is read.

        Args:
            snapshot: The User whose Conversation it was.
            conversation_id: The past Conversation.
            messages: Its messages still kept, oldest first.
            threads: The Life Threads the stored evidence is in.
            pattern_types: The Pattern Types to tag against.

        Returns:
            The new Observations kept; none when the step didn't run or its
            answer couldn't be read.
        """
        if not may_keep_observations(snapshot):
            return []
        tagged = self._tag(
            snapshot,
            conversation_id,
            messages,
            threads,
            pattern_types,
            {},
            self._thought_experiments_asked_in(snapshot, conversation_id),
            None,
            {},
            {},
        )
        if tagged is None:
            return []
        already_kept = {
            repeat_key(observation)
            for observation in self._repositories.observations.list_for_user(
                snapshot.user.id
            )
            if observation.conversation_id == conversation_id
        }
        not_gathered = not_gathered_pattern_types(
            list(self._patterns_told(snapshot, pattern_types).values()),
            [],
            snapshot.user.contested_gathering_enabled,
        )
        new = [
            observation
            for observation in tagged.planned.kept
            if repeat_key(observation) not in already_kept
            and not names_one_of(observation, not_gathered)
        ]
        self._repositories.observations.add_many(new)
        return new

    def _tag(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        messages: list[ConversationMessage],
        threads: Sequence[LifeThread],
        pattern_types: Sequence[PatternType],
        unclear: Mapping[int, Observation],
        thought_experiments: Mapping[int, str],
        life_now: LifeNow | None,
        told: Mapping[int, CatalogPattern],
        predictions: Mapping[int, Prediction],
    ) -> Tagged | None:
        """Ask the model for a Conversation's Observations and check them.

        Nothing is saved but how many were tagged and dropped, in the Model
        Call Log.

        Args:
            snapshot: The User whose Conversation it was.
            conversation_id: The Conversation.
            messages: Its messages, oldest first.
            threads: The Life Threads an Observation may belong to.
            pattern_types: The Pattern Types to tag against.
            unclear: The unclear stories asked about in it, by number.
            thought_experiments: The questions that put a Thought Experiment
                to the User in it, as asked, by number.
            life_now: Their open Life Threads and latest Day Summaries, for
                telling which exclusions apply; None to flag none.
            told: The Patterns Zeph has told them, by number, for reading
                how they took one; empty to read none.
            predictions: Their open Predictions, by number, for reading
                how one went; empty to read none.

        Returns:
            The Observations that passed and those dropped, the unclear
            stories the model settled, the exclusions that apply, how
            they took the Patterns they were told and how their
            Predictions went; None
            when the User wrote nothing in their own words, there is no
            Pattern Type or the answer couldn't be read.
        """
        user_texts = users_own_texts(messages)
        if not user_texts or not pattern_types:
            return None
        numbered_threads = dict(enumerate(threads, start=1))
        now = self._clock.now()
        time_zone = snapshot.user.time_zone
        ruled_out_topics = snapshot.settings.get(PATTERN_RULED_OUT_TOPICS)
        answer = self._ask(
            snapshot,
            describe_conversation_to_tag(
                numbered_threads,
                pattern_types,
                messages,
                now,
                time_zone,
                unclear,
                thought_experiments,
                life_now,
                ruled_out_topics,
                told,
                predictions,
            ),
        )
        if answer is None:
            logger.warning("Pattern tagging gave no readable answer")
            return None
        types_by_id = {pattern_type.id: pattern_type for pattern_type in pattern_types}
        exclusion_flags = (
            plan_exclusion_flags(
                read_exclusions_answer(answer), types_by_id, snapshot.user.id, now
            )
            if life_now is not None
            else []
        )
        reactions = plan_reactions(
            read_reactions_answer(answer), told, conversation_id, now
        )
        entries = read_tagging_answer(answer) or []
        planned = plan_observations(
            entries,
            TaggingContext(
                user_id=snapshot.user.id,
                conversation_id=conversation_id,
                pattern_types=types_by_id,
                threads=numbered_threads,
                user_texts=user_texts,
                time_zone=time_zone,
                now=now,
                thought_experiment_numbers=frozenset(thought_experiments),
                ruled_out_topics=frozenset(
                    topic.casefold() for topic in ruled_out_topics
                ),
                ignored_pattern_type_ids=ignored_pattern_types(exclusion_flags),
                not_gathered_pattern_type_ids=not_gathered_pattern_types(
                    list(told.values()),
                    reactions,
                    snapshot.user.contested_gathering_enabled,
                ),
                deleted_quotes=self._repositories.observations.list_deleted_quotes(
                    snapshot.user.id, conversation_id
                ),
                never_again_pattern_type_ids=(
                    self._repositories.patterns.list_never_again(snapshot.user.id)
                ),
            ),
        )
        self._model_call_log.record_tagging_shape(
            snapshot, TaggingShape(tagged=len(entries), dropped=planned.dropped)
        )
        return Tagged(
            planned=planned,
            settled=read_settled_answer(answer),
            exclusion_flags=exclusion_flags,
            reactions=reactions_to_keep(
                reactions,
                list(told.values()),
                snapshot.user.contested_gathering_enabled,
            ),
            prediction_outcomes=plan_prediction_outcomes(
                read_prediction_outcomes_answer(answer),
                predictions,
                conversation_id,
                now,
            ),
        )

    def _open_predictions(
        self, snapshot: UserSnapshot, told: Mapping[int, CatalogPattern]
    ) -> dict[int, Prediction]:
        """Number the Predictions the User may still say the outcome of.

        Args:
            snapshot: The User.
            told: The Patterns Zeph has told them, by number.

        Returns:
            The open Predictions of their shared Patterns, oldest first,
            by number from 1; none read when no Pattern is shared.
        """
        shared_ids = {
            pattern.id
            for pattern in told.values()
            if pattern.state == PatternState.SHARED
        }
        if not shared_ids:
            return {}
        still_open = [
            prediction
            for prediction in self._repositories.patterns.list_predictions(
                snapshot.user.id
            )
            if prediction.pattern_id in shared_ids and prediction.is_open
        ]
        return dict(enumerate(still_open, start=1))

    def _patterns_told(
        self, snapshot: UserSnapshot, pattern_types: Sequence[PatternType]
    ) -> dict[int, CatalogPattern]:
        """Number the Patterns Zeph has told the User.

        Args:
            snapshot: The User.
            pattern_types: The Pattern Types in the catalog now.

        Returns:
            Their shared, confirmed and contested Patterns whose Pattern
            Type is still in the catalog, by number from 1.
        """
        known = {pattern_type.id for pattern_type in pattern_types}
        told = [
            pattern
            for pattern in self._repositories.patterns.list_of_pattern_types(
                snapshot.user.id
            )
            if pattern.state in STATES_OF_A_PATTERN_TOLD
            and pattern.pattern_type_id in known
        ]
        return dict(enumerate(told, start=1))

    def _life_now(self, snapshot: UserSnapshot) -> LifeNow:
        """Read what is going on in a User's life now.

        Args:
            snapshot: The User.

        Returns:
            Their open Life Threads and their latest Day Summaries, as many
            as the Admin-set number.
        """
        user_id = snapshot.user.id
        days = snapshot.settings.get(PATTERN_EXCLUSION_SUMMARY_DAYS)
        return LifeNow(
            open_threads=[
                thread
                for thread in self._repositories.life_threads.list_for_user(user_id)
                if thread.is_open
            ],
            summaries=(
                self._repositories.user_memory.list_summaries(user_id, limit=days)
                if days
                else []
            ),
        )

    def _unclear_asked_in(
        self, snapshot: UserSnapshot, conversation_id: UUID
    ) -> dict[int, Observation]:
        """Find the unclear Observations an aimed Curiosity asked about here.

        Args:
            snapshot: The User whose Conversation it was.
            conversation_id: The ended Conversation.

        Returns:
            Those still unclear, numbered from 1; none when no aimed
            Curiosity about one was raised in it.
        """
        aimed_at = {
            curiosity.source_observation_id
            for curiosity in self._repositories.curiosities.list_raised_in(
                conversation_id
            )
            if curiosity.aim == CuriosityAim.EXPLORATION
        } - {None}
        if not aimed_at:
            return {}
        unclear = [
            observation
            for observation in self._repositories.observations.list_for_user(
                snapshot.user.id
            )
            if observation.id in aimed_at and observation.unclear
        ]
        return dict(enumerate(unclear, start=1))

    def _thought_experiments_asked_in(
        self, snapshot: UserSnapshot, conversation_id: UUID
    ) -> dict[int, str]:
        """Find the questions that put a Thought Experiment to the User here.

        The words are the Curiosity's, as asked, so an Admin's edit since
        then doesn't change what the tagging model reads. A starter one put
        to a new User counts like one an Exploration's try put.

        Args:
            snapshot: The User whose Conversation it was.
            conversation_id: The ended Conversation.

        Returns:
            The questions, numbered from 1 in the order they were asked;
            none when no Curiosity put one in it.
        """
        raised = [
            curiosity
            for curiosity in self._repositories.curiosities.list_raised_in(
                conversation_id
            )
            if curiosity.aim in AIMS_WRITTEN_BY_CODE
        ]
        if not raised:
            return {}
        putting = {
            attempt.curiosity_id
            for attempt in self._repositories.explorations.list_tries(snapshot.user.id)
            if attempt.thought_experiment_id is not None
        } | {
            curiosity.id
            for curiosity in raised
            if curiosity.thought_experiment_id is not None
        }
        asked = sorted(
            (curiosity for curiosity in raised if curiosity.id in putting),
            key=lambda curiosity: curiosity.raised_at or curiosity.created_at,
        )
        return {
            number: curiosity.question
            for number, curiosity in enumerate(asked, start=1)
        }

    def _ask(self, snapshot: UserSnapshot, description: str) -> str | None:
        """Ask the model for the Observations, once more if it can't be read.

        Args:
            snapshot: The User whose Conversation it was.
            description: The Threads, catalog, tag lists, unclear stories
                asked about and Conversation.

        Returns:
            Its answer, with readable Observations; None if both answers
            were unreadable.
        """
        settings = snapshot.settings
        for _ in range(2):
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.PATTERN_TAGGING,
                model=settings.get(PATTERN_TAGGING_MODEL),
                thinking=thinking_to_use(
                    settings, PATTERN_TAGGING_MODEL, PATTERN_TAGGING_THINKING
                ),
                instructions=settings.get(PATTERN_TAGGING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
            if read_tagging_answer(answer) is not None:
                return answer
        return None
