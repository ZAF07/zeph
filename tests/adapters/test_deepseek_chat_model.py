import logging

import pytest
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from companion.adapters.deepseek.chat_model import (
    MAX_TOOL_ROUNDS,
    UnsupportedModelError,
    answer_with_tools,
    build_client,
    to_langchain_messages,
    to_model_answer,
)
from companion.core.models import ChatLine, ChatRole, ToolCallRecord
from companion.core.ports import ChatTool


def test_history_becomes_langchain_messages_after_the_instructions() -> None:
    messages = to_langchain_messages(
        "You are Zeph.",
        [
            ChatLine(role=ChatRole.USER, text="hi"),
            ChatLine(role=ChatRole.COMPANION, text="hey!"),
        ],
    )

    assert messages == [
        SystemMessage("You are Zeph."),
        HumanMessage("hi"),
        AIMessage("hey!"),
    ]


class ScriptedLangChainModel:
    """Stands in for a LangChain chat model, answering with set messages."""

    def __init__(self, *responses: AIMessage) -> None:
        self.responses = list(responses)
        self.received: list[list[BaseMessage]] = []

    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        self.received.append(list(messages))
        return self.responses.pop(0)


def search_tool() -> ChatTool:
    return ChatTool(
        name="web_search",
        description="Search the web.",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}},
        run=lambda arguments: f"results for {arguments['query']}",
    )


def asks_for_search(query: str, call_id: str) -> AIMessage:
    return AIMessage(
        "",
        tool_calls=[{"name": "web_search", "args": {"query": query}, "id": call_id}],
    )


def test_tool_calls_are_run_and_their_results_sent_back_until_a_reply() -> None:
    chat = ScriptedLangChainModel(
        asks_for_search("seneca", "call_1"), AIMessage("Seneca was a Stoic.")
    )

    reply = answer_with_tools(
        chat.invoke,
        ScriptedLangChainModel().invoke,
        [SystemMessage("x")],
        [search_tool()],
    )

    assert reply.text == "Seneca was a Stoic."
    second_request = chat.received[1]
    assert second_request[1] == asks_for_search("seneca", "call_1")
    assert second_request[2] == ToolMessage("results for seneca", tool_call_id="call_1")


def test_a_call_to_a_tool_that_was_not_offered_runs_nothing() -> None:
    chat = ScriptedLangChainModel(
        AIMessage(
            "", tool_calls=[{"name": "delete_everything", "args": {}, "id": "c1"}]
        ),
        AIMessage("ok"),
    )

    answer_with_tools(chat.invoke, ScriptedLangChainModel().invoke, [], [search_tool()])

    assert chat.received[1][-1] == ToolMessage(
        "There is no tool called delete_everything.", tool_call_id="c1"
    )


def test_after_too_many_tool_rounds_the_model_must_answer_without_tools() -> None:
    chat = ScriptedLangChainModel(
        *[asks_for_search("again", f"c{n}") for n in range(MAX_TOOL_ROUNDS)]
    )
    final = ScriptedLangChainModel(AIMessage("Here's what I found."))

    reply = answer_with_tools(chat.invoke, final.invoke, [], [search_tool()])

    assert reply.text == "Here's what I found."
    assert len(chat.received) == MAX_TOOL_ROUNDS
    assert len(final.received[0]) == 2 * MAX_TOOL_ROUNDS


def test_a_tool_call_with_broken_arguments_is_sent_back_so_the_model_retries() -> None:
    broken_call = AIMessage(
        "",
        invalid_tool_calls=[
            {
                "name": "web_search",
                "args": '{"query": ',
                "id": "c1",
                "error": "bad JSON",
                "type": "invalid_tool_call",
            }
        ],
    )
    chat = ScriptedLangChainModel(broken_call, AIMessage("ok"))

    reply = answer_with_tools(
        chat.invoke, ScriptedLangChainModel().invoke, [], [search_tool()]
    )

    assert reply.text == "ok"
    assert chat.received[1][-1] == ToolMessage(
        "The arguments for web_search were not valid JSON. Try again.",
        tool_call_id="c1",
    )


def with_usage(message: AIMessage, tokens_in: int, tokens_out: int) -> AIMessage:
    message.usage_metadata = {
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "total_tokens": tokens_in + tokens_out,
    }
    return message


