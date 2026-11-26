from collections.abc import Mapping, Sequence

from companion.core.models import (
    Audience,
    Condition,
    PatternNarrowing,
    Power,
    Relationship,
    SituationSetting,
    Stakes,
    Stance,
    StateGoingIn,
)

WHERE_WORDS: Mapping[tuple[Condition, str], str] = {
    (Condition.AUDIENCE, Audience.ONE_TO_ONE.value): "one-to-one",
    (Condition.AUDIENCE, Audience.GROUP.value): "in a group",
    (Condition.AUDIENCE, Audience.IN_FRONT_OF_OTHERS.value): (
        "with other people watching"
    ),
    (Condition.STAKES, Stakes.LOW.value): "when little is riding on it",
    (Condition.STAKES, Stakes.HIGH.value): "when a lot is riding on it",
    (Condition.RELATIONSHIP, Relationship.PARTNER.value): "with a partner",
    (Condition.RELATIONSHIP, Relationship.FAMILY.value): "with family",
    (Condition.RELATIONSHIP, Relationship.FRIEND.value): "with friends",
    (Condition.RELATIONSHIP, Relationship.ACQUAINTANCE.value): (
        "with people they know a little"
    ),
    (Condition.RELATIONSHIP, Relationship.COLLEAGUE.value): "with colleagues",
    (Condition.RELATIONSHIP, Relationship.STRANGER.value): "with strangers",
    (Condition.POWER, Power.ABOVE.value): "with people above them",
    (Condition.POWER, Power.EQUAL.value): "with their equals",
    (Condition.POWER, Power.BELOW.value): "with people below them",
    (Condition.STANCE, Stance.SUPPORTIVE.value): (
        "when the other person is on their side"
    ),
    (Condition.STANCE, Stance.NEUTRAL.value): (
        "when the other person is neither for nor against them"
    ),
    (Condition.STANCE, Stance.HOSTILE.value): "when the other person is against them",
    (Condition.SETTING, SituationSetting.HOME.value): "at home",
    (Condition.SETTING, SituationSetting.WORK.value): "at work",
    (Condition.SETTING, SituationSetting.SOCIAL.value): "out with friends",
    (Condition.SETTING, SituationSetting.ONLINE.value): "online",
    (Condition.STATE_GOING_IN, StateGoingIn.WORN_OUT.value): (
        "on days they were worn out"
    ),
    (Condition.STATE_GOING_IN, StateGoingIn.UNDER_PRESSURE.value): (
        "on days they were under pressure"
    ),
    (Condition.STATE_GOING_IN, StateGoingIn.LOW.value): "on days they were feeling low",
    (Condition.STATE_GOING_IN, StateGoingIn.STEADY.value): "on days they felt steady",
}
STATE_GENTLY = (
    "Where it names how they were doing, say that gently, as something about "
    "those days and in their own words where you can; never as a label for them."
)


def where_words(condition: Condition, value: str) -> str:
    """Put one value of a Condition in plain words, as said about the User.

    Args:
        condition: The Condition.
        value: One of its values, as stored.

    Returns:
        E.g. "in a group", "when a lot is riding on it". The state going in
        is put as something about the day, never a label for the User.
    """
    return WHERE_WORDS[(condition, value)]


def describe_narrowing(narrowing: PatternNarrowing) -> str:
    """Write one narrowing in plain words.

    Args:
        narrowing: The narrowing.

    Returns:
        E.g. "in a group; not one-to-one".
    """
    holds_with = ", ".join(
        where_words(narrowing.tag, value) for value in narrowing.holds_with
    )
    not_with = ", ".join(
        where_words(narrowing.tag, value) for value in narrowing.not_with
    )
    return f"{holds_with}; not {not_with}"


def describe_where_it_shows(narrowings: Sequence[PatternNarrowing]) -> str:
    """Write where a Pattern shows and where it doesn't, in plain words.

    Args:
        narrowings: The Pattern's kept narrowings.

    Returns:
        E.g. " It shows in a group; not one-to-one."; "" when it isn't
        narrowed. A narrowing by the state going in adds the rule to say
        it gently.
    """
    shown = "".join(
        f" It shows {describe_narrowing(narrowing)}." for narrowing in narrowings
    )
    names_state = any(
        narrowing.tag == Condition.STATE_GOING_IN for narrowing in narrowings
    )
    return f"{shown} {STATE_GENTLY}" if names_state else shown
