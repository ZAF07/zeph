import json
import logging
from collections.abc import Callable, Sequence
from typing import Any

import httpx

from companion.adapters.chat_tools import (
    MAX_TOOL_ROUNDS,
    broken_arguments_message,
    to_tool_schema,
    unknown_tool_message,
)
from companion.core.models import (
    INSTRUCTIONS_SEPARATOR,
    ChatLine,
    ChatRole,
    ModelAnswer,
    ToolCallRecord,
    join_instructions,
)
from companion.core.ports import ChatTool

logger = logging.getLogger(__name__)

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_THAT_ALWAYS_THINK = frozenset(
    {"anthropic/claude-opus-5.5", "anthropic/claude-fable-5.2"}
)

CLAUDE_MAKER = "anthropic"

AskOpenRouter = Callable[[list[dict[str, Any]], bool], dict[str, Any]]


class OpenRouterReplyError(RuntimeError):
    """Raised when OpenRouter answers without a reply, e.g. with an error body."""


def model_maker(model: str) -> str:
    """Name the provider that made a model.

    Args:
        model: The OpenRouter model name, e.g. "anthropic/claude-haiku-5.5".

    Returns:
        The part of the name before the "/", e.g. "anthropic".
    """
    return model.split("/")[0]


def caches_prompts(model: str) -> bool:
    """Say whether a model's instructions are marked for prompt caching.

    Args:
        model: The OpenRouter model name.

    Returns:
        True for Claude models (made by Anthropic), which cache only what is
        marked; False for the rest, which get no marker.
    """
    return model_maker(model) == CLAUDE_MAKER


def to_system_message(
    model: str, instructions: str, message_instructions: str = ""
) -> dict[str, Any]:
    """Put a call's instructions into the system message.

    A Claude model caches only what is marked, up to the marker. So its fixed
    instructions go in a text part of their own carrying a `cache_control`
    marker, and the tools (which come before them) and that part are read
    from the cache on the next call. The instructions for this one call
    follow in a second part with no marker. Empty fixed instructions get no
    part, because Anthropic refuses an empty text part.

    Any other model gets the two joined as plain text, the fixed
    instructions first, so a provider that caches the same start of a
    request by itself (e.g. DeepSeek) can.

    Args:
        model: The OpenRouter model name.
        instructions: The instructions that stay the same from call to call.
        message_instructions: The instructions made for this one call; "" if none.

    Returns:
        The system message.
    """
    if not caches_prompts(model) or not instructions:
        return {
            "role": "system",
            "content": join_instructions(instructions, message_instructions),
        }
    parts: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": instructions,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    if message_instructions:
        parts.append(
            {"type": "text", "text": INSTRUCTIONS_SEPARATOR + message_instructions}
        )
    return {"role": "system", "content": parts}


def to_openrouter_messages(
    model: str,
    instructions: str,
    history: list[ChatLine],
    message_instructions: str = "",
) -> list[dict[str, Any]]:
    """Turn instructions and Conversation history into Chat Completions messages.

    Args:
        model: The OpenRouter model name, which decides how the instructions
            are sent (see `to_system_message`).
        instructions: What the model should be and do.
        history: The Conversation so far, oldest first.
        message_instructions: The instructions made for this one call; "" if none.

    Returns:
        A system message followed by one message per history line.
    """
    messages = [to_system_message(model, instructions, message_instructions)]
    for line in history:
        role = "user" if line.role == ChatRole.USER else "assistant"
        messages.append({"role": role, "content": line.text})
    return messages


def reply_message(body: dict[str, Any]) -> dict[str, Any]:
    """Read the model's message from a Chat Completions reply.

    Args:
        body: The reply body.

    Returns:
        The message.

    Raises:
        OpenRouterReplyError: If the body or its choice holds an error, the
            choice finished with an error, or there is no reply.
    """
    if body.get("error") or not body.get("choices"):
        raise OpenRouterReplyError(f"OpenRouter sent no reply: {body.get('error')}")
    choice: dict[str, Any] = body["choices"][0]
    if choice.get("error") or choice.get("finish_reason") == "error":
        error = choice.get("error") or "the reply ended with an error"
        raise OpenRouterReplyError(f"OpenRouter sent no reply: {error}")
    message: dict[str, Any] = choice["message"]
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
        result = broken_arguments_message(name)
        return ToolCallRecord(name, {"raw": raw_arguments}, result)
    tool = tools_by_name.get(name)
    result = tool.run(arguments) if tool else unknown_tool_message(name)
    return ToolCallRecord(name, arguments, result)


def build_request(
    model: str,
    thinking: bool,
    messages: list[dict[str, Any]],
    tools: Sequence[ChatTool],
    may_call_tools: bool,
) -> dict[str, Any]:
    """Build one Chat Completions request body.

    When the model may no longer call tools, the tools are still sent, with
    `tool_choice` "none", because the messages already hold tool calls and
    some providers (e.g. Anthropic) refuse those without the tools.

    Only the model's maker may answer, because our own provider keys are the
    makers' keys: any other host would be paid with OpenRouter credits. A
    model its maker does not serve fails.

    A model that always thinks refuses to be told not to, so thinking off
    is left unsaid for it and it thinks only as much as it needs.

    Args:
        model: The OpenRouter model name, sent as given.
        thinking: Whether the model should think before it answers.
        messages: The messages so far, made for this model.
        tools: The tools offered; none sends no tools.
        may_call_tools: Whether the model may call a tool this round.

    Returns:
        The request body.
    """
    request: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "provider": {"only": [model_maker(model)]},
    }
    if thinking or model not in MODELS_THAT_ALWAYS_THINK:
        request["reasoning"] = {"enabled": thinking}
    if tools:
        request["tools"] = [to_tool_schema(tool) for tool in tools]
        if not may_call_tools:
            request["tool_choice"] = "none"
    return request


