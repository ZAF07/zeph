from dataclasses import replace
from uuid import uuid4

import pytest

from companion.core.agenda import missing_condition_need
from companion.core.condition_coverage import CONDITION_ORDER
from companion.core.models import (
    Audience,
    CatalogPattern,
    Condition,
    EvidenceKind,
    ExplorationApproach,
    ExplorationNeed,
    ExplorationTry,
    Observation,
    ObservationDirection,
    PatternNarrowing,
    PatternState,
    Power,
    Relationship,
    SituationSetting,
    Stakes,
    Stance,
    StateGoingIn,
    TryOutcome,
)
from companion.core.narrowing_words import (
    STATE_GENTLY,
    WHERE_WORDS,
    describe_how_to_say_state,
    describe_narrowing,
    describe_where_it_shows,
)
from companion.core.pattern_scoring import (
    PatternScore,
    narrowings_of,
    score_observations,
    without_narrowing,
)
from companion.core.pattern_sharing import (
    NotSeenYet,
    PatternToShare,
    describe_not_seen,
    describe_three_parts,
    not_seen_yet,
)
from companion.core.ready_gate import describe_pattern_to_argue
from tests.test_ready_gate_rules import BELONG, NOW, PATTERN_TYPES, WEIGHING, story

NUMBERS = WEIGHING.numbers
AGAINST = ObservationDirection.AGAINST
VALUES_OF = {
    Condition.RELATIONSHIP: Relationship,
    Condition.POWER: Power,
    Condition.STANCE: Stance,
    Condition.SETTING: SituationSetting,
    Condition.AUDIENCE: Audience,
    Condition.STAKES: Stakes,
    Condition.STATE_GOING_IN: StateGoingIn,
}


def under(
    about: str,
    direction: ObservationDirection = ObservationDirection.FOR,
    audience: Audience | None = None,
    stakes: Stakes | None = None,
    state: StateGoingIn | None = None,
    stance: Stance | None = None,
) -> Observation:
    """A clear story with a colleague at work, under the Conditions given."""
    told = story(about=about, direction=direction, relationship=Relationship.COLLEAGUE)
    return replace(
        told,
        tags=replace(
            told.tags,
            setting=SituationSetting.WORK,
            audience=audience,
            stakes=stakes,
            state_going_in=state,
            stance=stance,
        ),
    )


def score_of(observations: list[Observation]) -> PatternScore:
    """A Pattern's score with evidence that only narrows it left out."""
    return WEIGHING.score(without_narrowing(observations, NUMBERS))


def test_any_condition_narrows_a_pattern() -> None:
    observations = [
        under("Priya", audience=Audience.GROUP),
        under("Sam", audience=Audience.GROUP),
        under("Ravi", AGAINST, audience=Audience.ONE_TO_ONE),
    ]

    assert narrowings_of(observations, NUMBERS) == (
        PatternNarrowing(
            tag=Condition.AUDIENCE, holds_with=("group",), not_with=("one-to-one",)
        ),
    )


def test_one_story_for_no_longer_narrows() -> None:
    observations = [
        under("Priya", audience=Audience.GROUP),
        under("Sam"),
        under("Ravi", AGAINST, audience=Audience.ONE_TO_ONE),
    ]

    assert narrowings_of(observations, NUMBERS) == ()
    assert narrowings_of(
        observations, replace(NUMBERS, narrowing_stories_needed=1)
    ) == (
        PatternNarrowing(
            tag=Condition.AUDIENCE, holds_with=("group",), not_with=("one-to-one",)
        ),
    )


def test_stories_that_dont_say_the_condition_dont_count_toward_the_bar() -> None:
    unclear = replace(
        under("Sam", audience=Audience.GROUP), second_pattern_type_id="ACH.WORTH.PERF"
    )
    observations = [
        under("Priya", audience=Audience.GROUP),
        unclear,
        under("Ravi", AGAINST, audience=Audience.ONE_TO_ONE),
    ]

    assert narrowings_of(observations, NUMBERS) == ()


def test_evidence_against_under_a_value_the_pattern_showed_in_never_narrows() -> None:
    observations = [
        under("Priya", audience=Audience.GROUP),
        under("Sam", audience=Audience.GROUP),
        under("Ravi", AGAINST, audience=Audience.GROUP),
        under("Lin", AGAINST, audience=Audience.ONE_TO_ONE),
    ]

    assert narrowings_of(observations, NUMBERS) == ()
    assert without_narrowing(observations, NUMBERS) == observations


