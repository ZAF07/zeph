import json
import logging
from typing import Any

import httpx
import pytest

from companion.adapters.openrouter.chat_model import (
    MAX_TOOL_ROUNDS,
    OpenRouterChatModel,
    OpenRouterReplyError,
)
from companion.core.models import ChatLine, ChatRole, ModelAnswer, ToolCallRecord
from companion.core.ports import ChatTool

HISTORY = [
    ChatLine(role=ChatRole.USER, text="hi"),
    ChatLine(role=ChatRole.COMPANION, text="hey!"),
    ChatLine(role=ChatRole.USER, text="how are you?"),
]

ADAPTER_LOGGER = "companion.adapters.openrouter.chat_model"

CACHED_INSTRUCTIONS = {
    "role": "system",
    "content": [
        {"type": "text", "text": "Be Zeph.", "cache_control": {"type": "ephemeral"}}
    ],
}


def openrouter_reply(
    content: str = "Doing well.", reasoning: str | None = None
) -> dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                    "reasoning": reasoning,
                }
            }
        ],
        "usage": {"prompt_tokens": 42, "completion_tokens": 7},
    }


def openrouter_with(
    response: httpx.Response, requests: list[httpx.Request]
) -> OpenRouterChatModel:
    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response

    return OpenRouterChatModel(
        "sk-or-test", http_client=httpx.Client(transport=httpx.MockTransport(handle))
    )


def generate(chat_model: OpenRouterChatModel, thinking: bool = False) -> ModelAnswer:
    return chat_model.generate(
        model="deepseek/deepseek-v4-pro-0813",
        thinking=thinking,
        instructions="Be Zeph.",
        history=HISTORY,
    )


def test_a_reply_sends_the_model_name_as_given_with_the_conversation() -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)

    generate(chat_model)

    [request] = requests
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer sk-or-test"
    body = json.loads(request.content)
    assert body["model"] == "deepseek/deepseek-v4-pro-0813"
    assert body["messages"] == [
        {"role": "system", "content": "Be Zeph."},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hey!"},
        {"role": "user", "content": "how are you?"},
    ]


@pytest.mark.parametrize("thinking", [True, False])
def test_the_thinking_switch_becomes_reasoning_enabled(thinking: bool) -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)

    generate(chat_model, thinking=thinking)

    [request] = requests
    assert json.loads(request.content)["reasoning"] == {"enabled": thinking}


def test_the_reply_text_tokens_and_reasoning_are_returned() -> None:
    chat_model = openrouter_with(
        httpx.Response(
            200, json=openrouter_reply("Doing well.", reasoning="They asked how I am.")
        ),
        [],
    )

    answer = generate(chat_model, thinking=True)

    assert answer == ModelAnswer(
        text="Doing well.",
        tokens_in=42,
        tokens_out=7,
        reasoning="They asked how I am.",
    )


def test_a_reply_with_no_reasoning_or_usage_has_none_and_no_tokens() -> None:
    chat_model = openrouter_with(
        httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "Hi."}}]},
        ),
        [],
    )

    answer = generate(chat_model)

    assert answer == ModelAnswer(text="Hi.", tokens_in=0, tokens_out=0)


def test_an_http_error_is_raised_for_the_caller_to_handle() -> None:
    chat_model = openrouter_with(
        httpx.Response(402, json={"error": {"message": "Insufficient credits"}}), []
    )

    with pytest.raises(httpx.HTTPStatusError):
        generate(chat_model)


def test_an_error_body_with_a_200_status_is_raised_clearly() -> None:
    chat_model = openrouter_with(
        httpx.Response(
            200, json={"error": {"code": 502, "message": "Provider returned error"}}
        ),
        [],
    )

    with pytest.raises(OpenRouterReplyError, match="Provider returned error"):
        generate(chat_model)


def test_an_error_inside_the_choice_with_a_200_status_is_raised_clearly() -> None:
    chat_model = openrouter_with(
        httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": ""},
                        "finish_reason": "error",
                        "error": {"message": "Provider returned error"},
                    }
                ]
            },
        ),
        [],
    )

    with pytest.raises(OpenRouterReplyError, match="Provider returned error"):
        generate(chat_model)


def test_a_choice_that_finished_with_an_error_is_raised_clearly() -> None:
    chat_model = openrouter_with(
        httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": ""},
                        "finish_reason": "error",
                    }
                ]
            },
        ),
        [],
    )

    with pytest.raises(OpenRouterReplyError, match="ended with an error"):
        generate(chat_model)


