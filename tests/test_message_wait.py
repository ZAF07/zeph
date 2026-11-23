from typing import Any

import pytest
from fastapi.testclient import TestClient

from companion.core.incoming_messages import MESSAGE_WAIT_PREFIX
from tests.fakes import FakeAuthVerifier, FakeChatChannel, FakeTimer
from tests.telegram_helpers import (
    connect_telegram,
    owner_headers,
    post_to_webhook,
    telegram_photo_update,
    telegram_sticker_update,
    telegram_text_update,
)
from tests.test_web_search import change_settings

FINISHED_WAIT = 3
TRAILING_WAIT = 13
NEITHER_WAIT = 7

WAIT_SETTINGS = {
    "message_wait_finished_seconds": FINISHED_WAIT,
    "message_wait_trailing_seconds": TRAILING_WAIT,
    "message_wait_seconds": NEITHER_WAIT,
    "message_wait_long_text_words": 15,
    "message_wait_trailing_words": ["and", "but", "so", "wait", "ok so", "lol"],
}

FOURTEEN_WORDS = "i finally told my boss that the new schedule is not working for me"
FIFTEEN_WORDS = f"{FOURTEEN_WORDS} anymore"


def message_waits(timer: FakeTimer) -> list[float]:
    """List the seconds of each Message wait started, in order."""
    return [
        seconds for key, seconds in timer.waits if key.startswith(MESSAGE_WAIT_PREFIX)
    ]


@pytest.fixture
def wait_settings(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
) -> dict[str, str]:
    """Connect the User and give each kind of wait its own length."""
    admin = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    change_settings(client, admin, WAIT_SETTINGS)
    return admin


@pytest.mark.parametrize(
    "text",
    [
        "what do you think I should do?",
        "you there?   ",
        f"{FIFTEEN_WORDS}.",
        f"{FIFTEEN_WORDS}!",
        f"{FIFTEEN_WORDS} 😂",
        f"{FIFTEEN_WORDS} ❤️",
        f"{FIFTEEN_WORDS} 👍🏽",
    ],
)
def test_a_text_that_reads_finished_gets_the_finished_wait(
    client: TestClient, timer: FakeTimer, wait_settings: dict[str, str], text: str
) -> None:
    assert post_to_webhook(client, telegram_text_update(text)) == 200

    assert message_waits(timer) == [FINISHED_WAIT]


@pytest.mark.parametrize(
    "text",
    [
        "and then...",
        "so…",
        "i went to the shop,",
        "it was fine but",
        "it was fine BUT  ",
        "wait",
        "ok so",
        "OK So  ",
        f"{FIFTEEN_WORDS}...",
    ],
)
def test_a_text_that_trails_off_gets_the_trailing_wait(
    client: TestClient, timer: FakeTimer, wait_settings: dict[str, str], text: str
) -> None:
    assert post_to_webhook(client, telegram_text_update(text)) == 200

    assert message_waits(timer) == [TRAILING_WAIT]


@pytest.mark.parametrize(
    "text",
    [
        "hey",
        f"{FOURTEEN_WORDS}.",
        "so what",
        "lol ok",
        f"{FIFTEEN_WORDS} honestly",
        f"{FIFTEEN_WORDS} at 30°",
        f"{FIFTEEN_WORDS} ™",
    ],
)
def test_any_other_text_gets_the_neither_wait(
    client: TestClient, timer: FakeTimer, wait_settings: dict[str, str], text: str
) -> None:
    assert post_to_webhook(client, telegram_text_update(text)) == 200

    assert message_waits(timer) == [NEITHER_WAIT]


@pytest.mark.parametrize(
    ("update", "wait"),
    [
        (telegram_photo_update(), TRAILING_WAIT),
        (telegram_photo_update("my cat"), NEITHER_WAIT),
        (telegram_photo_update("is she cute?"), FINISHED_WAIT),
        (telegram_sticker_update(), NEITHER_WAIT),
    ],
)
def test_a_photo_or_sticker_gets_the_wait_its_caption_reads_as(
    client: TestClient,
    timer: FakeTimer,
    wait_settings: dict[str, str],
    update: dict[str, Any],
    wait: int,
) -> None:
    assert post_to_webhook(client, update) == 200

    assert message_waits(timer) == [wait]


def test_each_text_restarts_the_wait_with_how_that_text_reads(
    client: TestClient, timer: FakeTimer, wait_settings: dict[str, str]
) -> None:
    for text in ("hey", "so", "how are you?"):
        assert post_to_webhook(client, telegram_text_update(text)) == 200

    assert message_waits(timer) == [NEITHER_WAIT, TRAILING_WAIT, FINISHED_WAIT]


@pytest.mark.parametrize(
    ("caption", "wait"),
    [(None, TRAILING_WAIT), ("is this ok?", FINISHED_WAIT)],
)
def test_an_album_is_judged_as_one_text_as_each_photo_arrives(
    client: TestClient,
    timer: FakeTimer,
    wait_settings: dict[str, str],
    caption: str | None,
    wait: int,
) -> None:
    for number in (1, 2, 3):
        update = telegram_photo_update(
            caption if number == 1 else None,
            file_unique_id=f"photo-{number}",
            album_id="album-1",
            message_id=number,
        )
        assert post_to_webhook(client, update) == 200

    assert message_waits(timer) == [wait, wait, wait]


def test_a_changed_wait_applies_from_the_next_text(
    client: TestClient, timer: FakeTimer, wait_settings: dict[str, str]
) -> None:
    assert post_to_webhook(client, telegram_text_update("and")) == 200
    change_settings(
        client,
        wait_settings,
        {"message_wait_trailing_seconds": 20, "message_wait_trailing_words": ["hmm"]},
    )
    for text in ("hmm", "and"):
        assert post_to_webhook(client, telegram_text_update(text)) == 200

    assert message_waits(timer) == [TRAILING_WAIT, 20, NEITHER_WAIT]
