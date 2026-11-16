import re
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from companion.core.evals.cases import (
    EvalKnowledgeDocument,
    UnderstandingCase,
    UnderstandingMessage,
)
from companion.core.evals.judge import JudgeSettings, judge_persona_rules
from companion.core.evals.made_up_memory import (
    give_made_up_memory,
    open_conversation_with,
)
from companion.core.evals.models import (
    CaseCheckResult,
    CaseOutcome,
    CaseStoppedError,
    Check,
    StopCheck,
)
from companion.core.evals.persona_eval import verdict_check
from companion.core.evals.ports import EvalCompanion
from companion.core.evals.understanding_checks import (
    CheckResult,
    ObservedUnderstanding,
    check_understanding,
)
from companion.core.models import (
    CheckInFrequency,
    ModelCall,
    ModelStep,
    Understanding,
)
from companion.core.ports import ChatModel, Repositories

TRACES_READ_AT_MOST = 200
CHECK_IN_DUE_FOR = timedelta(hours=1)
KNOWLEDGE_PASSAGE_SOURCE = re.compile(r"^From “(.+?)” \(", re.MULTILINE)


def upload_knowledge_documents(
    companion: EvalCompanion, documents: Sequence[EvalKnowledgeDocument]
) -> None:
    """Upload Knowledge Documents as an Admin and set when each helps.

    Args:
        companion: The app on the Eval database.
        documents: The documents.
    """
    for document in documents:
        file_name = re.sub(r"\W+", "-", document.title.lower()) + ".txt"
        document_id = companion.upload_knowledge(
            file_name,
            document.text.encode(),
            title=document.title,
            source=document.source,
            tradition=document.tradition,
        )
        companion.wait_until_knowledge_ready(document_id)
        companion.edit_knowledge_details(
            document_id, {"when_it_helps": document.when_it_helps}
        )


def calls_in_new_traces(
    repositories: Repositories, user_id: UUID, seen_trace_ids: set[UUID]
) -> list[ModelCall]:
    """Read the User's model calls in traces not seen before, and mark them seen.

    Args:
        repositories: Where the Model Call Log is stored.
        user_id: The User's ID.
        seen_trace_ids: The traces already read; new ones are added.

    Returns:
        The calls in the new traces.
    """
    overviews = repositories.model_calls.list_traces(
        user_id=user_id,
        since=None,
        step=None,
        errors_only=False,
        limit=TRACES_READ_AT_MOST,
    )
    calls: list[ModelCall] = []
    for overview in overviews:
        if overview.trace.id in seen_trace_ids:
            continue
        seen_trace_ids.add(overview.trace.id)
        details = repositories.model_calls.get_trace(overview.trace.id)
        if details is not None:
            calls += details.calls
    return calls


def knowledge_in_reply(calls: Sequence[ModelCall]) -> list[str]:
    """List the Knowledge documents whose passages reached the reply.

    Args:
        calls: The Message's model calls.

    Returns:
        The titles, each once, as the reply's instructions name them.
    """
    instructions = "\n".join(
        call.content.instructions
        for call in calls
        if call.step == ModelStep.REPLY and call.content
    )
    return list(dict.fromkeys(KNOWLEDGE_PASSAGE_SOURCE.findall(instructions)))


def describe_what_was_done(
    understanding: Understanding, understanding_input: str, calls: Sequence[ModelCall]
) -> ObservedUnderstanding:
    """Describe what a saved Understanding and the reply after it did.

    Args:
        understanding: The Message's saved Understanding.
        understanding_input: What the Understanding model was given.
        calls: The Message's model calls.

    Returns:
        What they did.
    """
    form = understanding.form
    return ObservedUnderstanding(
        need=understanding.need,
        understanding_input=understanding_input,
        raised_threads=[item.title for item in form.bring_up],
        raised_curiosities=len(form.curiosities),
        asked_why=understanding.asked_why,
        knowledge_documents=(
            [chosen.title for chosen in form.knowledge.documents]
            if form.knowledge
            else []
        ),
        knowledge_in_reply=knowledge_in_reply(calls),
        woven_in=any(
            call.check_in_shape is not None and call.check_in_shape.woven_in
            for call in calls
        ),
    )


