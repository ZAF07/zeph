from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from companion.core.models import (
    CatalogPattern,
    LifeThread,
    NarrowingTag,
    Observation,
    PatternState,
    PatternType,
    Power,
    Prediction,
)
from companion.core.pattern_sharing import may_be_quoted

STATES_SHOWN_IN_ORDER = (
    PatternState.SHARED,
    PatternState.CONFIRMED,
    PatternState.CONTESTED,
    PatternState.CLOSED,
)
POWER_WORDS_TO_THE_USER = {
    Power.ABOVE.value: "people above you",
    Power.EQUAL.value: "your equals",
    Power.BELOW.value: "people below you",
}


@dataclass(frozen=True)
class WhereItShows:
    """Where a Pattern shows and where it doesn't, in words said to the User.

    Attributes:
        shows_with: Who it shows with, e.g. "family".
        not_with: Who it was shown not to happen with.
    """

    shows_with: tuple[str, ...]
    not_with: tuple[str, ...]


@dataclass(frozen=True)
class QuotesFromLifeThread:
    """A Pattern's quotes from one part of the User's life.

    Attributes:
        life_thread: The Life Thread's title; None for quotes in no Thread.
        quotes: The Observations quoted, newest day first.
    """

    life_thread: str | None
    quotes: tuple[Observation, ...]


@dataclass(frozen=True)
class ToldPattern:
    """A Pattern the Companion told the User about, as the User sees it.

    It holds no score: only words and evidence.

    Attributes:
        pattern: The Pattern.
        wording: Its Pattern Type's approved wording.
        where_it_shows: Where counter-tests showed it holds and doesn't.
        told_at: When the Companion first told the User about it.
        quote_groups: Its quotes by Life Thread, the Thread with the newest
            quote first and quotes in no Thread last.
        predictions: The Predictions given for it, newest first.
    """

    pattern: CatalogPattern
    wording: str
    where_it_shows: tuple[WhereItShows, ...]
    told_at: datetime
    quote_groups: tuple[QuotesFromLifeThread, ...]
    predictions: tuple[Prediction, ...]


def was_told(pattern: CatalogPattern) -> bool:
    """Say whether the Companion told the User about a Pattern, so they may see it.

    Args:
        pattern: The Pattern.

    Returns:
        True for a shared, confirmed or contested Pattern, and for a closed
        one that was shared before it closed.
    """
    if pattern.state == PatternState.CLOSED:
        return pattern.shared_at is not None
    return pattern.state in STATES_SHOWN_IN_ORDER


def told_at(pattern: CatalogPattern) -> datetime:
    """Say when the Companion first told the User about a Pattern.

    Args:
        pattern: A Pattern the User was told.

    Returns:
        When it was shared; when it last moved for one with no such time.
    """
    return pattern.shared_at or pattern.updated_at


def where_it_shows(pattern: CatalogPattern) -> tuple[WhereItShows, ...]:
    """Put a Pattern's narrowings in words said to the User.

    Args:
        pattern: The Pattern.

    Returns:
        One entry per narrowing, with "people above you" for a power tag.
    """
    shown = []
    for narrowing in pattern.narrowings:
        words = POWER_WORDS_TO_THE_USER if narrowing.tag == NarrowingTag.POWER else {}
        shown.append(
            WhereItShows(
                shows_with=tuple(
                    words.get(value, value) for value in narrowing.holds_with
                ),
                not_with=tuple(words.get(value, value) for value in narrowing.not_with),
            )
        )
    return tuple(shown)


def group_quotes(
    quotes: Sequence[Observation], thread_titles: Mapping[UUID, str]
) -> tuple[QuotesFromLifeThread, ...]:
    """Group a Pattern's quotes by the part of the User's life they come from.

    Args:
        quotes: The Observations to show.
        thread_titles: The User's Life Thread titles by ID.

    Returns:
        A group per Life Thread, the Thread with the newest quote first,
        then one group for quotes in no Thread; quotes newest day first.
    """
    newest_first = sorted(
        quotes, key=lambda quote: (quote.day, quote.tagged_at), reverse=True
    )
    by_thread: dict[str | None, list[Observation]] = {}
    for quote in newest_first:
        title = thread_titles.get(quote.thread_id) if quote.thread_id else None
        by_thread.setdefault(title, []).append(quote)
    in_no_thread = by_thread.pop(None, [])
    groups = [
        QuotesFromLifeThread(life_thread=title, quotes=tuple(thread_quotes))
        for title, thread_quotes in by_thread.items()
    ]
    if in_no_thread:
        groups.append(
            QuotesFromLifeThread(life_thread=None, quotes=tuple(in_no_thread))
        )
    return tuple(groups)


def told_patterns(
    patterns: Sequence[CatalogPattern],
    pattern_types: Mapping[str, PatternType],
    observations: Sequence[Observation],
    predictions: Sequence[Prediction],
    threads: Sequence[LifeThread],
) -> list[ToldPattern]:
    """Pick the Patterns a User may see, each with its quotes and Predictions.

    A User sees a Pattern only once the Companion has told them about it.
    Its quotes are the ones that may be quoted back when it is shared:
    clear evidence for it from their own life that carries weight.

    Args:
        patterns: The User's Patterns of Pattern Types.
        pattern_types: The Pattern Types in the catalog now, by ID.
        observations: The User's Observations.
        predictions: The Predictions given to the User.
        threads: The User's Life Threads.

    Returns:
        The Patterns they were told whose Pattern Type is in the catalog:
        being tested first, then confirmed, disagreed with and closed, the
        newest told first within each.
    """
    thread_titles = {thread.id: thread.title for thread in threads}
    told = sorted(
        (
            pattern
            for pattern in patterns
            if was_told(pattern) and pattern.pattern_type_id in pattern_types
        ),
        key=told_at,
        reverse=True,
    )
    told.sort(key=lambda pattern: STATES_SHOWN_IN_ORDER.index(pattern.state))
    shown = []
    for pattern in told:
        pattern_type = pattern_types[pattern.pattern_type_id]
        shown.append(
            ToldPattern(
                pattern=pattern,
                wording=pattern_type.approved_wording,
                where_it_shows=where_it_shows(pattern),
                told_at=told_at(pattern),
                quote_groups=group_quotes(
                    [
                        observation
                        for observation in observations
                        if may_be_quoted(observation, pattern_type)
                    ],
                    thread_titles,
                ),
                predictions=tuple(
                    prediction
                    for prediction in reversed(predictions)
                    if prediction.pattern_id == pattern.id
                ),
            )
        )
    return shown
