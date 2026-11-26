from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from companion.core.models import (
    Curiosity,
    CuriosityAim,
    CuriositySensitivity,
    CuriosityState,
    EvidenceKind,
    ExplorationApproach,
    ExplorationNeed,
    ExplorationTry,
    Observation,
    ObservationDirection,
    Relationship,
    SituationSetting,
    SituationTags,
    ThoughtExperiment,
    ThoughtExperimentDetails,
)
from companion.core.thought_experiments import (
    leading_flags,
    pick_thought_experiment,
    put_to_user,
    thought_experiments_this_week,
    unclear_pairs,
)

NOW = datetime(2026, 11, 24, 12, tzinfo=UTC)
BELONG = "CONF.AVOID.BELONG"
WORTH = "ACH.WORTH.PERF"
PLAN = "CTRL.UNCERT.PLAN"
USER_ID = uuid4()
EXPLORATION_ID = uuid4()


def observation(
    second: str | None = None, first: str = BELONG, day: int = 20
) -> Observation:
    """Make one Observation of CONF.AVOID.BELONG, unclear with `second` if given."""
    return Observation(
        id=uuid4(),
        user_id=USER_ID,
        conversation_id=uuid4(),
        pattern_type_id=first,
        pattern_type_version="0.2.0",
        sign_id="I1",
        direction=ObservationDirection.FOR,
        quote="it's fine honestly",
        context="Said yes to Mei again.",
        day=date(2026, 11, day),
        thread_id=None,
        about="Mei, their sister",
        tags=SituationTags(
            relationship=Relationship.FAMILY,
            power=None,
            setting=SituationSetting.HOME,
            stance=None,
        ),
        evidence_kind=EvidenceKind.REAL_STORY,
        second_pattern_type_id=second,
        second_pattern_type_version="0.1.0" if second else None,
        situational=False,
        tagged_at=NOW,
    )


def thought_experiment(
    pair: tuple[str, str] = (BELONG, WORTH),
    on: bool = True,
    archived: bool = False,
    created_minutes: int = 0,
) -> ThoughtExperiment:
    """Make one Thought Experiment telling the two Pattern Types apart."""
    return ThoughtExperiment(
        id=uuid4(),
        details=ThoughtExperimentDetails(
            wording="A friend asks you to read their speech. What do you say?",
            pattern_type_id=pair[0],
            other_pattern_type_id=pair[1],
            sensitivity=CuriositySensitivity.LOW,
            starter=False,
            on=on,
        ),
        created_at=NOW + timedelta(minutes=created_minutes),
        updated_at=NOW,
        archived_at=NOW if archived else None,
    )


def asked(
    thought_experiment_id: UUID,
    state: CuriosityState = CuriosityState.RAISED,
    raised_days_ago: int = 1,
) -> tuple[ExplorationTry, Curiosity]:
    """Make a try that put a Thought Experiment to the User, with its Curiosity."""
    curiosity = Curiosity(
        id=uuid4(),
        user_id=USER_ID,
        question="Put this made-up situation to them",
        why="",
        not_before=None,
        sensitivity=CuriositySensitivity.LOW,
        state=state,
        created_at=NOW - timedelta(days=raised_days_ago + 1),
        aim=CuriosityAim.EXPLORATION,
        exploration_id=EXPLORATION_ID,
        raised_at=(
            NOW - timedelta(days=raised_days_ago)
            if state == CuriosityState.RAISED
            else None
        ),
    )
    attempt = ExplorationTry(
        curiosity_id=curiosity.id,
        exploration_id=EXPLORATION_ID,
        user_id=USER_ID,
        need=ExplorationNeed.UNCLEAR,
        approach=ExplorationApproach.THOUGHT_EXPERIMENT,
        created_at=curiosity.created_at,
        thought_experiment_id=thought_experiment_id,
    )
    return attempt, curiosity


@pytest.mark.parametrize(
    "wording",
    [
        "Your partner forgets your birthday. Wouldn't you be hurt?",
        "Surely you'd tell them how you feel?",
        "Most people would say no. What would you do?",
        "Your boss asks for one more favour. Be honest: would you say yes?",
        "A friend cancels again. Isn’t it time you said something?",
        "Would you be selfish and say no, or help out?",
    ],
)
def test_wording_that_suggests_the_answer_is_flagged(wording: str) -> None:
    flags = leading_flags(wording)

    assert flags
    assert all("Ask what they would do" in flag for flag in flags)


