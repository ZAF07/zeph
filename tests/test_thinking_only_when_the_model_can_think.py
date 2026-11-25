from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine

import companion.core
from companion.core.models import PlatformSettings
from companion.core.platform_settings import (
    RESPONSE_MODEL,
    RESPONSE_THINKING,
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

THINKS = "deepseek/deepseek-v4.1-flash-1017"
CANT_THINK = "deepseek/deepseek-v4-pro-0813"


def settings_with(model: str, thinking: bool) -> PlatformSettings:
    """Make platform settings where one listed model can't think.

    Args:
        model: The model Response composition uses.
        thinking: Whether its thinking is saved as on.

    Returns:
        The settings.
    """
    return PlatformSettings(
        {
            "models_that_cannot_think": [CANT_THINK],
            "response_model": model,
            "response_thinking": thinking,
        }
    )


def saved_values(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    """Read each editable setting's saved value.

    Args:
        client: The test client.
        headers: An Admin's headers.

    Returns:
        The value of each setting, by key.
    """
    settings = client.get("/api/admin/settings", headers=headers).json()["settings"]
    return {key: setting["value"] for key, setting in settings.items()}


def test_a_model_that_can_think_thinks_when_its_switch_is_on() -> None:
    settings = settings_with(THINKS, thinking=True)

    assert thinking_to_use(settings, RESPONSE_MODEL, RESPONSE_THINKING) is True


def test_a_model_that_can_think_does_not_think_when_its_switch_is_off() -> None:
    settings = settings_with(THINKS, thinking=False)

    assert thinking_to_use(settings, RESPONSE_MODEL, RESPONSE_THINKING) is False


def test_a_model_that_cant_think_never_thinks() -> None:
    settings = settings_with(CANT_THINK, thinking=True)

    assert thinking_to_use(settings, RESPONSE_MODEL, RESPONSE_THINKING) is False


def test_every_listed_model_can_think_to_begin_with(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.get("/api/admin/core-services", headers=headers).json()

    assert response["models_that_cannot_think"] == []


def test_core_services_say_which_models_cant_think(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    set_platform_setting(engine, "models_that_cannot_think", [CANT_THINK])

    response = client.get("/api/admin/core-services", headers=headers).json()

    assert response["models_that_cannot_think"] == [CANT_THINK]


def test_thinking_cant_be_turned_on_with_a_model_that_cant_think(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    set_platform_setting(engine, "models_that_cannot_think", [CANT_THINK])

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"response_model": CANT_THINK, "response_thinking": True}},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        f"The Response composition thinking can't be on: {CANT_THINK} can't think."
    )
    saved = saved_values(client, headers)
    assert saved["response_model"] == THINKS
    assert saved["response_thinking"] is False


def test_thinking_cant_be_turned_on_when_the_saved_model_cant_think(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    set_platform_setting(engine, "models_that_cannot_think", [CANT_THINK])
    set_platform_setting(engine, "response_model", CANT_THINK)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"response_thinking": True}},
        headers=headers,
    )

    assert response.status_code == 422
    assert saved_values(client, headers)["response_thinking"] is False


def test_changing_to_a_model_that_cant_think_saves_thinking_as_off(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    set_platform_setting(engine, "models_that_cannot_think", [CANT_THINK])
    set_platform_setting(engine, "response_thinking", True)
    set_platform_setting(engine, "safeguard_thinking", True)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"response_model": CANT_THINK}},
        headers=headers,
    )

    assert response.status_code == 200
    saved = saved_values(client, headers)
    assert saved["response_model"] == CANT_THINK
    assert saved["response_thinking"] is False
    assert saved["safeguard_thinking"] is True


def test_thinking_off_can_be_saved_with_a_model_that_cant_think(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    set_platform_setting(engine, "models_that_cannot_think", [CANT_THINK])

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"response_model": CANT_THINK, "response_thinking": False}},
        headers=headers,
    )

    assert response.status_code == 200
    assert saved_values(client, headers)["response_model"] == CANT_THINK


def test_thinking_can_be_turned_on_with_a_model_that_can_think(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)
    set_platform_setting(engine, "models_that_cannot_think", [CANT_THINK])
    set_platform_setting(engine, "response_model", CANT_THINK)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"response_model": THINKS, "response_thinking": True}},
        headers=headers,
    )

    assert response.status_code == 200
    assert saved_values(client, headers)["response_thinking"] is True


def test_a_call_for_a_model_that_cant_think_is_made_with_thinking_off(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    set_platform_setting(engine, "models_that_cannot_think", [CANT_THINK])
    set_platform_setting(engine, "response_model", CANT_THINK)
    set_platform_setting(engine, "response_thinking", True)
    chat_model.script("ok")

    send_to_webhook(client, telegram_text_update("hello"))

    [call] = chat_model.calls
    assert call.model == CANT_THINK
    assert call.thinking is False


def test_every_core_service_asks_whether_its_model_should_think() -> None:
    """Check no core module reads a thinking switch straight from the settings.

    The core services live in many modules, so their source is checked: each
    call must go through `thinking_to_use`.
    """
    core_modules = Path(companion.core.__file__).parent.rglob("*.py")

    for module in core_modules:
        assert "thinking=settings.get(" not in module.read_text(), module.name
