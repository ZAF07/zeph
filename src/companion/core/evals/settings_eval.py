from companion.core.evals.cases import SettingsCase
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


def called_the_right_tools(case: SettingsCase, called: list[str]) -> bool:
    """Say whether a reply changed exactly the settings it should have.

    Args:
        case: The settings request.
        called: The settings tools the reply called.

    Returns:
        True if it called every expected tool and no other tool that
        changes a setting.
    """
    changing = set(called) - READ_ONLY_SETTINGS_TOOLS
    return changing == set(case.tools)


def describe_settings_case(case: SettingsCase, called: list[str]) -> str:
    """Write the tools expected and called as one line.

    Args:
        case: The settings request.
        called: The settings tools the reply called.

    Returns:
        E.g. "delete my account please → expected no tool, called
        start_deleting_my_data".
    """
    expected = ", ".join(case.tools) or "no tool"
    called_names = ", ".join(called) or "no tool"
    return f"{case.message} → expected {expected}, called {called_names}"


def check_settings_case(
    case: SettingsCase, companion: EvalCompanion
) -> CaseCheckResult:
    """Send a settings request and check the reply called the right tools.

    Args:
        case: The settings request.
        companion: The app on the Eval database.

    Returns:
        One check; a failed case notes Zeph's reply.
    """
    companion.connect_user(check_ins=True)
    companion.clear_called_tools()

    replies = companion.send_text(case.message)

    called = [name for name in companion.called_tools() if name in SETTINGS_TOOLS]
    passed = called_the_right_tools(case, called)
    return CaseCheckResult(
        outcome=CaseOutcome.PASS if passed else CaseOutcome.FAIL,
        checks=[
            Check(
                name="tools",
                passed=passed,
                detail=describe_settings_case(case, called),
            )
        ],
        notes=[] if passed else replies.texts,
    )
