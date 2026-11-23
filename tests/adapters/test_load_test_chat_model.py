import logging
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.load_test.chat_model import (
    CANNED_REPLY,
    CallShape,
    LoadTestChatModel,
    LoadTestPhotoViewer,
    shape_of,
)
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.check_ins import read_check_in_decision
from companion.core.curiosities import (
    NO_DUE_CURIOSITIES,
    read_curiosity_keeping_answer,
)
from companion.core.life_threads import read_thread_keeping_answer
from companion.core.models import ChatLine, ChatRole, PhotoImage
from companion.core.move_outcomes import read_move_outcome_keeping_answer
from companion.core.patterns import read_pattern_keeping_answer
from companion.core.personal_stickers import read_stickers_to_keep
from companion.core.platform_settings import (
    CHECK_IN_PROMPT,
    CURIOSITY_KEEPING_PROMPT,
    KNOWLEDGE_WHEN_IT_HELPS_PROMPT,
    LIFE_THREAD_KEEPING_PROMPT,
    MEMORY_PROCESSING_PROMPT,
    MOVE_OUTCOME_KEEPING_PROMPT,
    PATTERN_KEEPING_PROMPT,
    PERSONA,
    PERSONA_OUTLOOK,
    PERSONAL_STICKER_KEEPING_PROMPT,
    PORTRAIT_PROMPT,
    REPLY_PLAN_PROMPT,
    SAFEGUARD_PROMPT,
    UNDERSTANDING_PROMPT,
)
from companion.core.post_conversation import read_processing_answer
from companion.core.reply_plan import read_reply_plan_form
from companion.core.safeguard import read_risk_type
from companion.core.understanding import read_understanding_form
from companion.core.woven_check_ins import BROUGHT_UP_CHECK_PROMPT
from tests.fakes import FakeChatChannel, FakeClock, FakeScheduler
from tests.telegram_helpers import (
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_telegram,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_check_in_sending import ONE_DAY, set_up_user_with_check_ins
from tests.test_post_conversation import quiet_gap


@pytest.fixture
def chat_model(engine: Engine) -> LoadTestChatModel:
    """The load-test chat model on the test database, without its waits."""
    return LoadTestChatModel(
        build_postgres_repositories(engine), sleep=lambda seconds: None
    )


def core_warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    """The warnings and errors the app's core logged, e.g. falling back."""
    return [
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("companion.core")
        and record.levelno >= logging.WARNING
    ]


def ask(model: LoadTestChatModel, instructions: str, text: str = "hi") -> str:
    """Make one call with the given instructions and return the answer's text."""
    answer = model.generate(
        model="deepseek-flash",
        thinking=False,
        instructions=instructions,
        history=[ChatLine(role=ChatRole.USER, text=text)],
    )
    return answer.text


def test_every_call_shape_is_told_apart_by_its_instructions(engine: Engine) -> None:
    settings = build_postgres_repositories(engine).platform_settings.load()
    persona, outlook = settings.get(PERSONA), settings.get(PERSONA_OUTLOOK)

    assert shape_of(settings.get(SAFEGUARD_PROMPT), settings) == CallShape.SAFEGUARD
    assert (
        shape_of(settings.get(UNDERSTANDING_PROMPT), settings)
        == CallShape.UNDERSTANDING
    )
    assert (
        shape_of(f"{outlook}\n\n{settings.get(REPLY_PLAN_PROMPT)}", settings)
        == CallShape.REPLY_PLAN
    )
    assert (
        shape_of(f"{persona}\n\n{settings.get(CHECK_IN_PROMPT)}", settings)
        == CallShape.CHECK_IN
    )
    assert (
        shape_of(settings.get(MEMORY_PROCESSING_PROMPT), settings)
        == CallShape.CONVERSATION_END
    )
    assert (
        shape_of(settings.get(LIFE_THREAD_KEEPING_PROMPT), settings)
        == CallShape.LIFE_THREADS
    )
    assert shape_of(settings.get(PATTERN_KEEPING_PROMPT), settings) == (
        CallShape.PATTERNS
    )
    assert (
        shape_of(settings.get(CURIOSITY_KEEPING_PROMPT), settings)
        == CallShape.CURIOSITIES
    )
    assert (
        shape_of(settings.get(MOVE_OUTCOME_KEEPING_PROMPT), settings)
        == CallShape.MOVE_OUTCOMES
    )
    assert shape_of(settings.get(PORTRAIT_PROMPT), settings) == CallShape.PORTRAIT
    assert (
        shape_of(settings.get(PERSONAL_STICKER_KEEPING_PROMPT), settings)
        == CallShape.PERSONAL_STICKERS
    )
    assert (
        shape_of(settings.get(KNOWLEDGE_WHEN_IT_HELPS_PROMPT), settings)
        == CallShape.KNOWLEDGE_WHEN_IT_HELPS
    )
    assert shape_of(BROUGHT_UP_CHECK_PROMPT, settings) == CallShape.BROUGHT_UP_CHECK
    assert shape_of(f"{persona}\n\nReply in Zeph's voice.", settings) == (
        CallShape.REPLY
    )


def test_each_canned_answer_is_read_by_the_app_as_a_real_answer(
    engine: Engine, chat_model: LoadTestChatModel
) -> None:
    repositories = build_postgres_repositories(engine)
    settings = repositories.platform_settings.load()
    kinds = repositories.check_ins.list_kinds()
    kind_lines = "\n".join(f"- {kind.name}: {kind.description}" for kind in kinds)
    check_in_description = f"Check-in Kinds you may choose from:\n{kind_lines}\n\n"
    persona, outlook = settings.get(PERSONA), settings.get(PERSONA_OUTLOOK)

    def keeping(prompt: Any) -> str:
        return ask(chat_model, settings.get(prompt))

    assert read_risk_type(keeping(SAFEGUARD_PROMPT)) is not None
    assert read_understanding_form(keeping(UNDERSTANDING_PROMPT)) is not None
    plan = ask(chat_model, f"{outlook}\n\n{settings.get(REPLY_PLAN_PROMPT)}")
    assert read_reply_plan_form(plan, [], NO_DUE_CURIOSITIES, {}) is not None
    decision = read_check_in_decision(
        ask(
            chat_model,
            f"{persona}\n\n{settings.get(CHECK_IN_PROMPT)}",
            check_in_description,
        ),
        kinds,
        shared_photos=[],
    )
    assert decision.kind is not None
    assert read_processing_answer(keeping(MEMORY_PROCESSING_PROMPT)) is not None
    assert read_thread_keeping_answer(keeping(LIFE_THREAD_KEEPING_PROMPT)) == []
    assert read_pattern_keeping_answer(keeping(PATTERN_KEEPING_PROMPT)) == []
    assert read_curiosity_keeping_answer(keeping(CURIOSITY_KEEPING_PROMPT)) == []
    assert read_move_outcome_keeping_answer(keeping(MOVE_OUTCOME_KEEPING_PROMPT)) == []
    assert read_stickers_to_keep(keeping(PERSONAL_STICKER_KEEPING_PROMPT)) == []
    assert keeping(PORTRAIT_PROMPT).strip()
    assert keeping(KNOWLEDGE_WHEN_IT_HELPS_PROMPT).strip()
    assert ask(chat_model, BROUGHT_UP_CHECK_PROMPT) == "no"
    assert ask(chat_model, f"{persona}\n\nReply in Zeph's voice.") == CANNED_REPLY


def test_a_check_in_with_no_plain_kind_offered_is_skipped(
    chat_model: LoadTestChatModel, engine: Engine
) -> None:
    repositories = build_postgres_repositories(engine)
    settings = repositories.platform_settings.load()
    kinds = repositories.check_ins.list_kinds()

    answer = ask(
        chat_model,
        f"{settings.get(PERSONA)}\n\n{settings.get(CHECK_IN_PROMPT)}",
        "Check-in Kinds you may choose from:\n- A look back at a photo: ...\n\n",
    )

    decision = read_check_in_decision(answer, kinds, shared_photos=[])
    assert decision.kind is None
    assert decision.skip_reason


def test_every_call_waits_between_three_and_eight_seconds(engine: Engine) -> None:
    waits: list[float] = []
    model = LoadTestChatModel(build_postgres_repositories(engine), sleep=waits.append)

    for _ in range(30):
        ask(model, "anything")

    assert len(waits) == 30
    assert all(3 <= seconds <= 8 for seconds in waits)
    assert len(set(waits)) > 1


def test_the_photo_viewer_describes_any_photo_after_a_wait() -> None:
    waits: list[float] = []
    viewer = LoadTestPhotoViewer(sleep=waits.append)

    answer = viewer.look(
        "deepseek-flash", False, "Describe it.", PhotoImage(b"jpeg", "image/jpeg")
    )

    assert answer.text.strip()
    [seconds] = waits
    assert 3 <= seconds <= 8


def test_a_message_gets_a_full_reply_with_no_fallbacks(
    client: TestClient,
    auth_verifier: Any,
    chat_channel: FakeChatChannel,
    caplog: pytest.LogCaptureFixture,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    with caplog.at_level(logging.WARNING):
        send_to_webhook(client, telegram_text_update("work has been a lot lately"))

    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID) == [CANNED_REPLY]
    assert core_warnings(caplog) == []


def test_an_ended_conversation_is_processed_into_a_day_summary(
    client: TestClient,
    auth_verifier: Any,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    send_to_webhook(client, telegram_text_update("work has been a lot lately"))

    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    with caplog.at_level(logging.WARNING):
        scheduler.tick()

    summaries = client.get("/api/day-summaries", headers=headers).json()["summaries"]
    assert len(summaries) == 1
    assert core_warnings(caplog) == []


def test_a_due_check_in_is_sent(
    client: TestClient,
    auth_verifier: Any,
    chat_channel: FakeChatChannel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    clock.advance(ONE_DAY)
    with caplog.at_level(logging.WARNING):
        scheduler.tick()

    assert len(chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)) == 1
    assert core_warnings(caplog) == []
