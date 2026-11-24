from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from companion.adapters.pattern_catalog_seed import read_pattern_catalog_seed
from companion.core.agenda import (
    AgendaInput,
    AgendaNumbers,
    OpenNeed,
    aimed_question,
    next_way,
    open_needs,
    plan_agenda,
    rank_explorations,
    tries_with_nothing,
    try_outcome,
)
from companion.core.models import (
    AgendaChanges,
    CatalogPattern,
    Curiosity,
    CuriosityAim,
    CuriositySensitivity,
    CuriosityState,
    EvidenceKind,
    Exploration,
    ExplorationNeed,
    ExplorationState,
    ExplorationTry,
    ExplorationWay,
    Observation,
    ObservationDirection,
    PatternState,
    Relationship,
    SituationSetting,
    SituationTags,
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
NUMBERS = AgendaNumbers(size=3, wait=timedelta(days=3), rest_after_tries=4)


def observation(
    setting: SituationSetting | None = SituationSetting.HOME,
    direction: ObservationDirection = ObservationDirection.FOR,
    second: str | None = None,
    days_ago: int = 0,
    pattern_type: str = BELONG,
    conversation_id: UUID = EARLIER,
    tagged_at: datetime = NOW - timedelta(days=10),
    relationship: Relationship | None = Relationship.FAMILY,
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
            relationship=relationship, power=None, setting=setting, stance=None
        ),
        evidence_kind=EvidenceKind.REAL_STORY,
        second_pattern_type_id=second,
        second_pattern_type_version="0.1.0" if second else None,
        situational=False,
        tagged_at=tagged_at,
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
    way: ExplorationWay = ExplorationWay.STORY_FOLLOW_UP,
    days_ago: int = 5,
    conversation_id: UUID = EARLIER,
    reaction: ThreadReaction | None = ThreadReaction.ENGAGED,
    outcome: TryOutcome | None = TryOutcome.VAGUE,
    aimed_at: Observation | None = None,
    part_of_life: SituationSetting | None = None,
    state: CuriosityState = CuriosityState.RAISED,
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
        way=way,
        created_at=curiosity.created_at,
        observation_id=aimed_at.id if aimed_at else None,
        part_of_life=part_of_life,
        outcome=outcome if raised_at else None,
    )


def keep(
    patterns: list[CatalogPattern],
    observations: list[Observation],
    explorations: list[Exploration] | None = None,
    tried: list[tuple[Curiosity, ExplorationTry]] | None = None,
    scores: dict[str, PatternScore] | None = None,
    numbers: AgendaNumbers = NUMBERS,
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
        ),
        numbers,
    )


def test_unclear_stories_come_first_then_a_missing_part_then_a_counter_test() -> None:
    older_unclear = observation(second=WORTH, days_ago=9)
    newer_unclear = observation(second=WORTH, days_ago=2)
    at_work = observation(setting=SituationSetting.WORK)

    needs = open_needs([older_unclear, at_work, newer_unclear], [])

    assert needs == [
        OpenNeed(ExplorationNeed.UNCLEAR, observation=newer_unclear),
        OpenNeed(ExplorationNeed.UNCLEAR, observation=older_unclear),
        OpenNeed(ExplorationNeed.MISSING_PART, part_of_life=SituationSetting.SOCIAL),
        OpenNeed(ExplorationNeed.COUNTER_TEST, observation=at_work),
    ]


def test_a_part_of_life_is_missing_only_while_another_is_seen() -> None:
    nowhere = observation(setting=None)
    everywhere = [
        observation(setting=SituationSetting.HOME),
        observation(setting=SituationSetting.WORK),
        observation(setting=SituationSetting.SOCIAL),
    ]

    assert [need.need for need in open_needs([nowhere], [])] == [
        ExplorationNeed.COUNTER_TEST
    ]
    assert [need.need for need in open_needs(everywhere, [])] == [
        ExplorationNeed.COUNTER_TEST
    ]
    [missing, _] = open_needs([observation(setting=SituationSetting.HOME)], [])
    assert missing.part_of_life == SituationSetting.WORK


def test_the_counter_test_closes_with_evidence_against_or_a_useful_counter_test() -> (
    None
):
    story = observation(setting=None)
    against = observation(setting=None, direction=ObservationDirection.AGAINST)
    its = exploration(pattern())
    _, useful = asked(its, outcome=TryOutcome.USEFUL)
    _, vague = asked(its, outcome=TryOutcome.VAGUE)

    assert open_needs([story, against], []) == []
    assert open_needs([story], [useful]) == []
    assert open_needs([story], [vague]) == [
        OpenNeed(ExplorationNeed.COUNTER_TEST, observation=story)
    ]


