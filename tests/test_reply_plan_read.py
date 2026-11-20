import json
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate, seed_platform_settings
from companion.core.response_composition import GUIDANCE_HEADING, MEMORY_HEADING
from tests.conftest import SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    ScriptedChatModel,
    reply_plan_answer,
)
from tests.telegram_helpers import (
    OWNER_TELEGRAM_USER_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_model_call_log import newest_call
from tests.test_photo_viewing import stored_setting
from tests.test_understanding import saved_reply_plans
from tests.test_understanding_migrations import downgrade_to

READ = "They aren't tired of the work; they're tired of proving they may stop."
OLD_REPLY_PLAN_PROMPT = "Pick a Need. Answer with JSON only."


def level_three(instructions: str) -> str:
    """The Reply's level 3 section: the Reply Plan's guidance."""
    after_heading = instructions.split(GUIDANCE_HEADING, 1)[1]
    return after_heading.split(MEMORY_HEADING, 1)[0]


def test_the_seeded_reply_plan_prompt_asks_for_a_read_and_says_when_to_give_it(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = seeded_settings["reply_plan_prompt"]

    for field in ('"where_we_are"', '"read"', '"say_read"'):
        assert field in prompt
    for condition in ("room", "worth saying", "repeat", "ask for your view"):
        assert condition in prompt
    assert "deepest Read" in prompt
    assert "never as fact" in prompt
    assert seeded_settings["persona_outlook"].strip()


def test_only_the_reply_plan_gets_the_outlook_and_the_reply_keeps_the_voice(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("hello"))

    outlook = seeded_settings["persona_outlook"]
    [reply_plan_call] = chat_model.reply_plan_calls
    assert reply_plan_call.instructions == (
        f"{outlook}\n\n{seeded_settings['reply_plan_prompt']}"
    )
    [reply_call] = chat_model.calls
    assert seeded_settings["persona"] in reply_call.instructions
    for other_call in (
        reply_call,
        *chat_model.understanding_calls,
        *chat_model.safeguard_calls,
    ):
        assert outlook not in other_call.instructions


def test_a_changed_outlook_is_used_from_the_next_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    response = client.patch(
        "/api/admin/settings",
        json={"values": {"persona_outlook": "People grow by being seen."}},
        headers=owner_headers(client, auth_verifier),
    )
    assert response.status_code == 200
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("hello"))

    [reply_plan_call] = chat_model.reply_plan_calls
    assert reply_plan_call.instructions.startswith("People grow by being seen.\n\n")


def test_the_outlook_is_an_admin_setting_with_a_hint(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    response = client.get(
        "/api/admin/settings", headers=owner_headers(client, auth_verifier)
    )

    outlook = response.json()["settings"]["persona_outlook"]
    assert outlook["value"].strip()
    assert "Read" in outlook["hint"]


def test_a_read_to_be_said_reaches_the_reply_at_level_three_as_zephs_view(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_reply_plan(
        reply_plan_answer(
            need="Think it through",
            where_we_are="asking for a view",
            read=READ,
            say_read=True,
        )
    )
    chat_model.script("here's what I notice")

    send_to_webhook(client, telegram_text_update("what do you think is going on?"))

    [reply_call] = chat_model.calls
    plan_section = level_three(reply_call.instructions)
    assert READ in plan_section
    assert "your view" in plan_section
    [saved] = saved_reply_plans(engine)
    assert saved["form"]["read"] == READ
    assert saved["form"]["say_read"] is True
    assert saved["form"]["where_we_are"] == "asking for a view"


def test_a_read_not_to_be_said_never_reaches_the_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_reply_plan(
        reply_plan_answer(
            need="Be heard",
            where_we_are="venting, just started",
            read=READ,
            say_read=False,
        )
    )
    chat_model.script("that sounds exhausting")

    send_to_webhook(client, telegram_text_update("work is so much right now"))

    [reply_call] = chat_model.calls
    assert READ not in reply_call.instructions
    [saved] = saved_reply_plans(engine)
    assert saved["form"]["read"] == READ
    assert saved["form"]["say_read"] is False


def test_saying_no_read_or_an_odd_say_read_says_nothing(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_reply_plan(
        reply_plan_answer(read="", say_read=True),
        reply_plan_answer(read=READ, say_read="yes"),
    )
    chat_model.script("hi", "hey")

    send_to_webhook(client, telegram_text_update("hello"))
    send_to_webhook(client, telegram_text_update("hello again"))

    first, second = saved_reply_plans(engine)
    assert (first["form"]["read"], first["form"]["say_read"]) == ("", False)
    assert (second["form"]["read"], second["form"]["say_read"]) == (READ, False)
    for reply_call in chat_model.calls:
        assert READ not in reply_call.instructions


def test_the_next_reply_plan_sees_where_we_were_and_the_reads_already_formed(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_reply_plan(
        reply_plan_answer(
            need="Be heard",
            where_we_are="venting, nearly spent",
            read=READ,
            say_read=False,
        ),
        reply_plan_answer(
            need="Think it through",
            where_we_are="asking for a view",
            read=READ,
            say_read=True,
        ),
    )
    chat_model.script("that sounds a lot", "here's what I notice")

    send_to_webhook(client, telegram_text_update("and then they called again"))
    send_to_webhook(client, telegram_text_update("what do you make of it?"))

    first_plan, second_plan = chat_model.reply_plan_calls
    assert "venting, nearly spent" not in first_plan.history[0].text
    earlier_plans = second_plan.history[0].text.split("Earlier Reply Plans")[1]
    assert "Where we were: venting, nearly spent" in earlier_plans
    assert f"Read (not said): {READ}" in earlier_plans


def test_the_log_records_whether_a_read_was_formed_and_said_never_its_words(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_reply_plan(
        reply_plan_answer(read=READ, say_read=False, where_we_are="venting")
    )
    chat_model.script("that sounds a lot")

    send_to_webhook(client, telegram_text_update("ugh"))

    admin = owner_headers(client, auth_verifier)
    reply_plan = newest_call(client, admin, "reply_plan")
    shape = reply_plan["reply_plan_shape"]
    assert (shape["read_formed"], shape["read_said"]) == (True, False)
    assert reply_plan["content"] is None
    assert READ not in json.dumps(reply_plan)


def test_an_admins_own_trace_shows_the_read_in_full(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_model.script_reply_plan(
        reply_plan_answer(read=READ, say_read=True, where_we_are="asking for a view")
    )
    chat_model.script("here's what I notice")

    send_to_webhook(
        client, telegram_text_update("what do you think?", OWNER_TELEGRAM_USER_ID)
    )

    reply_plan = newest_call(client, admin, "reply_plan")
    assert (
        reply_plan["reply_plan_shape"]["read_formed"],
        reply_plan["reply_plan_shape"]["read_said"],
    ) == (True, True)
    assert READ in reply_plan["content"]["response"]
    assert "asking for a view" in reply_plan["content"]["response"]


def test_a_failed_reply_plan_forms_no_read(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_reply_plan(TimeoutError("DeepSeek timed out"))
    chat_model.script("I'm here")

    send_to_webhook(client, telegram_text_update("meh"))

    shape = newest_call(client, owner_headers(client, auth_verifier), "reply_plan")[
        "reply_plan_shape"
    ]
    assert (shape["read_formed"], shape["read_said"]) == (False, False)


def test_an_existing_install_gets_the_reply_plan_prompt_that_asks_for_a_read(
    engine: Engine, database_url: str, seeded_settings: dict[str, Any]
) -> None:
    downgrade_to(database_url, "0069")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = :old "
                    "WHERE key = 'reply_plan_prompt'"
                ),
                {"old": json.dumps(OLD_REPLY_PLAN_PROMPT)},
            )
    finally:
        migrate(database_url)
    seed_platform_settings(engine, SEED_FILE)

    assert (
        stored_setting(engine, "reply_plan_prompt")
        == seeded_settings["reply_plan_prompt"]
    )


def test_a_plain_user_cannot_change_the_outlook(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner_headers(client, auth_verifier)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"persona_outlook": "Anything goes."}},
        headers=auth_headers(auth_verifier, "user_maya"),
    )

    assert response.status_code == 403
