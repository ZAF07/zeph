from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from companion.adapters.deepseek.chat_model import to_langchain_messages
from companion.core.models import ChatLine, ChatRole


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
