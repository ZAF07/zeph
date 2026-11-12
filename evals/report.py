from dataclasses import dataclass, field

from evals.cases import SafeguardCase, SettingsCase
from evals.judge import NO_VERSION, RuleVerdict, VersionVerdict


@dataclass(frozen=True)
class SafeguardResult:
    """What the Safeguard made of one labelled message.

    Attributes:
        case: The labelled message.
        risk_type: The risk type of the Safeguard Event it recorded, or None
            if it saw no crisis.
    """

    case: SafeguardCase
    risk_type: str | None

    @property
    def is_right(self) -> bool:
        """Whether the Safeguard saw a crisis exactly when there was one.

        Returns:
            True if it caught a crisis or let a false alarm through.
        """
        return self.case.is_crisis == (self.risk_type is not None)

    def describe(self) -> str:
        """Write the case as one line of the report.

        Returns:
            E.g. "plan (clear_crisis): I have the pills → none" or
            "traffic (false_alarm): this traffic is killing me → abuse".
        """
        caught = self.risk_type or "none"
        return f"{self.case.id} ({self.case.kind}): {self.case.message} → {caught}"


@dataclass(frozen=True)
class PersonaResult:
    """The judge's verdicts on one scripted conversation.

    Attributes:
        conversation_id: The conversation's ID.
        verdicts: One verdict per rule it was judged against.
    """

    conversation_id: str
    verdicts: list[RuleVerdict]


@dataclass(frozen=True)
class KnowledgeStepResult:
    """Which version of a document a reply used after one change.

    Attributes:
        case_id: The Knowledge case's ID.
        step: What had just happened, e.g. "text edited".
        expected: The version the reply should use.
        older: The versions that are out of date by now.
        verdict: The version the judge says the reply used.
    """

    case_id: str
    step: str
    expected: str
    older: list[str]
    verdict: VersionVerdict

    @property
    def passed(self) -> bool:
        """Whether the reply used the current version.

        Returns:
            True if it did.
        """
        return self.verdict.version == self.expected

    def describe(self) -> str:
        """Write the step's outcome as one line of the report.

        Returns:
            E.g. "FAIL text edited: uses an old version (original), expected
            edited. Says 7 counts."
        """
        used = self.verdict.version
        if self.passed:
            outcome = f"PASS {self.step}: uses {used}."
        elif used in self.older:
            outcome = (
                f"FAIL {self.step}: uses an old version ({used}), "
                f"expected {self.expected}."
            )
        elif used == NO_VERSION:
            outcome = f"FAIL {self.step}: uses no version, expected {self.expected}."
        else:
            outcome = f"FAIL {self.step}: uses {used}, expected {self.expected}."
        return f"{outcome} {self.verdict.reason}"


READ_ONLY_SETTINGS_TOOLS = frozenset({"list_memories"})


@dataclass(frozen=True)
class SettingsResult:
    """The settings tools a reply called for one settings request.

    Attributes:
        case: The settings request.
        called: The settings tools the reply called, in order.
    """

    case: SettingsCase
    called: list[str]

    @property
    def passed(self) -> bool:
        """Whether the reply changed exactly the settings it should have.

        Returns:
            True if it called every expected tool and no other tool that
            changes a setting.
        """
        changing = set(self.called) - READ_ONLY_SETTINGS_TOOLS
        return changing == set(self.case.tools)

    def describe(self) -> str:
        """Write the case as one line of the report.

        Returns:
            E.g. "FAIL delete-account: delete my account please → expected
            no tool, called start_deleting_my_data".
        """
        mark = "PASS" if self.passed else "FAIL"
        expected = ", ".join(self.case.tools) or "no tool"
        called = ", ".join(self.called) or "no tool"
        return (
            f"{mark} {self.case.id}: {self.case.message} → expected {expected}, "
            f"called {called}"
        )


def verdict_line(verdict: RuleVerdict) -> str:
    """Write a rule verdict as one line of the report.

    Args:
        verdict: The verdict.

    Returns:
        E.g. "PASS no_lists: Plain texts."
    """
    mark = "PASS" if verdict.passed else "FAIL"
    return f"{mark} {verdict.rule}: {verdict.reason}"


@dataclass
class EvalReport:
    """Everything one `make eval` run found, printed at the end.

    Attributes:
        settings_source: Where the platform settings came from.
        safeguard: Each Safeguard case's result.
        persona: Each scripted conversation's verdicts.
        knowledge: Each Knowledge step's result.
        settings: Each settings request's result.
        tokens_in: Tokens sent to the LLM, by the app and the judge.
        tokens_out: Tokens the LLM wrote, for the app and the judge.
    """

    settings_source: str = "not loaded"
    safeguard: list[SafeguardResult] = field(default_factory=list)
    persona: list[PersonaResult] = field(default_factory=list)
    knowledge: list[KnowledgeStepResult] = field(default_factory=list)
    settings: list[SettingsResult] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0

    def safeguard_lines(self) -> list[str]:
        """Write the Safeguard part of the report.

        Returns:
            The lines: the score, then each missed crisis and false alarm.
        """
        right = sum(result.is_right for result in self.safeguard)
        wrong = [result for result in self.safeguard if not result.is_right]
        missed = [result for result in wrong if result.case.is_crisis]
        false_alarms = [result for result in wrong if not result.case.is_crisis]
        lines = [f"Safeguard: {right} of {len(self.safeguard)} right"]
        lines.append(f"  Missed crises ({len(missed)}):")
        lines += [f"    {result.describe()}" for result in missed]
        lines.append(f"  False alarms ({len(false_alarms)}):")
        lines += [f"    {result.describe()}" for result in false_alarms]
        return lines

    def persona_lines(self) -> list[str]:
        """Write the Persona part of the report.

        Returns:
            The lines: the score, then each conversation's verdicts.
        """
        verdicts = [verdict for result in self.persona for verdict in result.verdicts]
        kept = sum(verdict.passed for verdict in verdicts)
        lines = [f"Persona: {kept} of {len(verdicts)} rules kept"]
        for result in self.persona:
            lines.append(f"  {result.conversation_id}")
            lines += [f"    {verdict_line(verdict)}" for verdict in result.verdicts]
        return lines

    def knowledge_lines(self) -> list[str]:
        """Write the Knowledge part of the report.

        Returns:
            The lines: the score, then each case's steps.
        """
        passed = sum(step.passed for step in self.knowledge)
        lines = [f"Knowledge: {passed} of {len(self.knowledge)} steps right"]
        case_id = None
        for step in self.knowledge:
            if step.case_id != case_id:
                case_id = step.case_id
                lines.append(f"  {case_id}")
            lines.append(f"    {step.describe()}")
        return lines

    def settings_lines(self) -> list[str]:
        """Write the Settings part of the report.

        Returns:
            The lines: the score, then each case.
        """
        passed = sum(result.passed for result in self.settings)
        lines = [f"Settings: {passed} of {len(self.settings)} right"]
        lines += [f"  {result.describe()}" for result in self.settings]
        return lines

    def lines(self) -> list[str]:
        """Write the whole report.

        Returns:
            The report's lines, with only the parts that ran.
        """
        lines = [
            f"Settings: {self.settings_source}",
            f"Tokens used (app and judge): {self.tokens_in} in, {self.tokens_out} out",
        ]
        if self.safeguard:
            lines += ["", *self.safeguard_lines()]
        if self.persona:
            lines += ["", *self.persona_lines()]
        if self.knowledge:
            lines += ["", *self.knowledge_lines()]
        if self.settings:
            lines += ["", *self.settings_lines()]
        return lines
