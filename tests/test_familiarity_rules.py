from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from companion.core.familiarity import FamiliarityBars, familiarity_of
from companion.core.models import (
    Curiosity,
    CuriosityAim,
    CuriositySensitivity,
    CuriosityState,
    Familiarity,
    FamiliarityCounts,
    PatternState,
    ThoughtExperiment,
    ThoughtExperimentDetails,
    ThreadReaction,
)
from companion.core.starter_thought_experiments import (
    StarterInput,
    StarterNumbers,
    plan_starters,
)

NOW = datetime(2026, 11, 24, 12, tzinfo=UTC)
USER_ID = uuid4()
BARS = FamiliarityBars(conversations=5, life_threads=3, real_stories=0)
NUMBERS = StarterNumbers(most=4, days=timedelta(days=14), per_conversation=1)


def counts(
    conversations: int = 0,
    life_threads: int = 0,
    real_stories: int = 0,
    **patterns: int,
) -> FamiliarityCounts:
    """Make a User's counts, with Patterns given by state name."""
    return FamiliarityCounts(
        conversations=conversations,
        life_threads=life_threads,
        real_story_observations=real_stories,
        pattern_states={
            PatternState(state): count for state, count in patterns.items()
        },
    )


@pytest.mark.parametrize(
    ("their_counts", "expected"),
    [
        (counts(), Familiarity.NEW),
        (counts(conversations=4, life_threads=3), Familiarity.NEW),
        (counts(conversations=5, life_threads=2), Familiarity.NEW),
        (counts(conversations=5, life_threads=3), Familiarity.GETTING_TO_KNOW),
        (counts(conversations=1, suspected=1), Familiarity.GETTING_TO_KNOW),
        (counts(conversations=1, ready=1), Familiarity.GETTING_TO_KNOW),
        (counts(conversations=1, contested=1), Familiarity.GETTING_TO_KNOW),
        (counts(conversations=1, noticed=3, unmatched=2, closed=1), Familiarity.NEW),
        (counts(conversations=1, shared=1), Familiarity.KNOWS_WELL),
        (counts(conversations=1, confirmed=1), Familiarity.KNOWS_WELL),
        (
            counts(conversations=9, life_threads=9, suspected=2),
            Familiarity.GETTING_TO_KNOW,
        ),
    ],
)
def test_familiarity_follows_the_counts_and_the_bars(
    their_counts: FamiliarityCounts, expected: Familiarity
) -> None:
    assert familiarity_of(their_counts, BARS) == expected


def test_the_real_stories_bar_counts_once_an_admin_sets_it() -> None:
    bars = replace(BARS, real_stories=2)
    enough_talk = counts(conversations=5, life_threads=3, real_stories=1)

    assert familiarity_of(enough_talk, bars) == Familiarity.NEW
    assert (
        familiarity_of(replace(enough_talk, real_story_observations=2), bars)
        == Familiarity.GETTING_TO_KNOW
    )


def starter(
    minutes: int = 0, on: bool = True, starter: bool = True
) -> ThoughtExperiment:
    """Make one starter Thought Experiment, added `minutes` after the first."""
    return ThoughtExperiment(
        id=uuid4(),
        details=ThoughtExperimentDetails(
            wording=f"Made-up situation {minutes}. What do you do?",
            pattern_type_id="CONF.AVOID.BELONG",
            other_pattern_type_id="ACH.WORTH.PERF",
            sensitivity=CuriositySensitivity.LOW,
            starter=starter,
            on=on,
        ),
        created_at=NOW - timedelta(days=30) + timedelta(minutes=minutes),
        updated_at=NOW,
    )


def put(
    thought_experiment_id: UUID,
    state: CuriosityState = CuriosityState.RAISED,
    reaction: ThreadReaction | None = None,
) -> Curiosity:
    """Make the Curiosity that put a starter to the User, or waits to."""
    asked = state == CuriosityState.RAISED
    return Curiosity(
        id=uuid4(),
        user_id=USER_ID,
        question="Put this made-up situation to them",
        why="",
        not_before=None,
        sensitivity=CuriositySensitivity.LOW,
        state=state,
        created_at=NOW - timedelta(days=2),
        aim=CuriosityAim.STARTER,
        raised_at=NOW - timedelta(days=1) if asked else None,
        reaction=reaction,
        thought_experiment_id=thought_experiment_id,
    )


def starters_for(
    thought_experiments: list[ThoughtExperiment],
    put_before: list[Curiosity] | None = None,
    familiarity: Familiarity = Familiarity.NEW,
    signed_up_days_ago: int = 1,
    put_by_agenda: frozenset[UUID] = frozenset(),
) -> StarterInput:
    """Make what the starters are planned from."""
    return StarterInput(
        user_id=USER_ID,
        signed_up_at=NOW - timedelta(days=signed_up_days_ago),
        familiarity=familiarity,
        now=NOW,
        thought_experiments=thought_experiments,
        starters=put_before or [],
        put_by_agenda=put_by_agenda,
    )


