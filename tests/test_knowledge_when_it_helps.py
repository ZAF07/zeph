import json
import re
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    MIGRATIONS_DIR,
    migrate,
    seed_platform_settings,
)
from tests.conftest import SEED_FILE
from tests.fakes import (
    DEFAULT_WHEN_IT_HELPS,
    FakeAuthVerifier,
    FakeChatChannel,
    FakeEmbedder,
    ScriptedChatModel,
    reply_plan_answer,
)
from tests.knowledge_helpers import list_documents, upload_document
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_understanding import saved_reply_plans

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
    client: TestClient, chat_model: ScriptedChatModel, text: str, reply_plan: str
) -> str:
    """Send a message the Reply Plan plans as given; return the reply's prompt."""
    chat_model.calls.clear()
    chat_model.reply_plan_calls.clear()
    chat_model.script_reply_plan(reply_plan)
    chat_model.script("mm, yes")
    assert send_to_webhook(client, telegram_text_update(text)) == 200
    [reply_call] = chat_model.calls
    return reply_call.instructions


def listed_number(chat_model: ScriptedChatModel, title: str) -> int:
    """Find the number the last Reply Plan call listed a document under."""
    [asked] = chat_model.reply_plan_calls[-1].history
    found = re.search(rf"^\[(\d+)\] “{re.escape(title)}”", asked.text, re.MULTILINE)
    assert found, asked.text
    return int(found.group(1))


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


