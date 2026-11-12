from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from companion.core.models import StoredSetting, User
from companion.core.ports import Clock, PlatformSettingsRepository
from companion.core.safeguard import HELPLINES_PLACEHOLDER

MODEL_CHOICES_KEY = "available_models"


class SettingKind(StrEnum):
    """What kind of value a setting holds, which decides how it is checked."""

    TEXT = "text"
    WHOLE_NUMBER = "whole_number"
    MODEL = "model"
    ON_OFF = "on_off"


@dataclass(frozen=True)
class EditableSetting:
    """A platform setting Admins may change, and the rule its value must meet.

    Attributes:
        key: The setting's key.
        label: The setting's name, as Admins see it.
        kind: What kind of value it holds.
        minimum: The smallest allowed whole number.
        maximum: The largest allowed whole number.
        max_length: The longest allowed text.
        required_placeholder: A placeholder the text must keep, e.g.
            "{helplines}"; None if there is none.
        placeholder_meaning: What the placeholder stands for, as Admins are
            told when it is missing.
    """

    key: str
    label: str
    kind: SettingKind
    minimum: int = 0
    maximum: int = 0
    max_length: int = 20_000
    required_placeholder: str | None = None
    placeholder_meaning: str = ""


@dataclass(frozen=True)
class CoreService:
    """A core service whose prompt and model Admins can change.

    Attributes:
        name: The service's name, as Admins see it.
        runs_when: When the service runs.
        description: What the service does.
        prompt_key: The setting holding its prompt.
        model_key: The setting holding the model it uses.
    """

    name: str
    runs_when: str
    description: str
    prompt_key: str
    model_key: str


EDITABLE_SETTINGS: tuple[EditableSetting, ...] = (
    EditableSetting("persona", "Persona", SettingKind.TEXT),
    EditableSetting("safeguard_prompt", "Safeguard prompt", SettingKind.TEXT),
    EditableSetting("safeguard_model", "Safeguard model", SettingKind.MODEL),
    EditableSetting(
        "crisis_reply",
        "Crisis Reply",
        SettingKind.TEXT,
        max_length=4_000,
        required_placeholder=HELPLINES_PLACEHOLDER,
        placeholder_meaning="where the Helplines go",
    ),
    EditableSetting("response_prompt", "Response composition prompt", SettingKind.TEXT),
    EditableSetting("response_model", "Response composition model", SettingKind.MODEL),
    EditableSetting(
        "memory_processing_prompt",
        "Post-conversation processing prompt",
        SettingKind.TEXT,
    ),
    EditableSetting(
        "memory_processing_model",
        "Post-conversation processing model",
        SettingKind.MODEL,
    ),
    EditableSetting(
        "memory_retrieval_prompt", "Memory retrieval prompt", SettingKind.TEXT
    ),
    EditableSetting(
        "memory_retrieval_model", "Memory retrieval model", SettingKind.MODEL
    ),
    EditableSetting("check_in_prompt", "Check-in prompt", SettingKind.TEXT),
    EditableSetting("check_in_model", "Check-in model", SettingKind.MODEL),
    EditableSetting(
        "check_in_ignore_threshold",
        "Ignore threshold",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=10,
    ),
    EditableSetting(
        "check_in_fewer_message",
        "“Would you like fewer?” message",
        SettingKind.TEXT,
        max_length=1_000,
    ),
    EditableSetting(
        "conversation_quiet_gap_minutes",
        "Conversation quiet gap",
        SettingKind.WHOLE_NUMBER,
        minimum=5,
        maximum=1440,
    ),
    EditableSetting(
        "daily_message_limit",
        "Daily message limit",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=10_000,
    ),
    EditableSetting(
        "daily_limit_reply",
        "Limit-reached reply",
        SettingKind.TEXT,
        max_length=1_000,
    ),
    EditableSetting("web_search_enabled", "Web search", SettingKind.ON_OFF),
    EditableSetting(
        "web_search_daily_limit",
        "Per-user daily web search limit",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=1000,
    ),
    EditableSetting("ai_notice", "AI notice", SettingKind.TEXT, max_length=2_000),
    EditableSetting(
        "ai_notice_short", "Short AI notice", SettingKind.TEXT, max_length=200
    ),
    EditableSetting(
        "user_memory_explanation",
        "Memory explanation",
        SettingKind.TEXT,
        max_length=4_000,
    ),
)