def test_a_new_user_gets_the_oldest_starter_as_a_waiting_curiosity() -> None:
    newer, older = starter(minutes=5), starter(minutes=1)

    changes = plan_starters(starters_for([newer, older]), NUMBERS)

    [curiosity] = changes.added
    assert curiosity.aim == CuriosityAim.STARTER
    assert curiosity.thought_experiment_id == older.id
    assert curiosity.state == CuriosityState.WAITING
    assert curiosity.sensitivity == CuriositySensitivity.LOW
    assert f'keeping its words: "{older.details.wording}"' in curiosity.question
    assert curiosity.exploration_id is None
    assert changes.updated == []


def test_only_starters_that_are_on_and_never_put_to_them_are_picked() -> None:
    asked, by_agenda = starter(1), starter(2)
    off, not_a_starter, archived = (
        starter(3, on=False),
        starter(4, starter=False),
        replace(starter(5), archived_at=NOW),
    )
    left = starter(6)

    changes = plan_starters(
        starters_for(
            [asked, by_agenda, off, not_a_starter, archived, left],
            [put(asked.id)],
            put_by_agenda=frozenset({by_agenda.id}),
        ),
        NUMBERS,
    )

    assert [curiosity.thought_experiment_id for curiosity in changes.added] == [left.id]


def test_none_is_written_while_one_waits_so_a_conversation_gets_at_most_the_cap() -> (
    None
):
    first, second, third = starter(1), starter(2), starter(3)
    waiting = put(first.id, CuriosityState.WAITING)

    one_at_a_time = plan_starters(
        starters_for([first, second, third], [waiting]), NUMBERS
    )
    two_at_a_time = plan_starters(
        starters_for([first, second, third], [waiting]),
        replace(NUMBERS, per_conversation=2),
    )

    assert one_at_a_time.added == []
    assert [curiosity.thought_experiment_id for curiosity in two_at_a_time.added] == [
        second.id
    ]


def test_no_more_are_written_once_the_admin_set_number_were_put() -> None:
    thought_experiments = [starter(minutes) for minutes in range(6)]
    four_asked = [
        put(thought_experiment.id) for thought_experiment in thought_experiments[:4]
    ]
    three_asked_one_waiting = [
        *four_asked[:3],
        put(thought_experiments[3].id, CuriosityState.WAITING),
    ]

    assert (
        plan_starters(starters_for(thought_experiments, four_asked), NUMBERS).added
        == []
    )
    assert (
        plan_starters(
            starters_for(thought_experiments, three_asked_one_waiting),
            replace(NUMBERS, per_conversation=3),
        ).added
        == []
    )
    assert (
        plan_starters(starters_for(thought_experiments), replace(NUMBERS, most=0)).added
        == []
    )


def test_one_closed_unasked_may_be_put_again_and_does_not_count() -> None:
    only = starter()

    changes = plan_starters(
        starters_for([only], [put(only.id, CuriosityState.CLOSED)]),
        replace(NUMBERS, most=1),
    )

    assert [curiosity.thought_experiment_id for curiosity in changes.added] == [only.id]


@pytest.mark.parametrize(
    "familiarity", [Familiarity.GETTING_TO_KNOW, Familiarity.KNOWS_WELL]
)
def test_starters_stop_once_zeph_is_getting_to_know_them(
    familiarity: Familiarity,
) -> None:
    first, second = starter(1), starter(2)
    waiting = put(first.id, CuriosityState.WAITING)

    changes = plan_starters(
        starters_for([first, second], [waiting], familiarity=familiarity), NUMBERS
    )

    assert changes.added == []
    assert changes.updated == [replace(waiting, state=CuriosityState.CLOSED)]


def test_starters_stop_after_the_admin_set_days_since_sign_up() -> None:
    first, second = starter(1), starter(2)
    waiting = put(first.id, CuriosityState.WAITING)

    in_time = plan_starters(starters_for([first], signed_up_days_ago=13), NUMBERS)
    too_late = plan_starters(
        starters_for([first, second], [waiting], signed_up_days_ago=14), NUMBERS
    )

    assert len(in_time.added) == 1
    assert too_late.added == []
    assert too_late.updated == [replace(waiting, state=CuriosityState.CLOSED)]


def test_starters_stop_when_the_user_asked_zeph_to_drop_one() -> None:
    first, second = starter(1), starter(2)
    dropped = put(first.id, reaction=ThreadReaction.ASKED_TO_DROP)

    changes = plan_starters(starters_for([first, second], [dropped]), NUMBERS)

    assert changes.added == []
