from dataclasses import dataclass

from companion.core.models import (
    Familiarity,
    FamiliarityCounts,
    PatternState,
    PlatformSettings,
    UserSnapshot,
)
from companion.core.platform_settings import (
    FAMILIARITY_CONVERSATIONS,
    FAMILIARITY_LIFE_THREADS,
    FAMILIARITY_REAL_STORIES,
)
from companion.core.ports import Repositories

STATES_ZEPH_KNOWS_WELL_AT = (PatternState.SHARED, PatternState.CONFIRMED)
STATES_ZEPH_IS_GETTING_TO_KNOW_AT = (
    PatternState.SUSPECTED,
    PatternState.READY,
    PatternState.CONTESTED,
)
FAMILIARITY_WORDS = {
    Familiarity.NEW: "new",
    Familiarity.GETTING_TO_KNOW: "getting to know",
    Familiarity.KNOWS_WELL: "knows well",
}


@dataclass(frozen=True)
class FamiliarityBars:
    """The Admin-set bars a new User passes to be one Zeph is getting to know.

    Attributes:
        conversations: The fewest Conversations.
        life_threads: The fewest Life Threads.
        real_stories: The fewest Observations from real stories.
    """

    conversations: int
    life_threads: int
    real_stories: int


def familiarity_of(counts: FamiliarityCounts, bars: FamiliarityBars) -> Familiarity:
    """Work out how well the Companion knows a User from what it has of them.

    Args:
        counts: Their Conversations, Life Threads, Observations from real
            stories and Patterns in each state.
        bars: The Admin-set bars.

    Returns:
        Knows well with a Pattern shared or confirmed; getting to know when
        every bar is met, or with a Pattern suspected, ready or contested;
        new otherwise.
    """
    if has_pattern_in(counts, STATES_ZEPH_KNOWS_WELL_AT):
        return Familiarity.KNOWS_WELL
    heard_enough = (
        counts.conversations >= bars.conversations
        and counts.life_threads >= bars.life_threads
        and counts.real_story_observations >= bars.real_stories
    )
    if heard_enough or has_pattern_in(counts, STATES_ZEPH_IS_GETTING_TO_KNOW_AT):
        return Familiarity.GETTING_TO_KNOW
    return Familiarity.NEW


def has_pattern_in(counts: FamiliarityCounts, states: tuple[PatternState, ...]) -> bool:
    """Say whether a User has a Pattern in any of some states.

    Args:
        counts: Their counts.
        states: The states.

    Returns:
        True when at least one of their Patterns is in one of them.
    """
    return any(counts.pattern_states.get(state, 0) > 0 for state in states)


def familiarity_bars(settings: PlatformSettings) -> FamiliarityBars:
    """Read the Admin-set bars Familiarity is worked out against.

    Args:
        settings: The platform settings.

    Returns:
        The bars.
    """
    return FamiliarityBars(
        conversations=settings.get(FAMILIARITY_CONVERSATIONS),
        life_threads=settings.get(FAMILIARITY_LIFE_THREADS),
        real_stories=settings.get(FAMILIARITY_REAL_STORIES),
    )


def describe_familiarity(familiarity: Familiarity) -> str:
    """Write the one line telling the Reply Plan how well Zeph knows the User.

    Args:
        familiarity: How well the Companion knows them.

    Returns:
        The line with a blank line after it.
    """
    return f"How well you know them (Familiarity): {FAMILIARITY_WORDS[familiarity]}\n\n"


class FamiliarityKeeper:
    """Works out a User's Familiarity again when a Conversation ends.

    No model call: code counts what the Companion has of them and compares
    it with the Admin-set bars.
    """

    def __init__(self, repositories: Repositories) -> None:
        """Set up the keeper.

        Args:
            repositories: Where Users and what is counted are stored.
        """
        self._repositories = repositories

    def keep(self, snapshot: UserSnapshot) -> Familiarity:
        """Work out the User's Familiarity and save it when it changed.

        Args:
            snapshot: The User whose Conversation ended.

        Returns:
            Their Familiarity now.
        """
        user = snapshot.user
        familiarity = familiarity_of(
            self._repositories.users.familiarity_counts(user.id),
            familiarity_bars(snapshot.settings),
        )
        if familiarity != user.familiarity:
            self._repositories.users.save_familiarity(user.id, familiarity)
        return familiarity
