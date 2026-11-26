from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from companion.adapters.pattern_catalog_seed import read_pattern_catalog_seed
from companion.core.agenda import (
    AgendaInput,
    AgendaNumbers,
    OpenNeed,
    aimed_question,
    approaches_for,
    describe_need,
    next_approach,
    open_needs,
    plan_agenda,
    rank_explorations,
    tries_with_nothing,
    try_outcome,
)
from companion.core.condition_coverage import VALUES_TO_LEARN
from companion.core.models import (
    AgendaChanges,
    Audience,
    CatalogPattern,
    Condition,
    Curiosity,
    CuriosityAim,
    CuriositySensitivity,
    CuriosityState,
    EvidenceKind,
    Exploration,
    ExplorationApproach,
    ExplorationNeed,
    ExplorationState,
    ExplorationTry,
    Observation,
    ObservationDirection,
    PatternState,
    Relationship,
    SituationSetting,
    SituationTags,
    Stakes,
    StateGoingIn,
    ThoughtExperiment,
    ThoughtExperimentDetails,
    ThreadReaction,
    TryOutcome,
)
from companion.core.pattern_catalog import read_pattern_types
from companion.core.pattern_scoring import PatternScore
from tests.conftest import PATTERN_CATALOG_DIR

NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
TODAY = date(2026, 11, 24)
USER_ID = uuid4()
ENDED = uuid4()
EARLIER = uuid4()
BELONG = "CONF.AVOID.BELONG"
WORTH = "ACH.WORTH.PERF"
PLAN = "CTRL.UNCERT.PLAN"
PATTERN_TYPES = {
    pattern_type.id: pattern_type
    for pattern_type in read_pattern_types(
        read_pattern_catalog_seed(PATTERN_CATALOG_DIR)
    )
}
NUMBERS = AgendaNumbers(
    size=3,
    wait=timedelta(days=3),
    rest_after_tries=4,
    thought_experiments_per_week=1,
    one_sided_stories=2,
)


def observation(
    setting: SituationSetting | None = SituationSetting.HOME,
    direction: ObservationDirection = ObservationDirection.FOR,
    second: str | None = None,
    days_ago: int = 0,
    pattern_type: str = BELONG,
    conversation_id: UUID = EARLIER,
    tagged_at: datetime = NOW - timedelta(days=10),
    relationship: Relationship | None = Relationship.FAMILY,
    audience: Audience | None = None,
    stakes: Stakes | None = None,
    state_going_in: StateGoingIn | None = None,
    situational: bool = False,
    excluded: bool = False,
) -> Observation:
    """A clear real story for CONF.AVOID.BELONG at home, unless changed."""
    return Observation(
        id=uuid4(),
        user_id=USER_ID,
        conversation_id=conversation_id,
        pattern_type_id=pattern_type,
        pattern_type_version="0.2.0",
        sign_id="I2",
        direction=direction,
        quote="I said yes again",
        context="Mei asked for help moving; they said yes though worn out",
        day=TODAY - timedelta(days=days_ago),
        thread_id=None,
        about="their sister",
        tags=SituationTags(
            relationship=relationship,
            power=None,
            setting=setting,
            stance=None,
            audience=audience,
            stakes=stakes,
            state_going_in=state_going_in,
        ),
        evidence_kind=EvidenceKind.REAL_STORY,
        second_pattern_type_id=second,
        second_pattern_type_version="0.1.0" if second else None,
        situational=situational,
        tagged_at=tagged_at,
        excluded=excluded,
    )


def pattern(
    state: PatternState = PatternState.SUSPECTED, pattern_type: str = BELONG
) -> CatalogPattern:
    """A User's Pattern of a Pattern Type, in a state."""
    return CatalogPattern(
        id=uuid4(),
        user_id=USER_ID,
        pattern_type_id=pattern_type,
        state=state,
        started_at=NOW - timedelta(days=30),
        updated_at=NOW - timedelta(days=30),
    )


def exploration(
    of: CatalogPattern,
    state: ExplorationState = ExplorationState.ACTIVE,
    days_old: int = 20,
    rested_at: datetime | None = None,
    woke_at: datetime | None = None,
) -> Exploration:
    """An Exploration of a Pattern."""
    return Exploration(
        id=uuid4(),
        user_id=USER_ID,
        pattern_id=of.id,
        pattern_type_id=of.pattern_type_id,
        state=state,
        created_at=NOW - timedelta(days=days_old),
        updated_at=NOW - timedelta(days=days_old),
        rested_at=rested_at,
        woke_at=woke_at,
    )


