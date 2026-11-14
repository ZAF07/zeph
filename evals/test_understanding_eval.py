import re
from collections.abc import Sequence
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
    EarlierLine,
    EvalKnowledgeDocument,
    UnderstandingCase,
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


def calls_since(
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
        user_id, None, None, False, TRACES_READ_AT_MOST
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


def observe(understanding: Understanding, shown: str) -> ObservedUnderstanding:
    """Describe what a saved Understanding did, for the checks.

    Args:
        understanding: The Message's saved Understanding.
        shown: What the Understanding model was given.

    Returns:
        What it did.
    """
    form = understanding.form
    return ObservedUnderstanding(
        need=understanding.need,
        shown=shown,
        raised_threads=[item.title for item in form.bring_up],
        raised_curiosities=len(form.curiosities),
        asked_why=understanding.asked_why,
        knowledge_documents=list(form.knowledge.documents) if form.knowledge else [],
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


def transcript_lines_for(earlier: Sequence[EarlierLine]) -> list[str]:
    """Write the earlier messages as lines of the Judge's transcript.

    Args:
        earlier: The messages already in the Conversation.

    Returns:
        One "Person:" or "Zeph:" line each.
    """
    return [
        f"{'Person' if line.from_person else 'Zeph'}: {line.text}" for line in earlier
    ]


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
    calls_since(repositories, user_id, seen_trace_ids)
    transcript_lines = transcript_lines_for(case.earlier)

    results = []
    understanding_lines = []
    for message in case.messages:
        already_sent = len(chat_channel.sent)
        assert send_to_webhook(client, telegram_text_update(message.text)) == 200
        transcript_lines.append(f"Person: {message.text}")
        transcript_lines += [
            f"Zeph: {sent.text}" for sent in chat_channel.sent[already_sent:]
        ]
        calls = calls_since(repositories, user_id, seen_trace_ids)
        understanding_calls = [
            call for call in calls if call.step == ModelStep.UNDERSTANDING
        ]
        conversation = repositories.conversations.get_latest_for_user(user_id)
        assert conversation is not None
        understandings = repositories.understandings.list_for_conversation(
            conversation.id
        )
        if not understanding_calls or not understandings:
            results.append(
                UnderstandingMessageResult(case.id, message.text, [], [], None)
            )
            continue
        [understanding_call] = understanding_calls
        content = understanding_call.content
        shown = "\n".join(line.text for line in content.history) if content else ""
        checks = check_understanding(message.expect, observe(understandings[-1], shown))
        checks.append(full_content_check(calls))
        rules = {rule: UNDERSTANDING_CASES.rules[rule] for rule in message.expect.rules}
        verdicts = (
            judge_persona_rules(chat_model, "\n".join(transcript_lines), rules)
            if rules
            else []
        )
        result = UnderstandingMessageResult(
            case.id,
            message.text,
            checks,
            verdicts,
            UnderstandingCallStats(
                understanding_call.duration_ms,
                understanding_call.tokens_in,
                understanding_call.tokens_out,
            ),
        )
        results.append(result)
        if not result.passed:
            understanding_lines += [
                f"The Understanding of “{message.text}” was given:",
                shown,
                "It answered:",
                content.response if content else "(no content kept)",
                "",
            ]

    eval_report.understanding += results
    failed = [result for result in results if not result.passed]
    assert not failed, "\n".join(
        [
            *understanding_lines,
            *transcript_lines,
            "",
            *[line for result in failed for line in result.describe()],
        ]
    )
