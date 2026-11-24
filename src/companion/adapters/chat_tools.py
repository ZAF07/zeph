from typing import Any

from companion.core.ports import ChatTool

MAX_TOOL_ROUNDS = 4


def to_tool_schema(tool: ChatTool) -> dict[str, Any]:
    """Describe a tool in the OpenAI function format chat model APIs take.

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


def broken_arguments_message(tool_name: str) -> str:
    """Tell the model a tool call's arguments were not valid JSON.

    Args:
        tool_name: The tool it tried to call.

    Returns:
        What the model is told back, so it can try again.
    """
    return f"The arguments for {tool_name} were not valid JSON. Try again."


def unknown_tool_message(tool_name: str) -> str:
    """Tell the model it called a tool it was not offered.

    Args:
        tool_name: The tool it tried to call.

    Returns:
        What the model is told back.
    """
    return f"There is no tool called {tool_name}."