@pytest.mark.parametrize(
    ("model", "maker"),
    [
        ("deepseek/deepseek-v4.1-flash-1017", "deepseek"),
        ("anthropic/claude-haiku-5.5", "anthropic"),
    ],
)
def test_only_the_models_maker_may_answer(model: str, maker: str) -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)

    chat_model.generate(
        model=model, thinking=False, instructions="Be Zeph.", history=HISTORY
    )

    assert json.loads(requests[0].content)["provider"] == {"only": [maker]}


def test_a_reply_paid_with_openrouter_credits_is_logged_as_a_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    reply = openrouter_reply()
    reply["usage"]["is_byok"] = False
    chat_model = openrouter_with(httpx.Response(200, json=reply), [])

    with caplog.at_level(logging.WARNING):
        generate(chat_model)

    assert "deepseek/deepseek-v4-pro-0813" in caplog.text
    assert "OpenRouter credits" in caplog.text


@pytest.mark.parametrize("usage", [{"is_byok": True}, {}])
def test_a_reply_paid_with_our_own_key_logs_no_warning(
    usage: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    reply = openrouter_reply()
    reply["usage"].update(usage)
    chat_model = openrouter_with(httpx.Response(200, json=reply), [])

    with caplog.at_level(logging.WARNING):
        generate(chat_model)

    assert not caplog.text


def generate_with_claude(chat_model: OpenRouterChatModel) -> ModelAnswer:
    return chat_model.generate(
        model="anthropic/claude-haiku-5.5",
        thinking=False,
        instructions="Be Zeph.",
        history=HISTORY,
    )


def test_a_claude_model_gets_its_instructions_marked_for_caching() -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)

    generate_with_claude(chat_model)

    assert json.loads(requests[0].content)["messages"] == [
        CACHED_INSTRUCTIONS,
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hey!"},
        {"role": "user", "content": "how are you?"},
    ]


def test_empty_instructions_for_a_claude_model_are_sent_unmarked() -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)

    chat_model.generate(
        model="anthropic/claude-haiku-5.5",
        thinking=False,
        instructions="",
        history=HISTORY,
    )

    system_message = json.loads(requests[0].content)["messages"][0]
    assert system_message == {"role": "system", "content": ""}


def test_a_deepseek_model_gets_no_caching_marker() -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)

    generate(chat_model)

    assert "cache_control" not in requests[0].content.decode()


def test_a_claude_model_gets_only_the_fixed_instructions_marked_for_caching() -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)

    chat_model.generate(
        model="anthropic/claude-haiku-5.5",
        thinking=False,
        instructions="Be Zeph.",
        history=HISTORY,
        message_instructions="They just asked about work.",
    )

    system_message = json.loads(requests[0].content)["messages"][0]
    assert system_message == {
        "role": "system",
        "content": [
            *CACHED_INSTRUCTIONS["content"],
            {"type": "text", "text": "\n\nThey just asked about work."},
        ],
    }


def test_a_claude_model_with_only_message_instructions_gets_them_unmarked() -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)

    chat_model.generate(
        model="anthropic/claude-haiku-5.5",
        thinking=False,
        instructions="",
        history=HISTORY,
        message_instructions="They just asked about work.",
    )

    system_message = json.loads(requests[0].content)["messages"][0]
    assert system_message == {
        "role": "system",
        "content": "They just asked about work.",
    }


def test_a_deepseek_model_gets_the_two_instructions_joined_fixed_part_first() -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)

    chat_model.generate(
        model="deepseek/deepseek-v4-pro-0813",
        thinking=False,
        instructions="Be Zeph.",
        history=HISTORY,
        message_instructions="They just asked about work.",
    )

    system_message = json.loads(requests[0].content)["messages"][0]
    assert system_message == {
        "role": "system",
        "content": "Be Zeph.\n\nThey just asked about work.",
    }


def test_the_cached_tokens_of_a_claude_reply_are_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    reply = openrouter_reply()
    reply["usage"]["prompt_tokens_details"] = {
        "cached_tokens": 4000,
        "cache_write_tokens": 12,
    }
    chat_model = openrouter_with(httpx.Response(200, json=reply), [])

    with caplog.at_level(logging.INFO, logger=ADAPTER_LOGGER):
        generate_with_claude(chat_model)

    assert caplog.messages == [
        "A call to anthropic/claude-haiku-5.5 read 4000 of its 42 prompt tokens "
        "from the cache and wrote 12 to it"
    ]