def asked(
    of: Exploration,
    need: ExplorationNeed = ExplorationNeed.COUNTER_TEST,
    approach: ExplorationApproach = ExplorationApproach.STORY_FOLLOW_UP,
    days_ago: int = 5,
    conversation_id: UUID = EARLIER,
    reaction: ThreadReaction | None = ThreadReaction.ENGAGED,
    outcome: TryOutcome | None = TryOutcome.VAGUE,
    aimed_at: Observation | None = None,
    condition: Condition | None = None,
    condition_value: str | None = None,
    state: CuriosityState = CuriosityState.RAISED,
    thought_experiment: ThoughtExperiment | None = None,
) -> tuple[Curiosity, ExplorationTry]:
    """An aimed Curiosity of an Exploration and its try, asked some days ago."""
    raised_at = (
        NOW - timedelta(days=days_ago) if state == CuriosityState.RAISED else None
    )
    curiosity = Curiosity(
        id=uuid4(),
        user_id=USER_ID,
        question="Ask about it.",
        why="To learn.",
        not_before=None,
        sensitivity=CuriositySensitivity.MEDIUM,
        state=state,
        created_at=NOW - timedelta(days=days_ago + 1),
        aim=CuriosityAim.EXPLORATION,
        raised_at=raised_at,
        raised_conversation_id=conversation_id if raised_at else None,
        reaction=reaction if raised_at else None,
        exploration_id=of.id,
    )
    return curiosity, ExplorationTry(
        curiosity_id=curiosity.id,
        exploration_id=of.id,
        user_id=USER_ID,
        need=need,
        approach=approach,
        created_at=curiosity.created_at,
        observation_id=aimed_at.id if aimed_at else None,
        condition=condition,
        condition_value=condition_value,
        outcome=outcome if raised_at else None,
        thought_experiment_id=thought_experiment.id if thought_experiment else None,
    )


def thought_experiment(
    pair: tuple[str, str] = (BELONG, WORTH),
    on: bool = True,
    archived: bool = False,
) -> ThoughtExperiment:
    """A Thought Experiment telling two Pattern Types apart, low sensitivity."""
    return ThoughtExperiment(
        id=uuid4(),
        details=ThoughtExperimentDetails(
            wording="A close friend reads your work and says one part fails. What "
            "stays with you more?",
            pattern_type_id=pair[0],
            other_pattern_type_id=pair[1],
            sensitivity=CuriositySensitivity.LOW,
            starter=False,
            on=on,
        ),
        created_at=NOW - timedelta(days=60),
        updated_at=NOW - timedelta(days=60),
        archived_at=NOW if archived else None,
    )


def keep(
    patterns: list[CatalogPattern],
    observations: list[Observation],
    explorations: list[Exploration] | None = None,
    tried: list[tuple[Curiosity, ExplorationTry]] | None = None,
    scores: dict[str, PatternScore] | None = None,
    numbers: AgendaNumbers = NUMBERS,
    thought_experiments: list[ThoughtExperiment] | None = None,
) -> AgendaChanges:
    """Keep the Agenda at the end of the Conversation ENDED."""
    tried = tried or []
    return plan_agenda(
        AgendaInput(
            user_id=USER_ID,
            patterns=patterns,
            observations=observations,
            scores=scores or {},
            pattern_types=PATTERN_TYPES,
            explorations=explorations or [],
            tries=[attempt for _, attempt in tried],
            aimed=[curiosity for curiosity, _ in tried],
            conversation_id=ENDED,
            now=NOW,
            time_zone="Asia/Singapore",
            thought_experiments=thought_experiments or [],
        ),
        numbers,
    )


def needs_of(
    observations: list[Observation],
    tries: list[ExplorationTry] | None = None,
    one_sided_stories: int = 2,
) -> list[OpenNeed]:
    """The open needs of a Pattern with these Observations and tries."""
    return open_needs(observations, tries or [], one_sided_stories)


def group_story(days_ago: int = 0, **changes: Any) -> Observation:
    """A clear story for the Pattern in a group, with nothing else tagged."""
    return observation(
        **{
            "setting": None,
            "relationship": None,
            "audience": Audience.GROUP,
            "days_ago": days_ago,
            **changes,
        }
    )


def test_unclear_stories_come_first_then_a_counter_test_then_a_condition() -> None:
    older_unclear = observation(second=WORTH, days_ago=9, setting=None)
    newer_unclear = observation(second=WORTH, days_ago=2, setting=None)
    older_at_home = observation(days_ago=6)
    newer_at_home = observation(days_ago=4)

    needs = needs_of([older_unclear, older_at_home, newer_unclear, newer_at_home])

    assert needs == [
        OpenNeed(ExplorationNeed.UNCLEAR, observation=newer_unclear),
        OpenNeed(ExplorationNeed.UNCLEAR, observation=older_unclear),
        OpenNeed(ExplorationNeed.COUNTER_TEST, observation=newer_at_home),
        OpenNeed(
            ExplorationNeed.MISSING_CONDITION,
            observation=newer_at_home,
            condition=Condition.RELATIONSHIP,
            value="friend",
        ),
    ]


def missing(needs: list[OpenNeed]) -> list[tuple[Condition | None, str | None]]:
    """The Condition and value of each missing-Condition need."""
    return [
        (need.condition, need.value)
        for need in needs
        if need.need == ExplorationNeed.MISSING_CONDITION
    ]


def test_one_story_alone_is_not_one_sided() -> None:
    assert missing(needs_of([group_story()])) == []


