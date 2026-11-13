from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

from companion.core.models import WebSearchResult
from companion.core.ports import ChatTool
from tests.fakes import (
    ChatModelCall,
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeWebSearch,
    ScriptedChatModel,
    ToolCall,
)
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)

BOOK_RESULT = WebSearchResult(
    title="The Miracle of Mindfulness - Wikipedia",
    url="https://en.wikipedia.org/wiki/The_Miracle_of_Mindfulness",
    content="The Miracle of Mindfulness is a 1975 book by Thich Nhat Hanh.",
)
BOOK_PAGE = "The Miracle of Mindfulness: An Introduction to the Practice of Meditation."


def reply_call(
    client: TestClient,
    chat_model: ScriptedChatModel,
    text: str,
    *script: str | ToolCall,
) -> ChatModelCall:
    """Send a Telegram message and return the reply call the model received."""
    chat_model.calls.clear()
    chat_model.script(*script)
    assert send_to_webhook(client, telegram_text_update(text)) == 200
    [call] = chat_model.calls
    return call


WEB_TOOLS = ("web_search", "fetch_page")


def web_tools(call: ChatModelCall) -> list[ChatTool]:
    """List the web tools a reply call was offered, leaving out the others."""
    return [tool for tool in call.tools if tool.name in WEB_TOOLS]


def tool_names(call: ChatModelCall) -> list[str]:
    """List the names of the web tools a reply call was offered."""
    return [tool.name for tool in web_tools(call)]


def search(query: str) -> ToolCall:
    """Script a web search tool call."""
    return ToolCall("web_search", {"query": query})


def change_settings(
    client: TestClient, admin: dict[str, str], values: dict[str, Any]
) -> None:
    """Save platform settings as an Admin."""
    response = client.patch(
        "/api/admin/settings", json={"values": values}, headers=admin
    )
    assert response.status_code == 200, response.text


def test_the_companion_searches_the_web_and_the_results_reach_the_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    web_search: FakeWebSearch,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    web_search.results = [BOOK_RESULT]
    web_search.pages[BOOK_RESULT.url] = BOOK_PAGE

    call = reply_call(
        client,
        chat_model,
        "what's that mindfulness book by Thich Nhat Hanh called?",
        search("Thich Nhat Hanh mindfulness book"),
        ToolCall("fetch_page", {"url": BOOK_RESULT.url}),
        "The Miracle of Mindfulness, going by Wikipedia",
    )

    assert tool_names(call) == ["web_search", "fetch_page"]
    assert web_search.queries == ["Thich Nhat Hanh mindfulness book"]
    assert web_search.fetched_urls == [BOOK_RESULT.url]
    search_result, page = call.tool_results
    assert BOOK_RESULT.title in search_result
    assert BOOK_RESULT.url in search_result
    assert BOOK_RESULT.content in search_result
    assert BOOK_RESULT.url in page
    assert BOOK_PAGE in page
    reminder = seeded_settings["web_result_source_reminder"]
    assert search_result.endswith(reminder)
    assert page.endswith(reminder)
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "The Miracle of Mindfulness, going by Wikipedia"
    ]