def test_a_claude_reply_that_says_nothing_about_the_cache_is_logged_as_none_cached(
    caplog: pytest.LogCaptureFixture,
) -> None:
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), [])

    with caplog.at_level(logging.INFO, logger=ADAPTER_LOGGER):
        generate_with_claude(chat_model)

    assert caplog.messages == [
        "A call to anthropic/claude-haiku-5.5 read 0 of its 42 prompt tokens "
        "from the cache and wrote 0 to it"
    ]


def test_the_cached_tokens_of_a_deepseek_reply_are_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    reply = openrouter_reply()
    reply["usage"]["prompt_tokens_details"] = {"cached_tokens": 30}
    chat_model = openrouter_with(httpx.Response(200, json=reply), [])

    with caplog.at_level(logging.INFO, logger=ADAPTER_LOGGER):
        generate(chat_model)

    assert caplog.messages == [
        "A call to deepseek/deepseek-v4-pro-0813 read 30 of its 42 prompt tokens "
        "from the cache and wrote 0 to it"
    ]


def tool_call_reply(
    arguments: str,
    call_id: str = "call_1",
    name: str = "web_search",
    reasoning_details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }
        ],
    }
    if reasoning_details is not None:
        message["reasoning_details"] = reasoning_details
    return {
        "choices": [{"message": message}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 3},
    }


def scripted_openrouter(
    replies: list[dict[str, Any]], requests: list[httpx.Request]
) -> OpenRouterChatModel:
    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=replies[len(requests) - 1])

    return OpenRouterChatModel(
        "sk-or-test", http_client=httpx.Client(transport=httpx.MockTransport(handle))
    )


def search_tool(queries: list[str] | None = None) -> ChatTool:
    def run(arguments: dict[str, Any]) -> str:
        if queries is not None:
            queries.append(arguments["query"])
        return f"results for {arguments['query']}"

    return ChatTool(
        name="web_search",
        description="Search the web.",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}},
        run=run,
    )


def generate_with_tools(chat_model: OpenRouterChatModel) -> ModelAnswer:
    return chat_model.generate(
        model="anthropic/claude-haiku-5.5",
        thinking=True,
        instructions="Be Zeph.",
        history=HISTORY,
        tools=[search_tool()],
    )


def test_tools_are_sent_in_the_openai_function_format() -> None:
    requests: list[httpx.Request] = []
    chat_model = scripted_openrouter([openrouter_reply()], requests)

    generate_with_tools(chat_model)

    [request] = requests
    assert json.loads(request.content)["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                },
            },
        }
    ]


def test_a_reply_without_tools_sends_no_tools() -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)

    generate(chat_model)

    [request] = requests
    assert "tools" not in json.loads(request.content)


def test_tool_calls_are_run_and_their_results_sent_back_until_a_reply() -> None:
    requests: list[httpx.Request] = []
    queries: list[str] = []
    chat_model = scripted_openrouter(
        [tool_call_reply('{"query": "seneca"}'), openrouter_reply("Found it.")],
        requests,
    )

    answer = chat_model.generate(
        model="anthropic/claude-haiku-5.5",
        thinking=False,
        instructions="Be Zeph.",
        history=HISTORY,
        tools=[search_tool(queries)],
    )

    assert answer.text == "Found it."
    assert queries == ["seneca"]
    second_messages = json.loads(requests[1].content)["messages"]
    assert second_messages[-2]["role"] == "assistant"
    assert second_messages[-2]["tool_calls"][0]["id"] == "call_1"
    assert second_messages[-1] == {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": "results for seneca",
    }


def test_a_claude_model_keeps_the_caching_marker_on_every_tool_round() -> None:
    requests: list[httpx.Request] = []
    chat_model = scripted_openrouter(
        [tool_call_reply('{"query": "seneca"}'), openrouter_reply("Found it.")],
        requests,
    )

    chat_model.generate(
        model="anthropic/claude-haiku-5.5",
        thinking=False,
        instructions="Be Zeph.",
        history=HISTORY,
        tools=[search_tool([])],
    )

    assert [json.loads(request.content)["messages"][0] for request in requests] == [
        CACHED_INSTRUCTIONS,
        CACHED_INSTRUCTIONS,
    ]