def test_only_the_two_conditions_with_the_most_stories_narrow() -> None:
    stories = [
        under("Priya", audience=Audience.GROUP, stakes=Stakes.HIGH),
        under("Sam", audience=Audience.GROUP, stakes=Stakes.HIGH),
        under("Jo", stakes=Stakes.HIGH, state=StateGoingIn.WORN_OUT),
        under("Kai", state=StateGoingIn.WORN_OUT),
        under("Ana", stakes=Stakes.HIGH, state=StateGoingIn.WORN_OUT),
    ]
    explained = under("Ravi", AGAINST, stakes=Stakes.LOW)
    not_explained = under("Lin", AGAINST, audience=Audience.ONE_TO_ONE)
    steady = under("Wei", AGAINST, state=StateGoingIn.STEADY)
    observations = [*stories, explained, not_explained, steady]

    kept = narrowings_of(observations, NUMBERS)

    assert [narrowing.tag for narrowing in kept] == [
        Condition.STAKES,
        Condition.STATE_GOING_IN,
    ]
    assert without_narrowing(observations, NUMBERS) == [*stories, not_explained]
    assert score_of(observations).points == score_of(stories).points - 140


def test_a_tie_for_the_last_narrowing_goes_by_the_fixed_order_of_conditions() -> None:
    observations = [
        under(
            "Priya", stakes=Stakes.HIGH, state=StateGoingIn.LOW, stance=Stance.HOSTILE
        ),
        under("Sam", stakes=Stakes.HIGH, state=StateGoingIn.LOW, stance=Stance.HOSTILE),
        under(
            "Ravi",
            AGAINST,
            stakes=Stakes.LOW,
            state=StateGoingIn.STEADY,
            stance=Stance.SUPPORTIVE,
        ),
    ]

    kept = narrowings_of(observations, NUMBERS)

    assert [narrowing.tag for narrowing in kept] == [Condition.STAKES, Condition.STANCE]
    assert CONDITION_ORDER.index(Condition.STANCE) < CONDITION_ORDER.index(
        Condition.STATE_GOING_IN
    )


def test_the_most_narrowings_is_the_admin_set_number() -> None:
    observations = [
        under("Priya", audience=Audience.GROUP, stakes=Stakes.HIGH),
        under("Sam", audience=Audience.GROUP, stakes=Stakes.HIGH),
        under("Ravi", AGAINST, audience=Audience.ONE_TO_ONE, stakes=Stakes.LOW),
    ]

    one = narrowings_of(observations, replace(NUMBERS, narrowings_per_pattern=1))

    assert [narrowing.tag for narrowing in one] == [Condition.AUDIENCE]


def test_evidence_against_a_kept_narrowing_explains_is_not_counted() -> None:
    stories = [
        under("Priya", audience=Audience.GROUP),
        under("Sam", audience=Audience.GROUP),
    ]
    one_to_one = under("Ravi", AGAINST, audience=Audience.ONE_TO_ONE)

    assert score_of([*stories, one_to_one]) == score_of(stories)


def test_conditions_never_add_points_or_situations() -> None:
    plain = [under("Priya"), under("Sam")]
    with_conditions = [
        under("Priya", audience=Audience.GROUP, stakes=Stakes.HIGH),
        under("Sam", audience=Audience.ONE_TO_ONE, state=StateGoingIn.LOW),
    ]

    assert score_of(with_conditions) == score_of(plain)


def test_one_life_thread_is_one_situation_whatever_its_conditions() -> None:
    in_a_group = under("Priya", audience=Audience.GROUP, stakes=Stakes.HIGH)
    one_to_one = replace(
        under("Priya", audience=Audience.ONE_TO_ONE, stakes=Stakes.LOW),
        thread_id=in_a_group.thread_id,
    )
    someone_else = replace(
        under("Sam", audience=Audience.ONE_TO_ONE), thread_id=in_a_group.thread_id
    )

    same_person = score_observations(
        [in_a_group, one_to_one], WEIGHING.sign_strengths, NUMBERS, WEIGHING.today
    )
    two_people = score_observations(
        [in_a_group, one_to_one, someone_else],
        WEIGHING.sign_strengths,
        NUMBERS,
        WEIGHING.today,
    )

    assert same_person == PatternScore(points=140, situations=1)
    assert two_people == PatternScore(points=280, situations=1)


def test_the_cap_inside_a_situation_is_per_person_not_per_mix() -> None:
    first = under("Priya", audience=Audience.GROUP)
    mixes = [
        replace(
            under("Priya", audience=audience, stakes=stakes), thread_id=first.thread_id
        )
        for audience in Audience
        for stakes in Stakes
    ]
    one_person_cap = replace(NUMBERS, people_per_situation=1)
    other_person = replace(under("Sam"), thread_id=first.thread_id)

    scored = score_observations(
        [*mixes, other_person], WEIGHING.sign_strengths, one_person_cap, WEIGHING.today
    )

    assert scored == PatternScore(points=140, situations=1)