def test_two_stories_sharing_a_value_open_a_need_for_a_value_not_seen() -> None:
    assert missing(needs_of([group_story(1), group_story(2)])) == [
        (Condition.AUDIENCE, "one-to-one")
    ]


def test_the_admin_set_number_of_stories_makes_a_condition_one_sided() -> None:
    stories = [group_story(1), group_story(2)]

    assert missing(needs_of(stories, one_sided_stories=3)) == []
    assert missing(needs_of([*stories, group_story(3)], one_sided_stories=3)) == [
        (Condition.AUDIENCE, "one-to-one")
    ]


def test_two_stories_with_different_values_are_not_one_sided() -> None:
    stories = [group_story(1), group_story(2, audience=Audience.ONE_TO_ONE)]

    assert missing(needs_of(stories)) == []


def test_a_value_already_seen_against_is_not_what_to_learn() -> None:
    stories = [
        group_story(1),
        group_story(2),
        group_story(
            3, audience=Audience.ONE_TO_ONE, direction=ObservationDirection.AGAINST
        ),
    ]

    assert missing(needs_of(stories)) == [(Condition.AUDIENCE, "in front of others")]


def test_a_condition_with_every_value_seen_is_no_need() -> None:
    stories = [
        group_story(1, audience=None, stakes=Stakes.HIGH),
        group_story(2, audience=None, stakes=Stakes.HIGH),
        group_story(
            3,
            audience=None,
            stakes=Stakes.LOW,
            direction=ObservationDirection.AGAINST,
        ),
    ]

    assert missing(needs_of(stories)) == []


def test_of_two_one_sided_conditions_only_the_one_with_most_stories_is_a_need() -> None:
    stories = [
        group_story(1, stakes=Stakes.HIGH),
        group_story(2, audience=None, stakes=Stakes.HIGH),
        group_story(3, stakes=Stakes.HIGH),
    ]

    assert missing(needs_of(stories)) == [(Condition.STAKES, "low")]


def test_a_tie_between_one_sided_conditions_goes_by_a_fixed_order() -> None:
    stories = [
        group_story(1, stakes=Stakes.HIGH, setting=SituationSetting.WORK),
        group_story(2, stakes=Stakes.HIGH, setting=SituationSetting.WORK),
    ]

    assert missing(needs_of(stories)) == [(Condition.AUDIENCE, "one-to-one")]


def test_home_work_and_social_are_asked_about_by_the_same_rule() -> None:
    at_home = [
        observation(days_ago=1, relationship=None),
        observation(days_ago=2, relationship=None),
    ]
    seen_apart = [
        observation(setting=SituationSetting.HOME, relationship=None),
        observation(setting=SituationSetting.WORK, relationship=None),
    ]

    assert missing(needs_of(at_home)) == [(Condition.SETTING, "work")]
    assert missing(needs_of(seen_apart)) == []
    assert missing(needs_of([observation(relationship=None)])) == []


def test_unclear_situational_and_excluded_stories_never_make_it_one_sided() -> None:
    clear = group_story(1)
    not_clear = [
        group_story(2, second=WORTH),
        group_story(3, situational=True),
        group_story(4, excluded=True),
    ]

    assert missing(needs_of([clear, *not_clear])) == []


def test_a_useful_try_closes_that_value_for_good_and_the_next_one_opens() -> None:
    its = exploration(pattern())
    stories = [group_story(1), group_story(2)]
    _, useful = asked(
        its,
        need=ExplorationNeed.MISSING_CONDITION,
        condition=Condition.AUDIENCE,
        condition_value="one-to-one",
        outcome=TryOutcome.USEFUL,
    )
    _, vague = asked(
        its,
        need=ExplorationNeed.MISSING_CONDITION,
        condition=Condition.AUDIENCE,
        condition_value="one-to-one",
        outcome=TryOutcome.VAGUE,
    )

    assert missing(needs_of(stories, [vague])) == [(Condition.AUDIENCE, "one-to-one")]
    assert missing(needs_of(stories, [useful])) == [
        (Condition.AUDIENCE, "in front of others")
    ]


def test_a_state_need_starts_from_no_story() -> None:
    worn_out = [
        group_story(1, audience=None, state_going_in=StateGoingIn.WORN_OUT),
        group_story(2, audience=None, state_going_in=StateGoingIn.WORN_OUT),
    ]

    [_, need] = needs_of(worn_out)

    assert (need.condition, need.observation) == (Condition.STATE_GOING_IN, None)


def test_the_counter_test_closes_with_evidence_against_or_a_useful_counter_test() -> (
    None
):
    story = observation(setting=None)
    against = observation(setting=None, direction=ObservationDirection.AGAINST)
    its = exploration(pattern())
    _, useful = asked(its, outcome=TryOutcome.USEFUL)
    _, vague = asked(its, outcome=TryOutcome.VAGUE)

    assert needs_of([story, against]) == []
    assert needs_of([story], [useful]) == []
    assert needs_of([story], [vague]) == [
        OpenNeed(ExplorationNeed.COUNTER_TEST, observation=story)
    ]


