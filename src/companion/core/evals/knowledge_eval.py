from dataclasses import asdict, dataclass
from datetime import timedelta

from companion.core.evals.cases import KnowledgeCase
from companion.core.evals.judge import NO_VERSION, VersionVerdict, judge_version
from companion.core.evals.models import CaseCheckResult, CaseOutcome, Check
from companion.core.evals.ports import EvalCompanion

DAY_BETWEEN_QUESTIONS = timedelta(days=1)


@dataclass(frozen=True)
class KnowledgeStepResult:
    """Which version of a document a reply used after one change.

    Attributes:
        step: What had just happened, e.g. "text edited".
        expected: The version the reply should use.
        older: The versions that are out of date by now.
        verdict: The version the Judge says the reply used.
    """

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
        """Write the step's outcome as one line.

        Returns:
            E.g. "uses an old version (original), expected edited. Says 7
            counts."
        """
        used = self.verdict.version
        if self.passed:
            outcome = f"uses {used}."
        elif used in self.older:
            outcome = f"uses an old version ({used}), expected {self.expected}."
        elif used == NO_VERSION:
            outcome = f"uses no version, expected {self.expected}."
        else:
            outcome = f"uses {used}, expected {self.expected}."
        return f"{outcome} {self.verdict.reason}"

    def check(self) -> Check:
        """Turn the step into a check.

        Returns:
            The check, named after the step.
        """
        return Check(name=self.step, passed=self.passed, detail=self.describe())


def ask(companion: EvalCompanion, question: str) -> str:
    """Ask a question in a new Conversation and return Zeph's reply.

    A day passes first, so the Conversation is new and the earlier answers
    aren't in its history.

    Args:
        companion: The app on the Eval database.
        question: What the User asks.

    Returns:
        Zeph's texts, one per line.
    """
    companion.move_clock(DAY_BETWEEN_QUESTIONS)
    return "\n".join(companion.send_text(question).texts)


def check_knowledge_case(
    case: KnowledgeCase, companion: EvalCompanion
) -> CaseCheckResult:
    """Change a Knowledge Document four ways and check replies use each version.

    After the upload, a text edit, a details edit and a file replacement, a
    User asks about it and the Judge decides which version the reply used.
    Any reply that uses an old version fails.

    Args:
        case: The made-up teaching and its changes.
        companion: The app on the Eval database.

    Returns:
        One check per step.
    """
    companion.connect_user()
    companion.upload_starter_library()
    text_versions = {
        "original": case.original_text,
        "edited": case.edited_text,
        "replacement": case.replacement_text,
    }
    details_versions = {
        "original": case.original_details.describe(),
        "edited": case.edited_details.describe(),
    }

    def which_version_reply_uses(
        document_id: str, question: str, versions: dict[str, str]
    ) -> VersionVerdict:
        """Wait for Ready, ask in a new Conversation and judge the reply.

        Args:
            document_id: The document that was just changed.
            question: What the User asks.
            versions: Each version's name and content, for the Judge.

        Returns:
            Which version the reply used.
        """
        companion.wait_until_knowledge_ready(document_id)
        reply = ask(companion, question)
        return judge_version(companion.judge_chat_model, question, reply, versions)

    document_id = companion.upload_knowledge(
        case.original_file_name,
        case.original_text.encode(),
        **asdict(case.original_details),
    )
    after_upload = which_version_reply_uses(document_id, case.question, text_versions)

    companion.edit_knowledge_text(document_id, case.edited_text)
    after_text_edit = which_version_reply_uses(
        document_id, case.question, text_versions
    )

    companion.edit_knowledge_details(document_id, asdict(case.edited_details))
    after_details_edit = which_version_reply_uses(
        document_id, case.source_question, details_versions
    )

    companion.replace_knowledge_file(
        document_id, case.replacement_file_name, case.replacement_text.encode()
    )
    after_replacement = which_version_reply_uses(
        document_id, case.question, text_versions
    )

    steps = [
        KnowledgeStepResult("uploaded", "original", [], after_upload),
        KnowledgeStepResult("text edited", "edited", ["original"], after_text_edit),
        KnowledgeStepResult(
            "details edited", "edited", ["original"], after_details_edit
        ),
        KnowledgeStepResult(
            "file replaced", "replacement", ["original", "edited"], after_replacement
        ),
    ]
    passed = all(step.passed for step in steps)
    return CaseCheckResult(
        outcome=CaseOutcome.PASS if passed else CaseOutcome.FAIL,
        checks=[step.check() for step in steps],
    )
