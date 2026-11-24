from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate, seed_platform_settings
from tests.conftest import SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    ScriptedChatModel,
    ToolCall,
    understanding_answer,
)
from tests.telegram_helpers import (
    auth_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_sending import set_up_user_with_check_ins
from tests.test_photo_viewing import stored_setting
from tests.test_settings_via_chat import me, reply_call
from tests.test_understanding_migrations import downgrade_to

DIRECTNESS_LINE = "How direct they want you to be with your Read: "


def reply_plan_input(chat_model: ScriptedChatModel) -> str:
    """What the Reply Plan model was given about the newest message."""
    reply_plan_call = chat_model.reply_plan_calls[-1]
    return reply_plan_call.history[0].text


def test_a_new_user_starts_on_balanced(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    assert me(client, auth_headers(auth_verifier, "user_maya"))["directness"] == (
        "balanced"
    )


def test_a_user_picks_how_direct_zeph_is_on_the_dashboard(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")

    response = client.patch("/api/me", json={"directness": "direct"}, headers=maya)

    assert response.status_code == 200
    assert response.json()["directness"] == "direct"
    assert me(client, maya)["directness"] == "direct"
    assert "directness" not in me(client, maya)["changed_in_chat"]


def test_an_unknown_directness_is_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")

    response = client.patch("/api/me", json={"directness": "brutal"}, headers=maya)

    assert response.status_code == 422
    assert me(client, maya)["directness"] == "balanced"


def test_changing_directness_in_chat_marks_it_changed_in_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    call = reply_call(
        client,
        chat_model,
        "you can be blunter with me, just say what you think",
        ToolCall("change_directness", {"directness": "direct"}),
        "Got it, I'll be more direct.",
    )

    assert "direct" in call.tool_results[0]
    assert me(client, headers)["directness"] == "direct"
    assert "directness" in me(client, headers)["changed_in_chat"]


def test_an_unknown_directness_in_chat_changes_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    call = reply_call(
        client,
        chat_model,
        "be harsh",
        ToolCall("change_directness", {"directness": "brutal"}),
        "Which do you mean?",
    )

    assert "Nothing changed" in call.tool_results[0]
    assert me(client, headers)["directness"] == "balanced"
    assert "directness" not in me(client, headers)["changed_in_chat"]


def test_a_dashboard_change_clears_the_directness_changed_in_chat_mark(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    reply_call(
        client,
        chat_model,
        "go gentle on me",
        ToolCall("change_directness", {"directness": "gentle"}),
        "Okay.",
    )

    client.patch("/api/me", json={"directness": "balanced"}, headers=headers)

    assert "directness" not in me(client, headers)["changed_in_chat"]


def test_the_reply_plan_is_given_the_directness(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.patch("/api/me", json={"directness": "gentle"}, headers=headers)
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("hello"))

    assert f"{DIRECTNESS_LINE}gentle" in reply_plan_input(chat_model)


def test_a_struggling_users_reply_plan_is_not_given_the_directness(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    client.patch("/api/me", json={"directness": "direct"}, headers=headers)
    chat_model.script_understanding(understanding_answer(struggling=True))
    chat_model.script("I'm here.")

    send_to_webhook(client, telegram_text_update("I can't cope with any of it"))

    assert DIRECTNESS_LINE not in reply_plan_input(chat_model)


def test_the_seeded_reply_plan_prompt_says_what_each_level_means(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = seeded_settings["reply_plan_prompt"]

    for level in ("- gentle:", "- balanced:", "- direct:"):
        assert level in prompt
    assert "ask for your view" in prompt
    assert "Whatever the setting" in prompt


def test_the_settings_instructions_mention_how_direct_zeph_is(
    seeded_settings: dict[str, Any],
) -> None:
    assert "how direct" in seeded_settings["reply_settings_instructions"]


def test_an_existing_install_puts_users_on_balanced_and_reloads_the_prompts(
    engine: Engine,
    database_url: str,
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")
    me(client, maya)
    downgrade_to(database_url, "0084")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = '\"The old one.\"' "
                    "WHERE key IN ('reply_plan_prompt', "
                    "'reply_settings_instructions')"
                )
            )
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    assert me(client, maya)["directness"] == "balanced"
    for key in ("reply_plan_prompt", "reply_settings_instructions"):
        assert stored_setting(engine, key) == seeded_settings[key]