def test_each_try_at_a_need_moves_to_a_different_approach_least_pushy_first() -> None:
    its = exploration(pattern())
    need = OpenNeed(ExplorationNeed.COUNTER_TEST)
    first = asked(its, approach=ExplorationApproach.STORY_FOLLOW_UP, days_ago=9)
    second = asked(its, approach=ExplorationApproach.WOULD_IT_DIFFER, days_ago=5)
    third = asked(its, approach=ExplorationApproach.THOUGHT_EXPERIMENT, days_ago=4)
    fourth = asked(its, approach=ExplorationApproach.NOTICE_THIS_WEEK, days_ago=2)

    def approach_after(*tried: tuple[Curiosity, ExplorationTry]) -> ExplorationApproach:
        return next_approach(
            need,
            [attempt for _, attempt in tried],
            {c.id: c.raised_at for c, _ in tried if c.raised_at},
        )

    assert approach_after() == ExplorationApproach.STORY_FOLLOW_UP
    assert approach_after(first) == ExplorationApproach.WOULD_IT_DIFFER
    assert approach_after(first, second) == ExplorationApproach.THOUGHT_EXPERIMENT
    assert approach_after(first, second, third) == ExplorationApproach.NOTICE_THIS_WEEK
    assert (
        approach_after(first, second, third, fourth)
        == ExplorationApproach.STORY_FOLLOW_UP
    )


def test_after_a_useful_try_the_same_approach_is_used_again() -> None:
    its = exploration(pattern())
    curiosity, useful = asked(
        its, approach=ExplorationApproach.WOULD_IT_DIFFER, outcome=TryOutcome.USEFUL
    )

    approach = next_approach(
        OpenNeed(ExplorationNeed.COUNTER_TEST), [useful], {curiosity.id: NOW}
    )

    assert approach == ExplorationApproach.WOULD_IT_DIFFER


def test_a_try_at_another_need_does_not_move_this_ones_approach() -> None:
    its = exploration(pattern())
    story = observation(second=WORTH)
    curiosity, at_work = asked(
        its,
        need=ExplorationNeed.MISSING_CONDITION,
        condition=Condition.SETTING,
        condition_value="work",
    )

    approach = next_approach(
        OpenNeed(ExplorationNeed.UNCLEAR, observation=story),
        [at_work],
        {curiosity.id: NOW},
    )

    assert approach == ExplorationApproach.STORY_FOLLOW_UP


@pytest.mark.parametrize(
    ("reaction", "settled", "new_evidence", "outcome"),
    [
        (ThreadReaction.BRUSHED_OFF, True, True, TryOutcome.BRUSHED_OFF),
        (ThreadReaction.ASKED_TO_DROP, False, True, TryOutcome.BRUSHED_OFF),
        (ThreadReaction.ENGAGED, True, False, TryOutcome.USEFUL),
        (ThreadReaction.ENGAGED, False, True, TryOutcome.USEFUL),
        (ThreadReaction.ENGAGED, False, False, TryOutcome.VAGUE),
        (None, False, True, TryOutcome.VAGUE),
        (None, True, False, TryOutcome.USEFUL),
    ],
)
def test_code_decides_how_a_try_came_back(
    reaction: ThreadReaction | None,
    settled: bool,
    new_evidence: bool,
    outcome: TryOutcome,
) -> None:
    assert try_outcome(reaction, settled, new_evidence) == outcome


def test_tries_with_nothing_count_in_a_row_since_the_last_useful_or_waking() -> None:
    its = exploration(pattern())
    tried = [
        asked(its, outcome=TryOutcome.VAGUE, days_ago=12),
        asked(its, outcome=TryOutcome.USEFUL, days_ago=9),
        asked(its, outcome=TryOutcome.VAGUE, days_ago=6),
        asked(its, outcome=TryOutcome.BRUSHED_OFF, days_ago=3),
    ]
    asked_at = {c.id: c.raised_at for c, _ in tried if c.raised_at}
    tries = [attempt for _, attempt in tried]

    assert tries_with_nothing(its, tries, asked_at) == 2
    woken = replace(its, woke_at=NOW - timedelta(days=4))
    assert tries_with_nothing(woken, tries, asked_at) == 1


def test_explorations_rank_by_score_then_oldest() -> None:
    low = exploration(pattern(pattern_type=PLAN), days_old=30)
    high_new = exploration(pattern(pattern_type=BELONG), days_old=2)
    high_old = exploration(pattern(pattern_type=WORTH), days_old=9)
    scores = {
        PLAN: PatternScore(points=120, situations=2),
        BELONG: PatternScore(points=300, situations=2),
        WORTH: PatternScore(points=300, situations=3),
    }

    assert rank_explorations([low, high_new, high_old], scores) == [
        high_old,
        high_new,
        low,
    ]


