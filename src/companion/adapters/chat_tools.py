import re
from typing import Any

from companion.core.ports import ChatTool

MAX_TOOL_ROUNDS = 4

TOOL_CALL_OPENING_TAG = (
    r"<(?:tool[ _]calls?|function_calls?|function=[^>]*|invoke\b[^>]*"
    r"|｜tool▁calls?▁begin｜)>"
)
TOOL_CALL_CLOSING_TAG = (
    r"<(?:/tool[ _]calls?|/function_calls?|/function|/invoke|｜tool▁calls?▁end｜)>"
)
TOOL_CALL_TAG = re.compile(
    r"</?(?:tool[ _]calls?|function_calls?|function(?:=[^>]*)?|invoke\b[^>]*"
    r"|parameter\b[^>]*|｜tool▁[^>]*｜)>",
    re.IGNORECASE,
)
CLOSED_TOOL_CALL = re.compile(
    f"{TOOL_CALL_OPENING_TAG}.*?{TOOL_CALL_CLOSING_TAG}", re.IGNORECASE | re.DOTALL
)
UNCLOSED_TOOL_CALL = re.compile(f"{TOOL_CALL_OPENING_TAG}.*", re.IGNORECASE | re.DOTALL)


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


def holds_tool_call_markup(text: str) -> bool:
    """Say whether a reply holds a tool call written out as text.

    Some models now and then write the call into their reply, e.g.
    "<tool_call>" or "<function=change_directness>", instead of calling the
    tool. Nothing is run then, and the markup must never reach a User.

    Args:
        text: The reply text.

    Returns:
        True if it holds a tool-call tag of any of the known kinds.
    """
    return TOOL_CALL_TAG.search(text) is not None


def without_tool_call_markup(text: str) -> str:
    """Take every tool call written out as text out of a reply.

    A call with its closing tag goes with everything inside it; one that
    never closes goes with the rest of the text; a tag left on its own goes
    too. The words around them stay.

    Args:
        text: The reply text.

    Returns:
        The text without the markup; "" if nothing else was in it. Text
        with no markup comes back as it is.
    """
    if not holds_tool_call_markup(text):
        return text
    without_closed = CLOSED_TOOL_CALL.sub("", text)
    without_unclosed = UNCLOSED_TOOL_CALL.sub("", without_closed)
    return TOOL_CALL_TAG.sub("", without_unclosed).strip()
