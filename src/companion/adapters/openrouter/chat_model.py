import json
from collections.abc import Sequence
from typing import Any

import httpx

from companion.core.models import ChatLine, ChatRole, ModelAnswer, ToolCallRecord
from companion.core.ports import ChatTool

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_TOOL_ROUNDS = 4


class OpenRouterReplyError(RuntimeError):
    """Raised when OpenRouter answers without a reply, e.g. with an error body."""


def to_openrouter_messages(
    instructions: str, history: list[ChatLine]
) -> list[dict[str, Any]]:
    """Turn instructions and Conversation history into Chat Completions messages.

    Args:
        instructions: What the model should be and do.
        history: The Conversation so far, oldest first.

    Returns:
        A system message followed by one message per history line.
    """
    messages: list[dict[str, Any]] = [{"role": "system", "content": instructions}]
    for line in history:
        role = "user" if line.role == ChatRole.USER else "assistant"
        messages.append({"role": role, "content": line.text})
    return messages


def to_tool_schema(tool: ChatTool) -> dict[str, Any]:
    """Describe a tool in the OpenAI function format OpenRouter takes.

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


def reply_message(body: dict[str, Any]) -> dict[str, Any]:
    """Read the model's message from a Chat Completions reply.

    Args:
        body: The reply body.

    Returns:
        The message.

    Raises:
        OpenRouterReplyError: If the body holds an error or no reply.
    """
    if body.get("error") or not body.get("choices"):
        raise OpenRouterReplyError(f"OpenRouter sent no reply: {body.get('error')}")
    message: dict[str, Any] = body["choices"][0]["message"]
    return message


def to_model_answer(
    bodies: Sequence[dict[str, Any]], tool_calls: Sequence[ToolCallRecord] = ()
) -> ModelAnswer:
    """Put the last reply's text together with the tokens, tool calls and reasoning.

    Args:
        bodies: Every reply body on the way to the answer, the last one holding
            the reply text.
        tool_calls: The tool calls made on the way, with their results.

    Returns:
        The answer; missing usage counts as no tokens, and the reasoning is
        None when no reply had any.

    Raises:
        OpenRouterReplyError: If a body holds an error or no reply.
    """
    messages = [reply_message(body) for body in bodies]
    usages = [body.get("usage") or {} for body in bodies]
    reasonings = [
        str(message["reasoning"]) for message in messages if message.get("reasoning")
    ]
    return ModelAnswer(
        text=str(messages[-1].get("content") or ""),
        tokens_in=sum(int(usage.get("prompt_tokens") or 0) for usage in usages),
        tokens_out=sum(int(usage.get("completion_tokens") or 0) for usage in usages),
        tool_calls=tuple(tool_calls),
        reasoning="\n\n".join(reasonings) if reasonings else None,
    )


def to_assistant_message(message: dict[str, Any]) -> dict[str, Any]:
    """Turn the model's tool-calling message into the one sent back next round.

    The reasoning details are kept as given, because Anthropic needs them to
    carry on thinking after a tool call.

    Args:
        message: The model's message, with its tool calls.

    Returns:
        The assistant message to send back.
    """
    assistant_message = {
        "role": "assistant",
        "content": message.get("content"),
        "tool_calls": message["tool_calls"],
    }
    if message.get("reasoning_details"):
        assistant_message["reasoning_details"] = message["reasoning_details"]
    return assistant_message


def run_tool_call(
    tool_call: dict[str, Any], tools_by_name: dict[str, ChatTool]
) -> ToolCallRecord:
    """Run one tool call the model made.

    A call whose arguments are not valid JSON is not run; the model is told
    so it can try again, and the arguments are kept as given, under "raw".

    Args:
        tool_call: The tool call, in the OpenAI function format.
        tools_by_name: The tools the model may call, by name.

    Returns:
        The call with the result the model is told back.
    """
    name = str(tool_call["function"]["name"])
    raw_arguments = tool_call["function"].get("arguments") or "{}"
    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError:
        arguments = None
    if not isinstance(arguments, dict):
        result = f"The arguments for {name} were not valid JSON. Try again."
        return ToolCallRecord(name, {"raw": raw_arguments}, result)
    tool = tools_by_name.get(name)
    result = tool.run(arguments) if tool else f"There is no tool called {name}."
    return ToolCallRecord(name, arguments, result)


class OpenRouterChatModel:
    """Generates text with any model OpenRouter offers, over plain HTTP."""

    def __init__(self, api_key: str, http_client: httpx.Client | None = None) -> None:
        """Set up the adapter.

        Args:
            api_key: The OpenRouter API key.
            http_client: The HTTP client to use; a new one is made if not given.
        """
        self._api_key = api_key
        self._http = http_client or httpx.Client(timeout=60)

    def generate(
        self,
        model: str,
        thinking: bool,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
    ) -> ModelAnswer:
        """Generate the next reply, calling tools first if the model wants to.

        Each round the tool results are sent back, until the model replies.
        After `MAX_TOOL_ROUNDS` rounds of tool calls the model must reply
        without calling any more.

        Args:
            model: The OpenRouter model name, sent as given, e.g.
                "deepseek/deepseek-v4.1-flash".
            thinking: Whether the model should think before it answers.
            instructions: What the model should be and do (Persona and prompt).
            history: The Conversation so far, oldest first.
            tools: The tools the model may call; none by default.

        Returns:
            The reply text, the tokens every round took, every tool call made
            and the model's reasoning.

        Raises:
            httpx.HTTPStatusError: If OpenRouter answers with an error status.
            OpenRouterReplyError: If OpenRouter answers with an error body.
        """
        messages = to_openrouter_messages(instructions, history)
        request: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "reasoning": {"enabled": thinking},
        }
        if tools:
            request["tools"] = [to_tool_schema(tool) for tool in tools]
        tools_by_name = {tool.name: tool for tool in tools}
        bodies: list[dict[str, Any]] = []
        tool_calls: list[ToolCallRecord] = []
        for _ in range(MAX_TOOL_ROUNDS):
            body = self._ask(request)
            bodies.append(body)
            message = reply_message(body)
            if not message.get("tool_calls"):
                return to_model_answer(bodies, tool_calls)
            messages.append(to_assistant_message(message))
            for tool_call in message["tool_calls"]:
                record = run_tool_call(tool_call, tools_by_name)
                tool_calls.append(record)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": record.result,
                    }
                )
        bodies.append(self._ask({**request, "tool_choice": "none"}))
        return to_model_answer(bodies, tool_calls)

    def _ask(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send one Chat Completions request to OpenRouter.

        Args:
            request: The request body.

        Returns:
            The reply body.

        Raises:
            httpx.HTTPStatusError: If OpenRouter answers with an error status.
        """
        response = self._http.post(
            OPENROUTER_CHAT_URL,
            json=request,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        return body