def test_a_suspected_pattern_gets_an_exploration_and_an_aimed_curiosity() -> None:
    suspected = pattern()
    noticed = pattern(PatternState.NOTICED, WORTH)
    story = observation(second=WORTH, days_ago=3)

    planned = keep([suspected, noticed], [story])

    [added] = planned.added
    assert (added.pattern_id, added.state) == (suspected.id, ExplorationState.ACTIVE)
    [curiosity] = planned.new_curiosities
    assert curiosity.aim == CuriosityAim.EXPLORATION
    assert curiosity.exploration_id == added.id
    assert curiosity.source_observation_id == story.id
    assert curiosity.state == CuriosityState.WAITING
    assert curiosity.not_before is None
    assert "Go back to what they told you about their sister on 21 Nov 2026" in (
        curiosity.question
    )
    assert "Conflict" not in curiosity.question + curiosity.why
    [attempt] = planned.new_tries
    assert (attempt.need, attempt.approach, attempt.observation_id) == (
        ExplorationNeed.UNCLEAR,
        ExplorationApproach.STORY_FOLLOW_UP,
        story.id,
    )


def test_only_the_admin_set_number_are_active_highest_score_first() -> None:
    patterns = [pattern(pattern_type=kind) for kind in (BELONG, WORTH, PLAN)]
    scores = {
        BELONG: PatternScore(points=150, situations=2),
        WORTH: PatternScore(points=400, situations=2),
        PLAN: PatternScore(points=250, situations=2),
    }
    observations = [observation(pattern_type=kind) for kind in (BELONG, WORTH, PLAN)]

    planned = keep(
        patterns,
        observations,
        scores=scores,
        numbers=replace(NUMBERS, size=2),
    )

    states = {item.pattern_type_id: item.state for item in planned.added}
    assert states == {
        WORTH: ExplorationState.ACTIVE,
        PLAN: ExplorationState.ACTIVE,
        BELONG: ExplorationState.WAITING,
    }
    assert {c.exploration_id for c in planned.new_curiosities} == {
        item.id for item in planned.added if item.state == ExplorationState.ACTIVE
    }


def test_a_try_asked_in_this_conversation_is_judged_and_none_is_written_now() -> None:
    suspected = pattern()
    story = observation(second=WORTH, days_ago=3)
    its = exploration(suspected)
    curiosity, attempt = asked(
        its,
        need=ExplorationNeed.UNCLEAR,
        aimed_at=story,
        days_ago=0,
        conversation_id=ENDED,
        outcome=None,
    )

    planned = keep([suspected], [story], [its], [(curiosity, attempt)])

    [judged] = planned.judged
    assert judged.outcome == TryOutcome.VAGUE
    assert planned.new_curiosities == []


def test_a_settled_unclear_story_is_a_useful_try() -> None:
    suspected = pattern()
    settled = observation(days_ago=3)
    its = exploration(suspected)
    tried = asked(
        its,
        need=ExplorationNeed.UNCLEAR,
        aimed_at=settled,
        days_ago=0,
        conversation_id=ENDED,
        outcome=None,
    )

    [judged] = keep([suspected], [settled], [its], [tried]).judged

    assert judged.outcome == TryOutcome.USEFUL


def test_new_evidence_from_the_conversation_makes_a_try_useful() -> None:
    suspected = pattern()
    its = exploration(suspected)
    new = observation(setting=SituationSetting.WORK, conversation_id=ENDED)
    tried = asked(its, days_ago=0, conversation_id=ENDED, outcome=None)

    [judged] = keep([suspected], [observation(), new], [its], [tried]).judged

    assert judged.outcome == TryOutcome.USEFUL


def test_after_a_try_with_nothing_the_next_is_a_different_approach_after_the_wait() -> (
    None
):
    suspected = pattern()
    story = observation(second=WORTH, days_ago=6)
    its = exploration(suspected)
    tried = asked(
        its,
        need=ExplorationNeed.UNCLEAR,
        aimed_at=story,
        days_ago=1,
        outcome=TryOutcome.BRUSHED_OFF,
    )

    planned = keep([suspected], [story], [its], [tried])

    [curiosity] = planned.new_curiosities
    assert curiosity.not_before == date(2026, 11, 26)
    [attempt] = planned.new_tries
    assert (attempt.need, attempt.approach) == (
        ExplorationNeed.UNCLEAR,
        ExplorationApproach.WOULD_IT_DIFFER,
    )


def test_after_a_useful_try_the_next_has_no_wait() -> None:
    suspected = pattern()
    its = exploration(suspected)
    tried = asked(
        its,
        outcome=TryOutcome.USEFUL,
        days_ago=1,
    )

    stories = [group_story(2), group_story(3)]

    [curiosity] = keep([suspected], stories, [its], [tried]).new_curiosities

    assert curiosity.not_before is None


def test_a_waiting_aimed_curiosity_for_the_top_need_is_left_alone() -> None:
    suspected = pattern()
    its = exploration(suspected)
    waiting = asked(
        its,
        state=CuriosityState.WAITING,
    )

    planned = keep([suspected], [observation()], [its], [waiting])

    assert planned.new_curiosities == []
    assert planned.closed_curiosity_ids == []