def test_a_what_if_answer_under_another_value_still_marks_where_it_stops() -> None:
    stories = [
        under("Priya", audience=Audience.GROUP),
        under("Sam", audience=Audience.GROUP),
    ]
    what_if = replace(
        under("Priya", AGAINST, audience=Audience.ONE_TO_ONE),
        evidence_kind=EvidenceKind.WHAT_IF_ANSWER,
    )

    assert [
        narrowing.not_with for narrowing in narrowings_of([*stories, what_if], NUMBERS)
    ] == [("one-to-one",)]


@pytest.mark.parametrize("condition", list(Condition))
def test_every_value_of_every_condition_has_plain_words(condition: Condition) -> None:
    for value in VALUES_OF[condition]:
        assert WHERE_WORDS[(condition, value.value)]


def test_each_condition_is_said_in_its_own_plain_words() -> None:
    audience = PatternNarrowing(Condition.AUDIENCE, ("group",), ("one-to-one",))
    stakes = PatternNarrowing(Condition.STAKES, ("high",), ("low",))
    people = PatternNarrowing(
        Condition.RELATIONSHIP, ("family", "friend"), ("partner",)
    )

    assert describe_narrowing(audience) == "in a group; not one-to-one"
    assert describe_where_it_shows([stakes, people]) == (
        " It shows when a lot is riding on it; not when little is riding on it."
        " It shows with family, with friends; not with a partner."
    )
    assert describe_where_it_shows([]) == ""


def test_the_state_going_in_is_said_gently_about_the_day_never_as_a_label() -> None:
    state = PatternNarrowing(Condition.STATE_GOING_IN, ("worn out",), ("steady",))

    assert describe_where_it_shows([state]) == (
        " It shows on days they were worn out; not on days they felt steady."
    )
    assert describe_how_to_say_state([state]) == f"{STATE_GENTLY}\n"
    assert "never as a label" in STATE_GENTLY
    assert describe_how_to_say_state([]) == ""


def test_a_shared_pattern_narrowed_by_state_tells_the_reply_to_say_it_gently() -> None:
    observations = [
        under("Priya", state=StateGoingIn.WORN_OUT),
        under("Sam", state=StateGoingIn.WORN_OUT),
        under("Ravi", AGAINST, state=StateGoingIn.STEADY),
    ]

    parts = describe_three_parts(to_share(observations))

    assert "It shows on days they were worn out; not on days they felt steady." in parts
    assert parts.count(STATE_GENTLY) == 1


def missing_condition_try(condition: Condition, value: str) -> ExplorationTry:
    """A useful missing-Condition try, which closes that value."""
    return ExplorationTry(
        curiosity_id=uuid4(),
        exploration_id=uuid4(),
        user_id=uuid4(),
        need=ExplorationNeed.MISSING_CONDITION,
        approach=ExplorationApproach.STORY_FOLLOW_UP,
        created_at=NOW,
        outcome=TryOutcome.USEFUL,
        condition=condition,
        condition_value=value,
    )


def to_share(observations: list[Observation], narrowed: bool = True) -> PatternToShare:
    """A ready Pattern to share, with what its Observations make of it."""
    pattern = CatalogPattern(
        id=uuid4(),
        user_id=uuid4(),
        pattern_type_id=BELONG,
        state=PatternState.READY,
        started_at=NOW,
        updated_at=NOW,
        narrowings=narrowings_of(observations, NUMBERS) if narrowed else (),
    )
    return PatternToShare(
        pattern=pattern,
        pattern_type=PATTERN_TYPES[BELONG],
        quotes=tuple(observations[:2]),
        scored=score_of(observations),
        not_seen=not_seen_yet(observations, [], 2),
    )


def test_a_sharing_reply_is_handed_one_unseen_value_of_a_one_sided_condition() -> None:
    plain = [story(about="Priya", relationship=None, power=None) for _ in range(2)]
    in_a_group = [
        replace(told, tags=replace(told.tags, setting=None, audience=Audience.GROUP))
        for told in plain
    ]

    assert not_seen_yet(in_a_group, [], 2) == NotSeenYet(
        condition=Condition.AUDIENCE, seen="group", not_seen="one-to-one"
    )
    assert not_seen_yet(in_a_group[:1], [], 2) is None


