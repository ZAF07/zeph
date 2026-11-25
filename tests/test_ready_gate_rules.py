from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from companion.adapters.pattern_catalog_seed import read_pattern_catalog_seed
from companion.core.models import (
    EvidenceKind,
    ExplorationNeed,
    ExplorationTry,
    ExplorationWay,
    NarrowingTag,
    Observation,
    ObservationDirection,
    PatternNarrowing,
    PatternTypeStatus,
    Power,
    ReadyCheck,
    Relationship,
    SignStrength,
    SituationSetting,
    SituationTags,
    TryOutcome,
)
from companion.core.observations import UserText
from companion.core.pattern_catalog import read_pattern_types
from companion.core.pattern_scoring import PatternScore, ScoringNumbers
from companion.core.ready_gate import (
    GateFacts,
    ReadyBars,
    UserSafety,
    Weighing,
    count_unchecked_quotes,
    gate_facts,
    narrowings_of,
    read_other_side_answer,
    ready_check,
)
from tests.conftest import PATTERN_CATALOG_DIR

TODAY = date(2026, 11, 25)
NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
BELONG = "CONF.AVOID.BELONG"
WORTH = "ACH.WORTH.PERF"
PATTERN_TYPES = {
    pattern_type.id: pattern_type
    for pattern_type in read_pattern_types(
        read_pattern_catalog_seed(PATTERN_CATALOG_DIR)
    )
}
BARS = ReadyBars(situations=3, conversations=2, points=300, against_under_points=100)
WEIGHING = Weighing(
    sign_strengths={
        (pattern_type.id, sign.id): sign.strength
        for pattern_type in PATTERN_TYPES.values()
        for sign in (*pattern_type.signs, *pattern_type.signs_against)
    },
    numbers=ScoringNumbers(
        sign_points={
            SignStrength.WEAK: 30,
            SignStrength.MODERATE: 70,
            SignStrength.STRONG: 140,
        },
        evidence_percents={
            EvidenceKind.REAL_STORY: 100,
            EvidenceKind.REPORTED_HABIT: 70,
            EvidenceKind.WHAT_IF_ANSWER: 40,
            EvidenceKind.OWN_OPINION: 30,
        },
        unclear_percent=25,
        half_life_days=75,
        people_per_situation=3,
    ),
    today=TODAY,
)
SAFE = UserSafety(
    excluded_pattern_type_ids=frozenset(),
    recent_safeguard_event=False,
    ruled_out_topics=frozenset({"abuse"}),
)
READY_FACTS = GateFacts(
    score=PatternScore(points=420, situations=3),
    clear_score=PatternScore(points=420, situations=3),
    score_without_situational=PatternScore(points=420, situations=3),
    conversations=2,
    counter_tested=True,
    points_against=0,
    exclusion_applies=False,
    recent_safeguard_event=False,
    ruled_out_topic=False,
    pattern_type_approved=True,
    unchecked_quotes=0,
    better_explanation=False,
)
FIRST_CONVERSATION = uuid4()
SECOND_CONVERSATION = uuid4()


def story(
    about: str = "Mei, their sister",
    thread: UUID | None = None,
    direction: ObservationDirection = ObservationDirection.FOR,
    sign: str | None = None,
    relationship: Relationship | None = Relationship.FAMILY,
    power: Power | None = Power.EQUAL,
    conversation: UUID = FIRST_CONVERSATION,
    second: str | None = None,
    quote: str = "I said yes again",
) -> Observation:
    """A fresh strong real story for CONF.AVOID.BELONG, in its own Life Thread."""
    against = direction == ObservationDirection.AGAINST
    return Observation(
        id=uuid4(),
        user_id=uuid4(),
        conversation_id=conversation,
        pattern_type_id=BELONG,
        pattern_type_version="0.3.0",
        sign_id=sign or ("D1" if against else "I2"),
        direction=direction,
        quote=quote,
        context="Agreed to help again.",
        day=TODAY,
        thread_id=thread or uuid4(),
        about=about,
        tags=SituationTags(
            relationship=relationship,
            power=power,
            setting=SituationSetting.HOME,
            stance=None,
        ),
        evidence_kind=EvidenceKind.REAL_STORY,
        second_pattern_type_id=second,
        second_pattern_type_version="0.2.0" if second else None,
        situational=False,
        tagged_at=NOW,
    )


