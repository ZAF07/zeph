import os

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from companion.adapters.clerk.auth_verifier import ClerkAuthVerifier
from companion.adapters.deepseek.chat_model import DeepSeekChatModel
from companion.adapters.telegram.chat_channel import TelegramChatChannel
from companion.core.models import ChatLine, ChatRole

pytestmark = pytest.mark.contract


def required_env(key: str) -> str:
    """Read a key the contract test needs, skipping the test when it is unset."""
    value = os.environ.get(key)
    if not value:
        pytest.skip(f"{key} is not set")
    return value


def test_telegram_bot_token_reaches_the_configured_bot() -> None:
    channel = TelegramChatChannel(required_env("TELEGRAM_BOT_TOKEN"))

    assert channel.get_bot_username() == required_env("TELEGRAM_BOT_USERNAME")


def test_clerk_refuses_a_token_it_did_not_sign() -> None:
    verifier = ClerkAuthVerifier(
        required_env("CLERK_SECRET_KEY"), authorized_parties=["http://localhost:3000"]
    )
    forged_token = jwt.encode(
        {"sub": "user_forged"},
        rsa.generate_private_key(public_exponent=65537, key_size=2048),
        algorithm="RS256",
        headers={"kid": "not-a-clerk-key"},
    )

    assert verifier.verify(forged_token) is None


def test_deepseek_generates_a_reply() -> None:
    chat_model = DeepSeekChatModel(required_env("DEEPSEEK_API_KEY"))

    reply = chat_model.generate(
        model="deepseek-chat",
        instructions="Reply with one short friendly sentence.",
        history=[ChatLine(role=ChatRole.USER, text="hi there")],
    )

    assert reply.strip()
