from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select

from companion.adapters.postgres.tables import knowledge_chunks
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeEmbedder,
    ScriptedChatModel,
)
from tests.knowledge_helpers import (
    blank_pdf,
    document_text,
    list_documents,
    pdf_with_text,
    upload_document,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)

MISSING_ID = "00000000-0000-0000-0000-000000000000"
BREATH_PASSAGES = [
    "Breathing in, notice the breath entering. Breathing out, notice the breath "
    "leaving. When attention wanders, return gently to the breath.",
    "The breath is always here, an anchor to the present moment. Counting each "
    "breath settles a scattered attention.",
    "Long breath or short breath, simply know it. Watching breathing without "
    "forcing it brings calm.",
]
TAX_PASSAGE = "Quarterly invoices, receipts and spreadsheets for accountants."


def chunk_count(engine: Engine) -> int:
    with engine.connect() as connection:
        count: int = connection.execute(
            select(func.count()).select_from(knowledge_chunks)
        ).scalar_one()
    return count


def reply_instructions(
    client: TestClient, chat_model: ScriptedChatModel, text: str
) -> str:
    """Send a Telegram message and return the instructions its reply was given."""
    chat_model.calls.clear()
    chat_model.script("mm, yes")
    assert send_to_webhook(client, telegram_text_update(text)) == 200
    [reply_call] = chat_model.calls
    return reply_call.instructions


def test_an_uploaded_text_document_starts_pending_and_becomes_ready(
    client: TestClient, auth_verifier: FakeAuthVerifier, clock: FakeClock
) -> None:
    admin = owner_headers(client, auth_verifier)

    response = upload_document(
        client,
        admin,
        "dhammapada.txt",
        b"All that we are is the result of what we have thought.",
        title="  Dhammapada ",
    )

    assert response.status_code == 201, response.text
    uploaded = response.json()
    assert uploaded["status"] == "pending"
    [document] = list_documents(client, admin)
    assert document == {
        "id": uploaded["id"],
        "title": "Dhammapada",
        "source": "trans. Max Müller",
        "tradition": "Buddhism",
        "file_name": "dhammapada.txt",
        "file_type": "text",
        "status": "ready",
        "failure_reason": None,
        "text_edited": False,
        "created_at": clock.now().isoformat().replace("+00:00", "Z"),
    }


def test_a_document_shows_the_text_read_from_its_file(
    client: TestClient, auth_verifier: FakeAuthVerifier, clock: FakeClock
) -> None:
    admin = owner_headers(client, auth_verifier)
    uploaded = upload_document(
        client, admin, "dhammapada.txt", "\ufeffMind is the forerunner.\n".encode()
    ).json()

    response = client.get(
        f"/api/admin/knowledge-documents/{uploaded['id']}", headers=admin
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": uploaded["id"],
        "title": "Dhammapada",
        "source": "trans. Max Müller",
        "tradition": "Buddhism",
        "file_name": "dhammapada.txt",
        "file_type": "text",
        "status": "ready",
        "failure_reason": None,
        "text_edited": False,
        "created_at": clock.now().isoformat().replace("+00:00", "Z"),
        "text": "Mind is the forerunner.",
    }