def test_the_unseen_value_is_the_agendas_open_missing_condition_need() -> None:
    observations = [
        under("Priya", audience=Audience.GROUP),
        under("Sam", audience=Audience.GROUP),
        under("Ravi", AGAINST, audience=Audience.ONE_TO_ONE),
    ]
    need = missing_condition_need(observations, [], 2)

    not_seen = not_seen_yet(observations, [], 2)

    assert need is not None and not_seen is not None
    assert (not_seen.condition, not_seen.not_seen) == (need.condition, need.value)
    assert not_seen == NotSeenYet(Condition.AUDIENCE, "group", "in front of others")


def test_a_value_a_useful_try_closed_is_not_handed_over() -> None:
    plain = [story(about="Priya", relationship=None, power=None) for _ in range(2)]
    in_a_group = [
        replace(told, tags=replace(told.tags, setting=None, audience=Audience.GROUP))
        for told in plain
    ]
    closed = [
        missing_condition_try(Condition.AUDIENCE, value.value) for value in Audience
    ]

    assert not_seen_yet(in_a_group, closed, 2) is None


def test_nothing_is_handed_over_when_no_condition_is_one_sided() -> None:
    plain = [story(about="Priya", relationship=None, power=None) for _ in range(2)]
    mixed = [
        replace(told, tags=replace(told.tags, setting=None, audience=audience))
        for told, audience in zip(
            plain, (Audience.GROUP, Audience.ONE_TO_ONE), strict=True
        )
    ]

    assert not_seen_yet(mixed, [], 2) is None
    assert describe_not_seen(None) == ""


def test_a_state_gap_is_never_handed_to_a_sharing_reply() -> None:
    plain = [story(about="Priya", relationship=None, power=None) for _ in range(2)]
    worn_out = [
        replace(
            told,
            tags=replace(told.tags, setting=None, state_going_in=StateGoingIn.WORN_OUT),
        )
        for told in plain
    ]
    need = missing_condition_need(worn_out, [], 2)

    assert need is not None and need.condition == Condition.STATE_GOING_IN
    assert not_seen_yet(worn_out, [], 2) is None


def test_the_unseen_value_is_to_be_said_as_not_known_never_as_a_claim() -> None:
    said = describe_not_seen(NotSeenYet(Condition.AUDIENCE, "group", "one-to-one"))

    assert "you have only heard about this in a group" in said
    assert "you haven't heard how it goes one-to-one" in said
    assert "as something you don't know" in said
    assert (
        "“I've only heard about this in a group. I don't know if it's the same "
        "one-to-one”"
    ) in said
    assert "never as a claim about them" in said
    assert "don't ask about it" in said


def test_a_shared_pattern_says_its_narrowing_one_unseen_value_and_the_prediction() -> (
    None
):
    observations = [
        under("Priya", audience=Audience.GROUP),
        under("Sam", audience=Audience.GROUP),
        under("Ravi", AGAINST, audience=Audience.ONE_TO_ONE),
    ]

    parts = describe_three_parts(to_share(observations))

    narrowing = parts.index("It shows in a group; not one-to-one.")
    not_seen = parts.index("One thing you don't know")
    prediction = parts.index(PATTERN_TYPES[BELONG].prediction_wordings[0])
    assert narrowing < not_seen < prediction
    assert parts.count("One thing you don't know") == 1
    assert parts.endswith("Then ask them what would prove it wrong.")


def test_a_shared_pattern_with_nothing_one_sided_says_no_unseen_value() -> None:
    plain = [story(about="Priya", relationship=None, power=None) for _ in range(2)]
    mixed = [
        replace(told, tags=replace(told.tags, setting=None, audience=audience))
        for told, audience in zip(
            plain, (Audience.GROUP, Audience.ONE_TO_ONE), strict=True
        )
    ]

    assert "One thing you don't know" not in describe_three_parts(to_share(mixed))


def test_the_other_side_is_given_every_kept_narrowing_in_plain_words() -> None:
    observations = [
        under("Priya", audience=Audience.GROUP, state=StateGoingIn.WORN_OUT),
        under("Sam", audience=Audience.GROUP, state=StateGoingIn.WORN_OUT),
        under("Ravi", AGAINST, audience=Audience.ONE_TO_ONE, state=StateGoingIn.STEADY),
    ]

    given = describe_pattern_to_argue(
        PATTERN_TYPES[BELONG],
        observations,
        narrowings_of(observations, NUMBERS),
        None,
        NOW,
    )

    assert "- It shows in a group; not one-to-one" in given
    assert (
        "- It shows on days they were worn out; not on days they felt steady" in given
    )
    assert "Not narrowed." not in given
