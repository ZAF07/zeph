import json
from typing import Any

import httpx
import pytest

from companion.adapters.openrouter.chat_model import (
    OpenRouterChatModel,
    ToolsNotSupportedError,
)
from companion.core.models import ChatLine, ChatRole, ModelAnswer
from companion.core.ports import ChatTool

HISTORY = [
    ChatLine(role=ChatRole.USER, text="hi"),
    ChatLine(role=ChatRole.COMPANION, text="hey!"),
    ChatLine(role=ChatRole.USER, text="how are you?"),
]


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
        model="deepseek/deepseek-v4-pro",
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
    assert body["model"] == "deepseek/deepseek-v4-pro"
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


def test_a_call_that_offers_tools_is_refused_clearly_and_sends_nothing() -> None:
    requests: list[httpx.Request] = []
    chat_model = openrouter_with(httpx.Response(200, json=openrouter_reply()), requests)
    tool = ChatTool(
        name="web_search",
        description="Search the web.",
        parameters={"type": "object", "properties": {}},
        run=lambda arguments: "",
    )

    with pytest.raises(ToolsNotSupportedError, match="tools"):
        chat_model.generate(
            model="deepseek/deepseek-v4-pro",
            thinking=False,
            instructions="Be Zeph.",
            history=HISTORY,
            tools=[tool],
        )

    assert requests == []