def test_markdown_and_pdf_documents_show_their_text(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    markdown = upload_document(
        client, admin, "notes.md", b"# Breath\n\nNotice the breath."
    ).json()
    pdf = upload_document(
        client, admin, "verses.pdf", pdf_with_text("Mind is the forerunner")
    ).json()

    assert document_text(client, admin, markdown["id"]) == (
        "# Breath\n\nNotice the breath."
    )
    assert "Mind is the forerunner" in str(document_text(client, admin, pdf["id"]))


def test_a_document_whose_file_had_no_text_shows_no_text(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    scan = upload_document(client, admin, "scan.pdf", blank_pdf()).json()

    response = client.get(f"/api/admin/knowledge-documents/{scan['id']}", headers=admin)

    assert response.json()["status"] == "failed"
    assert response.json()["text"] is None


def test_viewing_a_missing_document_is_not_found(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    response = client.get(f"/api/admin/knowledge-documents/{MISSING_ID}", headers=admin)

    assert response.status_code == 404


def test_markdown_and_pdf_documents_become_ready(
    client: TestClient, auth_verifier: FakeAuthVerifier, engine: Engine
) -> None:
    admin = owner_headers(client, auth_verifier)

    upload_document(client, admin, "notes.md", b"# Breath\n\nNotice the breath.")
    upload_document(
        client, admin, "verses.pdf", pdf_with_text("Mind is the forerunner")
    )

    documents = list_documents(client, admin)
    assert sorted((d["file_type"], d["status"]) for d in documents) == [
        ("markdown", "ready"),
        ("pdf", "ready"),
    ]
    assert chunk_count(engine) == 2


def test_a_pdf_with_no_text_fails_with_the_reason(
    client: TestClient, auth_verifier: FakeAuthVerifier, engine: Engine
) -> None:
    admin = owner_headers(client, auth_verifier)

    response = upload_document(client, admin, "scan.pdf", blank_pdf())

    assert response.json()["status"] == "pending"
    [document] = list_documents(client, admin)
    assert document["status"] == "failed"
    assert document["failure_reason"] == "Scanned PDF — no text found"
    assert chunk_count(engine) == 0


def test_a_broken_pdf_or_non_utf8_text_fails_with_the_reason(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    upload_document(client, admin, "broken.pdf", b"not really a pdf", title="Broken")
    upload_document(client, admin, "latin1.txt", "café".encode("latin-1"), title="Odd")

    reasons = {d["title"]: d["failure_reason"] for d in list_documents(client, admin)}
    assert reasons == {
        "Broken": "Couldn’t read this PDF.",
        "Odd": "Couldn’t read the text. Save the file as UTF-8 and try again.",
    }


def test_a_document_that_could_not_be_indexed_can_be_retried(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    embedder: FakeEmbedder,
    engine: Engine,
) -> None:
    admin = owner_headers(client, auth_verifier)
    embedder.failure = RuntimeError("model download failed")
    upload_document(client, admin, "breath.txt", BREATH_PASSAGES[0].encode())
    [failed] = list_documents(client, admin)
    assert failed["status"] == "failed"
    assert failed["failure_reason"] == "Couldn’t index the document. Try again."

    embedder.failure = None
    response = client.post(
        f"/api/admin/knowledge-documents/{failed['id']}/retry", headers=admin
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "pending"
    [document] = list_documents(client, admin)
    assert document["status"] == "ready"
    assert document["failure_reason"] is None
    assert chunk_count(engine) == 1


def test_only_a_failed_document_can_be_retried(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_document(client, admin, "breath.txt", BREATH_PASSAGES[0].encode())
    [ready] = list_documents(client, admin)

    retry_ready = client.post(
        f"/api/admin/knowledge-documents/{ready['id']}/retry", headers=admin
    )
    retry_missing = client.post(
        f"/api/admin/knowledge-documents/{MISSING_ID}/retry", headers=admin
    )

    assert retry_ready.status_code == 409
    assert retry_missing.status_code == 404


def test_uploads_with_a_wrong_file_type_blank_details_or_no_content_are_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    wrong_type = upload_document(client, admin, "essay.docx", b"words")
    blank_title = upload_document(client, admin, "a.txt", b"words", title="  ")
    blank_source = upload_document(client, admin, "a.txt", b"words", source="")
    empty_file = upload_document(client, admin, "a.txt", b"")

    assert wrong_type.status_code == 422
    assert wrong_type.json()["detail"] == (
        "Upload a text (.txt), Markdown (.md) or PDF (.pdf) file."
    )
    assert blank_title.json()["detail"] == "A document needs a title."
    assert blank_source.status_code == 422
    assert empty_file.json()["detail"] == "The file is empty."
    assert list_documents(client, admin) == []


def test_documents_are_listed_newest_first(
    client: TestClient, auth_verifier: FakeAuthVerifier, clock: FakeClock
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_document(client, admin, "a.txt", b"First words", title="Older")
    clock.advance(timedelta(days=1))
    upload_document(client, admin, "b.txt", b"Second words", title="Newer")

    titles = [document["title"] for document in list_documents(client, admin)]

    assert titles == ["Newer", "Older"]


def test_matching_knowledge_reaches_the_reply_with_where_it_is_from(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    embedder: FakeEmbedder,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_document(client, admin, "tax.txt", TAX_PASSAGE.encode(), title="Taxes")
    for number, passage in enumerate(BREATH_PASSAGES, start=1):
        upload_document(
            client,
            admin,
            f"breath-{number}.md",
            passage.encode(),
            title=f"On the breath {number}",
            source="Owner’s summary",
            tradition="Mindfulness",
        )
    connect_telegram(client, auth_verifier, chat_channel)

    instructions = reply_instructions(
        client, chat_model, "my attention keeps drifting, the breath helps"
    )

    assert embedder.queries[-1] == "my attention keeps drifting, the breath helps"
    assert seeded_settings["knowledge_chunks_per_reply"] == 3
    assert seeded_settings["reply_knowledge_intro"] in instructions
    assert (
        f"From “On the breath 1” (Owner’s summary, Mindfulness):\n{BREATH_PASSAGES[0]}"
    ) in instructions
    for passage in BREATH_PASSAGES:
        assert passage in instructions
    assert TAX_PASSAGE not in instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["mm, yes"]


def test_a_failed_document_never_reaches_the_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    embedder: FakeEmbedder,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_document(client, admin, "scan.pdf", blank_pdf(), title="Scan")
    connect_telegram(client, auth_verifier, chat_channel)

    instructions = reply_instructions(client, chat_model, "notice the breath")

    assert instructions == (
        f"{seeded_settings['persona']}\n\n{seeded_settings['response_prompt']}"
    )


def test_a_deleted_document_and_its_chunks_are_gone_from_replies(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_document(client, admin, "breath.txt", BREATH_PASSAGES[0].encode())
    upload_document(client, admin, "tax.txt", TAX_PASSAGE.encode(), title="Taxes")
    [breath] = [d for d in list_documents(client, admin) if d["title"] != "Taxes"]
    connect_telegram(client, auth_verifier, chat_channel)
    assert BREATH_PASSAGES[0] in reply_instructions(client, chat_model, "the breath")

    response = client.delete(
        f"/api/admin/knowledge-documents/{breath['id']}", headers=admin
    )

    assert response.status_code == 204
    assert [d["title"] for d in list_documents(client, admin)] == ["Taxes"]
    assert chunk_count(engine) == 1
    assert BREATH_PASSAGES[0] not in reply_instructions(
        client, chat_model, "the breath"
    )
    missing = client.delete(
        f"/api/admin/knowledge-documents/{MISSING_ID}", headers=admin
    )
    assert missing.status_code == 404


def test_the_reply_still_goes_when_knowledge_search_fails(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    embedder: FakeEmbedder,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_document(client, admin, "breath.txt", BREATH_PASSAGES[0].encode())
    connect_telegram(client, auth_verifier, chat_channel)
    embedder.failure = RuntimeError("model gone")

    instructions = reply_instructions(client, chat_model, "the breath")

    assert seeded_settings["reply_knowledge_intro"] not in instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["mm, yes"]


def test_only_admins_can_manage_knowledge(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    user = auth_headers(auth_verifier, "user_maya")

    listed = client.get("/api/admin/knowledge-documents", headers=user)
    viewed = client.get(f"/api/admin/knowledge-documents/{MISSING_ID}", headers=user)
    uploaded = upload_document(client, user, "a.txt", b"words")
    deleted = client.delete(
        f"/api/admin/knowledge-documents/{MISSING_ID}", headers=user
    )

    assert [
        listed.status_code,
        viewed.status_code,
        uploaded.status_code,
        deleted.status_code,
    ] == [403, 403, 403, 403]