def test_a_waiting_aimed_curiosity_no_longer_aimed_at_the_top_need_is_replaced() -> (
    None
):
    suspected = pattern()
    its = exploration(suspected)
    unclear = observation(second=WORTH)
    waiting = asked(
        its,
        state=CuriosityState.WAITING,
    )

    planned = keep([suspected], [observation(), unclear], [its], [waiting])

    assert planned.closed_curiosity_ids == [waiting[0].id]
    [attempt] = planned.new_tries
    assert attempt.observation_id == unclear.id


def test_it_rests_after_the_tries_with_nothing_and_frees_its_place() -> None:
    first, second = pattern(pattern_type=BELONG), pattern(pattern_type=WORTH)
    tired = exploration(first)
    next_in_line = exploration(second, state=ExplorationState.WAITING)
    tried = [
        asked(tired, days_ago=days, outcome=TryOutcome.VAGUE) for days in (9, 7, 5)
    ]
    tried.append(
        asked(tired, days_ago=0, conversation_id=ENDED, reaction=None, outcome=None)
    )
    waiting = asked(
        next_in_line,
        state=CuriosityState.WAITING,
    )

    planned = keep(
        [first, second],
        [observation(), observation(pattern_type=WORTH)],
        [tired, next_in_line],
        [*tried, waiting],
        scores={BELONG: PatternScore(points=500, situations=2)},
        numbers=replace(NUMBERS, size=1),
    )

    changed = {item.id: item for item in planned.changed}
    assert changed[tired.id].state == ExplorationState.RESTING
    assert changed[tired.id].rested_at == NOW
    assert changed[next_in_line.id].state == ExplorationState.ACTIVE
    assert planned.closed_curiosity_ids == []


def test_asked_to_drop_rests_it_at_once() -> None:
    suspected = pattern()
    its = exploration(suspected)
    tried = asked(
        its,
        days_ago=0,
        conversation_id=ENDED,
        reaction=ThreadReaction.ASKED_TO_DROP,
        outcome=None,
    )

    [changed] = keep([suspected], [observation()], [its], [tried]).changed

    assert changed.state == ExplorationState.RESTING


def test_a_resting_exploration_wakes_only_on_a_new_observation() -> None:
    suspected = pattern()
    resting = exploration(
        suspected, state=ExplorationState.RESTING, rested_at=NOW - timedelta(days=2)
    )
    old = observation(tagged_at=NOW - timedelta(days=5))
    new = observation(setting=SituationSetting.WORK, tagged_at=NOW - timedelta(hours=1))

    still = keep([suspected], [old], [resting])
    woken = keep([suspected], [old, new], [resting])

    assert still.changed == []
    assert still.new_curiosities == []
    [awake] = woken.changed
    assert (awake.state, awake.woke_at) == (ExplorationState.ACTIVE, NOW)
    assert len(woken.new_curiosities) == 1


def test_an_exploration_whose_pattern_is_no_longer_suspected_leaves_the_agenda() -> (
    None
):
    noticed = pattern(PatternState.NOTICED)
    its = exploration(noticed)
    waiting = asked(its, state=CuriosityState.WAITING)

    planned = keep([noticed], [observation()], [its], [waiting])

    [changed] = planned.changed
    assert changed.state == ExplorationState.WAITING
    assert planned.closed_curiosity_ids == [waiting[0].id]
    assert planned.new_curiosities == []


CONDITION_NEEDS = [
    OpenNeed(
        ExplorationNeed.MISSING_CONDITION,
        observation=None if condition == Condition.STATE_GOING_IN else observation(),
        condition=condition,
        value=value,
    )
    for condition, values in VALUES_TO_LEARN.items()
    for value in values
]


@pytest.mark.parametrize(
    "open_need",
    [
        OpenNeed(ExplorationNeed.UNCLEAR, observation=observation()),
        OpenNeed(ExplorationNeed.COUNTER_TEST, observation=observation()),
        OpenNeed(ExplorationNeed.COUNTER_TEST),
        *CONDITION_NEEDS,
    ],
)
def test_every_aimed_question_is_written_by_code_without_the_pattern(
    open_need: OpenNeed,
) -> None:
    belong = PATTERN_TYPES[BELONG]

    for approach in approaches_for(open_need):
        if approach == ExplorationApproach.THOUGHT_EXPERIMENT:
            continue
        question, why = aimed_question(open_need, approach, belong)

        assert question.startswith(("Ask", "Go back"))
        assert why
        assert belong.name not in question + why + describe_need(open_need)
        assert "I said yes again" not in question + why + describe_need(open_need)