def test_tool_instructions_forbid_personal_details_and_ask_for_sources(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    call = reply_call(client, chat_model, "hi", "hey")

    search_tool, fetch_tool = web_tools(call)
    assert search_tool.description == seeded_settings["web_search_tool_description"]
    assert "Never put the person's personal details" in search_tool.description
    assert fetch_tool.description == seeded_settings["page_fetch_tool_description"]
    assert search_tool.parameters["required"] == ["query"]
    assert fetch_tool.parameters["required"] == ["url"]
    instructions = seeded_settings["reply_web_search_instructions"]
    assert instructions in call.instructions
    assert "say where it came from" in instructions


def test_with_web_search_off_the_tools_are_not_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    response = client.put(
        "/api/admin/features/web_search", json={"on": False}, headers=admin
    )
    assert response.status_code == 200, response.text

    call = reply_call(client, chat_model, "who won the match last night?", "no idea")

    assert web_tools(call) == []
    assert seeded_settings["reply_web_search_instructions"] not in call.instructions
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["no idea"]


def test_at_the_daily_limit_the_tools_are_gone_until_the_users_next_day(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    web_search: FakeWebSearch,
    clock: FakeClock,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    client.patch(
        "/api/me",
        json={"time_zone": "Asia/Singapore"},
        headers=auth_headers(auth_verifier, "user_maya"),
    )
    change_settings(client, admin, {"web_search_daily_limit": 2})

    first = reply_call(
        client, chat_model, "q1", search("stoicism"), search("seneca"), "ok"
    )
    at_limit = reply_call(client, chat_model, "q2", "hmm")
    clock.advance(timedelta(hours=6, minutes=59))
    same_local_day = reply_call(client, chat_model, "q3", "hmm")
    clock.advance(timedelta(minutes=1))
    next_local_day = reply_call(client, chat_model, "q4", "hmm")

    assert tool_names(first) == ["web_search", "fetch_page"]
    assert web_search.queries == ["stoicism", "seneca"]
    assert web_tools(at_limit) == []
    assert web_tools(same_local_day) == []
    assert tool_names(next_local_day) == ["web_search", "fetch_page"]
    limit_note = seeded_settings["reply_web_search_limit_note"]
    web_instructions = seeded_settings["reply_web_search_instructions"]
    assert limit_note not in first.instructions
    assert limit_note in at_limit.instructions
    assert web_instructions not in at_limit.instructions
    assert limit_note in same_local_day.instructions
    assert limit_note not in next_local_day.instructions


def test_a_search_past_the_limit_within_one_reply_is_not_made(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    web_search: FakeWebSearch,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, admin, {"web_search_daily_limit": 1})

    call = reply_call(
        client,
        chat_model,
        "tell me about seneca",
        search("seneca"),
        ToolCall("fetch_page", {"url": BOOK_RESULT.url}),
        "here's what I know",
    )

    assert web_search.queries == ["seneca"]
    assert web_search.fetched_urls == []
    assert "No more web searches today" in call.tool_results[1]
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == ["here's what I know"]


def test_a_limit_of_zero_offers_no_tools(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, admin, {"web_search_daily_limit": 0})

    call = reply_call(client, chat_model, "hi", "hey")

    assert web_tools(call) == []


def test_the_limit_note_tells_the_companion_not_to_claim_it_searched(
    seeded_settings: dict[str, Any],
) -> None:
    limit_note = seeded_settings["reply_web_search_limit_note"]

    assert "until tomorrow" in limit_note
    assert "may be out of date" in limit_note
    assert "Never say or suggest that you searched" in limit_note


def test_with_web_search_off_the_limit_note_is_not_added(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    seeded_settings: dict[str, Any],
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, admin, {"web_search_daily_limit": 0})
    response = client.put(
        "/api/admin/features/web_search", json={"on": False}, headers=admin
    )
    assert response.status_code == 200, response.text

    call = reply_call(client, chat_model, "who won the match last night?", "no idea")

    assert web_tools(call) == []
    assert seeded_settings["reply_web_search_limit_note"] not in call.instructions
    unavailable_note = seeded_settings["reply_features_unavailable_note"]
    assert unavailable_note.split("{features}")[0] in call.instructions


def test_an_admin_edited_limit_note_is_used_in_the_next_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    edited_note = "No more lookups today; say so and answer from memory."
    change_settings(
        client,
        admin,
        {"web_search_daily_limit": 0, "reply_web_search_limit_note": edited_note},
    )

    call = reply_call(client, chat_model, "who won the match last night?", "hmm")

    assert edited_note in call.instructions
    services = client.get("/api/admin/core-services", headers=admin).json()
    extra_prompts = {
        service["name"]: [prompt["key"] for prompt in service["extra_prompts"]]
        for service in services["services"]
    }
    assert "reply_web_search_limit_note" in extra_prompts["Response composition"]


def test_the_reply_still_goes_when_the_web_search_fails(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    web_search: FakeWebSearch,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    web_search.failure = RuntimeError("service down")

    call = reply_call(
        client,
        chat_model,
        "what's the weather like?",
        search("weather"),
        ToolCall("fetch_page", {"url": BOOK_RESULT.url}),
        "can't check right now, sorry",
    )

    assert "The web search didn't work" in call.tool_results[0]
    assert "The page couldn't be read" in call.tool_results[1]
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [
        "can't check right now, sorry"
    ]


def test_tool_calls_without_a_query_or_web_address_are_not_made(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    web_search: FakeWebSearch,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    call = reply_call(
        client,
        chat_model,
        "hi",
        ToolCall("web_search", {"query": "  "}),
        ToolCall("fetch_page", {"url": "file:///etc/passwd"}),
        "hey",
    )

    assert web_search.queries == []
    assert web_search.fetched_urls == []
    assert "needs a query" in call.tool_results[0]
    assert "needs a web address" in call.tool_results[1]


def test_no_results_and_an_empty_page_are_said_plainly(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    call = reply_call(
        client,
        chat_model,
        "hi",
        search("zzzz"),
        ToolCall("fetch_page", {"url": "https://example.com/empty"}),
        "hey",
    )

    assert call.tool_results[0] == 'No web results for "zzzz".'
    assert "The page couldn't be read" in call.tool_results[1]
