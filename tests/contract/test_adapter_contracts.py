import os
import threading
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from companion.adapters.clerk.accounts import ClerkAccounts
from companion.adapters.clerk.auth_verifier import ClerkAuthVerifier
from companion.adapters.deepseek.chat_model import DeepSeekChatModel
from companion.adapters.deepseek.photo_viewer import DeepSeekPhotoViewer
from companion.adapters.evals.stand_ins import InlineUserWorkQueue
from companion.adapters.fastembed.embedder import FastEmbedEmbedder
from companion.adapters.openrouter.chat_model import OpenRouterChatModel
from companion.adapters.postgres.tables import EMBEDDING_SIZE
from companion.adapters.tavily.web_search import TavilyWebSearch
from companion.adapters.telegram.chat_channel import TelegramChatChannel
from companion.adapters.user_work_queue import ThreadPoolUserWorkQueue
from companion.core.models import ChatLine, ChatRole, PhotoImage
from companion.core.ports import ChatTool, UserWorkQueue
from tests.fakes import FakeUserWorkQueue

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


def test_clerk_treats_deleting_an_account_it_does_not_have_as_done() -> None:
    accounts = ClerkAccounts(required_env("CLERK_SECRET_KEY"))

    accounts.delete_account("user_zeph_no_such_account_8f3k2q")


def test_deepseek_generates_a_reply() -> None:
    chat_model = DeepSeekChatModel(required_env("DEEPSEEK_API_KEY"))

    reply = chat_model.generate(
        model="deepseek-flash",
        thinking=False,
        instructions="Reply with one short friendly sentence.",
        history=[ChatLine(role=ChatRole.USER, text="hi there")],
    )

    assert reply.text.strip()
    assert reply.tokens_in > 0
    assert reply.tokens_out > 0


@pytest.mark.parametrize("model", ["deepseek-flash", "deepseek-chat"])
def test_deepseek_thinks_only_when_asked(model: str) -> None:
    chat_model = DeepSeekChatModel(required_env("DEEPSEEK_API_KEY"))

    def answer(thinking: bool) -> str | None:
        return chat_model.generate(
            model=model,
            thinking=thinking,
            instructions="Answer with one number.",
            history=[ChatLine(role=ChatRole.USER, text="What is 17 times 23?")],
        ).reasoning

    assert answer(thinking=True)
    assert answer(thinking=False) is None


def test_openrouter_generates_a_deepseek_reply() -> None:
    chat_model = OpenRouterChatModel(required_env("OPENROUTER_API_KEY"))

    reply = chat_model.generate(
        model="deepseek/deepseek-v4.1-flash",
        thinking=False,
        instructions="Reply with one short friendly sentence.",
        history=[ChatLine(role=ChatRole.USER, text="hi there")],
    )

    assert reply.text.strip()
    assert reply.tokens_in > 0
    assert reply.tokens_out > 0


def test_openrouter_returns_reasoning_when_thinking_is_on() -> None:
    chat_model = OpenRouterChatModel(required_env("OPENROUTER_API_KEY"))

    reply = chat_model.generate(
        model="deepseek/deepseek-v4.1-flash",
        thinking=True,
        instructions="Answer with one number.",
        history=[ChatLine(role=ChatRole.USER, text="What is 17 times 23?")],
    )

    assert "391" in reply.text
    assert reply.reasoning


def test_deepseek_describes_a_photo() -> None:
    photo_viewer = DeepSeekPhotoViewer(required_env("DEEPSEEK_API_KEY"))
    image_file = Path(__file__).parents[2] / "evals/images/weekend-list.jpg"

    answer = photo_viewer.look(
        model="deepseek-flash",
        thinking=False,
        instructions="Write out the handwritten list in the photo.",
        photo=PhotoImage(content=image_file.read_bytes(), media_type="image/jpeg"),
    )

    assert "compost" in answer.text.lower()
    assert answer.tokens_in > 0


def test_deepseek_calls_an_offered_tool_and_uses_its_result() -> None:
    chat_model = DeepSeekChatModel(required_env("DEEPSEEK_API_KEY"))
    queries: list[str] = []

    def run_search(arguments: dict[str, object]) -> str:
        queries.append(str(arguments.get("query", "")))
        return "Result: the secret word of the day is 'lantern'."

    reply = chat_model.generate(
        model="deepseek-flash",
        thinking=True,
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
    assert "lantern" in reply.text.lower()


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


@pytest.fixture(params=["thread_pool", "evals_inline", "fake"])
def work_queue(request: pytest.FixtureRequest) -> UserWorkQueue:
    """Each User work queue adapter, and the fake tests use in its place."""
    queues: dict[str, UserWorkQueue] = {
        "thread_pool": ThreadPoolUserWorkQueue(max_running=4),
        "evals_inline": InlineUserWorkQueue(),
        "fake": FakeUserWorkQueue(),
    }
    return queues[request.param]


def test_user_work_queues_run_each_keys_work_in_order_one_at_a_time(
    work_queue: UserWorkQueue,
) -> None:
    runs: list[str] = []
    done = threading.Event()
    other_user_done = threading.Event()

    def first() -> None:
        work_queue.add("user-1", lambda: runs.append("added while first ran"))
        runs.append("first")

    work_queue.add("user-1", first)
    work_queue.add("user-1", lambda: runs.append("second"))
    work_queue.add("user-2", other_user_done.set)
    work_queue.add("user-1", done.set)

    assert done.wait(timeout=2)
    assert other_user_done.wait(timeout=2)
    assert runs == ["first", "added while first ran", "second"]


def test_user_work_queues_log_failed_work_and_still_run_later_work(
    work_queue: UserWorkQueue, caplog: pytest.LogCaptureFixture
) -> None:
    after = threading.Event()

    def fail() -> None:
        raise RuntimeError("boom")

    work_queue.add("user-1", fail)
    work_queue.add("user-1", after.set)

    assert after.wait(timeout=2)
    assert "A User's queued work failed" in caplog.text
