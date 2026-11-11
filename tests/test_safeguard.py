from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, inspect, text

from companion.core.models import ChatLine, ChatRole
from tests.fakes import FakeAuthVerifier, FakeChatChannel, ScriptedChatModel
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)

SINGAPORE_HELPLINES = (
    "Samaritans of Singapore (SOS): 1767 (24 hours)\n"
    "IMH Mental Health Helpline: 6389 2222 (24 hours)\n"
    "Emergency ambulance (SCDF): 995 (24 hours)"
)
INTERNATIONAL_FALLBACK = "Find A Helpline: findahelpline.com"


def connect_user_in(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    country: str | None,
) -> None:
    """Connect Maya on Telegram and set her country, if given."""
    connect_telegram(client, auth_verifier, chat_channel)
    if country is not None:
        response = client.patch(
            "/api/me",
            json={"country": country},
            headers=auth_headers(auth_verifier, "user_maya"),
        )
        assert response.status_code == 200


def use_simple_crisis_reply(client: TestClient, admin: dict[str, str]) -> None:
    """Change the Crisis Reply wording to something short to compare against."""
    response = client.patch(
        "/api/admin/settings",
        json={"values": {"crisis_reply": "I'm an AI. Please reach out:\n{helplines}"}},
        headers=admin,
    )
    assert response.status_code == 200