def test_an_admin_edits_when_it_helps_and_the_next_reply_plan_sees_it(
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
    reply_instructions(client, chat_model, "hello", reply_plan_answer())

    assert response.status_code == 200, response.text
    assert response.json()["when_it_helps"] == "When they can't sleep for worry."
    assert response.json()["title"] == "On the breath"
    [reply_plan_call] = chat_model.reply_plan_calls
    [asked] = reply_plan_call.history
    assert (
        "[1] “On the breath” (Owner’s notes, Mindfulness): "
        "When they can't sleep for worry."
    ) in asked.text


def test_the_reply_plan_sees_only_ready_documents(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_ready(client, admin, "On the breath", BREATH_TEXT)
    upload_document(client, admin, "scan.pdf", b"%PDF-1.4 broken", title="Scan")
    connect_telegram(client, auth_verifier, chat_channel)

    reply_instructions(client, chat_model, "hello", reply_plan_answer())

    [reply_plan_call] = chat_model.reply_plan_calls
    [asked] = reply_plan_call.history
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
        reply_plan_answer(need="Be heard"),
    )

    assert seeded_settings["reply_knowledge_intro"] not in instructions
    assert BREATH_TEXT not in instructions
    assert set(embedder.queries[searches_before:]) == {
        "my attention keeps drifting, the breath helps",
        "They're just saying hi.\nmy attention keeps drifting, the breath helps",
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
    reply_instructions(client, chat_model, "hello", reply_plan_answer())

    instructions = reply_instructions(
        client,
        chat_model,
        "yeah, exactly",
        reply_plan_answer(
            need="Think it through",
            knowledge_documents=[listed_number(chat_model, "On grief")],
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


def test_the_reply_plan_picks_documents_by_their_listed_number(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_ready(client, admin, "On the breath", BREATH_TEXT)
    grief = upload_ready(client, admin, "On grief", GRIEF_TEXT)
    upload_ready(client, admin, "Taxes", TAX_TEXT)
    connect_telegram(client, auth_verifier, chat_channel)
    set_settings(client, admin, {"knowledge_closeness_percent": 0})
    reply_instructions(client, chat_model, "hello", reply_plan_answer())
    grief_number = listed_number(chat_model, "On grief")

    instructions = reply_instructions(
        client,
        chat_model,
        "it keeps coming in waves",
        reply_plan_answer(
            knowledge_documents=[grief_number], knowledge_search=BREATH_SEARCH
        ),
    )

    assert f"From “On grief” (Owner’s notes, Mindfulness):\n{GRIEF_TEXT}" in (
        instructions
    )
    assert BREATH_TEXT not in instructions
    assert TAX_TEXT not in instructions
    chosen = saved_reply_plans(engine)[-1]["form"]["knowledge"]
    assert chosen == {
        "documents": [{"document_id": grief["id"], "title": "On grief"}],
        "search": BREATH_SEARCH,
    }


def test_a_chosen_document_is_kept_when_the_next_message_is_planned(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_ready(client, admin, "On grief", GRIEF_TEXT)
    connect_telegram(client, auth_verifier, chat_channel)
    set_settings(client, admin, {"knowledge_closeness_percent": 0})
    chosen = reply_plan_answer(knowledge_documents=[1], knowledge_search=BREATH_SEARCH)

    first = reply_instructions(client, chat_model, "it comes in waves", chosen)
    second = reply_instructions(client, chat_model, "still waves", chosen)

    assert GRIEF_TEXT in first
    assert GRIEF_TEXT in second


@pytest.mark.parametrize(
    "picked",
    [
        2,
        0,
        -1,
        True,
        "1",
        "On grief",
        "“On grief” (Owner’s notes, Mindfulness)",
        {"document": 1},
    ],
)
def test_a_number_not_in_the_list_or_a_title_picks_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    embedder: FakeEmbedder,
    engine: Engine,
    seeded_settings: dict[str, Any],
    picked: Any,
) -> None:
    admin = owner_headers(client, auth_verifier)
    upload_ready(client, admin, "On grief", GRIEF_TEXT)
    connect_telegram(client, auth_verifier, chat_channel)
    set_settings(client, admin, {"knowledge_closeness_percent": 0})

    instructions = reply_instructions(
        client,
        chat_model,
        "it keeps coming in waves",
        reply_plan_answer(knowledge_documents=[picked], knowledge_search=BREATH_SEARCH),
    )

    assert seeded_settings["reply_knowledge_intro"] not in instructions
    assert GRIEF_TEXT not in instructions
    assert BREATH_SEARCH not in embedder.queries
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["mm, yes"]
    assert saved_reply_plans(engine)[-1]["form"]["knowledge"] is None


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
        reply_plan_answer(knowledge_documents=[1], knowledge_search=BREATH_SEARCH),
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
    chosen = reply_plan_answer(knowledge_documents=[1], knowledge_search=BREATH_SEARCH)

    set_settings(client, admin, {"knowledge_closeness_percent": 99})
    strict = reply_instructions(client, chat_model, "the breath", chosen)
    set_settings(client, admin, {"knowledge_closeness_percent": 0})
    loose = reply_instructions(client, chat_model, "the breath", chosen)

    assert GRIEF_TEXT not in strict
    assert GRIEF_TEXT in loose


def test_an_unknown_document_number_or_a_missing_phrase_searches_nothing(
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
        reply_plan_answer(knowledge_documents=[2], knowledge_search=BREATH_SEARCH),
    )
    no_phrase = reply_instructions(
        client,
        chat_model,
        "the breath",
        reply_plan_answer(knowledge_documents=[1]),
    )

    assert seeded_settings["reply_knowledge_intro"] not in unknown
    assert seeded_settings["reply_knowledge_intro"] not in no_phrase
    assert BREATH_SEARCH not in embedder.queries[searches_before:]


def test_an_existing_install_gets_the_reply_plan_prompt_that_picks_knowledge_by_number(
    engine: Engine, database_url: str, seeded_settings: dict[str, Any]
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0036")
    try:
        seed_platform_settings(engine, SEED_FILE)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = :old "
                    "WHERE key = 'understanding_prompt'"
                ),
                {"old": json.dumps("Name documents by title exactly as written.")},
            )
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    with engine.connect() as connection:
        prompts = dict(
            connection.execute(
                text(
                    "SELECT key, value FROM platform_settings "
                    "WHERE key IN ('understanding_prompt', 'reply_plan_prompt')"
                )
            ).all()
        )
    assert prompts["understanding_prompt"] == seeded_settings["understanding_prompt"]
    assert prompts["reply_plan_prompt"] == seeded_settings["reply_plan_prompt"]
    assert '"knowledge": {"documents": [<number>]' in prompts["reply_plan_prompt"]
