import json
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

import pytest

from companion.core.check_in_decision import kinds_with_pattern_settled
from companion.core.models import (
    CatalogPattern,
    CheckInKind,
    EvidenceKind,
    NarrowingTag,
    ObservationDirection,
    PatternNarrowing,
    PatternReaction,
    PatternState,
    ReactionToPattern,
    Relationship,
)
from companion.core.observations import (
    names_one_of,
    not_gathered_pattern_types,
    plan_reactions,
    reactions_to_keep,
)
from companion.core.pattern_scoring import reaction_points
from companion.core.pattern_sharing import (
    SharedCheck,
    describe_where_it_shows,
    pick_quotes,
    read_shared_check,
    within_weekly_limit,
)
from tests.test_ready_gate_rules import (
    BELONG,
    NOW,
    PATTERN_TYPES,
    TODAY,
    WEIGHING,
    WORTH,
    story,
)

BELONGING = PATTERN_TYPES[BELONG]
CONVERSATION = uuid4()


def pattern(state: PatternState = PatternState.SHARED) -> CatalogPattern:
    """A User's Pattern of CONF.AVOID.BELONG in the given state."""
    return CatalogPattern(
        id=uuid4(),
        user_id=uuid4(),
        pattern_type_id=BELONG,
        state=state,
        started_at=NOW,
        updated_at=NOW,
    )


def reaction(
    kind: PatternReaction, days_ago: int = 0, pattern_id: object = None
) -> ReactionToPattern:
    """How a User took a Pattern some days ago."""
    return ReactionToPattern(
        id=uuid4(),
        user_id=uuid4(),
        pattern_id=pattern_id or uuid4(),  # type: ignore[arg-type]
        reaction=kind,
        conversation_id=CONVERSATION,
        reacted_at=NOW - timedelta(days=days_ago),
    )


def test_quotes_come_one_per_situation_at_most_three() -> None:
    mei_thread = uuid4()
    observations = [
        story(thread=mei_thread, quote="first Mei"),
        story(thread=mei_thread, quote="second Mei"),
        story(about="their manager", quote="manager"),
        story(about="Jun", quote="Jun"),
        story(about="Priya", quote="Priya"),
    ]

    quotes = pick_quotes(observations, BELONGING)

    assert len(quotes) == 3
    assert len({quote.thread_id for quote in quotes}) == 3
    assert [quote.quote for quote in quotes if quote.thread_id == mei_thread] in (
        ["first Mei"],
        ["second Mei"],
        [],
    )


def test_real_stories_are_quoted_before_habits_and_newer_before_older() -> None:
    habit = replace(story(quote="habit"), evidence_kind=EvidenceKind.REPORTED_HABIT)
    older = replace(story(quote="older"), day=TODAY - timedelta(days=9))
    newer = story(quote="newer")

    quotes = pick_quotes([habit, older, newer], BELONGING)

    assert [quote.quote for quote in quotes] == ["newer", "older", "habit"]


@pytest.mark.parametrize(
    "not_quotable",
    [
        story(direction=ObservationDirection.AGAINST),
        story(second=WORTH),
        replace(story(), excluded=True),
        replace(story(), situational=True),
        replace(story(), evidence_kind=EvidenceKind.WHAT_IF_ANSWER),
        replace(story(), ruled_out_topic="abuse", raised_by_user=False),
        replace(story(), pattern_type_id=WORTH),
    ],
    ids=[
        "against",
        "unclear",
        "excluded",
        "situational",
        "what-if answer",
        "ruled-out topic they didn't raise",
        "another Pattern Type's",
    ],
)
def test_only_clear_weighty_evidence_for_from_their_life_is_quoted(
    not_quotable: object,
) -> None:
    quotable = story(quote="kept")

    quotes = pick_quotes([not_quotable, quotable], BELONGING)  # type: ignore[list-item]

    assert [quote.quote for quote in quotes] == ["kept"]


def test_a_ruled_out_topic_they_raised_themselves_may_be_quoted() -> None:
    raised = replace(story(), ruled_out_topic="abuse", raised_by_user=True)

    assert pick_quotes([raised], BELONGING) == (raised,)


def test_the_weekly_limit_allows_one_more_only_while_under_it() -> None:
    assert within_weekly_limit(0, 1)
    assert not within_weekly_limit(1, 1)
    assert not within_weekly_limit(0, 0)


def test_agreeing_adds_a_weak_sign_for_that_fades_and_adds_up() -> None:
    numbers = WEIGHING.numbers

    once = reaction_points([reaction(PatternReaction.AGREED)], numbers, TODAY, None)
    twice = reaction_points(
        [reaction(PatternReaction.AGREED), reaction(PatternReaction.AGREED)],
        numbers,
        TODAY,
        None,
    )
    faded = reaction_points(
        [reaction(PatternReaction.AGREED, days_ago=75)], numbers, TODAY, None
    )

    assert once == 30
    assert twice == 60
    assert faded == pytest.approx(15)


