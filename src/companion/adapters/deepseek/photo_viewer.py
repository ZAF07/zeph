import base64

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from companion.adapters.deepseek.chat_model import to_model_answer
from companion.core.models import ModelAnswer, PhotoImage


def to_photo_messages(instructions: str, photo: PhotoImage) -> list[BaseMessage]:
    """Put the instructions and a photo into the messages DeepSeek takes.

    DeepSeek accepts images only in a `user` message, so the photo goes there
    as a data URL.

    Args:
        instructions: What to write about the photo.
        photo: The photo's image.

    Returns:
        A system message with the instructions, then a user message with the
        photo.
    """
    encoded = base64.b64encode(photo.content).decode()
    data_url = f"data:{photo.media_type};base64,{encoded}"
    return [
        SystemMessage(instructions),
        HumanMessage(content=[{"type": "image_url", "image_url": {"url": data_url}}]),
    ]


class DeepSeekPhotoViewer:
    """Looks at photos with a DeepSeek model that can see images."""

    def __init__(self, api_key: str) -> None:
        """Set up the adapter.

        Args:
            api_key: The DeepSeek API key.
        """
        self._api_key = SecretStr(api_key)

    def look(self, model: str, instructions: str, photo: PhotoImage) -> ModelAnswer:
        """Look at a photo and write what the instructions ask for.

        Args:
            model: The DeepSeek model to use, e.g. "deepseek-chat".
            instructions: What to write about the photo.
            photo: The photo's image.

        Returns:
            The text and the tokens it took.
        """
        client = ChatDeepSeek(model_name=model, api_key=self._api_key, timeout=60)
        response = client.invoke(to_photo_messages(instructions, photo))
        return to_model_answer(response.text, [response])
