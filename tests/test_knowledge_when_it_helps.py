from typing import Any

from fastapi.testclient import TestClient

from tests.fakes import (
    DEFAULT_WHEN_IT_HELPS,
    FakeAuthVerifier,
    FakeChatChannel,
    FakeEmbedder,
    ScriptedChatModel,
    understanding_answer,
)
from tests.knowledge_helpers import list_documents, upload_document
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)

BREATH_TEXT = (
    "Breathing in, notice the breath entering. Breathing out, notice the breath "
    "leaving. When attention wanders, return gently to the breath."
)
GRIEF_TEXT = (
    "Grief comes in waves. Breathing slowly through each wave, notice the "
    "breath and let the sorrow pass without holding on."
)
TAX_TEXT = "Quarterly invoices, receipts and spreadsheets for accountants."
BREATH_SEARCH = "notice the breath when attention wanders"


def upload_ready(
    client: TestClient, admin: dict[str, str], title: str, text: str
) -> dict[str, Any]:
    """Upload a text Knowledge document and return it once it is indexed."""
    response = upload_document(
        client,
        admin,
        f"{title.lower().replace(' ', '-')}.txt",
        text.encode(),
        title=title,
        source="Owner’s notes",
        tradition="Mindfulness",
    )
    assert response.status_code == 201, response.text
    [document] = [d for d in list_documents(client, admin) if d["title"] == title]
    assert document["status"] == "ready", document
    return document


def reply_instructions(
    client: TestClient, chat_model: ScriptedChatModel, text: str, understanding: str
) -> str:
    """Send a message the Understanding reads as given; return the reply's prompt."""
    chat_model.calls.clear()
    chat_model.understanding_calls.clear()
    chat_model.script_understanding(understanding)
    chat_model.script("mm, yes")
    assert send_to_webhook(client, telegram_text_update(text)) == 200
    [reply_call] = chat_model.calls
    return reply_call.instructions


def set_settings(
    client: TestClient, admin: dict[str, str], changes: dict[str, Any]
) -> None:
    """Change platform settings through the admin API."""
    response = client.patch(
        "/api/admin/settings", json={"values": changes}, headers=admin
    )
    assert response.status_code == 200, response.text


