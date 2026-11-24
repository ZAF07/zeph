from collections.abc import Sequence
from typing import Any

import httpx

from companion.core.models import ChatLine, ChatRole, ModelAnswer
from companion.core.ports import ChatTool

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


class ToolsNotSupportedError(NotImplementedError):
    """Raised when the OpenRouter adapter is asked to let the model call tools."""


class OpenRouterReplyError(RuntimeError):
    """Raised when OpenRouter answers without a reply, e.g. with an error body."""


def to_openrouter_messages(
    instructions: str, history: list[ChatLine]
) -> list[dict[str, str]]:
    """Turn instructions and Conversation history into Chat Completions messages.

    Args:
        instructions: What the model should be and do.
        history: The Conversation so far, oldest first.

    Returns:
        A system message followed by one message per history line.
    """
    messages = [{"role": "system", "content": instructions}]
    for line in history:
        role = "user" if line.role == ChatRole.USER else "assistant"
        messages.append({"role": role, "content": line.text})
    return messages


def to_model_answer(body: dict[str, Any]) -> ModelAnswer:
    """Read the reply text, tokens and reasoning from a Chat Completions reply.

    Args:
        body: The reply body.

    Returns:
        The answer; missing usage counts as no tokens, and the reasoning is
        None when the reply has none.

    Raises:
        OpenRouterReplyError: If the body holds an error or no reply.
    """
    if body.get("error") or not body.get("choices"):
        raise OpenRouterReplyError(f"OpenRouter sent no reply: {body.get('error')}")
    message = body["choices"][0]["message"]
    usage = body.get("usage") or {}
    reasoning = message.get("reasoning")
    return ModelAnswer(
        text=str(message.get("content") or ""),
        tokens_in=int(usage.get("prompt_tokens") or 0),
        tokens_out=int(usage.get("completion_tokens") or 0),
        reasoning=str(reasoning) if reasoning else None,
    )


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
        """Generate the next reply.

        Args:
            model: The OpenRouter model name, sent as given, e.g.
                "deepseek/deepseek-v4.1-flash".
            thinking: Whether the model should think before it answers.
            instructions: What the model should be and do (Persona and prompt).
            history: The Conversation so far, oldest first.
            tools: The tools the model may call; none are supported yet.

        Returns:
            The reply text, the tokens it took and the model's reasoning.

        Raises:
            ToolsNotSupportedError: If any tools are given.
            httpx.HTTPStatusError: If OpenRouter answers with an error status.
            OpenRouterReplyError: If OpenRouter answers with an error body.
        """
        if tools:
            raise ToolsNotSupportedError(
                "The OpenRouter adapter can't let the model call tools yet. "
                "Set CHAT_MODEL_ADAPTER=deepseek for replies that use tools."
            )
        response = self._http.post(
            OPENROUTER_CHAT_URL,
            json={
                "model": model,
                "messages": to_openrouter_messages(instructions, history),
                "reasoning": {"enabled": thinking},
            },
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        return to_model_answer(body)
