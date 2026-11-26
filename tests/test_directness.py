from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    migrate,
    seed_copy,
    seed_platform_settings,
)
from tests.conftest import COPY_SEED_FILE, SEED_FILE
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
HELP_SLOT = "account.directness.help"
HELP_BEFORE_ASKING = (
    "How soon and how plainly Zeph tells you what it thinks is really going on. "
    "Whatever you pick, Zeph gives its view when you ask, and takes extra care "
    "when things are hard."
)
INSTRUCTIONS_WITH_ASKING = (
    "how direct you are with your view of what is going on for them and with "
    "the questions you ask them, whether"
)
INSTRUCTIONS_BEFORE_ASKING = (
    "how direct you are with your view of what is going on for them, whether"
)
EXAMPLES_WITH_ASKING = (
    'think", "you can just ask me straight", "you ask a lot, ease up", "stop'
)
EXAMPLES_BEFORE_ASKING = 'think", "stop'


def set_before_asking(engine: Engine, help_text: str, instructions: str) -> None:
    """Store the help text and the settings instructions as given."""
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE copy_slots SET text = :text WHERE key = :key"),
            {"text": help_text, "key": HELP_SLOT},
        )
        connection.execute(
            text(
                "UPDATE platform_settings SET value = to_jsonb(CAST(:value AS TEXT)) "
                "WHERE key = 'reply_settings_instructions'"
            ),
            {"value": instructions},
        )


def help_text_of(client: TestClient) -> str:
    """The Account page's help text for how direct Zeph is, as stored."""
    help_text: str = client.get("/api/copy").json()["texts"][HELP_SLOT]
    return help_text


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
    downgrade_to(database_url, "0085")
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


def test_the_account_page_says_directness_also_changes_how_zeph_asks(
    client: TestClient,
) -> None:
    help_text = help_text_of(client)

    assert "how it asks you things" in help_text
    assert "Gentle asks less often" in help_text
    assert "direct asks sooner" in help_text
    assert "backs off when you’d rather not answer" in help_text


def test_the_chat_tool_says_directness_also_changes_how_zeph_asks(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    call = reply_call(
        client,
        chat_model,
        "you ask a lot of questions, ease up",
        ToolCall("change_directness", {"directness": "gentle"}),
        "Sure, I'll ease up.",
    )

    descriptions = {tool.name: tool.description for tool in call.tools}
    assert "the questions you ask" in descriptions["change_directness"]
    assert "ask your own questions less often" in call.tool_results[0]
    assert INSTRUCTIONS_WITH_ASKING in seeded_settings["reply_settings_instructions"]
    assert EXAMPLES_WITH_ASKING in seeded_settings["reply_settings_instructions"]


def test_an_existing_install_gets_the_words_on_how_zeph_asks(
    engine: Engine,
    database_url: str,
    client: TestClient,
    seeded_settings: dict[str, Any],
) -> None:
    new_help_text = help_text_of(client)
    new_instructions = seeded_settings["reply_settings_instructions"]
    instructions_before = new_instructions.replace(
        INSTRUCTIONS_WITH_ASKING, INSTRUCTIONS_BEFORE_ASKING
    ).replace(EXAMPLES_WITH_ASKING, EXAMPLES_BEFORE_ASKING)
    downgrade_to(database_url, "0111")
    try:
        set_before_asking(engine, HELP_BEFORE_ASKING, instructions_before)
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)
    seed_copy(engine, COPY_SEED_FILE)

    assert help_text_of(client) == new_help_text
    assert stored_setting(engine, "reply_settings_instructions") == new_instructions


def test_an_admins_own_words_on_directness_are_kept_by_the_migration(
    engine: Engine, database_url: str, client: TestClient
) -> None:
    downgrade_to(database_url, "0111")
    try:
        set_before_asking(engine, "Our own help text.", "Our own instructions.")
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)
    seed_copy(engine, COPY_SEED_FILE)

    assert help_text_of(client) == "Our own help text."
    assert stored_setting(engine, "reply_settings_instructions") == (
        "Our own instructions."
    )
