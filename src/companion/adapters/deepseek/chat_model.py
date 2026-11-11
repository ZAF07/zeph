from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from companion.core.models import ChatLine, ChatRole


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


class DeepSeekChatModel:
    """Generates text with DeepSeek through LangChain's chat-model interface."""

    def __init__(self, api_key: str) -> None:
        """Set up the adapter.

        Args:
            api_key: The DeepSeek API key.
        """
        self._api_key = SecretStr(api_key)

    def generate(self, model: str, instructions: str, history: list[ChatLine]) -> str:
        """Generate the next reply.

        Args:
            model: The DeepSeek model to use, e.g. "deepseek-chat".
            instructions: What the model should be and do (Persona and prompt).
            history: The Conversation so far, oldest first.

        Returns:
            The reply text.
        """
        client = ChatDeepSeek(model_name=model, api_key=self._api_key, timeout=60)
        response = client.invoke(to_langchain_messages(instructions, history))
        return response.text