def useful_counter_test() -> ExplorationTry:
    """A counter-test try that came back useful."""
    return ExplorationTry(
        curiosity_id=uuid4(),
        exploration_id=uuid4(),
        user_id=uuid4(),
        need=ExplorationNeed.COUNTER_TEST,
        way=ExplorationWay.OTHER_PERSON,
        created_at=NOW - timedelta(days=3),
        outcome=TryOutcome.USEFUL,
    )


def three_stories_in_two_conversations() -> list[Observation]:
    """Evidence that passes every stored check, once a counter-test was answered."""
    return [
        story(about="Mei, their sister"),
        story(about="Jun, a friend", relationship=Relationship.FRIEND),
        story(
            about="Priya, a colleague",
            relationship=Relationship.COLLEAGUE,
            conversation=SECOND_CONVERSATION,
        ),
    ]


def facts_of(
    observations: list[Observation],
    tries: list[ExplorationTry] | None = None,
    safety: UserSafety = SAFE,
    pattern_type_id: str = BELONG,
) -> GateFacts:
    """The facts about a Pattern, with quotes checked and no better explanation."""
    facts = gate_facts(
        PATTERN_TYPES[pattern_type_id],
        observations,
        [useful_counter_test()] if tries is None else tries,
        safety,
        WEIGHING,
    )
    return replace(facts, unchecked_quotes=0, better_explanation=False)


def test_a_pattern_passing_all_ten_checks_is_ready() -> None:
    assert ready_check(READY_FACTS, BARS) is None
    assert ready_check(facts_of(three_stories_in_two_conversations()), BARS) is None


@pytest.mark.parametrize(
    ("changes", "blocked_by"),
    [
        ({"score": PatternScore(points=420, situations=2)}, ReadyCheck.SITUATIONS),
        ({"conversations": 1}, ReadyCheck.CONVERSATIONS),
        ({"clear_score": PatternScore(points=120, situations=3)}, ReadyCheck.CLEAR),
        ({"clear_score": PatternScore(points=420, situations=2)}, ReadyCheck.CLEAR),
        (
            {
                "score": PatternScore(points=299, situations=3),
                "clear_score": PatternScore(points=420, situations=3),
            },
            ReadyCheck.SCORE,
        ),
        ({"counter_tested": False}, ReadyCheck.COUNTER_TEST),
        ({"points_against": 100}, ReadyCheck.COUNTER_TEST),
        (
            {"score_without_situational": PatternScore(points=280, situations=2)},
            ReadyCheck.SITUATIONAL,
        ),
        ({"exclusion_applies": True}, ReadyCheck.SAFE),
        ({"recent_safeguard_event": True}, ReadyCheck.SAFE),
        ({"ruled_out_topic": True}, ReadyCheck.SAFE),
        ({"pattern_type_approved": False}, ReadyCheck.ALLOWED),
        ({"unchecked_quotes": 1}, ReadyCheck.QUOTES),
        ({"unchecked_quotes": None}, ReadyCheck.QUOTES),
        ({"better_explanation": True}, ReadyCheck.OTHER_SIDE),
        ({"better_explanation": None}, ReadyCheck.OTHER_SIDE),
    ],
)
def test_each_check_alone_blocks_ready(
    changes: dict[str, object], blocked_by: ReadyCheck
) -> None:
    assert ready_check(replace(READY_FACTS, **changes), BARS) == blocked_by