def test_each_try_at_a_need_moves_to_a_different_way_least_pushy_first() -> None:
    its = exploration(pattern())
    need = OpenNeed(ExplorationNeed.COUNTER_TEST)
    first = asked(its, way=ExplorationWay.STORY_FOLLOW_UP, days_ago=9)
    second = asked(its, way=ExplorationWay.OTHER_PERSON, days_ago=5)
    third = asked(its, way=ExplorationWay.NOTICE_THIS_WEEK, days_ago=2)

    def way_after(*tried: tuple[Curiosity, ExplorationTry]) -> ExplorationWay:
        return next_way(
            need,
            [attempt for _, attempt in tried],
            {c.id: c.raised_at for c, _ in tried if c.raised_at},
        )

    assert way_after() == ExplorationWay.STORY_FOLLOW_UP
    assert way_after(first) == ExplorationWay.OTHER_PERSON
    assert way_after(first, second) == ExplorationWay.NOTICE_THIS_WEEK
    assert way_after(first, second, third) == ExplorationWay.STORY_FOLLOW_UP


def test_after_a_useful_try_the_same_way_is_used_again() -> None:
    its = exploration(pattern())
    curiosity, useful = asked(
        its, way=ExplorationWay.OTHER_PERSON, outcome=TryOutcome.USEFUL
    )

    way = next_way(
        OpenNeed(ExplorationNeed.COUNTER_TEST), [useful], {curiosity.id: NOW}
    )

    assert way == ExplorationWay.OTHER_PERSON


def test_a_try_at_another_need_does_not_move_this_ones_way() -> None:
    its = exploration(pattern())
    story = observation(second=WORTH)
    curiosity, at_work = asked(
        its,
        need=ExplorationNeed.MISSING_PART,
        part_of_life=SituationSetting.WORK,
    )

    way = next_way(
        OpenNeed(ExplorationNeed.UNCLEAR, observation=story),
        [at_work],
        {curiosity.id: NOW},
    )

    assert way == ExplorationWay.STORY_FOLLOW_UP


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
    assert (attempt.need, attempt.way, attempt.observation_id) == (
        ExplorationNeed.UNCLEAR,
        ExplorationWay.STORY_FOLLOW_UP,
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


def test_after_a_try_with_nothing_the_next_is_a_different_way_after_the_wait() -> None:
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
    assert (attempt.need, attempt.way) == (
        ExplorationNeed.UNCLEAR,
        ExplorationWay.OTHER_PERSON,
    )


def test_after_a_useful_try_the_next_has_no_wait() -> None:
    suspected = pattern()
    its = exploration(suspected)
    tried = asked(
        its,
        need=ExplorationNeed.MISSING_PART,
        part_of_life=SituationSetting.WORK,
        outcome=TryOutcome.USEFUL,
        days_ago=1,
    )

    [curiosity] = keep([suspected], [observation()], [its], [tried]).new_curiosities

    assert curiosity.not_before is None


def test_a_waiting_aimed_curiosity_for_the_top_need_is_left_alone() -> None:
    suspected = pattern()
    its = exploration(suspected)
    waiting = asked(
        its,
        need=ExplorationNeed.MISSING_PART,
        part_of_life=SituationSetting.WORK,
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
        need=ExplorationNeed.MISSING_PART,
        part_of_life=SituationSetting.WORK,
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
        need=ExplorationNeed.MISSING_PART,
        part_of_life=SituationSetting.WORK,
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


@pytest.mark.parametrize("need", list(ExplorationNeed))
@pytest.mark.parametrize("way", list(ExplorationWay))
def test_every_aimed_question_is_written_by_code_without_the_pattern(
    need: ExplorationNeed, way: ExplorationWay
) -> None:
    belong = PATTERN_TYPES[BELONG]
    open_need = OpenNeed(
        need,
        observation=observation() if need != ExplorationNeed.MISSING_PART else None,
        part_of_life=SituationSetting.WORK
        if need == ExplorationNeed.MISSING_PART
        else None,
    )

    question, why = aimed_question(open_need, way, belong)

    assert question.startswith(("Ask", "Go back"))
    assert why
    assert belong.name not in question + why
    assert "I said yes again" not in question