def test_open_wording_is_not_flagged() -> None:
    assert (
        leading_flags(
            "A close friend asks you to read their wedding speech, and it isn't "
            "good. The wedding is in two days. What do you tell them, and what "
            "goes through your mind first?"
        )
        == []
    )


def test_each_leading_phrase_is_flagged_once_and_named() -> None:
    flags = leading_flags("Surely, surely you would. Wouldn't you?")

    assert len(flags) == 2
    assert flags[0].startswith("“Surely”")
    assert flags[1].startswith("“Wouldn't you”")


def test_pairs_are_ranked_by_how_much_unclear_evidence_they_have() -> None:
    observations = [
        observation(PLAN, day=22),
        observation(WORTH, day=20),
        observation(WORTH, day=21),
        observation(),
        observation(BELONG, first=WORTH, day=19),
    ]

    assert unclear_pairs(BELONG, observations) == [
        frozenset({BELONG, WORTH}),
        frozenset({BELONG, PLAN}),
    ]


def test_with_equal_unclear_evidence_the_newest_pair_comes_first() -> None:
    observations = [observation(WORTH, day=20), observation(PLAN, day=22)]

    assert unclear_pairs(BELONG, observations)[0] == frozenset({BELONG, PLAN})


def test_the_thought_experiment_for_the_pair_with_most_unclear_evidence_is_picked() -> (
    None
):
    plan_one = thought_experiment((PLAN, BELONG))
    worth_one = thought_experiment((WORTH, BELONG))
    observations = [observation(WORTH), observation(WORTH), observation(PLAN)]

    picked = pick_thought_experiment(
        BELONG, observations, [plan_one, worth_one], put_to=set()
    )

    assert picked == worth_one


def test_switched_off_archived_and_already_put_ones_are_never_picked() -> None:
    off = thought_experiment(on=False)
    archived = thought_experiment(archived=True)
    already = thought_experiment(created_minutes=1)
    fresh = thought_experiment(created_minutes=2)

    picked = pick_thought_experiment(
        BELONG, [observation(WORTH)], [off, archived, already, fresh], {already.id}
    )

    assert picked == fresh


def test_the_next_pair_is_used_when_the_top_pair_has_none_left() -> None:
    plan_one = thought_experiment((BELONG, PLAN))
    observations = [observation(WORTH), observation(WORTH), observation(PLAN)]

    assert pick_thought_experiment(BELONG, observations, [plan_one], set()) == (
        plan_one
    )


def test_none_is_picked_without_unclear_evidence() -> None:
    assert (
        pick_thought_experiment(BELONG, [observation()], [thought_experiment()], set())
        is None
    )


def test_oldest_first_among_those_for_the_same_pair() -> None:
    newer = thought_experiment(created_minutes=5)
    older = thought_experiment(created_minutes=1)

    assert (
        pick_thought_experiment(BELONG, [observation(WORTH)], [newer, older], set())
        == older
    )


def test_a_thought_experiment_waiting_or_asked_is_put_to_the_user() -> None:
    raised_id, waiting_id, closed_id = uuid4(), uuid4(), uuid4()
    raised = asked(raised_id)
    waiting = asked(waiting_id, CuriosityState.WAITING)
    closed = asked(closed_id, CuriosityState.CLOSED)

    assert put_to_user(
        [raised[0], waiting[0], closed[0]],
        {c.id: c for _, c in (raised, waiting, closed)},
    ) == {raised_id, waiting_id}


def test_this_weeks_count_is_those_asked_in_seven_days_or_waiting() -> None:
    tries = [
        asked(uuid4(), raised_days_ago=2),
        asked(uuid4(), raised_days_ago=8),
        asked(uuid4(), CuriosityState.WAITING),
        asked(uuid4(), CuriosityState.CLOSED),
    ]
    other_way = replace(tries[0][0], curiosity_id=uuid4(), thought_experiment_id=None)

    count = thought_experiments_this_week(
        [attempt for attempt, _ in tries] + [other_way],
        {curiosity.id: curiosity for _, curiosity in tries},
        NOW,
    )

    assert count == 2