def test_a_condition_is_asked_by_three_approaches_and_never_a_thought_experiment() -> (
    None
):
    its = exploration(pattern())
    need = OpenNeed(
        ExplorationNeed.MISSING_CONDITION,
        observation=observation(),
        condition=Condition.AUDIENCE,
        value="one-to-one",
    )
    tried = [
        asked(
            its,
            need=ExplorationNeed.MISSING_CONDITION,
            condition=Condition.AUDIENCE,
            condition_value="one-to-one",
            approach=approach,
            days_ago=days_ago,
        )
        for approach, days_ago in [
            (ExplorationApproach.STORY_FOLLOW_UP, 9),
            (ExplorationApproach.WOULD_IT_DIFFER, 6),
            (ExplorationApproach.NOTICE_THIS_WEEK, 3),
        ]
    ]

    def after(count: int) -> ExplorationApproach:
        return next_approach(
            need,
            [attempt for _, attempt in tried[:count]],
            {c.id: c.raised_at for c, _ in tried[:count] if c.raised_at},
        )

    assert [after(count) for count in range(4)] == [
        ExplorationApproach.STORY_FOLLOW_UP,
        ExplorationApproach.WOULD_IT_DIFFER,
        ExplorationApproach.NOTICE_THIS_WEEK,
        ExplorationApproach.STORY_FOLLOW_UP,
    ]


def test_the_would_it_differ_question_names_the_value_to_learn() -> None:
    need = OpenNeed(
        ExplorationNeed.MISSING_CONDITION,
        observation=observation(),
        condition=Condition.STAKES,
        value="low",
    )

    question, _ = aimed_question(
        need, ExplorationApproach.WOULD_IT_DIFFER, PATTERN_TYPES[BELONG]
    )

    assert question.endswith(
        "Ask whether it would have gone differently if less had been riding on it."
    )


def test_a_state_gap_is_asked_openly_never_by_would_it_differ_and_names_no_state() -> (
    None
):
    need = OpenNeed(
        ExplorationNeed.MISSING_CONDITION,
        condition=Condition.STATE_GOING_IN,
        value="steady",
    )
    state_words = [
        word for state in StateGoingIn for word in (state.value, "tired", "stress")
    ]

    assert approaches_for(need) == (
        ExplorationApproach.STORY_FOLLOW_UP,
        ExplorationApproach.NOTICE_THIS_WEEK,
    )
    for approach in approaches_for(need):
        question, why = aimed_question(need, approach, PATTERN_TYPES[BELONG])
        written = (question + why + describe_need(need)).lower()
        assert "how they were doing going into it" in question
        assert not [word for word in state_words if word in written]


def test_a_one_sided_pattern_gets_an_aimed_question_once_it_was_counter_tested() -> (
    None
):
    suspected = pattern()
    its = exploration(suspected)
    counter_test = asked(its, outcome=TryOutcome.USEFUL, days_ago=6)
    newest = group_story(1)

    planned = keep([suspected], [newest, group_story(2)], [its], [counter_test])

    [curiosity] = planned.new_curiosities
    [attempt] = planned.new_tries
    assert (
        attempt.need,
        attempt.approach,
        attempt.condition,
        attempt.condition_value,
        attempt.observation_id,
    ) == (
        ExplorationNeed.MISSING_CONDITION,
        ExplorationApproach.STORY_FOLLOW_UP,
        Condition.AUDIENCE,
        "one-to-one",
        newest.id,
    )
    assert "one-to-one, with just one other person" in curiosity.question
    assert curiosity.not_before is None


def condition_try(its: Exploration, **changes: Any) -> tuple[Curiosity, ExplorationTry]:
    """A try at learning how it goes one-to-one, vague unless changed."""
    return asked(
        its,
        **{
            "need": ExplorationNeed.MISSING_CONDITION,
            "condition": Condition.AUDIENCE,
            "condition_value": "one-to-one",
            **changes,
        },
    )


def test_a_condition_try_with_nothing_leads_to_the_next_approach_after_the_wait() -> (
    None
):
    suspected = pattern()
    its = exploration(suspected)
    tried = [
        asked(its, outcome=TryOutcome.USEFUL, days_ago=9),
        condition_try(its, days_ago=1),
    ]

    planned = keep([suspected], [group_story(3), group_story(4)], [its], tried)

    [curiosity] = planned.new_curiosities
    [attempt] = planned.new_tries
    assert (attempt.approach, attempt.condition_value) == (
        ExplorationApproach.WOULD_IT_DIFFER,
        "one-to-one",
    )
    assert curiosity.not_before == TODAY + timedelta(days=2)


def test_a_condition_is_never_asked_about_two_conversations_in_a_row() -> None:
    suspected = pattern()
    its = exploration(suspected)
    tried = [
        asked(its, outcome=TryOutcome.USEFUL, days_ago=9),
        condition_try(its, days_ago=0, conversation_id=ENDED, outcome=None),
    ]

    planned = keep([suspected], [group_story(3), group_story(4)], [its], tried)

    assert planned.new_curiosities == []


def test_condition_tries_with_nothing_rest_the_exploration() -> None:
    suspected = pattern()
    its = exploration(suspected)
    tried = [
        asked(its, outcome=TryOutcome.USEFUL, days_ago=20),
        *[condition_try(its, days_ago=days_ago) for days_ago in (12, 9, 6, 3)],
    ]

    planned = keep([suspected], [group_story(13), group_story(14)], [its], tried)

    [changed] = planned.changed
    assert changed.state == ExplorationState.RESTING
    assert planned.new_curiosities == []


