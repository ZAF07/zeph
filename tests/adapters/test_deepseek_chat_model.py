from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from companion.adapters.deepseek.chat_model import (
    MAX_TOOL_ROUNDS,
    answer_with_tools,
    to_langchain_messages,
)
from companion.core.models import ChatLine, ChatRole
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

    assert reply == "Seneca was a Stoic."
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

    assert reply == "Here's what I found."
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

    assert reply == "ok"
    assert chat.received[1][-1] == ToolMessage(
        "The arguments for web_search were not valid JSON. Try again.",
        tool_call_id="c1",
    )
