import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.fastembed.embedder import FastEmbedEmbedder
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import ModelCall, ModelStep, Understanding
from companion.core.ports import Repositories
from evals.cases import (
    CASES_DIR,
    EvalKnowledgeDocument,
    UnderstandingCase,
    UnderstandingMessage,
    load_understanding_cases,
)
from evals.judge import judge_persona_rules
from evals.made_up_memory import give_made_up_memory, open_conversation_with
from evals.report import (
    EvalReport,
    UnderstandingCallStats,
    UnderstandingMessageResult,
)
from evals.running_clock import RunningClock
from evals.test_knowledge_eval import wait_until_ready
from evals.token_counting_chat_model import TokenCountingChatModel
from evals.understanding_checks import (
    CheckResult,
    ObservedUnderstanding,
    check_understanding,
)
from tests.fakes import FakeAuthVerifier, FakeChatChannel, FakeClock
from tests.knowledge_helpers import upload_document
from tests.telegram_helpers import (
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)

pytestmark = pytest.mark.eval

UNDERSTANDING_CASES = load_understanding_cases(CASES_DIR / "understanding.yaml")
TRACES_READ_AT_MOST = 200
KNOWLEDGE_PASSAGE_SOURCE = re.compile(r"^From “(.+?)” \(", re.MULTILINE)


@pytest.fixture
def clock() -> FakeClock:
    """A clock that moves with real time, so Understanding calls are timed.

    Typing pauses still don't wait. It replaces the evals' frozen clock for
    this eval only.
    """
    return RunningClock(datetime.now(UTC))


def upload_knowledge_documents(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    documents: Sequence[EvalKnowledgeDocument],
) -> None:
    """Upload Knowledge Documents as an Admin and set when each helps.

    Args:
        client: The backend's test client.
        auth_verifier: Hands out the Admin's sign-in.
        documents: The documents.
    """
    if not documents:
        return
    admin = owner_headers(client, auth_verifier)
    for document in documents:
        file_name = re.sub(r"\W+", "-", document.title.lower()) + ".txt"
        response = upload_document(
            client,
            admin,
            file_name,
            document.text.encode(),
            title=document.title,
            source=document.source,
            tradition=document.tradition,
        )
        assert response.status_code == 201, response.text
        document_id = response.json()["id"]
        wait_until_ready(client, admin, document_id)
        response = client.patch(
            f"/api/admin/knowledge-documents/{document_id}",
            json={"when_it_helps": document.when_it_helps},
            headers=admin,
        )
        assert response.status_code == 200, response.text


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
        assert details is not None
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
        knowledge_documents=list(form.knowledge.documents) if form.knowledge else [],
        knowledge_in_reply=knowledge_in_reply(calls),
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


def send_and_collect_lines(
    client: TestClient, chat_channel: FakeChatChannel, text: str
) -> list[str]:
    """Send one Message through the webhook and write it and Zeph's replies.

    Args:
        client: The backend's test client.
        chat_channel: Records what Zeph sends.
        text: What the person sends.

    Returns:
        The Message's transcript line, then one per reply text.
    """
    already_sent = len(chat_channel.sent)
    assert send_to_webhook(client, telegram_text_update(text)) == 200
    return [
        transcript_line(True, text),
        *(
            transcript_line(False, sent.text)
            for sent in chat_channel.sent[already_sent:]
        ),
    ]


@dataclass(frozen=True)
class CheckedMessage:
    """One Message's result, and what to print if it failed.

    Attributes:
        result: The result for the report.
        failure_details: What the Understanding was given and answered;
            empty when the Message passed.
    """

    result: UnderstandingMessageResult
    failure_details: list[str]


def check_message(
    case_id: str,
    message: UnderstandingMessage,
    calls: Sequence[ModelCall],
    understanding: Understanding | None,
    transcript: str,
    chat_model: TokenCountingChatModel,
) -> CheckedMessage:
    """Check one Message's Understanding and reply, and judge the reply.

    Args:
        case_id: The case's ID.
        message: The Message and what it should do.
        calls: Its model calls, from the Model Call Log.
        understanding: Its saved Understanding; None if none was saved.
        transcript: The Conversation so far, for the Judge.
        chat_model: The model that judges.

    Returns:
        Its result; a Message with no logged Understanding call fails.
    """
    understanding_calls = [
        call for call in calls if call.step == ModelStep.UNDERSTANDING
    ]
    if not understanding_calls or understanding is None:
        return CheckedMessage(
            UnderstandingMessageResult(case_id, message.text, [], [], None), []
        )
    understanding_call = understanding_calls[-1]
    content = understanding_call.content
    understanding_input = (
        "\n".join(line.text for line in content.history) if content else ""
    )
    checks = check_understanding(
        message.expect,
        describe_what_was_done(understanding, understanding_input, calls),
    )
    checks.append(full_content_check(calls))
    rules = {rule: UNDERSTANDING_CASES.rules[rule] for rule in message.expect.rules}
    verdicts = judge_persona_rules(chat_model, transcript, rules) if rules else []
    result = UnderstandingMessageResult(
        case_id,
        message.text,
        checks,
        verdicts,
        UnderstandingCallStats(
            understanding_call.duration_ms,
            understanding_call.tokens_in,
            understanding_call.tokens_out,
        ),
    )
    if result.passed:
        return CheckedMessage(result, [])
    return CheckedMessage(
        result,
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


@pytest.mark.parametrize(
    "case",
    UNDERSTANDING_CASES.cases,
    ids=[case.id for case in UNDERSTANDING_CASES.cases],
)
def test_the_understanding_reads_the_user_and_the_reply_follows_it(
    case: UnderstandingCase,
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: TokenCountingChatModel,
    embedder: FastEmbedEmbedder,
    clock: FakeClock,
    eval_report: EvalReport,
) -> None:
    upload_knowledge_documents(client, auth_verifier, case.memory.knowledge_documents)
    clock.advance(case.now - clock.now())
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    user_id = UUID(client.get("/api/me", headers=headers).json()["id"])
    repositories = build_postgres_repositories(engine)
    open_conversation_id = open_conversation_with(
        repositories, user_id, case.earlier, clock.now()
    )
    give_made_up_memory(
        repositories, embedder, user_id, case.memory, clock.now(), open_conversation_id
    )
    seen_trace_ids: set[UUID] = set()
    calls_in_new_traces(repositories, user_id, seen_trace_ids)
    transcript_lines = [
        transcript_line(line.from_person, line.text) for line in case.earlier
    ]

    checked_messages = []
    for message in case.messages:
        transcript_lines += send_and_collect_lines(client, chat_channel, message.text)
        checked_messages.append(
            check_message(
                case.id,
                message,
                calls_in_new_traces(repositories, user_id, seen_trace_ids),
                latest_understanding(repositories, user_id),
                "\n".join(transcript_lines),
                chat_model,
            )
        )

    eval_report.understanding += [checked.result for checked in checked_messages]
    failed = [checked for checked in checked_messages if not checked.result.passed]
    assert not failed, "\n".join(
        [
            *(line for checked in failed for line in checked.failure_details),
            *transcript_lines,
            "",
            *(line for checked in failed for line in checked.result.describe()),
        ]
    )
