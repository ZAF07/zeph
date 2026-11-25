from typing import Any

from fastapi.testclient import TestClient

from companion.core.chat_settings import CLAIM_CHECK_PROMPT, UNBACKED_CLAIM_NOTE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    ScriptedChatModel,
    ToolCall,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_sending import set_up_user_with_check_ins
from tests.test_features import switch_for_everyone
from tests.test_model_call_log import newest_call
from tests.test_settings_via_chat import me

GO_EASIER = "could you go a bit easier on me when you tell me what you think?"
FALSE_CLAIM = "of course. you're on gentle now"
TRUE_CLAIM = "done, I'll go gentler with my view from here"


def send(client: TestClient, chat_model: ScriptedChatModel, *script: Any) -> None:
    """Send the request to go easier, answered by the scripted reply calls."""
    chat_model.calls.clear()
    chat_model.script(*script)
    assert send_to_webhook(client, telegram_text_update(GO_EASIER)) == 200


def test_a_reply_that_says_it_is_done_with_no_tool_called_is_written_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_channel.sent.clear()
    chat_model.script_claim_check("yes")

    send(
        client,
        chat_model,
        FALSE_CLAIM,
        ToolCall("change_directness", {"directness": "gentle"}),
        TRUE_CLAIM,
    )

    first, second = chat_model.calls
    assert UNBACKED_CLAIM_NOTE not in first.instructions
    assert second.instructions == f"{first.instructions}\n\n{UNBACKED_CLAIM_NOTE}"
    assert second.fixed_instructions == first.fixed_instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [TRUE_CLAIM]
    assert me(client, headers)["directness"] == "gentle"
    assert len(chat_model.claim_check_calls) == 1


def test_a_claim_still_made_with_no_tool_called_is_never_sent(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_channel.sent.clear()
    chat_model.script_claim_check("yes", "yes")

    send(client, chat_model, FALSE_CLAIM, "all set, gentle it is")

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        seeded_settings["reply_failed_message"]
    ]
    assert me(client, headers)["directness"] == "balanced"


def test_a_second_draft_that_drops_the_claim_is_sent(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_channel.sent.clear()
    chat_model.script_claim_check("yes", "no")

    send(client, chat_model, FALSE_CLAIM, "do you want me to hold back more?")

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "do you want me to hold back more?"
    ]
    assert len(chat_model.claim_check_calls) == 2


def test_the_claim_check_reads_the_settings_and_the_reply_as_written(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_channel.sent.clear()

    send(client, chat_model, "that sounds hard.\n\nwhat happened?")

    [check] = chat_model.claim_check_calls
    described = check.history[0].text
    assert check.instructions == CLAIM_CHECK_PROMPT
    assert check.thinking is False
    assert check.model == seeded_settings["check_in_model"]
    assert "- change_directness: Change how direct you are" in described
    assert "- pause_check_ins: " in described
    assert described.endswith("The reply:\nthat sounds hard.\n\nwhat happened?")
    assert chat_model.call_order[-2:] == ["reply", "claim_check"]
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "that sounds hard.",
        "what happened?",
    ]
    step = newest_call(
        client, owner_headers(client, auth_verifier), "settings_claim_check"
    )
    assert step["step"] == "settings_claim_check"


def test_a_reply_that_called_a_settings_tool_is_not_checked(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    send(
        client,
        chat_model,
        ToolCall("change_directness", {"directness": "gentle"}),
        TRUE_CLAIM,
    )

    assert chat_model.claim_check_calls == []
    assert len(chat_model.calls) == 1


def test_a_failed_claim_check_lets_the_reply_go(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_channel.sent.clear()
    chat_model.script_claim_check(RuntimeError("model down"))

    send(client, chat_model, "mm, I hear you")

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["mm, I hear you"]


def test_with_settings_in_chat_off_a_claim_to_have_deleted_data_is_still_checked(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    switch_for_everyone(
        client, owner_headers(client, auth_verifier), "settings_in_chat", False
    )

    send(client, chat_model, "mm, I hear you")

    [check] = chat_model.claim_check_calls
    assert "- start_deleting_my_data: " in check.history[0].text
    assert "change_directness" not in check.history[0].text
