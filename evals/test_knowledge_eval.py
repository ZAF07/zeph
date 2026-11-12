import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from companion.adapters.knowledge_seed import read_knowledge_seed
from evals.cases import CASES_DIR, KnowledgeCase, load_knowledge_cases
from evals.judge import judge_version
from evals.report import EvalReport, KnowledgeStepResult
from evals.token_counting_chat_model import TokenCountingChatModel
from tests.conftest import KNOWLEDGE_SEED_FILE
from tests.fakes import FakeAuthVerifier, FakeChatChannel, FakeClock
from tests.knowledge_helpers import upload_document
from tests.telegram_helpers import (
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)

pytestmark = pytest.mark.eval

KNOWLEDGE_CASES = load_knowledge_cases(CASES_DIR / "knowledge.yaml")
READY_TIMEOUT_SECONDS = 120


def upload_starter_library(client: TestClient, admin: dict[str, str]) -> None:
    """Upload the starter Knowledge library, so retrieval has to choose."""
    for upload in read_knowledge_seed(KNOWLEDGE_SEED_FILE):
        response = upload_document(
            client,
            admin,
            upload.file_name,
            upload.content,
            title=upload.title,
            source=upload.source,
            tradition=upload.tradition,
        )
        assert response.status_code == 201, response.text


def wait_until_ready(
    client: TestClient, admin: dict[str, str], document_id: str
) -> None:
    """Wait until a Knowledge document is Ready, failing if it fails or stalls."""
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        response = client.get(
            f"/api/admin/knowledge-documents/{document_id}", headers=admin
        )
        document_status = response.json()["status"]
        if document_status == "ready":
            return
        assert document_status != "failed", response.json()["failure_reason"]
        time.sleep(1)
    pytest.fail(f"Knowledge document {document_id} was not Ready in time")


def ask(
    client: TestClient, chat_channel: FakeChatChannel, clock: FakeClock, question: str
) -> str:
    """Ask a question in a new Conversation and return Zeph's reply.

    A day passes first, so the Conversation is new and the earlier answers
    aren't in its history.
    """
    clock.advance(timedelta(days=1))
    already_sent = len(chat_channel.sent)
    assert send_to_webhook(client, telegram_text_update(question)) == 200
    return "\n".join(sent.text for sent in chat_channel.sent[already_sent:])


@pytest.mark.parametrize("case", KNOWLEDGE_CASES, ids=[c.id for c in KNOWLEDGE_CASES])
def test_replies_use_the_current_version_of_a_knowledge_document(
    case: KnowledgeCase,
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: TokenCountingChatModel,
    clock: FakeClock,
    eval_report: EvalReport,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    upload_starter_library(client, admin)
    texts = {
        "original": case.original_text,
        "edited": case.edited_text,
        "replacement": case.replacement_text,
    }
    details = {
        "original": case.original_details.describe(),
        "edited": case.edited_details.describe(),
    }
    steps: list[KnowledgeStepResult] = []

    def check_reply(
        step: str, question: str, versions: dict[str, str], expected: str
    ) -> None:
        wait_until_ready(client, admin, document_id)
        reply = ask(client, chat_channel, clock, question)
        verdict = judge_version(chat_model, question, reply, versions)
        older = list(versions)[: list(versions).index(expected)]
        result = KnowledgeStepResult(case.id, step, expected, older, verdict)
        steps.append(result)
        eval_report.knowledge.append(result)

    uploaded = upload_document(
        client,
        admin,
        case.original_file_name,
        case.original_text.encode(),
        title=case.original_details.title,
        source=case.original_details.source,
        tradition=case.original_details.tradition,
    )
    assert uploaded.status_code == 201, uploaded.text
    document_id = uploaded.json()["id"]
    check_reply("uploaded", case.question, texts, "original")

    edited = client.put(
        f"/api/admin/knowledge-documents/{document_id}/text",
        json={"text": case.edited_text},
        headers=admin,
    )
    assert edited.status_code == 200, edited.text
    check_reply("text edited", case.question, texts, "edited")

    new_details = case.edited_details
    renamed = client.patch(
        f"/api/admin/knowledge-documents/{document_id}",
        json={
            "title": new_details.title,
            "source": new_details.source,
            "tradition": new_details.tradition,
        },
        headers=admin,
    )
    assert renamed.status_code == 200, renamed.text
    check_reply("details edited", case.source_question, details, "edited")

    replaced = client.put(
        f"/api/admin/knowledge-documents/{document_id}/file",
        files={"file": (case.replacement_file_name, case.replacement_text.encode())},
        headers=admin,
    )
    assert replaced.status_code == 200, replaced.text
    check_reply("file replaced", case.question, texts, "replacement")

    failed = [step.describe() for step in steps if not step.passed]
    assert not failed, "\n".join(failed)
