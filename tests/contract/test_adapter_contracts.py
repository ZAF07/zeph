import os

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from companion.adapters.clerk.auth_verifier import ClerkAuthVerifier
from companion.adapters.deepseek.chat_model import DeepSeekChatModel
from companion.adapters.fastembed.embedder import FastEmbedEmbedder
from companion.adapters.postgres.tables import EMBEDDING_SIZE
from companion.adapters.tavily.web_search import TavilyWebSearch
from companion.adapters.telegram.chat_channel import TelegramChatChannel
from companion.core.models import ChatLine, ChatRole
from companion.core.ports import ChatTool

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


def test_telegram_says_an_unknown_sticker_set_does_not_exist() -> None:
    channel = TelegramChatChannel(required_env("TELEGRAM_BOT_TOKEN"))

    assert channel.get_sticker_set("zeph_no_such_set_8f3k2q") is None


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


def test_deepseek_calls_an_offered_tool_and_uses_its_result() -> None:
    chat_model = DeepSeekChatModel(required_env("DEEPSEEK_API_KEY"))
    queries: list[str] = []

    def run_search(arguments: dict[str, object]) -> str:
        queries.append(str(arguments.get("query", "")))
        return "Result: the secret word of the day is 'lantern'."

    reply = chat_model.generate(
        model="deepseek-chat",
        instructions=(
            "Always use the web_search tool before answering. "
            "Then answer in one short sentence."
        ),
        history=[ChatLine(role=ChatRole.USER, text="What's the secret word today?")],
        tools=[
            ChatTool(
                name="web_search",
                description="Search the web.",
                parameters={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
                run=run_search,
            )
        ],
    )

    assert queries
    assert "lantern" in reply.lower()


def test_tavily_searches_the_web_and_reads_a_page() -> None:
    web_search = TavilyWebSearch(required_env("TAVILY_API_KEY"))

    results = web_search.search("Thich Nhat Hanh The Miracle of Mindfulness")
    page = web_search.fetch_page("https://en.wikipedia.org/wiki/Thich_Nhat_Hanh")

    assert results
    assert all(result.url.startswith("http") for result in results)
    assert any(result.title and result.content for result in results)
    assert "Thich Nhat Hanh" in page


def test_fastembed_embeddings_have_the_size_the_vector_store_keeps() -> None:
    embedder = FastEmbedEmbedder()

    passages = embedder.embed_passages(["Notice the breath.", "Return gently."])
    query = embedder.embed_query("how do I calm down?")

    assert [len(vector) for vector in passages] == [EMBEDDING_SIZE, EMBEDDING_SIZE]
    assert len(query) == EMBEDDING_SIZE