def unclear_story_tried_twice(
    its: Exploration, story: Observation
) -> list[tuple[Curiosity, ExplorationTry]]:
    """Two tries with nothing at an unclear story, 10 and 8 days ago."""
    return [
        asked(
            its,
            need=ExplorationNeed.UNCLEAR,
            aimed_at=story,
            approach=ExplorationApproach.STORY_FOLLOW_UP,
            days_ago=10,
        ),
        asked(
            its,
            need=ExplorationNeed.UNCLEAR,
            aimed_at=story,
            approach=ExplorationApproach.WOULD_IT_DIFFER,
            days_ago=8,
        ),
    ]


def test_after_another_person_an_unclear_story_gets_a_thought_experiment() -> None:
    suspected = pattern()
    story = observation(second=WORTH, days_ago=12)
    its = exploration(suspected)
    worth_one = thought_experiment()

    planned = keep(
        [suspected],
        [story],
        [its],
        unclear_story_tried_twice(its, story),
        thought_experiments=[thought_experiment((BELONG, PLAN)), worth_one],
    )

    [attempt] = planned.new_tries
    assert (attempt.need, attempt.approach, attempt.thought_experiment_id) == (
        ExplorationNeed.UNCLEAR,
        ExplorationApproach.THOUGHT_EXPERIMENT,
        worth_one.id,
    )
    [curiosity] = planned.new_curiosities
    assert worth_one.details.wording in curiosity.question
    assert "keeping its words" in curiosity.question
    assert curiosity.sensitivity == CuriositySensitivity.LOW
    assert PATTERN_TYPES[BELONG].name not in curiosity.question + curiosity.why


def test_with_none_to_ask_the_next_approach_is_used() -> None:
    suspected = pattern()
    story = observation(second=WORTH, days_ago=12)
    its = exploration(suspected)

    planned = keep(
        [suspected],
        [story],
        [its],
        unclear_story_tried_twice(its, story),
        thought_experiments=[
            thought_experiment(on=False),
            thought_experiment(archived=True),
            thought_experiment((BELONG, PLAN)),
        ],
    )

    [attempt] = planned.new_tries
    assert (attempt.approach, attempt.thought_experiment_id) == (
        ExplorationApproach.NOTICE_THIS_WEEK,
        None,
    )


def test_never_more_than_the_admin_set_number_a_week_for_a_pattern() -> None:
    suspected = pattern()
    story = observation(second=WORTH, days_ago=12)
    its = exploration(suspected)
    asked_one = thought_experiment()
    tried = [
        asked(
            its,
            need=ExplorationNeed.UNCLEAR,
            aimed_at=story,
            approach=ExplorationApproach.WOULD_IT_DIFFER,
            days_ago=10,
        ),
        asked(
            its,
            need=ExplorationNeed.UNCLEAR,
            aimed_at=story,
            approach=ExplorationApproach.THOUGHT_EXPERIMENT,
            days_ago=4,
            outcome=TryOutcome.USEFUL,
            thought_experiment=asked_one,
        ),
    ]
    options = [asked_one, thought_experiment()]

    limited = keep([suspected], [story], [its], tried, thought_experiments=options)
    raised = keep(
        [suspected],
        [story],
        [its],
        tried,
        numbers=replace(NUMBERS, thought_experiments_per_week=2),
        thought_experiments=options,
    )

    assert limited.new_tries[0].approach == ExplorationApproach.NOTICE_THIS_WEEK
    assert raised.new_tries[0].approach == ExplorationApproach.THOUGHT_EXPERIMENT
    assert raised.new_tries[0].thought_experiment_id == options[1].id


def test_a_counter_test_never_gets_a_thought_experiment() -> None:
    suspected = pattern()
    its = exploration(suspected)
    tried = [
        asked(its, approach=ExplorationApproach.STORY_FOLLOW_UP, days_ago=10),
        asked(its, approach=ExplorationApproach.WOULD_IT_DIFFER, days_ago=8),
    ]

    planned = keep(
        [suspected],
        [observation(setting=None)],
        [its],
        tried,
        thought_experiments=[thought_experiment()],
    )

    [attempt] = planned.new_tries
    assert (attempt.need, attempt.approach) == (
        ExplorationNeed.COUNTER_TEST,
        ExplorationApproach.NOTICE_THIS_WEEK,
    )


def test_a_waiting_thought_experiment_switched_off_or_archived_is_closed() -> None:
    suspected = pattern()
    story = observation(second=WORTH, days_ago=12)
    its = exploration(suspected)
    archived = thought_experiment(archived=True)
    waiting = asked(
        its,
        need=ExplorationNeed.UNCLEAR,
        aimed_at=story,
        approach=ExplorationApproach.THOUGHT_EXPERIMENT,
        state=CuriosityState.WAITING,
        thought_experiment=archived,
    )

    planned = keep(
        [suspected], [story], [its], [waiting], thought_experiments=[archived]
    )

    assert planned.closed_curiosity_ids == [waiting[0].id]
    [attempt] = planned.new_tries
    assert attempt.thought_experiment_id is None
