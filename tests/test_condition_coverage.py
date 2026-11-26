from companion.core.condition_coverage import (
    ValueCoverage,
    coverage_of,
    missing_condition,
)
from companion.core.models import (
    Audience,
    Condition,
    ObservationDirection,
    Relationship,
    SituationSetting,
    Stakes,
    StateGoingIn,
)
from tests.test_agenda import WORTH, observation


def test_the_table_counts_clear_stories_for_and_against_per_condition_value() -> None:
    table = coverage_of(
        [
            observation(audience=Audience.GROUP, stakes=Stakes.HIGH),
            observation(audience=Audience.GROUP),
            observation(
                audience=Audience.GROUP, direction=ObservationDirection.AGAINST
            ),
            observation(
                audience=Audience.ONE_TO_ONE,
                state_going_in=StateGoingIn.STEADY,
                setting=SituationSetting.WORK,
                relationship=Relationship.COLLEAGUE,
                direction=ObservationDirection.AGAINST,
            ),
        ]
    )

    assert table[Condition.AUDIENCE] == {
        "group": ValueCoverage(stories_for=2, stories_against=1),
        "one-to-one": ValueCoverage(stories_for=0, stories_against=1),
    }
    assert table[Condition.STAKES] == {"high": ValueCoverage(stories_for=1)}
    assert table[Condition.STATE_GOING_IN] == {
        "steady": ValueCoverage(stories_against=1)
    }
    assert table[Condition.SETTING] == {
        "home": ValueCoverage(stories_for=2, stories_against=1),
        "work": ValueCoverage(stories_against=1),
    }
    assert table[Condition.RELATIONSHIP] == {
        "family": ValueCoverage(stories_for=2, stories_against=1),
        "colleague": ValueCoverage(stories_against=1),
    }
    assert table[Condition.POWER] == {}
    assert table[Condition.STANCE] == {}


def test_the_table_leaves_out_unclear_situational_and_excluded_stories() -> None:
    table = coverage_of(
        [
            observation(audience=Audience.GROUP),
            observation(audience=Audience.GROUP, second=WORTH),
            observation(audience=Audience.GROUP, situational=True),
            observation(audience=Audience.GROUP, excluded=True),
        ]
    )

    assert table[Condition.AUDIENCE] == {"group": ValueCoverage(stories_for=1)}


def test_stories_only_against_never_make_a_condition_one_sided() -> None:
    table = coverage_of(
        [
            observation(
                audience=Audience.GROUP,
                direction=ObservationDirection.AGAINST,
                setting=None,
                relationship=None,
            )
            for _ in range(3)
        ]
    )

    assert missing_condition(table, one_sided_stories=2) is None


def test_the_missing_condition_says_what_was_seen_and_what_to_learn() -> None:
    table = coverage_of(
        [
            observation(stakes=Stakes.HIGH, setting=None, relationship=None)
            for _ in range(2)
        ]
    )

    missing = missing_condition(table, one_sided_stories=2)

    assert missing is not None
    assert (missing.condition, missing.seen_value, missing.value, missing.stories) == (
        Condition.STAKES,
        "high",
        "low",
        2,
    )
    assert missing_condition(table, 2, closed={(Condition.STAKES, "low")}) is None