def make_check_in_due(repositories: Repositories, user_id: UUID, now: datetime) -> None:
    """Turn the made-up User's Check-ins on, with one due an hour ago.

    Args:
        repositories: Where Users are stored.
        user_id: The User's ID.
        now: The case's time.

    Raises:
        ValueError: If the made-up User isn't there.
    """
    user = repositories.users.get(user_id)
    if user is None:
        raise ValueError("The made-up User is missing")
    repositories.users.update(
        replace(
            user,
            check_ins=replace(
                user.check_ins,
                enabled=True,
                frequency=CheckInFrequency.MOST_DAYS,
                next_due_at=now - CHECK_IN_DUE_FOR,
            ),
        )
    )


def full_content_check(calls: Sequence[ModelCall]) -> CheckResult:
    """Check every model call for the Message kept its full content.

    Args:
        calls: The Message's model calls.

    Returns:
        The check's outcome.
    """
    without = [call.step.value for call in calls if call.content is None]
    if without:
        return CheckResult(
            "full content", False, f"no content kept for {', '.join(without)}"
        )
    return CheckResult("full content", True, f"kept for all {len(calls)} model calls")


def transcript_line(from_person: bool, text: str) -> str:
    """Write one message as a line of the Judge's transcript.

    Args:
        from_person: True if the person sent it; False if Zeph did.
        text: What it says.

    Returns:
        E.g. "Person: hey".
    """
    return f"{'Person' if from_person else 'Zeph'}: {text}"


def send_and_collect_lines(companion: EvalCompanion, text: str) -> list[str]:
    """Send one Message and write it and Zeph's replies as transcript lines.

    Args:
        companion: The app on the Eval database.
        text: What the person sends.

    Returns:
        The Message's transcript line, then one per reply text.
    """
    replies = companion.send_text(text)
    return [
        transcript_line(True, text),
        *(transcript_line(False, reply) for reply in replies.texts),
    ]


