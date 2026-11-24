from typing import Any

import pytest

from companion.core.models import Setting
from companion.core.platform_settings import (
    AVAILABLE_MODELS,
    CHECK_IN_THINKING,
    CORE_SERVICES,
    CURIOSITY_KEEPING_THINKING,
    KNOWLEDGE_WHEN_IT_HELPS_THINKING,
    LIFE_THREAD_KEEPING_THINKING,
    MEMORY_PROCESSING_THINKING,
    MOVE_OUTCOME_KEEPING_THINKING,
    PATTERN_KEEPING_THINKING,
    PATTERN_TAGGING_THINKING,
    PERSONAL_STICKER_KEEPING_THINKING,
    PHOTO_THINKING,
    PORTRAIT_THINKING,
    REPLY_PLAN_THINKING,
    RESPONSE_THINKING,
    SAFEGUARD_THINKING,
    UNDERSTANDING_THINKING,
)

CURRENT_MODEL = "deepseek/deepseek-v4.1-flash-1017"
PRO_MODEL = "deepseek/deepseek-v4-pro-0813"

THINKING_CALLS: list[Setting[bool]] = [
    UNDERSTANDING_THINKING,
    REPLY_PLAN_THINKING,
    SAFEGUARD_THINKING,
    MEMORY_PROCESSING_THINKING,
    LIFE_THREAD_KEEPING_THINKING,
    PORTRAIT_THINKING,
    CURIOSITY_KEEPING_THINKING,
    MOVE_OUTCOME_KEEPING_THINKING,
    PATTERN_KEEPING_THINKING,
    PATTERN_TAGGING_THINKING,
    CHECK_IN_THINKING,
]

NOT_THINKING_CALLS: list[Setting[bool]] = [
    RESPONSE_THINKING,
    KNOWLEDGE_WHEN_IT_HELPS_THINKING,
    PERSONAL_STICKER_KEEPING_THINKING,
    PHOTO_THINKING,
]


def test_the_current_model_and_the_pro_model_are_the_ones_to_pick(
    seeded_settings: dict[str, Any],
) -> None:
    assert seeded_settings[AVAILABLE_MODELS.key] == [CURRENT_MODEL, PRO_MODEL]


@pytest.mark.parametrize(
    "service", CORE_SERVICES, ids=lambda service: service.model_key
)
def test_every_call_starts_on_the_current_model(
    service: Any, seeded_settings: dict[str, Any]
) -> None:
    assert seeded_settings[service.model_key] == CURRENT_MODEL


@pytest.mark.parametrize("setting", THINKING_CALLS, ids=lambda setting: setting.key)
def test_calls_that_make_judgments_start_with_thinking_on(
    setting: Setting[bool], seeded_settings: dict[str, Any]
) -> None:
    assert seeded_settings[setting.key] is True


@pytest.mark.parametrize("setting", NOT_THINKING_CALLS, ids=lambda setting: setting.key)
def test_other_calls_start_with_thinking_off(
    setting: Setting[bool], seeded_settings: dict[str, Any]
) -> None:
    assert seeded_settings[setting.key] is False


def test_every_core_service_has_a_thinking_setting() -> None:
    assert len(THINKING_CALLS + NOT_THINKING_CALLS) == len(CORE_SERVICES)
    assert {setting.key for setting in THINKING_CALLS + NOT_THINKING_CALLS} == {
        service.thinking_key for service in CORE_SERVICES
    }
