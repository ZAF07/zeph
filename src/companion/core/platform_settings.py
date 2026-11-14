from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from companion.core.features import FEATURES_PLACEHOLDER, UNAVAILABLE_NOTE_SETTING
from companion.core.message_retention import RETENTION_DAYS_SETTING
from companion.core.models import StoredSetting, User
from companion.core.ports import Clock, PlatformSettingsRepository
from companion.core.safeguard import HELPLINES_PLACEHOLDER
from companion.core.telegram_connection import DASHBOARD_URL_PLACEHOLDER
from companion.core.user_memory import (
    MEMORY_NOT_AVAILABLE_NOTE_SETTING,
    MEMORY_PAUSED_NOTE_SETTING,
)

MODEL_CHOICES_KEY = "available_models"


class SettingKind(StrEnum):
    """What kind of value a setting holds, which decides how it is checked."""

    TEXT = "text"
    WHOLE_NUMBER = "whole_number"
    MODEL = "model"


@dataclass(frozen=True)
class RequiredPlaceholder:
    """A placeholder a text setting must keep.

    Attributes:
        text: The placeholder, e.g. "{helplines}".
        meaning: What it stands for, as Admins are told when it is missing.
    """

    text: str
    meaning: str


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
        required_placeholders: The placeholders the text must keep.
        hint: One line on when the setting is used, shown under its label;
            None if it needs none.
    """

    key: str
    label: str
    kind: SettingKind
    minimum: int = 0
    maximum: int = 0
    max_length: int = 20_000
    required_placeholders: tuple[RequiredPlaceholder, ...] = ()
    hint: str | None = None


@dataclass(frozen=True)
class ExtraPromptGroup:
    """A named group of extra prompts on a core service's card.

    Attributes:
        name: The group's name, as Admins see it.
        keys: The text settings in the group, in order.
    """

    name: str
    keys: tuple[str, ...]


@dataclass(frozen=True)
class CoreService:
    """A core service whose prompt and model Admins can change.

    Attributes:
        name: The service's name, as Admins see it.
        runs_when: When the service runs.
        description: What the service does.
        prompt_key: The setting holding its prompt.
        model_key: The setting holding the model it uses.
        extra_prompt_keys: Other text settings shown with its prompt, e.g.
            a tool description it uses.
        extra_prompt_groups: Other text settings shown with its prompt in
            named groups.
    """

    name: str
    runs_when: str
    description: str
    prompt_key: str
    model_key: str
    extra_prompt_keys: tuple[str, ...] = ()
    extra_prompt_groups: tuple[ExtraPromptGroup, ...] = ()


EDITABLE_SETTINGS: tuple[EditableSetting, ...] = (
    EditableSetting("persona", "Persona", SettingKind.TEXT),
    EditableSetting("safeguard_prompt", "Safeguard prompt", SettingKind.TEXT),
    EditableSetting("safeguard_model", "Safeguard model", SettingKind.MODEL),
    EditableSetting(
        "crisis_reply",
        "Crisis Reply",
        SettingKind.TEXT,
        max_length=4_000,
        required_placeholders=(
            RequiredPlaceholder(HELPLINES_PLACEHOLDER, "where the Helplines go"),
        ),
    ),
    EditableSetting("response_prompt", "Response composition prompt", SettingKind.TEXT),
    EditableSetting("response_model", "Response composition model", SettingKind.MODEL),
    EditableSetting(
        "sticker_tool_description",
        "send_sticker tool description",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        "web_search_tool_description",
        "web_search tool description",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        "page_fetch_tool_description",
        "fetch_page tool description",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        "reply_web_search_instructions",
        "Web search instructions",
        SettingKind.TEXT,
        max_length=4_000,
        hint="Added to the reply instructions when web search is offered.",
    ),
    EditableSetting(
        "reply_web_search_limit_note",
        "Web Search Limit reached note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Used instead of the web search instructions once the User has "
            "reached their Web Search Limit for the day."
        ),
    ),
    EditableSetting(
        "web_result_source_reminder",
        "Web source reminder",
        SettingKind.TEXT,
        max_length=2_000,
        hint="Put at the end of every web search result and page the reply reads.",
    ),
    EditableSetting(
        "reply_settings_instructions",
        "Settings in Chat instructions",
        SettingKind.TEXT,
        max_length=4_000,
        hint=(
            "Added to the reply instructions, so the reply can change the "
            "User’s settings when they ask in chat."
        ),
    ),
    EditableSetting(
        "reply_delete_data_instructions",
        "Delete data instructions",
        SettingKind.TEXT,
        max_length=4_000,
        hint=(
            "Used instead of the Settings in Chat instructions when Settings "
            "in Chat doesn’t work for the User."
        ),
    ),
    EditableSetting(
        "reply_data_deletion_cancelled_note",
        "Data deletion cancelled note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Added when the User’s message cancelled their request to delete "
            "their data."
        ),
    ),
    EditableSetting(
        "reply_memory_intro",
        "Memory intro",
        SettingKind.TEXT,
        max_length=2_000,
        hint="Put before the User Memory given to each reply.",
    ),
    EditableSetting(
        "reply_knowledge_intro",
        "Knowledge intro",
        SettingKind.TEXT,
        max_length=2_000,
        hint="Put before the Knowledge passages given to each reply.",
    ),
    EditableSetting(
        UNAVAILABLE_NOTE_SETTING,
        "Features unavailable note",
        SettingKind.TEXT,
        max_length=2_000,
        required_placeholders=(
            RequiredPlaceholder(
                FEATURES_PLACEHOLDER,
                "the names of the Features that don’t work for them",
            ),
            RequiredPlaceholder(DASHBOARD_URL_PLACEHOLDER, "the link to the Dashboard"),
        ),
        hint=(
            "Added when a Feature doesn’t work for the User. {features} becomes "
            "those Features’ names and {dashboard_url} the Dashboard’s address."
        ),
    ),
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
    EditableSetting(
        "shared_photos_memory_description",
        "Shared Photos description for memory retrieval",
        SettingKind.TEXT,
        max_length=2_000,
    ),
    EditableSetting(
        "photo_description_prompt", "Photo description prompt", SettingKind.TEXT
    ),
    EditableSetting("photo_model", "Photo viewing model", SettingKind.MODEL),
    EditableSetting(
        "ask_about_photo_tool_description",
        "ask_about_photo tool description",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        "send_photo_tool_description",
        "send_photo tool description",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        "photo_not_viewed_note",
        "“Didn’t come through” note",
        SettingKind.TEXT,
        max_length=2_000,
    ),
    EditableSetting(
        "photo_viewing_off_note",
        "“Photo Viewing off” note",
        SettingKind.TEXT,
        max_length=2_000,
    ),
    EditableSetting(
        "photo_retry_count",
        "Photo retries",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=5,
    ),
    EditableSetting(
        "photo_album_wait_seconds",
        "Album wait",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=30,
    ),
    EditableSetting(
        "photo_album_max_photos",
        "Most photos per album",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=10,
    ),
    EditableSetting(
        "personal_sticker_keeping_prompt",
        "Personal Sticker keeping prompt",
        SettingKind.TEXT,
    ),
    EditableSetting(
        "personal_sticker_keeping_model",
        "Personal Sticker keeping model",
        SettingKind.MODEL,
    ),
    EditableSetting(
        "personal_stickers_limit",
        "Most Personal Stickers per User",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=200,
    ),
    EditableSetting(
        "sticker_adding_quiet_gap_minutes",
        "Sticker adding quiet gap",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=60,
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
    EditableSetting(
        "onboarding_unfinished_reply",
        "“Finish onboarding first” reply",
        SettingKind.TEXT,
        max_length=1_000,
        required_placeholders=(
            RequiredPlaceholder(DASHBOARD_URL_PLACEHOLDER, "the link to the Dashboard"),
        ),
    ),
    EditableSetting(
        RETENTION_DAYS_SETTING,
        "Message retention",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=365,
    ),
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
    EditableSetting(
        "photo_viewing_explanation",
        "Photo Viewing explanation",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        MEMORY_PAUSED_NOTE_SETTING,
        "“Memory is paused” note",
        SettingKind.TEXT,
        max_length=1_000,
    ),
    EditableSetting(
        MEMORY_NOT_AVAILABLE_NOTE_SETTING,
        "“Memory isn’t available” note",
        SettingKind.TEXT,
        max_length=1_000,
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
        extra_prompt_groups=(
            ExtraPromptGroup(
                "Web search",
                (
                    "web_search_tool_description",
                    "page_fetch_tool_description",
                    "reply_web_search_instructions",
                    "reply_web_search_limit_note",
                    "web_result_source_reminder",
                ),
            ),
            ExtraPromptGroup(
                "Settings in chat",
                (
                    "reply_settings_instructions",
                    "reply_delete_data_instructions",
                    "reply_data_deletion_cancelled_note",
                ),
            ),
            ExtraPromptGroup(
                "Memory and Knowledge", ("reply_memory_intro", "reply_knowledge_intro")
            ),
            ExtraPromptGroup("Features", (UNAVAILABLE_NOTE_SETTING,)),
            ExtraPromptGroup("Stickers", ("sticker_tool_description",)),
        ),
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
        extra_prompt_keys=("shared_photos_memory_description",),
    ),
    CoreService(
        name="Photo viewing",
        runs_when="Every photo, before the Safeguard",
        description=(
            "Looks at each photo a User sends and writes a detailed "
            "description. The Safeguard, the reply and memory read the "
            "description; the photo itself is never kept. The reply can look "
            "again with a question when the description can’t answer."
        ),
        prompt_key="photo_description_prompt",
        model_key="photo_model",
        extra_prompt_keys=(
            "ask_about_photo_tool_description",
            "send_photo_tool_description",
        ),
    ),
    CoreService(
        name="Personal Sticker keeping",
        runs_when="After quiet gap, when the User sent stickers",
        description=(
            "Keeps the stickers a User sent whose meaning was clear, each with "
            "a “when to use” note about the moment, so Zeph can reply in their "
            "own stickers. Runs only while Personal Stickers works for them."
        ),
        prompt_key="personal_sticker_keeping_prompt",
        model_key="personal_sticker_keeping_model",
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


EDITABLE_SETTINGS_BY_KEY: dict[str, EditableSetting] = {
    setting.key: setting for setting in EDITABLE_SETTINGS
}


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
            for placeholder in setting.required_placeholders:
                if placeholder.text not in value:
                    raise InvalidSettingError(
                        f"The {setting.label} must include {placeholder.text}, "
                        f"{placeholder.meaning}."
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
        if value not in self.model_choices():
            raise InvalidSettingError(
                f"The {setting.label} must be one of the listed models."
            )
        return value
