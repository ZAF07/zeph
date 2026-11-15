from typing import Any

import pytest

from companion.core.models import Setting
from companion.core.platform_settings import (
    CHECK_IN_MODEL,
    CURIOSITY_KEEPING_MODEL,
    KNOWLEDGE_WHEN_IT_HELPS_MODEL,
    LIFE_THREAD_KEEPING_MODEL,
    MEMORY_PROCESSING_MODEL,
    PERSONAL_STICKER_KEEPING_MODEL,
    PHOTO_MODEL,
    PORTRAIT_MODEL,
    RESPONSE_MODEL,
    SAFEGUARD_MODEL,
    UNDERSTANDING_MODEL,
)

REASONING_CALLS: list[Setting[str]] = [
    UNDERSTANDING_MODEL,
    SAFEGUARD_MODEL,
    MEMORY_PROCESSING_MODEL,
    LIFE_THREAD_KEEPING_MODEL,
    PORTRAIT_MODEL,
    CURIOSITY_KEEPING_MODEL,
    CHECK_IN_MODEL,
]

WRITING_CALLS: list[Setting[str]] = [
    RESPONSE_MODEL,
    KNOWLEDGE_WHEN_IT_HELPS_MODEL,
    PERSONAL_STICKER_KEEPING_MODEL,
    PHOTO_MODEL,
]


@pytest.mark.parametrize("setting", REASONING_CALLS, ids=lambda s: s.key)
def test_calls_that_make_judgments_default_to_the_reasoner(
    setting: Setting[str], seeded_settings: dict[str, Any]
) -> None:
    assert seeded_settings[setting.key] == "deepseek-reasoner"


@pytest.mark.parametrize("setting", WRITING_CALLS, ids=lambda s: s.key)
def test_other_calls_stay_on_the_chat_model(
    setting: Setting[str], seeded_settings: dict[str, Any]
) -> None:
    assert seeded_settings[setting.key] == "deepseek-chat"