def test_indexing_a_document_drafts_when_it_helps(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    chat_model.script_when_it_helps(
        "  When someone's attention keeps drifting and they want to settle.  "
    )

    document = upload_ready(client, admin, "On the breath", BREATH_TEXT)

    assert document["when_it_helps"] == (
        "When someone's attention keeps drifting and they want to settle."
    )
    [draft_call] = chat_model.when_it_helps_calls
    assert draft_call.model == seeded_settings["knowledge_when_it_helps_model"]
    [asked] = draft_call.history
    assert "On the breath" in asked.text
    assert "Owner’s notes" in asked.text
    assert BREATH_TEXT in asked.text


def test_a_failed_draft_still_makes_the_document_ready_with_no_description(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    chat_model.script_when_it_helps(RuntimeError("model gone"))

    document = upload_ready(client, admin, "On the breath", BREATH_TEXT)

    assert document["when_it_helps"] == ""


def test_reindexing_keeps_a_description_and_drafts_a_missing_one(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    chat_model.script_when_it_helps(RuntimeError("model gone"))
    document = upload_ready(client, admin, "On the breath", BREATH_TEXT)
    url = f"/api/admin/knowledge-documents/{document['id']}"

    client.put(f"{url}/text", json={"text": GRIEF_TEXT}, headers=admin)
    after_first_edit = client.get(url, headers=admin).json()
    client.put(f"{url}/text", json={"text": BREATH_TEXT}, headers=admin)
    after_second_edit = client.get(url, headers=admin).json()

    assert after_first_edit["when_it_helps"] == DEFAULT_WHEN_IT_HELPS
    assert after_second_edit["when_it_helps"] == DEFAULT_WHEN_IT_HELPS
    assert len(chat_model.when_it_helps_calls) == 2


def test_an_admin_edits_when_it_helps_and_the_next_understanding_sees_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    document = upload_ready(client, admin, "On the breath", BREATH_TEXT)
    connect_telegram(client, auth_verifier, chat_channel)

    response = client.patch(
        f"/api/admin/knowledge-documents/{document['id']}",
        json={"when_it_helps": "  When they can't sleep for worry.  "},
        headers=admin,
    )
    reply_instructions(client, chat_model, "hello", understanding_answer())

    assert response.status_code == 200, response.text
    assert response.json()["when_it_helps"] == "When they can't sleep for worry."
    assert response.json()["title"] == "On the breath"
    [understanding_call] = chat_model.understanding_calls
    [asked] = understanding_call.history
    assert (
        "- “On the breath” (Owner’s notes, Mindfulness): "
        "When they can't sleep for worry."
    ) in asked.text


def test_the_understanding_sees_only_ready_documents(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_ready(client, admin, "On the breath", BREATH_TEXT)
    upload_document(client, admin, "scan.pdf", b"%PDF-1.4 broken", title="Scan")
    connect_telegram(client, auth_verifier, chat_channel)

    reply_instructions(client, chat_model, "hello", understanding_answer())

    [understanding_call] = chat_model.understanding_calls
    [asked] = understanding_call.history
    assert "“On the breath”" in asked.text
    assert "Scan" not in asked.text


def test_with_no_documents_chosen_the_reply_gets_no_knowledge(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    embedder: FakeEmbedder,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_ready(client, admin, "On the breath", BREATH_TEXT)
    connect_telegram(client, auth_verifier, chat_channel)
    searches_before = len(embedder.queries)

    instructions = reply_instructions(
        client,
        chat_model,
        "my attention keeps drifting, the breath helps",
        understanding_answer(need="Be heard"),
    )

    assert seeded_settings["reply_knowledge_intro"] not in instructions
    assert BREATH_TEXT not in instructions
    assert set(embedder.queries[searches_before:]) == {
        "my attention keeps drifting, the breath helps"
    }
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["mm, yes"]


def test_passages_come_only_from_the_chosen_documents(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    embedder: FakeEmbedder,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    for number in range(1, seeded_settings["knowledge_chunks_per_reply"] + 1):
        upload_ready(client, admin, f"On the breath {number}", BREATH_TEXT)
    upload_ready(client, admin, "On grief", GRIEF_TEXT)
    upload_ready(client, admin, "Taxes", TAX_TEXT)
    connect_telegram(client, auth_verifier, chat_channel)
    set_settings(client, admin, {"knowledge_closeness_percent": 0})

    instructions = reply_instructions(
        client,
        chat_model,
        "yeah, exactly",
        understanding_answer(
            need="Think it through",
            knowledge_documents=["on GRIEF"],
            knowledge_search=BREATH_SEARCH,
        ),
    )

    assert embedder.queries[-1] == BREATH_SEARCH
    assert seeded_settings["reply_knowledge_intro"] in instructions
    assert f"From “On grief” (Owner’s notes, Mindfulness):\n{GRIEF_TEXT}" in (
        instructions
    )
    assert BREATH_TEXT not in instructions
    assert TAX_TEXT not in instructions


def test_a_weak_match_in_a_chosen_document_adds_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_ready(client, admin, "Taxes", TAX_TEXT)
    connect_telegram(client, auth_verifier, chat_channel)

    instructions = reply_instructions(
        client,
        chat_model,
        "the breath helps",
        understanding_answer(
            knowledge_documents=["Taxes"], knowledge_search=BREATH_SEARCH
        ),
    )

    assert seeded_settings["reply_knowledge_intro"] not in instructions
    assert TAX_TEXT not in instructions


def test_the_admin_sets_the_knowledge_closeness_bar(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_ready(client, admin, "On grief", GRIEF_TEXT)
    connect_telegram(client, auth_verifier, chat_channel)
    chosen = understanding_answer(
        knowledge_documents=["On grief"], knowledge_search=BREATH_SEARCH
    )

    set_settings(client, admin, {"knowledge_closeness_percent": 99})
    strict = reply_instructions(client, chat_model, "the breath", chosen)
    set_settings(client, admin, {"knowledge_closeness_percent": 0})
    loose = reply_instructions(client, chat_model, "the breath", chosen)

    assert GRIEF_TEXT not in strict
    assert GRIEF_TEXT in loose


def test_an_unknown_document_title_or_a_missing_phrase_searches_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    embedder: FakeEmbedder,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_ready(client, admin, "On the breath", BREATH_TEXT)
    connect_telegram(client, auth_verifier, chat_channel)
    searches_before = len(embedder.queries)

    unknown = reply_instructions(
        client,
        chat_model,
        "the breath",
        understanding_answer(
            knowledge_documents=["Seneca"], knowledge_search=BREATH_SEARCH
        ),
    )
    no_phrase = reply_instructions(
        client,
        chat_model,
        "the breath",
        understanding_answer(knowledge_documents=["On the breath"]),
    )

    assert seeded_settings["reply_knowledge_intro"] not in unknown
    assert seeded_settings["reply_knowledge_intro"] not in no_phrase
    assert BREATH_SEARCH not in embedder.queries[searches_before:]