def test_tokens_are_added_up_across_every_tool_round() -> None:
    chat = ScriptedLangChainModel(
        with_usage(asks_for_search("seneca", "c1"), 100, 10),
        with_usage(AIMessage("Seneca was a Stoic."), 250, 20),
    )

    reply = answer_with_tools(
        chat.invoke, ScriptedLangChainModel().invoke, [], [search_tool()]
    )

    assert (reply.tokens_in, reply.tokens_out) == (350, 30)


def test_a_response_without_usage_counts_as_no_tokens() -> None:
    chat = ScriptedLangChainModel(AIMessage("hi"))

    reply = answer_with_tools(
        chat.invoke, ScriptedLangChainModel().invoke, [], [search_tool()]
    )

    assert (reply.tokens_in, reply.tokens_out) == (0, 0)


def test_every_tool_call_is_reported_with_its_arguments_and_result() -> None:
    broken_call = AIMessage(
        "",
        invalid_tool_calls=[
            {
                "name": "web_search",
                "args": '{"query": ',
                "id": "c2",
                "error": "bad JSON",
                "type": "invalid_tool_call",
            }
        ],
    )
    chat = ScriptedLangChainModel(
        asks_for_search("seneca", "c1"), broken_call, AIMessage("Seneca was a Stoic.")
    )

    reply = answer_with_tools(
        chat.invoke, ScriptedLangChainModel().invoke, [], [search_tool()]
    )

    assert reply.tool_calls == (
        ToolCallRecord("web_search", {"query": "seneca"}, "results for seneca"),
        ToolCallRecord(
            "web_search",
            {"raw": '{"query": '},
            "The arguments for web_search were not valid JSON. Try again.",
        ),
    )


def test_the_models_reasoning_is_kept_when_it_gives_one() -> None:
    thinking = AIMessage(
        "Seneca was a Stoic.",
        additional_kwargs={"reasoning_content": "They asked about Seneca."},
    )

    assert to_model_answer(thinking.text, [thinking]).reasoning == (
        "They asked about Seneca."
    )
    assert to_model_answer("hi", [AIMessage("hi")]).reasoning is None


def thinking_sent(model: str, thinking: bool) -> tuple[str, object]:
    client = build_client("key", model, thinking)
    return client.model_name, client.extra_body


def test_thinking_is_switched_on_or_off_in_the_request() -> None:
    assert thinking_sent("deepseek-flash", True) == (
        "deepseek-flash",
        {"thinking": {"type": "enabled"}},
    )
    assert thinking_sent("deepseek-flash", False) == (
        "deepseek-flash",
        {"thinking": {"type": "disabled"}},
    )


def test_the_old_chat_name_is_sent_as_flash_with_thinking_as_asked() -> None:
    assert thinking_sent("deepseek-chat", False) == (
        "deepseek-flash",
        {"thinking": {"type": "disabled"}},
    )
    assert thinking_sent("deepseek-chat", True) == (
        "deepseek-flash",
        {"thinking": {"type": "enabled"}},
    )


def test_the_old_reasoner_name_is_sent_as_flash_and_always_thinks(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        sent = thinking_sent("deepseek-reasoner", False)

    assert sent == ("deepseek-flash", {"thinking": {"type": "enabled"}})
    assert "deepseek-reasoner always thinks" in caplog.text


def test_the_old_reasoner_name_asked_to_think_logs_no_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        sent = thinking_sent("deepseek-reasoner", True)

    assert sent == ("deepseek-flash", {"thinking": {"type": "enabled"}})
    assert not caplog.text


@pytest.mark.parametrize(
    ("openrouter_name", "direct_name"),
    [
        ("deepseek/deepseek-v4.1-flash-1017", "deepseek-flash"),
        ("deepseek/deepseek-v4-pro-0813", "deepseek-v4-pro"),
    ],
)
def test_an_openrouter_deepseek_name_is_sent_as_its_direct_name(
    openrouter_name: str, direct_name: str
) -> None:
    assert thinking_sent(openrouter_name, False) == (
        direct_name,
        {"thinking": {"type": "disabled"}},
    )


@pytest.mark.parametrize(
    "model", ["anthropic/claude-sonnet-5.5", "deepseek/deepseek-unknown"]
)
def test_a_model_direct_deepseek_cant_call_fails_clearly(model: str) -> None:
    with pytest.raises(UnsupportedModelError) as error:
        build_client("key", model, False)

    assert model in str(error.value)
    assert "Pick a DeepSeek model" in str(error.value)
