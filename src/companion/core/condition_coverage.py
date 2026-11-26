from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass

from companion.core.models import (
    Audience,
    Condition,
    Observation,
    ObservationDirection,
    Power,
    Relationship,
    SituationSetting,
    Stakes,
    Stance,
    StateGoingIn,
)

CONDITION_ORDER = (
    Condition.AUDIENCE,
    Condition.STAKES,
    Condition.RELATIONSHIP,
    Condition.POWER,
    Condition.STANCE,
    Condition.SETTING,
    Condition.STATE_GOING_IN,
)
VALUES_TO_LEARN: Mapping[Condition, tuple[str, ...]] = {
    Condition.AUDIENCE: (
        Audience.ONE_TO_ONE.value,
        Audience.GROUP.value,
        Audience.IN_FRONT_OF_OTHERS.value,
    ),
    Condition.STAKES: (Stakes.LOW.value, Stakes.HIGH.value),
    Condition.RELATIONSHIP: (
        Relationship.FRIEND.value,
        Relationship.COLLEAGUE.value,
        Relationship.FAMILY.value,
        Relationship.PARTNER.value,
    ),
    Condition.POWER: (Power.ABOVE.value, Power.EQUAL.value, Power.BELOW.value),
    Condition.STANCE: (
        Stance.SUPPORTIVE.value,
        Stance.NEUTRAL.value,
        Stance.HOSTILE.value,
    ),
    Condition.SETTING: (
        SituationSetting.HOME.value,
        SituationSetting.WORK.value,
        SituationSetting.SOCIAL.value,
    ),
    Condition.STATE_GOING_IN: (
        StateGoingIn.STEADY.value,
        StateGoingIn.WORN_OUT.value,
        StateGoingIn.UNDER_PRESSURE.value,
        StateGoingIn.LOW.value,
    ),
}


@dataclass(frozen=True)
class ValueCoverage:
    """How many clear stories a Pattern has under one value of a Condition.

    Attributes:
        stories_for: Clear stories for the Pattern with that value.
        stories_against: Clear stories against it with that value.
    """

    stories_for: int = 0
    stories_against: int = 0


CoverageTable = Mapping[Condition, Mapping[str, ValueCoverage]]


@dataclass(frozen=True)
class MissingCondition:
    """A value of a Condition worth asking about, for a one-sided Pattern.

    Attributes:
        condition: The Condition whose stories so far all share one value.
        value: The value not seen yet, which is what to learn.
        seen_value: The one value the stories for the Pattern share.
        stories: How many clear stories for the Pattern share it.
    """

    condition: Condition
    value: str
    seen_value: str
    stories: int


def is_clear(observation: Observation) -> bool:
    """Say whether an Observation counts as a clear story in the coverage table.

    Args:
        observation: The Observation.

    Returns:
        True when it is not unclear, not situational and not excluded.
    """
    return not (observation.unclear or observation.situational or observation.excluded)


def condition_value(observation: Observation, condition: Condition) -> str | None:
    """Read one Condition of an Observation.

    Args:
        observation: The Observation.
        condition: The Condition.

    Returns:
        Its value as stored; None when the story didn't say it.
    """
    value = getattr(observation.tags, condition.value)
    return value.value if value else None


def coverage_of(observations: Sequence[Observation]) -> CoverageTable:
    """Count a Pattern's clear stories for and against, per Condition value.

    Worked out from the Observations each time and never stored, so it
    can't drift from the evidence. Unclear, situational and excluded
    Observations are left out, and so is a Condition a story didn't say.

    Args:
        observations: The Observations of the Pattern.

    Returns:
        For each Condition, the values seen with their counts. A value with
        no clear story is not in the table.
    """
    table: dict[Condition, dict[str, ValueCoverage]] = {
        condition: {} for condition in Condition
    }
    for observation in observations:
        if not is_clear(observation):
            continue
        is_for = observation.direction == ObservationDirection.FOR
        for condition in Condition:
            value = condition_value(observation, condition)
            if value is None:
                continue
            seen = table[condition].get(value, ValueCoverage())
            table[condition][value] = ValueCoverage(
                stories_for=seen.stories_for + (1 if is_for else 0),
                stories_against=seen.stories_against + (0 if is_for else 1),
            )
    return table


def missing_condition(
    table: CoverageTable,
    one_sided_stories: int,
    closed: Set[tuple[Condition, str]] = frozenset(),
) -> MissingCondition | None:
    """Pick the one Condition value worth asking about, if any.

    A Condition is one-sided when at least the Admin-set number of clear
    stories for the Pattern have it known and all share one value. It is
    worth asking about while another of its values has no clear story, for
    or against, and no useful try closed that value. Only the most
    one-sided Condition is picked: the one with the most stories behind
    it, ties going by `CONDITION_ORDER`.

    Args:
        table: The Pattern's coverage table.
        one_sided_stories: The Admin-set number of stories to be one-sided.
        closed: The Condition values a useful try already closed.

    Returns:
        The Condition with the first of its values still to learn; None
        when no Condition is one-sided with a value left to learn.
    """
    found: list[MissingCondition] = []
    for condition in CONDITION_ORDER:
        seen_for = {
            value: coverage.stories_for
            for value, coverage in table[condition].items()
            if coverage.stories_for
        }
        if len(seen_for) != 1:
            continue
        [(seen_value, stories)] = seen_for.items()
        to_learn = [
            value
            for value in VALUES_TO_LEARN[condition]
            if value not in table[condition] and (condition, value) not in closed
        ]
        if stories >= one_sided_stories and to_learn:
            found.append(MissingCondition(condition, to_learn[0], seen_value, stories))
    return max(found, key=lambda missing: missing.stories, default=None)