def test_several_tool_calls_in_one_round_each_get_their_result() -> None:
    requests: list[httpx.Request] = []
    two_calls = tool_call_reply('{"query": "a"}', call_id="c1")
    second_call = tool_call_reply('{"query": "b"}', call_id="c2")
    two_calls["choices"][0]["message"]["tool_calls"].append(
        second_call["choices"][0]["message"]["tool_calls"][0]
    )
    chat_model = scripted_openrouter([two_calls, openrouter_reply()], requests)

    generate_with_tools(chat_model)

    messages = json.loads(requests[1].content)["messages"]
    assert [call["id"] for call in messages[-3]["tool_calls"]] == ["c1", "c2"]
    assert messages[-2:] == [
        {"role": "tool", "tool_call_id": "c1", "content": "results for a"},
        {"role": "tool", "tool_call_id": "c2", "content": "results for b"},
    ]


def test_a_call_to_a_tool_that_was_not_offered_runs_nothing() -> None:
    requests: list[httpx.Request] = []
    chat_model = scripted_openrouter(
        [tool_call_reply("{}", name="delete_everything"), openrouter_reply()],
        requests,
    )

    generate_with_tools(chat_model)

    tool_message = json.loads(requests[1].content)["messages"][-1]
    assert tool_message["content"] == "There is no tool called delete_everything."


def test_a_tool_call_with_broken_arguments_is_sent_back_so_the_model_retries() -> None:
    requests: list[httpx.Request] = []
    chat_model = scripted_openrouter(
        [tool_call_reply('{"query": "sen'), openrouter_reply("Done.")], requests
    )

    answer = generate_with_tools(chat_model)

    tool_message = json.loads(requests[1].content)["messages"][-1]
    assert tool_message == {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": "The arguments for web_search were not valid JSON. Try again.",
    }
    assert answer.tool_calls == (
        ToolCallRecord(
            "web_search",
            {"raw": '{"query": "sen'},
            "The arguments for web_search were not valid JSON. Try again.",
        ),
    )


def test_after_too_many_tool_rounds_the_model_must_answer_without_tools() -> None:
    requests: list[httpx.Request] = []
    replies = [
        tool_call_reply('{"query": "again"}', call_id=f"call_{round_number}")
        for round_number in range(MAX_TOOL_ROUNDS)
    ]
    chat_model = scripted_openrouter([*replies, openrouter_reply("Final.")], requests)

    answer = generate_with_tools(chat_model)

    assert answer.text == "Final."
    assert len(requests) == MAX_TOOL_ROUNDS + 1
    for request in requests[:-1]:
        assert "tool_choice" not in json.loads(request.content)
    final_request = json.loads(requests[-1].content)
    assert final_request["tool_choice"] == "none"
    assert [tool["function"]["name"] for tool in final_request["tools"]] == [
        "web_search"
    ]


def test_tokens_are_added_up_across_every_tool_round() -> None:
    chat_model = scripted_openrouter(
        [tool_call_reply('{"query": "a"}'), openrouter_reply()], []
    )

    answer = generate_with_tools(chat_model)

    assert (answer.tokens_in, answer.tokens_out) == (10 + 42, 3 + 7)


def test_every_tool_call_is_reported_with_its_arguments_and_result() -> None:
    chat_model = scripted_openrouter(
        [
            tool_call_reply('{"query": "a"}', call_id="c1"),
            tool_call_reply('{"query": "b"}', call_id="c2"),
            openrouter_reply(),
        ],
        [],
    )

    answer = generate_with_tools(chat_model)

    assert answer.tool_calls == (
        ToolCallRecord("web_search", {"query": "a"}, "results for a"),
        ToolCallRecord("web_search", {"query": "b"}, "results for b"),
    )


def test_reasoning_details_are_kept_on_the_assistant_message_for_the_next_round() -> (
    None
):
    requests: list[httpx.Request] = []
    reasoning_details = [
        {"type": "reasoning.text", "text": "I should search.", "signature": "sig-1"}
    ]
    chat_model = scripted_openrouter(
        [
            tool_call_reply('{"query": "a"}', reasoning_details=reasoning_details),
            openrouter_reply(),
        ],
        requests,
    )

    generate_with_tools(chat_model)

    assistant_message = json.loads(requests[1].content)["messages"][-2]
    assert assistant_message["reasoning_details"] == reasoning_details


def test_reasoning_from_every_round_is_returned() -> None:
    first = tool_call_reply('{"query": "a"}')
    first["choices"][0]["message"]["reasoning"] = "I should search."
    chat_model = scripted_openrouter(
        [first, openrouter_reply(reasoning="Now I can answer.")], []
    )

    answer = generate_with_tools(chat_model)

    assert answer.reasoning == "I should search.\n\nNow I can answer."