def test_safeguard_checks_every_message_before_the_reply_is_written(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    chat_model.script("hey you", "glad to hear")

    send_to_webhook(client, telegram_text_update("hi zeph"))
    send_to_webhook(client, telegram_text_update("work was fine today"))

    assert chat_model.call_order == ["safeguard", "reply", "safeguard", "reply"]
    first, second = chat_model.safeguard_calls
    assert first.model == seeded_settings["safeguard_model"]
    assert first.history == [
        ChatLine(
            role=ChatRole.USER,
            text="Latest message to classify:\nPerson: hi zeph",
        )
    ]
    assert second.history == [
        ChatLine(
            role=ChatRole.USER,
            text=(
                "Earlier in the conversation:\n"
                "Person: hi zeph\n"
                "Companion: hey you\n\n"
                "Latest message to classify:\n"
                "Person: work was fine today"
            ),
        )
    ]


def test_a_crisis_gets_the_crisis_reply_with_the_users_country_helplines(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    use_simple_crisis_reply(client, admin)
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    chat_model.script_safeguard("suicide_or_self_harm")

    send_to_webhook(client, telegram_text_update("i don't want to be here anymore"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        f"I'm an AI. Please reach out:\n{SINGAPORE_HELPLINES}"
    ]
    assert chat_model.calls == []


def test_the_seeded_crisis_reply_says_plainly_that_zeph_is_an_ai(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    chat_model.script_safeguard("medical_emergency")

    send_to_webhook(client, telegram_text_update("my chest hurts and i can't breathe"))

    [crisis_reply] = chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)
    assert "I’m an AI" in crisis_reply
    assert SINGAPORE_HELPLINES in crisis_reply
    assert "{helplines}" not in crisis_reply


@pytest.mark.parametrize("country", ["GB", None])
def test_a_user_whose_country_has_no_helplines_gets_the_international_fallback(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    country: str | None,
) -> None:
    admin = owner_headers(client, auth_verifier)
    use_simple_crisis_reply(client, admin)
    connect_user_in(client, auth_verifier, chat_channel, country)
    chat_model.script_safeguard("abuse")

    send_to_webhook(client, telegram_text_update("he hit me again last night"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        f"I'm an AI. Please reach out:\n{INTERNATIONAL_FALLBACK}"
    ]


def test_a_crisis_saves_a_safeguard_event_without_the_message_text(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    chat_model.script_safeguard("danger_to_others")
    secret_text = "i am going to hurt my neighbour tonight"

    send_to_webhook(client, telegram_text_update(secret_text))

    response = client.get("/api/admin/safeguard-events", headers=admin)
    [event] = response.json()["events"]
    assert event["risk_type"] == "danger_to_others"
    assert event["user_email"] == "user_maya@example.com"
    assert event["created_at"] == "2026-11-11T09:00:00Z"
    assert event["helplines_country"] == "SG"
    assert secret_text not in response.text
    columns = {
        column["name"] for column in inspect(engine).get_columns("safeguard_events")
    }
    assert columns == {"id", "user_id", "risk_type", "created_at", "helplines_country"}
    with engine.connect() as connection:
        row = connection.execute(text("SELECT * FROM safeguard_events")).one()
    assert secret_text not in str(row)


def test_a_fallback_crisis_event_records_no_helpline_country(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_user_in(client, auth_verifier, chat_channel, "GB")
    chat_model.script_safeguard("abuse")

    send_to_webhook(client, telegram_text_update("help"))

    [event] = client.get("/api/admin/safeguard-events", headers=admin).json()["events"]
    assert event["helplines_country"] is None


def test_a_message_that_is_not_a_crisis_gets_a_normal_reply_and_no_event(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    chat_model.script_safeguard("none")
    chat_model.script("ugh, mondays. what happened?")

    send_to_webhook(client, telegram_text_update("so stressed and sad about work"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "ugh, mondays. what happened?"
    ]
    events = client.get("/api/admin/safeguard-events", headers=admin).json()
    assert events["events"] == []


@pytest.mark.parametrize(
    ("answer", "risk_type"),
    [
        ("Abuse", "abuse"),
        (" medical_emergency.\n", "medical_emergency"),
        ("Label: suicide_or_self_harm", "suicide_or_self_harm"),
    ],
)
def test_the_safeguard_answer_is_read_loosely(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    answer: str,
    risk_type: str,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    chat_model.script_safeguard(answer)

    send_to_webhook(client, telegram_text_update("message"))

    [event] = client.get("/api/admin/safeguard-events", headers=admin).json()["events"]
    assert event["risk_type"] == risk_type


def test_an_answer_without_a_label_is_asked_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    chat_model.script_safeguard("I'm so sorry you're going through this.", "none")
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("hi"))

    assert len(chat_model.safeguard_calls) == 2
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["hey"]


def test_two_answers_without_a_label_are_treated_as_a_crisis(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    use_simple_crisis_reply(client, admin)
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    chat_model.script_safeguard("Please reach out to someone.", "I'm not sure")

    send_to_webhook(client, telegram_text_update("i can't do this anymore"))

    assert chat_model.calls == []
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        f"I'm an AI. Please reach out:\n{SINGAPORE_HELPLINES}"
    ]
    [event] = client.get("/api/admin/safeguard-events", headers=admin).json()["events"]
    assert event["risk_type"] == "unclear"


def test_the_crisis_reply_is_part_of_the_conversation_that_follows(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    use_simple_crisis_reply(client, admin)
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    chat_model.script_safeguard("suicide_or_self_harm", "none")
    chat_model.script("i'm here. did you manage to call?")

    send_to_webhook(client, telegram_text_update("i want to end it"))
    send_to_webhook(client, telegram_text_update("ok i called them"))

    [call] = chat_model.calls
    assert call.history == [
        ChatLine(role=ChatRole.USER, text="i want to end it"),
        ChatLine(
            role=ChatRole.COMPANION,
            text=f"I'm an AI. Please reach out:\n{SINGAPORE_HELPLINES}",
        ),
        ChatLine(role=ChatRole.USER, text="ok i called them"),
    ]


def test_safeguard_prompt_and_model_changes_apply_to_the_next_message(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    client.patch(
        "/api/admin/settings",
        json={
            "values": {
                "safeguard_prompt": "Classify the risk. Edited by an Admin.",
                "safeguard_model": "deepseek-reasoner",
            }
        },
        headers=admin,
    )
    chat_model.safeguard_prompt = "Classify the risk. Edited by an Admin."
    chat_model.script("hey")

    send_to_webhook(client, telegram_text_update("hi"))

    [call] = chat_model.safeguard_calls
    assert call.model == "deepseek-reasoner"


def test_a_failing_safeguard_never_lets_a_normal_reply_through(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_user_in(client, auth_verifier, chat_channel, "SG")
    chat_model.script_safeguard(RuntimeError("model down"))

    send_to_webhook(client, telegram_text_update("hi"))

    assert chat_model.calls == []
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["reply_failed_message"]
    ]


def test_the_safeguard_prompt_says_everyday_stress_or_sadness_is_not_a_crisis(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = seeded_settings["safeguard_prompt"].lower()

    assert "stress" in prompt
    assert "sadness" in prompt
    assert "not a crisis" in prompt