CORE_SERVICES: tuple[CoreService, ...] = (
    CoreService(
        name="Safeguard",
        runs_when="Every incoming message, first",
        description=(
            "Checks each message for crisis. On a crisis Zeph sends the Crisis "
            "Reply with Helplines instead of a normal reply."
        ),
        prompt_key="safeguard_prompt",
        model_key="safeguard_model",
    ),
    CoreService(
        name="Response composition",
        runs_when="Every reply",
        description=(
            "Writes Zeph’s reply from the Persona, the relevant memories, recent "
            "Conversation Summaries, Knowledge and the Conversation so far."
        ),
        prompt_key="response_prompt",
        model_key="response_model",
    ),
    CoreService(
        name="Post-conversation processing",
        runs_when="After quiet gap",
        description=(
            "After a Conversation goes quiet, writes the Conversation Summary "
            "and mood, and adds, updates or removes Memory Items by category."
        ),
        prompt_key="memory_processing_prompt",
        model_key="memory_processing_model",
    ),
    CoreService(
        name="Memory retrieval",
        runs_when="Every reply",
        description=(
            "Picks the Memory Categories that matter for the message, so the "
            "reply gets only relevant memories plus the always-included ones."
        ),
        prompt_key="memory_retrieval_prompt",
        model_key="memory_retrieval_model",
    ),
    CoreService(
        name="Check-ins",
        runs_when="Scheduler tick, for Users who are due",
        description=(
            "Decides whether to reach out to a User who opted in, which "
            "Check-in Kind to use and what to say, or to skip and give space, "
            "from their recent Conversation Summaries and Memory Items."
        ),
        prompt_key="check_in_prompt",
        model_key="check_in_model",
    ),
)


class InvalidSettingError(ValueError):
    """Raised when a setting change is not allowed or its value is not valid."""


class PlatformSettingsService:
    """Lets Admins read and change the platform settings they manage.

    Every core service reads its settings when it runs, so a saved change
    applies to the next message without a restart (ADR-0004).
    """

    def __init__(self, settings: PlatformSettingsRepository, clock: Clock) -> None:
        """Set up the service.

        Args:
            settings: Where platform settings are stored.
            clock: Tells the current time.
        """
        self._settings = settings
        self._clock = clock
        self._editable_by_key = {setting.key: setting for setting in EDITABLE_SETTINGS}

    def list_editable(self) -> list[StoredSetting]:
        """Read every setting Admins may change.

        Returns:
            The settings with when and by whom they were last saved.
        """
        return self._settings.get_many(list(self._editable_by_key))

    def model_choices(self) -> list[str]:
        """List the models Admins can pick for a core service.

        Returns:
            The model names.
        """
        choices: list[str] = self._settings.get(MODEL_CHOICES_KEY)
        return choices

    def update(self, admin: User, values: Mapping[str, Any]) -> list[StoredSetting]:
        """Check and save setting changes, all together or not at all.

        Args:
            admin: The Admin making the change.
            values: The new value for each setting key.

        Returns:
            Every editable setting after the change.

        Raises:
            InvalidSettingError: If a key may not be changed or a value is not
                valid; nothing is saved.
        """
        validated_values = {
            key: self._validated_value(key, value) for key, value in values.items()
        }
        if validated_values:
            self._settings.save_many(validated_values, self._clock.now(), admin.id)
        return self.list_editable()

    def _validated_value(self, key: str, value: Any) -> Any:
        """Check one new value against its setting's rule.

        Args:
            key: The setting's key.
            value: The new value.

        Returns:
            The value to save; text has surrounding spaces removed.

        Raises:
            InvalidSettingError: If the key may not be changed or the value
                does not meet the rule.
        """
        setting = self._editable_by_key.get(key)
        if setting is None:
            raise InvalidSettingError(f"'{key}' can't be changed here.")
        if setting.kind == SettingKind.TEXT:
            if not isinstance(value, str) or not value.strip():
                raise InvalidSettingError(f"The {setting.label} needs some text.")
            if len(value) > setting.max_length:
                raise InvalidSettingError(
                    f"The {setting.label} must be at most "
                    f"{setting.max_length} characters."
                )
            placeholder = setting.required_placeholder
            if placeholder is not None and placeholder not in value:
                raise InvalidSettingError(
                    f"The {setting.label} must include {placeholder}, "
                    f"{setting.placeholder_meaning}."
                )
            return value.strip()
        if setting.kind == SettingKind.WHOLE_NUMBER:
            is_whole_number = isinstance(value, int) and not isinstance(value, bool)
            if not is_whole_number or not setting.minimum <= value <= setting.maximum:
                raise InvalidSettingError(
                    f"The {setting.label} must be a whole number from "
                    f"{setting.minimum} to {setting.maximum}."
                )
            return value
        if setting.kind == SettingKind.ON_OFF:
            if not isinstance(value, bool):
                raise InvalidSettingError(f"{setting.label} must be on or off.")
            return value
        if value not in self.model_choices():
            raise InvalidSettingError(
                f"The {setting.label} must be one of the listed models."
            )
        return value
