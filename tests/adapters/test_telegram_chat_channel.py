import json

import httpx

from companion.adapters.telegram.chat_channel import TelegramChatChannel


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
