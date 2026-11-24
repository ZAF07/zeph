import base64
import json
from typing import Any

import httpx
import pytest

from companion.adapters.openrouter.chat_model import OpenRouterReplyError
from companion.adapters.openrouter.photo_viewer import OpenRouterPhotoViewer
from companion.core.models import ModelAnswer, PhotoImage

PHOTO = PhotoImage(content=b"png-bytes", media_type="image/png")


def openrouter_reply(
    content: str = "A handwritten list.", reasoning: str | None = None
) -> dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                    "reasoning": reasoning,
                }
            }
        ],
        "usage": {"prompt_tokens": 310, "completion_tokens": 9},
    }


def openrouter_with(
    response: httpx.Response, requests: list[httpx.Request]
) -> OpenRouterPhotoViewer:
    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response

    return OpenRouterPhotoViewer(
        "sk-or-test", http_client=httpx.Client(transport=httpx.MockTransport(handle))
    )


def look(photo_viewer: OpenRouterPhotoViewer, thinking: bool = False) -> ModelAnswer:
    return photo_viewer.look(
        model="deepseek/deepseek-v4.1-flash-1017",
        thinking=thinking,
        instructions="Describe the photo.",
        photo=PHOTO,
    )


def test_the_photo_goes_as_a_data_url_in_a_user_message_after_the_instructions() -> (
    None
):
    requests: list[httpx.Request] = []
    photo_viewer = openrouter_with(
        httpx.Response(200, json=openrouter_reply()), requests
    )

    look(photo_viewer)

    [request] = requests
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer sk-or-test"
    data_url = "data:image/png;base64," + base64.b64encode(b"png-bytes").decode()
    assert json.loads(request.content)["messages"] == [
        {"role": "system", "content": "Describe the photo."},
        {
            "role": "user",
            "content": [{"type": "image_url", "image_url": {"url": data_url}}],
        },
    ]


def test_the_data_url_carries_the_photos_media_type() -> None:
    requests: list[httpx.Request] = []
    photo_viewer = openrouter_with(
        httpx.Response(200, json=openrouter_reply()), requests
    )

    photo_viewer.look(
        model="deepseek/deepseek-v4.1-flash-1017",
        thinking=False,
        instructions="Describe the photo.",
        photo=PhotoImage(content=b"jpeg-bytes", media_type="image/jpeg"),
    )

    [image_part] = json.loads(requests[0].content)["messages"][1]["content"]
    assert image_part["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_the_model_name_is_sent_as_given_to_its_maker_only_with_no_tools() -> None:
    requests: list[httpx.Request] = []
    photo_viewer = openrouter_with(
        httpx.Response(200, json=openrouter_reply()), requests
    )

    photo_viewer.look(
        model="anthropic/claude-haiku-5.5",
        thinking=False,
        instructions="Describe the photo.",
        photo=PHOTO,
    )

    body = json.loads(requests[0].content)
    assert body["model"] == "anthropic/claude-haiku-5.5"
    assert body["provider"] == {"only": ["anthropic"]}
    assert "tools" not in body


@pytest.mark.parametrize("thinking", [True, False])
def test_the_thinking_switch_becomes_reasoning_enabled(thinking: bool) -> None:
    requests: list[httpx.Request] = []
    photo_viewer = openrouter_with(
        httpx.Response(200, json=openrouter_reply()), requests
    )

    look(photo_viewer, thinking=thinking)

    assert json.loads(requests[0].content)["reasoning"] == {"enabled": thinking}


def test_the_text_tokens_and_reasoning_are_returned() -> None:
    photo_viewer = openrouter_with(
        httpx.Response(
            200, json=openrouter_reply("Milk, eggs.", reasoning="It is a list.")
        ),
        [],
    )

    answer = look(photo_viewer, thinking=True)

    assert answer == ModelAnswer(
        text="Milk, eggs.", tokens_in=310, tokens_out=9, reasoning="It is a list."
    )


def test_no_reasoning_in_the_reply_gives_none() -> None:
    photo_viewer = openrouter_with(httpx.Response(200, json=openrouter_reply()), [])

    assert look(photo_viewer).reasoning is None


def test_an_error_status_is_raised() -> None:
    photo_viewer = openrouter_with(
        httpx.Response(402, json={"error": {"message": "no credits"}}), []
    )

    with pytest.raises(httpx.HTTPStatusError):
        look(photo_viewer)


def test_an_error_body_is_raised_as_a_clear_error() -> None:
    photo_viewer = openrouter_with(
        httpx.Response(200, json={"error": {"message": "provider down"}}), []
    )

    with pytest.raises(OpenRouterReplyError, match="provider down"):
        look(photo_viewer)


def test_an_error_inside_the_choice_is_raised_as_a_clear_error() -> None:
    photo_viewer = openrouter_with(
        httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": ""},
                        "finish_reason": "error",
                        "error": {"message": "Provider returned error"},
                    }
                ]
            },
        ),
        [],
    )

    with pytest.raises(OpenRouterReplyError, match="Provider returned error"):
        look(photo_viewer)
