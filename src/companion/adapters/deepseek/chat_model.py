from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from companion.core.models import ChatLine, ChatRole
from companion.core.ports import ChatTool

MAX_TOOL_ROUNDS = 4

AskModel = Callable[[list[BaseMessage]], AIMessage]


def to_langchain_messages(
    instructions: str, history: list[ChatLine]
) -> list[BaseMessage]:
    """Turn instructions and Conversation history into LangChain messages.

    Args:
        instructions: What the model should be and do.
        history: The Conversation so far, oldest first.

    Returns:
        A system message followed by one message per history line.
    """
    messages: list[BaseMessage] = [SystemMessage(instructions)]
    for line in history:
        if line.role == ChatRole.USER:
            messages.append(HumanMessage(line.text))
        else:
            messages.append(AIMessage(line.text))
    return messages


def to_tool_schema(tool: ChatTool) -> dict[str, Any]:
    """Describe a tool in the OpenAI function format DeepSeek takes.

    Args:
        tool: The tool.

    Returns:
        The tool's schema.
    """
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


def answer_with_tools(
    ask: AskModel,
    ask_without_tools: AskModel,
    messages: list[BaseMessage],
    tools: Sequence[ChatTool],
) -> str:
    """Let the model call tools, sending back each result, until it replies.

    A call whose arguments are not valid JSON is sent back as an error so
    the model can try again. After `MAX_TOOL_ROUNDS` rounds of tool calls
    the model must reply without calling any more.

    Args:
        ask: Asks the model, with the tools bound, for its next message.
        ask_without_tools: Asks the same model, told not to call tools.
        messages: The messages so far; tool calls and results are added.
        tools: The tools the model may call.

    Returns:
        The reply text.
    """
    tools_by_name = {tool.name: tool for tool in tools}
    for _ in range(MAX_TOOL_ROUNDS):
        response = ask(messages)
        if not response.tool_calls and not response.invalid_tool_calls:
            return response.text
        messages.append(response)
        for broken_call in response.invalid_tool_calls:
            messages.append(
                ToolMessage(
                    f"The arguments for {broken_call['name']} were not valid "
                    "JSON. Try again.",
                    tool_call_id=broken_call["id"] or "",
                )
            )
        for tool_call in response.tool_calls:
            tool = tools_by_name.get(tool_call["name"])
            result = (
                tool.run(tool_call["args"])
                if tool
                else f"There is no tool called {tool_call['name']}."
            )
            messages.append(ToolMessage(result, tool_call_id=tool_call["id"]))
    return ask_without_tools(messages).text


class DeepSeekChatModel:
    """Generates text with DeepSeek through LangChain's chat-model interface."""

    def __init__(self, api_key: str) -> None:
        """Set up the adapter.

        Args:
            api_key: The DeepSeek API key.
        """
        self._api_key = SecretStr(api_key)

    def generate(
        self,
        model: str,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
    ) -> str:
        """Generate the next reply, calling tools first if the model wants to.

        Args:
            model: The DeepSeek model to use, e.g. "deepseek-chat".
            instructions: What the model should be and do (Persona and prompt).
            history: The Conversation so far, oldest first.
            tools: The tools the model may call; none by default.

        Returns:
            The reply text.
        """
        client = ChatDeepSeek(model_name=model, api_key=self._api_key, timeout=60)
        messages = to_langchain_messages(instructions, history)
        if not tools:
            return client.invoke(messages).text
        schemas = [to_tool_schema(tool) for tool in tools]
        return answer_with_tools(
            client.bind_tools(schemas).invoke,
            client.bind_tools(schemas, tool_choice="none").invoke,
            messages,
            tools,
        )
