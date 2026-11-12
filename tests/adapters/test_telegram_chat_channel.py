import json
from collections.abc import Callable

import httpx

from companion.adapters.telegram.chat_channel import TelegramChatChannel
from companion.core.models import ChannelSticker, StickerImage


def test_typing_is_shown_with_a_chat_action() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def telegram_api(request: httpx.Request) -> httpx.Response:
        method = request.url.path.rsplit("/", 1)[-1]
        calls.append((method, json.loads(request.content)))
        return httpx.Response(200, json={"ok": True, "result": {}})

    channel = TelegramChatChannel(
        "123:abc",
        http_client=httpx.Client(transport=httpx.MockTransport(telegram_api)),
    )

    channel.show_typing(42)

    assert calls == [("sendChatAction", {"chat_id": 42, "action": "typing"})]


def channel_answering(
    answer: Callable[[str, dict[str, object]], httpx.Response],
    calls: list[tuple[str, dict[str, object]]],
) -> TelegramChatChannel:
    """Build a channel whose Bot API calls are recorded and answered by a test."""

    def telegram_api(request: httpx.Request) -> httpx.Response:
        method = request.url.path.rsplit("/", 1)[-1]
        body = json.loads(request.content) if request.content else {}
        calls.append((method, body))
        return answer(request.url.path, body)

    return TelegramChatChannel(
        "123:abc",
        http_client=httpx.Client(transport=httpx.MockTransport(telegram_api)),
    )


def ok(result: object) -> httpx.Response:
    """A successful Bot API answer."""
    return httpx.Response(200, json={"ok": True, "result": result})


def test_a_sticker_is_sent_by_its_file_id() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    channel = channel_answering(lambda path, body: ok({}), calls)

    channel.send_sticker(42, "file-seedling")

    assert calls == [("sendSticker", {"chat_id": 42, "sticker": "file-seedling"})]


def test_a_sticker_set_is_read_with_an_image_for_each_sticker() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    still = {
        "file_id": "f1",
        "file_unique_id": "u1",
        "emoji": "🌱",
        "set_name": "CalmCreatures",
        "is_animated": False,
        "is_video": False,
        "thumbnail": {"file_id": "t1"},
    }
    animated = {
        "file_id": "f2",
        "file_unique_id": "u2",
        "emoji": "🌙",
        "set_name": "CalmCreatures",
        "is_animated": True,
        "is_video": False,
        "thumbnail": {"file_id": "t2"},
    }
    video_without_thumbnail = {
        "file_id": "f3",
        "file_unique_id": "u3",
        "is_animated": False,
        "is_video": True,
    }
    sticker_set = {
        "name": "CalmCreatures",
        "stickers": [still, animated, video_without_thumbnail],
    }
    channel = channel_answering(lambda path, body: ok(sticker_set), calls)

    stickers = channel.get_sticker_set("CalmCreatures")

    assert calls == [("getStickerSet", {"name": "CalmCreatures"})]
    assert stickers == [
        ChannelSticker("f1", "u1", "🌱", "CalmCreatures", "f1"),
        ChannelSticker("f2", "u2", "🌙", "CalmCreatures", "t2"),
        ChannelSticker("f3", "u3", None, None, None),
    ]


def test_an_unknown_sticker_set_is_none() -> None:
    channel = channel_answering(
        lambda path, body: httpx.Response(
            400, json={"ok": False, "description": "Bad Request: STICKERSET_INVALID"}
        ),
        [],
    )

    assert channel.get_sticker_set("NoSuchSet") is None


def test_a_sticker_image_is_downloaded_with_its_media_type() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def answer(path: str, body: dict[str, object]) -> httpx.Response:
        if path.endswith("/getFile"):
            return ok({"file_id": "f1", "file_path": "stickers/file_7.webp"})
        assert path == "/file/bot123:abc/stickers/file_7.webp"
        return httpx.Response(200, content=b"webp-bytes")

    channel = channel_answering(answer, calls)

    image = channel.get_sticker_image("f1")

    assert image == StickerImage(content=b"webp-bytes", media_type="image/webp")
    assert calls[0] == ("getFile", {"file_id": "f1"})


def test_a_sticker_file_that_is_not_an_image_has_no_image() -> None:
    channel = channel_answering(
        lambda path, body: ok({"file_id": "f2", "file_path": "stickers/file_8.tgs"}),
        [],
    )

    assert channel.get_sticker_image("f2") is None
