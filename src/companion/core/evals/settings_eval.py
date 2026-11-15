from dataclasses import dataclass

from companion.core.evals.cases import SettingsCase
from companion.core.evals.made_up_memory import save_memory_items
from companion.core.evals.models import CaseCheckResult, CaseOutcome, Check
from companion.core.evals.ports import EvalCompanion

SETTINGS_TOOLS = frozenset(
    {
        "pause_check_ins",
        "resume_check_ins",
        "change_check_in_frequency",
        "change_quiet_hours",
        "turn_user_memory_on_or_off",
        "turn_photo_viewing_on_or_off",
        "list_memories",
        "forget_memory",
        "change_time_zone",
        "start_deleting_my_data",
    }
)
READ_ONLY_SETTINGS_TOOLS = frozenset({"list_memories"})


@dataclass(frozen=True)
class SettingsResult:
    """The settings tools a reply called, and the Memory Items left after it.

    Attributes:
        case: The settings request.
        called: The settings tools the reply called, in order.
        memory_after: The contents of every Memory Item the User has after
            the reply.
    """

    case: SettingsCase
    called: list[str]
    memory_after: list[str]

    @property
    def wrongly_forgotten(self) -> list[str]:
        """The case's Memory Items that were deleted but should have stayed.

        Returns:
            Their contents, in the order the case lists them.
        """
        return [
            content
            for content in self.case.memory_item_contents
            if content not in self.case.forgotten and content not in self.memory_after
        ]

    @property
    def wrongly_kept(self) -> list[str]:
        """The case's Memory Items that should have been deleted but stayed.

        Returns:
            Their contents, in the order the case lists them.
        """
        return [
            content for content in self.case.forgotten if content in self.memory_after
        ]

    @property
    def passed(self) -> bool:
        """Whether the reply changed exactly what it should have.

        Returns:
            True if it called every expected tool and no other tool that
            changes a setting, and deleted exactly the case's Memory Items
            it should have.
        """
        changing = set(self.called) - READ_ONLY_SETTINGS_TOOLS
        return (
            changing == set(self.case.tools)
            and not self.wrongly_forgotten
            and not self.wrongly_kept
        )

    def describe(self) -> str:
        """Write the tools expected and called as one line.

        Returns:
            E.g. "delete my account please → expected no tool, called
            start_deleting_my_data", with any Memory Item wrongly kept or
            deleted after it.
        """
        expected = ", ".join(self.case.tools) or "no tool"
        called = ", ".join(self.called) or "no tool"
        line = f"{self.case.message} → expected {expected}, called {called}"
        if self.wrongly_kept:
            line += "; still remembers: " + ", ".join(self.wrongly_kept)
        if self.wrongly_forgotten:
            line += "; wrongly forgot: " + ", ".join(self.wrongly_forgotten)
        return line


def check_settings_case(
    case: SettingsCase, companion: EvalCompanion
) -> CaseCheckResult:
    """Send a settings request and check the reply changed exactly what it should.

    A User given Memory Items by the case skips "What brings you here?" in
    onboarding, so only the case's own Memory Items say why they came.

    Args:
        case: The settings request.
        companion: The app on the Eval database.

    Returns:
        One check; a failed case notes Zeph's reply.
    """
    user_id = companion.connect_user(
        check_ins=True, onboarding_reasons=not case.memories
    )
    save_memory_items(companion.repositories, user_id, case.memories, companion.now())
    companion.clear_called_tools()

    replies = companion.send_text(case.message)

    result = SettingsResult(
        case,
        [name for name in companion.called_tools() if name in SETTINGS_TOOLS],
        companion.memory_item_contents(),
    )
    return CaseCheckResult(
        outcome=CaseOutcome.PASS if result.passed else CaseOutcome.FAIL,
        checks=[Check(name="tools", passed=result.passed, detail=result.describe())],
        notes=[] if result.passed else replies.texts,
    )