def test_the_other_side_is_the_last_check_so_it_is_asked_only_when_the_rest_pass() -> (
    None
):
    not_asked = replace(READY_FACTS, better_explanation=None)

    assert ready_check(not_asked, BARS) == ReadyCheck.OTHER_SIDE
    assert (
        ready_check(replace(not_asked, pattern_type_approved=False), BARS)
        == ReadyCheck.ALLOWED
    )
    assert (
        ready_check(replace(not_asked, unchecked_quotes=None), BARS)
        == ReadyCheck.QUOTES
    )


def test_two_situations_are_not_enough() -> None:
    facts = facts_of(three_stories_in_two_conversations()[1:])

    assert ready_check(facts, BARS) == ReadyCheck.SITUATIONS


def test_one_long_conversation_is_not_enough() -> None:
    stories = [
        replace(observation, conversation_id=FIRST_CONVERSATION)
        for observation in three_stories_in_two_conversations()
    ]

    assert ready_check(facts_of(stories), BARS) == ReadyCheck.CONVERSATIONS


def test_a_pattern_resting_on_unclear_stories_is_not_ready() -> None:
    clear = three_stories_in_two_conversations()
    unclear = [
        story(about=f"person {number}", second=WORTH, conversation=SECOND_CONVERSATION)
        for number in range(12)
    ]
    facts = facts_of([clear[0], clear[1], *unclear])

    assert facts.score.situations >= BARS.situations
    assert facts.score.points >= BARS.points
    assert ready_check(facts, BARS) == ReadyCheck.CLEAR


def test_a_score_under_the_bar_is_not_ready() -> None:
    weak = [
        replace(observation, sign_id="I1")
        for observation in three_stories_in_two_conversations()
    ]

    assert ready_check(facts_of(weak), BARS) == ReadyCheck.SCORE
    assert facts_of(weak).score.points < BARS.points


def test_a_pattern_never_tested_against_itself_is_not_ready() -> None:
    facts = facts_of(three_stories_in_two_conversations(), tries=[])

    assert ready_check(facts, BARS) == ReadyCheck.COUNTER_TEST


def test_a_counter_test_that_was_only_brushed_off_does_not_count() -> None:
    brushed_off = replace(useful_counter_test(), outcome=TryOutcome.BRUSHED_OFF)
    facts = facts_of(three_stories_in_two_conversations(), tries=[brushed_off])

    assert ready_check(facts, BARS) == ReadyCheck.COUNTER_TEST


def test_too_much_evidence_against_with_the_same_kind_of_person_blocks() -> None:
    stories = three_stories_in_two_conversations()
    against = story(
        about="Wei, their brother",
        direction=ObservationDirection.AGAINST,
        relationship=Relationship.FAMILY,
    )
    more = story(about="Lin, their aunt", conversation=SECOND_CONVERSATION)
    facts = facts_of([*stories, more, against], tries=[])

    assert narrowings_of([*stories, more, against]) == ()
    assert facts.points_against == 140
    assert ready_check(facts, BARS) == ReadyCheck.COUNTER_TEST


def test_a_counter_test_showing_it_does_not_happen_with_friends_narrows_it() -> None:
    with_seniors = [
        story(about="Mei, their sister"),
        story(about="their mother"),
        story(about="their uncle", conversation=SECOND_CONVERSATION),
    ]
    not_with_friends = story(
        about="Jun, a friend",
        direction=ObservationDirection.AGAINST,
        relationship=Relationship.FRIEND,
    )
    observations = [*with_seniors, not_with_friends]
    facts = facts_of(observations, tries=[])

    assert narrowings_of(observations) == (
        PatternNarrowing(
            tag=NarrowingTag.RELATIONSHIP, holds_with=("family",), not_with=("friend",)
        ),
    )
    assert facts.counter_tested
    assert facts.points_against == 0
    assert facts.score.points == 420
    assert ready_check(facts, BARS) is None