@dataclass(frozen=True)
class CheckedMessage:
    """One Message's checks, and what to note if it failed.

    Attributes:
        text: What the person sent.
        checks: Each check on its Understanding, then each Judge rule.
        call: Its Understanding call's time and tokens; None if no call was
            logged, which fails the Message.
        failure_details: What the Understanding was given and answered;
            empty when the Message passed.
    """

    text: str
    checks: list[Check]
    call: dict[str, int] | None
    failure_details: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Whether its Understanding call was logged and every check passed.

        Returns:
            True if it did.
        """
        return self.call is not None and all(check.passed for check in self.checks)


def check_message(
    case: UnderstandingCase,
    message: UnderstandingMessage,
    calls: Sequence[ModelCall],
    understanding: Understanding | None,
    transcript: str,
    judge_chat_model: ChatModel,
    judge: JudgeSettings,
) -> CheckedMessage:
    """Check one Message's Understanding and reply, and judge the reply.

    Args:
        case: The case, for its rules.
        message: The Message and what it should do.
        calls: Its model calls, from the Model Call Log.
        understanding: Its saved Understanding; None if none was saved.
        transcript: The Conversation so far, for the Judge.
        judge_chat_model: The model that judges.
        judge: The Judge's model, thinking and prompts.

    Returns:
        Its checks; a Message with no logged Understanding call fails.
    """
    understanding_calls = [
        call for call in calls if call.step == ModelStep.UNDERSTANDING
    ]
    if not understanding_calls or understanding is None:
        return CheckedMessage(message.text, [], None)
    understanding_call = understanding_calls[-1]
    content = understanding_call.content
    understanding_input = (
        "\n".join(line.text for line in content.history) if content else ""
    )
    results = check_understanding(
        message.expect,
        describe_what_was_done(understanding, understanding_input, calls),
    )
    results.append(full_content_check(calls))
    rules = {rule: case.rules[rule] for rule in message.expect.rules}
    verdicts = (
        judge_persona_rules(judge_chat_model, judge, transcript, rules) if rules else []
    )
    checks = [
        *(
            Check(result.name, result.passed, result.detail, group=message.text)
            for result in results
        ),
        *(verdict_check(verdict, group=message.text) for verdict in verdicts),
    ]
    checked = CheckedMessage(
        message.text,
        checks,
        {
            "duration_ms": understanding_call.duration_ms,
            "tokens_in": understanding_call.tokens_in,
            "tokens_out": understanding_call.tokens_out,
        },
    )
    if checked.passed:
        return checked
    return CheckedMessage(
        checked.text,
        checked.checks,
        checked.call,
        [
            f"The Understanding of “{message.text}” was given:",
            understanding_input,
            "It answered:",
            content.response if content else "(no content kept)",
            "",
        ],
    )


def latest_understanding(
    repositories: Repositories, user_id: UUID
) -> Understanding | None:
    """Read the newest Understanding in the User's latest Conversation.

    Args:
        repositories: Where Conversations and Understandings are stored.
        user_id: The User's ID.

    Returns:
        The Understanding; None if there is none.
    """
    conversation = repositories.conversations.get_latest_for_user(user_id)
    if conversation is None:
        return None
    understandings = repositories.understandings.list_for_conversation(conversation.id)
    return understandings[-1] if understandings else None


def message_facts(checked: CheckedMessage) -> dict[str, Any]:
    """Write a checked Message's outcome for the report.

    Args:
        checked: The checked Message.

    Returns:
        Its text, whether it passed and its Understanding call's time and
        tokens.
    """
    return {"text": checked.text, "passed": checked.passed, "call": checked.call}


def check_understanding_case(
    case: UnderstandingCase,
    companion: EvalCompanion,
    judge: JudgeSettings,
    should_stop: StopCheck,
) -> CaseCheckResult:
    """Give a made-up User a memory, send Messages and check each Understanding.

    Args:
        case: The made-up memory, Conversation and Messages.
        companion: The app on the Eval database.
        judge: The Judge's model, thinking and prompts.
        should_stop: Says why the run is to stop, or None to carry on;
            asked before each Message after the first.

    Returns:
        Every Message's checks, grouped by Message; its facts hold each
        Message's outcome and Understanding call. A failed case notes what
        the Understanding was given and answered, and the conversation.

    Raises:
        CaseStoppedError: If the run is to stop before the last Message.
    """
    upload_knowledge_documents(companion, case.memory.knowledge_documents)
    companion.move_clock(case.now - companion.now())
    user_id = companion.connect_user()
    repositories = companion.repositories
    if case.check_in_due:
        make_check_in_due(repositories, user_id, companion.now())
    open_conversation_id = open_conversation_with(
        repositories, user_id, case.earlier, companion.now()
    )
    give_made_up_memory(
        repositories,
        companion.embedder,
        user_id,
        case.memory,
        companion.now(),
        open_conversation_id,
    )
    seen_trace_ids: set[UUID] = set()
    calls_in_new_traces(repositories, user_id, seen_trace_ids)
    transcript_lines = [
        transcript_line(line.from_person, line.text) for line in case.earlier
    ]

    checked_messages: list[CheckedMessage] = []
    for message in case.messages:
        stop_reason = should_stop() if checked_messages else None
        if stop_reason is not None:
            raise CaseStoppedError(
                f"Stopped after {len(checked_messages)} of "
                f"{len(case.messages)} Messages: {stop_reason}."
            )
        transcript_lines += send_and_collect_lines(companion, message.text)
        checked_messages.append(
            check_message(
                case,
                message,
                calls_in_new_traces(repositories, user_id, seen_trace_ids),
                latest_understanding(repositories, user_id),
                "\n".join(transcript_lines),
                companion.judge_chat_model,
                judge,
            )
        )

    failed = [checked for checked in checked_messages if not checked.passed]
    return CaseCheckResult(
        outcome=CaseOutcome.FAIL if failed else CaseOutcome.PASS,
        checks=[check for checked in checked_messages for check in checked.checks],
        facts={"messages": [message_facts(checked) for checked in checked_messages]},
        notes=(
            [
                *(line for checked in failed for line in checked.failure_details),
                *transcript_lines,
            ]
            if failed
            else []
        ),
    )