def test_pushing_back_is_a_weak_sign_against_and_brushing_off_counts_nothing() -> None:
    numbers = WEIGHING.numbers

    assert (
        reaction_points([reaction(PatternReaction.PUSHED_BACK)], numbers, TODAY, None)
        == -30
    )
    assert (
        reaction_points([reaction(PatternReaction.BRUSHED_OFF)], numbers, TODAY, None)
        == 0
    )


def test_the_shared_check_reads_shared_and_the_prediction() -> None:
    answer = json.dumps({"shared": True, "prediction": " Notice whether you say yes. "})

    assert read_shared_check(f"```json\n{answer}\n```") == SharedCheck(
        shared=True, prediction="Notice whether you say yes."
    )
    assert read_shared_check('{"shared": false}') == SharedCheck(False, "")


@pytest.mark.parametrize(
    "answer", ["yes", '{"shared": "yes"}', '{"prediction": "x"}', "[true]", "{oops}"]
)
def test_an_unreadable_shared_check_reads_as_nothing(answer: str) -> None:
    assert read_shared_check(answer) is None


def test_reactions_are_kept_once_per_pattern_shown() -> None:
    told = {1: pattern(), 2: pattern()}
    entries = [
        {"pattern": 1, "reaction": "agreed"},
        {"pattern": 1, "reaction": "pushed_back"},
        {"pattern": 2, "reaction": "loved it"},
        {"pattern": 9, "reaction": "agreed"},
        {"pattern": True, "reaction": "agreed"},
        "agreed",
    ]

    reactions = plan_reactions(entries, told, CONVERSATION, NOW)

    assert [
        (item.pattern_id, item.reaction, item.conversation_id, item.reacted_at)
        for item in reactions
    ] == [(told[1].id, PatternReaction.AGREED, CONVERSATION, NOW)]


def test_gathering_off_stops_new_observations_for_patterns_they_disagreed_with() -> (
    None
):
    contested = pattern(PatternState.CONTESTED)
    shared = replace(pattern(), pattern_type_id=WORTH)
    pushed_back_now = [
        reaction(PatternReaction.PUSHED_BACK, pattern_id=shared.id),
    ]

    assert not_gathered_pattern_types([contested, shared], [], True) == frozenset()
    assert not_gathered_pattern_types([contested, shared], [], False) == {BELONG}
    assert not_gathered_pattern_types([contested, shared], pushed_back_now, False) == {
        BELONG,
        WORTH,
    }


def test_gathering_off_keeps_only_a_new_push_back_on_a_contested_pattern() -> None:
    contested = pattern(PatternState.CONTESTED)
    shared = pattern()
    agreed_with_contested = reaction(PatternReaction.AGREED, pattern_id=contested.id)
    pushed_back_again = reaction(PatternReaction.PUSHED_BACK, pattern_id=contested.id)
    agreed_with_shared = reaction(PatternReaction.AGREED, pattern_id=shared.id)
    reactions = [agreed_with_contested, pushed_back_again, agreed_with_shared]
    told = [contested, shared]

    assert reactions_to_keep(reactions, told, True) == reactions
    assert reactions_to_keep(reactions, told, False) == [
        pushed_back_again,
        agreed_with_shared,
    ]


def test_an_observation_names_a_pattern_type_first_or_second() -> None:
    unclear = story(second=WORTH)

    assert names_one_of(unclear, frozenset({BELONG}))
    assert names_one_of(unclear, frozenset({WORTH}))
    assert not names_one_of(story(), frozenset({WORTH}))
    assert not names_one_of(story(), frozenset())


def test_where_it_shows_is_put_in_plain_words() -> None:
    narrowings = [
        PatternNarrowing(
            tag=NarrowingTag.RELATIONSHIP,
            holds_with=(Relationship.FAMILY.value, Relationship.FRIEND.value),
            not_with=(Relationship.PARTNER.value,),
        ),
        PatternNarrowing(
            tag=NarrowingTag.POWER, holds_with=("above",), not_with=("equal",)
        ),
    ]

    assert describe_where_it_shows(narrowings) == (
        " It shows with family, friend; not with partner."
        " It shows with people above them; not with their equals."
    )
    assert describe_where_it_shows([]) == ""


def test_a_check_in_offers_only_pattern_kinds_once_there_is_a_pattern_to_share() -> (
    None
):
    hello = CheckInKind(id=uuid4(), name="A casual hello", description="", sort_order=0)
    noticed = replace(
        hello, id=uuid4(), name="Something I've noticed", shares_pattern=True
    )

    assert kinds_with_pattern_settled((hello, noticed), True) == (noticed,)
    assert kinds_with_pattern_settled((hello, noticed), False) == (hello,)