def test_a_pattern_is_narrowed_by_where_the_other_person_stands_too() -> None:
    observations = [
        story(about="Mei", power=Power.EQUAL),
        story(
            about="an intern",
            direction=ObservationDirection.AGAINST,
            relationship=Relationship.FAMILY,
            power=Power.BELOW,
        ),
    ]

    assert narrowings_of(observations) == (
        PatternNarrowing(
            tag=NarrowingTag.POWER, holds_with=("equal",), not_with=("below",)
        ),
    )


def test_evidence_against_with_no_kind_of_person_tagged_never_narrows() -> None:
    observations = [
        story(about="Mei"),
        story(
            about="themselves",
            direction=ObservationDirection.AGAINST,
            relationship=None,
            power=None,
        ),
    ]

    assert narrowings_of(observations) == ()


def test_stories_where_anyone_would_act_the_same_by_the_catalog_now_block() -> None:
    stories = three_stories_in_two_conversations()
    with_a_boss = [
        replace(observation, tags=replace(observation.tags, power=Power.ABOVE))
        for observation in stories
    ]
    facts = facts_of(with_a_boss)

    assert facts.score.points >= BARS.points
    assert facts.score_without_situational == PatternScore(points=0, situations=0)
    assert ready_check(facts, BARS) == ReadyCheck.SITUATIONAL


def test_an_exclusion_a_recent_safeguard_event_or_a_ruled_out_topic_is_not_safe() -> (
    None
):
    stories = three_stories_in_two_conversations()
    excluded = replace(SAFE, excluded_pattern_type_ids=frozenset({BELONG}))
    other_excluded = replace(SAFE, excluded_pattern_type_ids=frozenset({WORTH}))
    in_crisis = replace(SAFE, recent_safeguard_event=True)
    asked_about = [replace(stories[0], ruled_out_topic="abuse"), *stories[1:]]
    raised = [replace(asked_about[0], raised_by_user=True), *stories[1:]]
    off_the_list = [replace(stories[0], ruled_out_topic="money"), *stories[1:]]

    assert ready_check(facts_of(stories, safety=excluded), BARS) == ReadyCheck.SAFE
    assert ready_check(facts_of(stories, safety=other_excluded), BARS) is None
    assert ready_check(facts_of(stories, safety=in_crisis), BARS) == ReadyCheck.SAFE
    assert ready_check(facts_of(asked_about), BARS) == ReadyCheck.SAFE
    assert ready_check(facts_of(raised), BARS) is None
    assert ready_check(facts_of(off_the_list), BARS) is None


def test_a_pattern_of_a_draft_pattern_type_is_never_ready() -> None:
    stories = three_stories_in_two_conversations()
    draft = replace(PATTERN_TYPES[BELONG], status=PatternTypeStatus.DRAFT)
    draft_facts = replace(
        gate_facts(draft, stories, [useful_counter_test()], SAFE, WEIGHING),
        unchecked_quotes=0,
        better_explanation=False,
    )

    assert ready_check(draft_facts, BARS) == ReadyCheck.ALLOWED


def test_a_quote_is_checked_again_against_the_texts_still_kept() -> None:
    kept = story(quote="I said yes again")
    changed = story(quote="I never said that", conversation=SECOND_CONVERSATION)
    texts_gone = story(quote="long ago", conversation=uuid4())
    texts = {
        FIRST_CONVERSATION: [UserText("ugh. I said yes again, of course", NOW)],
        SECOND_CONVERSATION: [UserText("nothing like it", NOW)],
    }

    assert count_unchecked_quotes([kept, texts_gone], texts) == 0
    assert count_unchecked_quotes([kept, changed, texts_gone], texts) == 1


@pytest.mark.parametrize(
    ("answer", "better"),
    [
        ('{"better_explanation": false, "why": "fits"}', False),
        ('```json\n{"better_explanation": true, "why": "a look-alike"}\n```', True),
        ('{"better_explanation": "no"}', None),
        ('{"why": "fits"}', None),
        ("I think it holds.", None),
        ("{not json}", None),
    ],
)
def test_the_other_side_answer_is_read_strictly(
    answer: str, better: bool | None
) -> None:
    assert read_other_side_answer(answer) == better