def answer_with_tools(
    ask: AskOpenRouter, messages: list[dict[str, Any]], tools: Sequence[ChatTool]
) -> ModelAnswer:
    """Let the model call tools, sending back each result, until it replies.

    After `MAX_TOOL_ROUNDS` rounds of tool calls the model must reply
    without calling any more.

    Args:
        ask: Sends the messages to the model, saying whether it may call
            tools, and returns the reply body.
        messages: The messages so far; tool calls and results are added.
        tools: The tools the model may call; with none, the first reply is
            the answer.

    Returns:
        The reply text, the tokens every round took, every tool call made
        and the model's reasoning.

    Raises:
        OpenRouterReplyError: If a reply body holds an error or no reply.
    """
    tools_by_name = {tool.name: tool for tool in tools}
    bodies: list[dict[str, Any]] = []
    tool_calls: list[ToolCallRecord] = []
    for _ in range(MAX_TOOL_ROUNDS):
        body = ask(messages, True)
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
    bodies.append(ask(messages, False))
    return to_model_answer(bodies, tool_calls)


def new_http_client() -> httpx.Client:
    """Make the HTTP client used when none is given.

    Returns:
        A client that waits up to a minute for a reply.
    """
    return httpx.Client(timeout=60)


def warn_if_paid_with_credits(model: str, body: dict[str, Any]) -> None:
    """Log a warning when a reply was paid with OpenRouter credits.

    Args:
        model: The model that was asked.
        body: The reply body, whose usage says if our own provider key paid.
    """
    if (body.get("usage") or {}).get("is_byok") is False:
        logger.warning(
            "A call to %s was paid with OpenRouter credits, not our own key", model
        )


def log_cached_tokens(model: str, body: dict[str, Any]) -> None:
    """Log how much of a call's prompt came from the prompt cache.

    A reply that says nothing about the cache counts as none.

    Args:
        model: The model that was asked.
        body: The reply body, whose usage holds the cached-token counts.
    """
    usage = body.get("usage") or {}
    details = usage.get("prompt_tokens_details") or {}
    logger.info(
        "A call to %s read %d of its %d prompt tokens from the cache "
        "and wrote %d to it",
        model,
        int(details.get("cached_tokens") or 0),
        int(usage.get("prompt_tokens") or 0),
        int(details.get("cache_write_tokens") or 0),
    )


def send_request(
    http_client: httpx.Client, api_key: str, request: dict[str, Any]
) -> dict[str, Any]:
    """Send one Chat Completions request to OpenRouter.

    Args:
        http_client: The HTTP client to send with.
        api_key: The OpenRouter API key.
        request: The request body.

    Returns:
        The reply body.

    Raises:
        httpx.HTTPStatusError: If OpenRouter answers with an error status.
    """
    response = http_client.post(
        OPENROUTER_CHAT_URL,
        json=request,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    response.raise_for_status()
    body: dict[str, Any] = response.json()
    warn_if_paid_with_credits(str(request["model"]), body)
    log_cached_tokens(str(request["model"]), body)
    return body


class OpenRouterChatModel:
    """Generates text with any model OpenRouter offers, over plain HTTP."""

    def __init__(self, api_key: str, http_client: httpx.Client | None = None) -> None:
        """Set up the adapter.

        Args:
            api_key: The OpenRouter API key.
            http_client: The HTTP client to use; a new one is made if not given.
        """
        self._api_key = api_key
        self._http = http_client or new_http_client()

    def generate(
        self,
        model: str,
        thinking: bool,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
        message_instructions: str = "",
    ) -> ModelAnswer:
        """Generate the next reply, calling tools first if the model wants to.

        Args:
            model: The OpenRouter model name, sent as given, e.g.
                "deepseek/deepseek-v4.1-flash-1017".
            thinking: Whether the model should think before it answers.
            instructions: What the model should be and do (Persona and
                prompt): the part that stays the same from call to call.
            history: The Conversation so far, oldest first.
            tools: The tools the model may call; none by default.
            message_instructions: The instructions made for this one call,
                read after `instructions`; "" by default.

        Returns:
            The reply text, the tokens every round took, every tool call made
            and the model's reasoning.

        Raises:
            httpx.HTTPStatusError: If OpenRouter answers with an error status.
            OpenRouterReplyError: If OpenRouter answers with an error body.
        """
        return answer_with_tools(
            lambda messages, may_call_tools: send_request(
                self._http,
                self._api_key,
                build_request(model, thinking, messages, tools, may_call_tools),
            ),
            to_openrouter_messages(model, instructions, history, message_instructions),
            tools,
        )
