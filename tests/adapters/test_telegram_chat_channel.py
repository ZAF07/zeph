import json

import httpx

from companion.adapters.telegram.chat_channel import TelegramChatChannel


def test_several_messages_are_sent_with_typing_between_them() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    pauses: list[float] = []

    def telegram_api(request: httpx.Request) -> httpx.Response:
        method = request.url.path.rsplit("/", 1)[-1]
        calls.append((method, json.loads(request.content)))
        return httpx.Response(200, json={"ok": True, "result": {}})

    channel = TelegramChatChannel(
        "123:abc",
        http_client=httpx.Client(transport=httpx.MockTransport(telegram_api)),
        sleep=pauses.append,
    )

    channel.send_texts(42, ["oh no", "what happened?"])

    assert calls == [
        ("sendMessage", {"chat_id": 42, "text": "oh no"}),
        ("sendChatAction", {"chat_id": 42, "action": "typing"}),
        ("sendMessage", {"chat_id": 42, "text": "what happened?"}),
    ]
    assert len(pauses) == 1
    assert pauses[0] > 0
