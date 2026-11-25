import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.core.models import PlatformSettings
from companion.core.platform_settings import (
    RESPONSE_MODEL,
    RESPONSE_THINKING,
    model_thinks,
    thinking_to_use,
)
from tests.fakes import FakeAuthVerifier, FakeChatChannel, ScriptedChatModel
from tests.telegram_helpers import (
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_conversation import set_platform_setting
from tests.test_thinking_only_when_the_model_can_think import saved_values

MODEL_THAT_CAN_THINK_OR_NOT = "anthropic/claude-haiku-5.5"
MODEL_THAT_ALWAYS_THINKS = "anthropic/claude-sonnet-5.5"
MODEL_THAT_CANT_THINK = "deepseek/deepseek-v4-pro-0813"
MODELS_THAT_ALWAYS_THINK = [
    "anthropic/claude-sonnet-5.5",
    "anthropic/claude-opus-5.5",
    "anthropic/claude-fable-5.2",
]


def settings_with(model: str, thinking: bool) -> PlatformSettings:
    """Make platform settings where one model always thinks and one can't.

    Args:
        model: The model Response composition uses.
        thinking: Whether its thinking is saved as on.

    Returns:
        The settings.
    """
    return PlatformSettings(
        {
            "models_that_always_think": [MODEL_THAT_ALWAYS_THINKS],
            "models_that_cannot_think": [MODEL_THAT_CANT_THINK],
            "response_model": model,
            "response_thinking": thinking,
        }
    )


def test_a_model_that_always_thinks_thinks_with_its_switch_off() -> None:
    settings = settings_with(MODEL_THAT_ALWAYS_THINKS, thinking=False)

    assert thinking_to_use(settings, RESPONSE_MODEL, RESPONSE_THINKING) is True


@pytest.mark.parametrize("thinking", [True, False])
def test_a_model_that_can_think_or_not_follows_its_switch(thinking: bool) -> None:
    settings = settings_with(MODEL_THAT_CAN_THINK_OR_NOT, thinking=thinking)

    assert thinking_to_use(settings, RESPONSE_MODEL, RESPONSE_THINKING) is thinking


@pytest.mark.parametrize(
    ("model", "wanted", "thinks"),
    [
        (MODEL_THAT_ALWAYS_THINKS, False, True),
        (MODEL_THAT_ALWAYS_THINKS, True, True),
        (MODEL_THAT_CANT_THINK, True, False),
        (MODEL_THAT_CAN_THINK_OR_NOT, False, False),
        (MODEL_THAT_CAN_THINK_OR_NOT, True, True),
    ],
)
def test_a_call_that_names_its_own_thinking_is_fitted_to_its_model(
    model: str, wanted: bool, thinks: bool
) -> None:
    settings = settings_with(MODEL_THAT_CAN_THINK_OR_NOT, thinking=False)

    assert model_thinks(settings, model, wanted) is thinks


def test_core_services_say_which_models_always_think(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.get("/api/admin/core-services", headers=headers).json()

    assert response["models_that_always_think"] == MODELS_THAT_ALWAYS_THINK


def test_thinking_cant_be_turned_off_with_a_model_that_always_thinks(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    set_platform_setting(engine, "response_thinking", True)
    saved_model = saved_values(client, headers)["response_model"]

    response = client.patch(
        "/api/admin/settings",
        json={
            "values": {
                "response_model": MODEL_THAT_ALWAYS_THINKS,
                "response_thinking": False,
            }
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "The Response composition thinking can't be off: "
        f"{MODEL_THAT_ALWAYS_THINKS} always thinks."
    )
    saved = saved_values(client, headers)
    assert saved["response_model"] == saved_model
    assert saved["response_thinking"] is True


def test_thinking_cant_be_turned_off_when_the_saved_model_always_thinks(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    set_platform_setting(engine, "response_model", MODEL_THAT_ALWAYS_THINKS)
    set_platform_setting(engine, "response_thinking", True)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"response_thinking": False}},
        headers=headers,
    )

    assert response.status_code == 422
    assert saved_values(client, headers)["response_thinking"] is True


def test_changing_to_a_model_that_always_thinks_saves_thinking_as_on(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    assert saved_values(client, headers)["response_thinking"] is False

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"response_model": MODEL_THAT_ALWAYS_THINKS}},
        headers=headers,
    )

    assert response.status_code == 200
    settings = response.json()["settings"]
    assert settings["response_model"]["value"] == MODEL_THAT_ALWAYS_THINKS
    assert settings["response_thinking"]["value"] is True
    assert settings["response_thinking"]["updated_by"] == "owner@example.com"
    assert settings["photo_thinking"]["updated_by"] is None


def test_thinking_already_on_is_not_saved_again_for_a_model_that_always_thinks(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    set_platform_setting(engine, "response_thinking", True)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"response_model": MODEL_THAT_ALWAYS_THINKS}},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["settings"]["response_thinking"]["updated_by"] is None


def test_thinking_can_be_turned_off_with_a_model_that_can_think_or_not(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    set_platform_setting(engine, "response_model", MODEL_THAT_ALWAYS_THINKS)
    set_platform_setting(engine, "response_thinking", True)

    response = client.patch(
        "/api/admin/settings",
        json={
            "values": {
                "response_model": MODEL_THAT_CAN_THINK_OR_NOT,
                "response_thinking": False,
            }
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert saved_values(client, headers)["response_thinking"] is False


def test_a_call_for_a_model_that_always_thinks_is_never_told_thinking_is_off(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    set_platform_setting(engine, "response_model", MODEL_THAT_ALWAYS_THINKS)
    set_platform_setting(engine, "response_thinking", False)
    chat_model.script("ok")

    send_to_webhook(client, telegram_text_update("hello"))

    [call] = chat_model.calls
    assert call.model == MODEL_THAT_ALWAYS_THINKS
    assert call.thinking is True
