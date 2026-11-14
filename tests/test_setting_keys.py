from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import Engine

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core import platform_settings
from companion.core.models import CheckInFrequency, PlatformSettings, Setting
from companion.core.platform_settings import (
    CHECK_IN_GAPS,
    CONVERSATION_QUIET_GAP,
    EDITABLE_SETTINGS,
    PERSONA,
    read_check_in_gaps,
    read_number,
    read_text,
    read_text_list,
    read_whole_number,
)

TYPED_KEYS: list[Setting[Any]] = [
    value for value in vars(platform_settings).values() if isinstance(value, Setting)
]


def test_every_seeded_setting_has_one_typed_key_that_reads_its_value(
    engine: Engine, seeded_settings: dict[str, Any]
) -> None:
    settings = build_postgres_repositories(engine).platform_settings.load()

    assert sorted(key.key for key in TYPED_KEYS) == sorted(seeded_settings)
    for key in TYPED_KEYS:
        settings.get(key)


def test_every_editable_setting_has_a_typed_key() -> None:
    typed = {key.key for key in TYPED_KEYS}

    assert {setting.key for setting in EDITABLE_SETTINGS} <= typed


def test_typed_keys_read_values_into_their_types(engine: Engine) -> None:
    settings = build_postgres_repositories(engine).platform_settings.load()

    assert settings.get(CONVERSATION_QUIET_GAP) == timedelta(minutes=60)
    assert settings.get(CHECK_IN_GAPS) == {
        CheckInFrequency.WEEKLY: timedelta(hours=168),
        CheckInFrequency.FEW_TIMES_A_WEEK: timedelta(hours=56),
        CheckInFrequency.MOST_DAYS: timedelta(hours=24),
    }
    assert isinstance(settings.get(PERSONA), str)


def test_a_missing_setting_raises_key_error() -> None:
    with pytest.raises(KeyError):
        PlatformSettings({}).get(PERSONA)


@pytest.mark.parametrize(
    ("read", "wrong_value"),
    [
        (read_text, 5),
        (read_whole_number, "5"),
        (read_whole_number, True),
        (read_whole_number, 1.5),
        (read_number, "0.05"),
        (read_number, False),
        (read_text_list, "deepseek-chat"),
        (read_text_list, ["deepseek-chat", 3]),
        (read_check_in_gaps, [168, 56, 24]),
    ],
)
def test_reading_a_value_of_the_wrong_shape_fails(
    read: Any, wrong_value: object
) -> None:
    with pytest.raises(TypeError):
        read(wrong_value)


def test_check_in_gaps_need_every_frequency() -> None:
    with pytest.raises(KeyError):
        read_check_in_gaps({"weekly": 168, "most_days": 24})


def test_numbers_may_be_whole_or_not() -> None:
    assert read_number(5) == 5.0
    assert read_number(0.05) == 0.05
