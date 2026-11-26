import base64
from typing import Any

import httpx

from companion.adapters.openrouter.chat_model import (
    build_request,
    new_http_client,
    send_request,
    to_model_answer,
    to_system_message,
)
from companion.core.models import ModelAnswer, PhotoImage


def to_photo_messages(
    model: str, instructions: str, photo: PhotoImage
) -> list[dict[str, Any]]:
    """Put the instructions and a photo into Chat Completions messages.

    The photo goes in a user message as a data URL, because some providers
    (e.g. DeepSeek) accept images only there.

    Args:
        model: The OpenRouter model name, which decides how the instructions
            are sent (see `to_system_message`).
        instructions: What to write about the photo.
        photo: The photo's image.

    Returns:
        A system message with the instructions, then a user message with the
        photo.
    """
    encoded = base64.b64encode(photo.content).decode()
    data_url = f"data:{photo.media_type};base64,{encoded}"
    return [
        to_system_message(model, instructions),
        {
            "role": "user",
            "content": [{"type": "image_url", "image_url": {"url": data_url}}],
        },
    ]


class OpenRouterPhotoViewer:
    """Looks at photos with any model on OpenRouter that can see images."""

    def __init__(self, api_key: str, http_client: httpx.Client | None = None) -> None:
        """Set up the adapter.

        Args:
            api_key: The OpenRouter API key.
            http_client: The HTTP client to use; a new one is made if not given.
        """
        self._api_key = api_key
        self._http = http_client or new_http_client()

    def look(
        self, model: str, thinking: bool, instructions: str, photo: PhotoImage
    ) -> ModelAnswer:
        """Look at a photo and write what the instructions ask for.

        Args:
            model: The OpenRouter model name, sent as given, e.g.
                "deepseek/deepseek-v4.1-flash-1017".
            thinking: Whether the model should think before it answers.
            instructions: What to write about the photo.
            photo: The photo's image.

        Returns:
            The text, the tokens it took and the model's reasoning.

        Raises:
            httpx.HTTPStatusError: If OpenRouter answers with an error status.
            OpenRouterReplyError: If OpenRouter answers with an error body.
        """
        request = build_request(
            model,
            thinking,
            to_photo_messages(model, instructions, photo),
            tools=(),
            may_call_tools=False,
        )
        return to_model_answer([send_request(self._http, self._api_key, request)])
