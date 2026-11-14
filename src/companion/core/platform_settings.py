from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Any

from companion.core.errors import InvalidError
from companion.core.models import CheckInFrequency, Setting, StoredSetting, User
from companion.core.ports import Clock, PlatformSettingsRepository

HELPLINES_PLACEHOLDER = "{helplines}"
FEATURES_PLACEHOLDER = "{features}"
DASHBOARD_URL_PLACEHOLDER = "{dashboard_url}"


def read_text(value: Any) -> str:
    """Read a stored text setting.

    Args:
        value: The stored value.

    Returns:
        The text.

    Raises:
        TypeError: If the value is not text.
    """
    if not isinstance(value, str):
        raise TypeError(f"Expected text, got {value!r}.")
    return value


def read_whole_number(value: Any) -> int:
    """Read a stored whole-number setting.

    Args:
        value: The stored value.

    Returns:
        The whole number.

    Raises:
        TypeError: If the value is not a whole number.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"Expected a whole number, got {value!r}.")
    return value


def read_number(value: Any) -> float:
    """Read a stored number setting, whole or not.

    Args:
        value: The stored value.

    Returns:
        The number.

    Raises:
        TypeError: If the value is not a number.
    """
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"Expected a number, got {value!r}.")
    return float(value)


def read_minutes(value: Any) -> timedelta:
    """Read a stored setting that holds a number of minutes.

    Args:
        value: The stored value.

    Returns:
        That many minutes.
    """
    return timedelta(minutes=read_whole_number(value))


def read_hours(value: Any) -> timedelta:
    """Read a stored setting that holds a number of hours.

    Args:
        value: The stored value.

    Returns:
        That many hours.
    """
    return timedelta(hours=read_whole_number(value))


def read_text_list(value: Any) -> list[str]:
    """Read a stored setting that holds a list of texts.

    Args:
        value: The stored value.

    Returns:
        The texts.

    Raises:
        TypeError: If the value is not a list of texts.
    """
    if not isinstance(value, list):
        raise TypeError(f"Expected a list, got {value!r}.")
    return [read_text(item) for item in value]


def read_check_in_gaps(value: Any) -> dict[CheckInFrequency, timedelta]:
    """Read the fewest hours between two Check-ins, for each frequency.

    Args:
        value: The stored value: hours by frequency, e.g. {"weekly": 168}.

    Returns:
        The gap for each frequency.

    Raises:
        TypeError: If the value is not a mapping of hours.
        KeyError: If a frequency is missing.
    """
    if not isinstance(value, dict):
        raise TypeError(f"Expected hours by frequency, got {value!r}.")
    return {
        frequency: read_hours(value[frequency.value]) for frequency in CheckInFrequency
    }


CONNECTION_TOKEN_TTL = Setting("connection_token_ttl_minutes", read_minutes)
WELCOME_MESSAGE = Setting("welcome_message", read_text)
CONNECTION_TOKEN_INVALID_REPLY = Setting("connection_token_invalid_reply", read_text)
TELEGRAM_CONNECTED_ELSEWHERE_REPLY = Setting(
    "telegram_connected_elsewhere_reply", read_text
)
ONBOARDING_UNFINISHED_REPLY = Setting("onboarding_unfinished_reply", read_text)
UNKNOWN_TELEGRAM_USER_REPLY = Setting("unknown_telegram_user_reply", read_text)
REPLY_FAILED_MESSAGE = Setting("reply_failed_message", read_text)
UNSUPPORTED_MESSAGE_REPLY = Setting("unsupported_message_reply", read_text)
STICKER_ADDING_SUMMARY_REPLY = Setting("sticker_adding_summary_reply", read_text)
STICKER_ADDING_QUIET_GAP = Setting("sticker_adding_quiet_gap_minutes", read_minutes)
AI_NOTICE = Setting("ai_notice", read_text)
AI_NOTICE_SHORT = Setting("ai_notice_short", read_text)
USER_MEMORY_EXPLANATION = Setting("user_memory_explanation", read_text)
PHOTO_VIEWING_EXPLANATION = Setting("photo_viewing_explanation", read_text)
MEMORY_PAUSED_NOTE = Setting("memory_paused_note", read_text)
MEMORY_NOT_AVAILABLE_NOTE = Setting("memory_not_available_note", read_text)
ONBOARDING_REASON_CHOICES = Setting("onboarding_reason_choices", read_text_list)
CONVERSATION_QUIET_GAP = Setting("conversation_quiet_gap_minutes", read_minutes)
MESSAGE_WAIT_SECONDS = Setting("message_wait_seconds", read_whole_number)
TYPING_REPEAT_SECONDS = Setting("typing_repeat_seconds", read_whole_number)
MESSAGE_RETENTION_DAYS = Setting("message_retention_days", read_whole_number)
TYPING_SECONDS_PER_CHARACTER = Setting("typing_seconds_per_character", read_number)
MIN_TYPING_SECONDS = Setting("min_typing_seconds", read_number)
MAX_TYPING_SECONDS = Setting("max_typing_seconds", read_number)
AVAILABLE_MODELS = Setting("available_models", read_text_list)
RESPONSE_MODEL = Setting("response_model", read_text)
PERSONA = Setting("persona", read_text)
RESPONSE_PROMPT = Setting("response_prompt", read_text)
PHOTO_MODEL = Setting("photo_model", read_text)
PHOTO_DESCRIPTION_PROMPT = Setting("photo_description_prompt", read_text)
ASK_ABOUT_PHOTO_TOOL_DESCRIPTION = Setting(
    "ask_about_photo_tool_description", read_text
)
SEND_PHOTO_TOOL_DESCRIPTION = Setting("send_photo_tool_description", read_text)
PHOTO_NOT_VIEWED_NOTE = Setting("photo_not_viewed_note", read_text)
PHOTO_VIEWING_OFF_NOTE = Setting("photo_viewing_off_note", read_text)
PHOTO_RETRY_COUNT = Setting("photo_retry_count", read_whole_number)
PHOTO_ALBUM_MAX_PHOTOS = Setting("photo_album_max_photos", read_whole_number)
SAFEGUARD_MODEL = Setting("safeguard_model", read_text)
SAFEGUARD_PROMPT = Setting("safeguard_prompt", read_text)
CRISIS_REPLY = Setting("crisis_reply", read_text)
MEMORY_PROCESSING_MODEL = Setting("memory_processing_model", read_text)
MEMORY_PROCESSING_PROMPT = Setting("memory_processing_prompt", read_text)
UNDERSTANDING_MODEL = Setting("understanding_model", read_text)
UNDERSTANDING_PROMPT = Setting("understanding_prompt", read_text)
REPLY_ASK_WHY_NOTE = Setting("reply_ask_why_note", read_text)
SHARED_PHOTOS_MEMORY_DESCRIPTION = Setting(
    "shared_photos_memory_description", read_text
)
REPLY_MEMORY_INTRO = Setting("reply_memory_intro", read_text)
RECENT_CONVERSATION_SUMMARIES = Setting(
    "recent_conversation_summaries", read_whole_number
)
OLDER_SUMMARIES_PER_REPLY = Setting("older_summaries_per_reply", read_whole_number)
OLDER_SUMMARIES_CLOSENESS_PERCENT = Setting(
    "older_summaries_closeness_percent", read_whole_number
)
KNOWLEDGE_CHUNKS_PER_REPLY = Setting("knowledge_chunks_per_reply", read_whole_number)
REPLY_KNOWLEDGE_INTRO = Setting("reply_knowledge_intro", read_text)
DAILY_MESSAGE_LIMIT = Setting("daily_message_limit", read_whole_number)
DAILY_LIMIT_REPLY = Setting("daily_limit_reply", read_text)
WEB_SEARCH_DAILY_LIMIT = Setting("web_search_daily_limit", read_whole_number)
WEB_SEARCH_TOOL_DESCRIPTION = Setting("web_search_tool_description", read_text)
PAGE_FETCH_TOOL_DESCRIPTION = Setting("page_fetch_tool_description", read_text)
WEB_RESULT_SOURCE_REMINDER = Setting("web_result_source_reminder", read_text)
REPLY_WEB_SEARCH_INSTRUCTIONS = Setting("reply_web_search_instructions", read_text)
REPLY_WEB_SEARCH_LIMIT_NOTE = Setting("reply_web_search_limit_note", read_text)
REPLY_SETTINGS_INSTRUCTIONS = Setting("reply_settings_instructions", read_text)
REPLY_DELETE_DATA_INSTRUCTIONS = Setting("reply_delete_data_instructions", read_text)
REPLY_FEATURES_UNAVAILABLE_NOTE = Setting("reply_features_unavailable_note", read_text)
DATA_DELETION_CONFIRMATION_WORD = Setting("data_deletion_confirmation_word", read_text)
DATA_DELETED_REPLY = Setting("data_deleted_reply", read_text)
REPLY_DATA_DELETION_CANCELLED_NOTE = Setting(
    "reply_data_deletion_cancelled_note", read_text
)
REPLY_DATA_DELETION_WORD_NOT_ALONE_NOTE = Setting(
    "reply_data_deletion_word_not_alone_note", read_text
)
ONBOARDING_NAME_MEMORY_CATEGORY = Setting("onboarding_name_memory_category", read_text)
ONBOARDING_REASONS_MEMORY_CATEGORY = Setting(
    "onboarding_reasons_memory_category", read_text
)
HOME_GOALS_MEMORY_CATEGORY = Setting("home_goals_memory_category", read_text)
STICKER_TOOL_DESCRIPTION = Setting("sticker_tool_description", read_text)
PERSONAL_STICKER_KEEPING_MODEL = Setting("personal_sticker_keeping_model", read_text)
PERSONAL_STICKER_KEEPING_PROMPT = Setting("personal_sticker_keeping_prompt", read_text)
PERSONAL_STICKERS_LIMIT = Setting("personal_stickers_limit", read_whole_number)
CHECK_IN_MODEL = Setting("check_in_model", read_text)
CHECK_IN_PROMPT = Setting("check_in_prompt", read_text)
CHECK_IN_IGNORE_THRESHOLD = Setting("check_in_ignore_threshold", read_whole_number)
CHECK_IN_FEWER_MESSAGE = Setting("check_in_fewer_message", read_text)
CHECK_IN_GAPS = Setting("check_in_hours_between", read_check_in_gaps)
CHECK_IN_REPLY_WINDOW = Setting("check_in_reply_window_hours", read_hours)


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
    EditableSetting(PERSONA.key, "Persona", SettingKind.TEXT),
    EditableSetting(SAFEGUARD_PROMPT.key, "Safeguard prompt", SettingKind.TEXT),
    EditableSetting(SAFEGUARD_MODEL.key, "Safeguard model", SettingKind.MODEL),
    EditableSetting(
        CRISIS_REPLY.key,
        "Crisis Reply",
        SettingKind.TEXT,
        max_length=4_000,
        required_placeholders=(
            RequiredPlaceholder(HELPLINES_PLACEHOLDER, "where the Helplines go"),
        ),
    ),
    EditableSetting(
        RESPONSE_PROMPT.key, "Response composition prompt", SettingKind.TEXT
    ),
    EditableSetting(
        RESPONSE_MODEL.key, "Response composition model", SettingKind.MODEL
    ),
    EditableSetting(
        STICKER_TOOL_DESCRIPTION.key,
        "send_sticker tool description",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        WEB_SEARCH_TOOL_DESCRIPTION.key,
        "web_search tool description",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        PAGE_FETCH_TOOL_DESCRIPTION.key,
        "fetch_page tool description",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        REPLY_WEB_SEARCH_INSTRUCTIONS.key,
        "Web search instructions",
        SettingKind.TEXT,
        max_length=4_000,
        hint="Added to the reply instructions when web search is offered.",
    ),
    EditableSetting(
        REPLY_WEB_SEARCH_LIMIT_NOTE.key,
        "Web Search Limit reached note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Used instead of the web search instructions once the User has "
            "reached their Web Search Limit for the day."
        ),
    ),
    EditableSetting(
        WEB_RESULT_SOURCE_REMINDER.key,
        "Web source reminder",
        SettingKind.TEXT,
        max_length=2_000,
        hint="Put at the end of every web search result and page the reply reads.",
    ),
    EditableSetting(
        REPLY_SETTINGS_INSTRUCTIONS.key,
        "Settings in Chat instructions",
        SettingKind.TEXT,
        max_length=4_000,
        hint=(
            "Added to the reply instructions, so the reply can change the "
            "User’s settings when they ask in chat."
        ),
    ),
    EditableSetting(
        REPLY_DELETE_DATA_INSTRUCTIONS.key,
        "Delete data instructions",
        SettingKind.TEXT,
        max_length=4_000,
        hint=(
            "Used instead of the Settings in Chat instructions when Settings "
            "in Chat doesn’t work for the User."
        ),
    ),
    EditableSetting(
        REPLY_DATA_DELETION_CANCELLED_NOTE.key,
        "Data deletion cancelled note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Added when the User’s message cancelled their request to delete "
            "their data."
        ),
    ),
    EditableSetting(
        REPLY_DATA_DELETION_WORD_NOT_ALONE_NOTE.key,
        "Data deletion word-not-alone note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Added instead when the User sent the confirmation word together "
            "with other texts in one Message, so it didn’t count."
        ),
    ),
    EditableSetting(
        REPLY_MEMORY_INTRO.key,
        "Memory intro",
        SettingKind.TEXT,
        max_length=2_000,
        hint="Put before the User Memory given to each reply.",
    ),
    EditableSetting(
        REPLY_KNOWLEDGE_INTRO.key,
        "Knowledge intro",
        SettingKind.TEXT,
        max_length=2_000,
        hint="Put before the Knowledge passages given to each reply.",
    ),
    EditableSetting(
        REPLY_FEATURES_UNAVAILABLE_NOTE.key,
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
        MEMORY_PROCESSING_PROMPT.key,
        "Post-conversation processing prompt",
        SettingKind.TEXT,
    ),
    EditableSetting(
        MEMORY_PROCESSING_MODEL.key,
        "Post-conversation processing model",
        SettingKind.MODEL,
    ),
    EditableSetting(UNDERSTANDING_PROMPT.key, "Understanding prompt", SettingKind.TEXT),
    EditableSetting(UNDERSTANDING_MODEL.key, "Understanding model", SettingKind.MODEL),
    EditableSetting(
        REPLY_ASK_WHY_NOTE.key,
        "“Gently ask why” note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Added when the User’s mood stands out and Zeph doesn’t know why, "
            "unless the previous reply already asked."
        ),
    ),
    EditableSetting(
        SHARED_PHOTOS_MEMORY_DESCRIPTION.key,
        "Shared Photos description for the Understanding",
        SettingKind.TEXT,
        max_length=2_000,
    ),
    EditableSetting(
        PHOTO_DESCRIPTION_PROMPT.key, "Photo description prompt", SettingKind.TEXT
    ),
    EditableSetting(PHOTO_MODEL.key, "Photo viewing model", SettingKind.MODEL),
    EditableSetting(
        ASK_ABOUT_PHOTO_TOOL_DESCRIPTION.key,
        "ask_about_photo tool description",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        SEND_PHOTO_TOOL_DESCRIPTION.key,
        "send_photo tool description",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        PHOTO_NOT_VIEWED_NOTE.key,
        "“Didn’t come through” note",
        SettingKind.TEXT,
        max_length=2_000,
    ),
    EditableSetting(
        PHOTO_VIEWING_OFF_NOTE.key,
        "“Photo Viewing off” note",
        SettingKind.TEXT,
        max_length=2_000,
    ),
    EditableSetting(
        PHOTO_RETRY_COUNT.key,
        "Photo retries",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=5,
    ),
    EditableSetting(
        PHOTO_ALBUM_MAX_PHOTOS.key,
        "Most photos per album",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=10,
    ),
    EditableSetting(
        PERSONAL_STICKER_KEEPING_PROMPT.key,
        "Personal Sticker keeping prompt",
        SettingKind.TEXT,
    ),
    EditableSetting(
        PERSONAL_STICKER_KEEPING_MODEL.key,
        "Personal Sticker keeping model",
        SettingKind.MODEL,
    ),
    EditableSetting(
        PERSONAL_STICKERS_LIMIT.key,
        "Most Personal Stickers per User",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=200,
    ),
    EditableSetting(
        STICKER_ADDING_QUIET_GAP.key,
        "Sticker adding quiet gap",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=60,
    ),
    EditableSetting(CHECK_IN_PROMPT.key, "Check-in prompt", SettingKind.TEXT),
    EditableSetting(CHECK_IN_MODEL.key, "Check-in model", SettingKind.MODEL),
    EditableSetting(
        CHECK_IN_IGNORE_THRESHOLD.key,
        "Ignore threshold",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=10,
    ),
    EditableSetting(
        CHECK_IN_FEWER_MESSAGE.key,
        "“Would you like fewer?” message",
        SettingKind.TEXT,
        max_length=1_000,
    ),
    EditableSetting(
        OLDER_SUMMARIES_PER_REPLY.key,
        "Most older Conversations per reply",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=10,
    ),
    EditableSetting(
        OLDER_SUMMARIES_CLOSENESS_PERCENT.key,
        "Older Conversation closeness bar",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
    ),
    EditableSetting(
        CONVERSATION_QUIET_GAP.key,
        "Conversation quiet gap",
        SettingKind.WHOLE_NUMBER,
        minimum=5,
        maximum=1440,
    ),
    EditableSetting(
        MESSAGE_WAIT_SECONDS.key,
        "Message wait",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=30,
    ),
    EditableSetting(
        TYPING_REPEAT_SECONDS.key,
        "Typing repeat",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=5,
    ),
    EditableSetting(
        DAILY_MESSAGE_LIMIT.key,
        "Daily message limit",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=10_000,
    ),
    EditableSetting(
        DAILY_LIMIT_REPLY.key,
        "Limit-reached reply",
        SettingKind.TEXT,
        max_length=1_000,
    ),
    EditableSetting(
        ONBOARDING_UNFINISHED_REPLY.key,
        "“Finish onboarding first” reply",
        SettingKind.TEXT,
        max_length=1_000,
        required_placeholders=(
            RequiredPlaceholder(DASHBOARD_URL_PLACEHOLDER, "the link to the Dashboard"),
        ),
    ),
    EditableSetting(
        MESSAGE_RETENTION_DAYS.key,
        "Message retention",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=365,
    ),
    EditableSetting(
        WEB_SEARCH_DAILY_LIMIT.key,
        "Per-user daily web search limit",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=1000,
    ),
    EditableSetting(AI_NOTICE.key, "AI notice", SettingKind.TEXT, max_length=2_000),
    EditableSetting(
        AI_NOTICE_SHORT.key, "Short AI notice", SettingKind.TEXT, max_length=200
    ),
    EditableSetting(
        USER_MEMORY_EXPLANATION.key,
        "Memory explanation",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        PHOTO_VIEWING_EXPLANATION.key,
        "Photo Viewing explanation",
        SettingKind.TEXT,
        max_length=4_000,
    ),
    EditableSetting(
        MEMORY_PAUSED_NOTE.key,
        "“Memory is paused” note",
        SettingKind.TEXT,
        max_length=1_000,
    ),
    EditableSetting(
        MEMORY_NOT_AVAILABLE_NOTE.key,
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
        prompt_key=SAFEGUARD_PROMPT.key,
        model_key=SAFEGUARD_MODEL.key,
    ),
    CoreService(
        name="Response composition",
        runs_when="Every reply",
        description=(
            "Writes Zeph’s reply from the Persona, the relevant memories, recent "
            "Conversation Summaries, Knowledge and the Conversation so far."
        ),
        prompt_key=RESPONSE_PROMPT.key,
        model_key=RESPONSE_MODEL.key,
        extra_prompt_groups=(
            ExtraPromptGroup(
                "Web search",
                (
                    WEB_SEARCH_TOOL_DESCRIPTION.key,
                    PAGE_FETCH_TOOL_DESCRIPTION.key,
                    REPLY_WEB_SEARCH_INSTRUCTIONS.key,
                    REPLY_WEB_SEARCH_LIMIT_NOTE.key,
                    WEB_RESULT_SOURCE_REMINDER.key,
                ),
            ),
            ExtraPromptGroup(
                "Settings in chat",
                (
                    REPLY_SETTINGS_INSTRUCTIONS.key,
                    REPLY_DELETE_DATA_INSTRUCTIONS.key,
                    REPLY_DATA_DELETION_CANCELLED_NOTE.key,
                    REPLY_DATA_DELETION_WORD_NOT_ALONE_NOTE.key,
                ),
            ),
            ExtraPromptGroup(
                "Memory and Knowledge",
                (REPLY_MEMORY_INTRO.key, REPLY_KNOWLEDGE_INTRO.key),
            ),
            ExtraPromptGroup("Understanding", (REPLY_ASK_WHY_NOTE.key,)),
            ExtraPromptGroup("Features", (REPLY_FEATURES_UNAVAILABLE_NOTE.key,)),
            ExtraPromptGroup("Stickers", (STICKER_TOOL_DESCRIPTION.key,)),
        ),
    ),
    CoreService(
        name="Post-conversation processing",
        runs_when="After quiet gap",
        description=(
            "After a Conversation goes quiet, writes the Conversation Summary "
            "and mood, and adds, updates or removes Memory Items by category."
        ),
        prompt_key=MEMORY_PROCESSING_PROMPT.key,
        model_key=MEMORY_PROCESSING_MODEL.key,
    ),
    CoreService(
        name="Understanding",
        runs_when="Every reply, before it is written",
        description=(
            "Reads what the User just said and picks the Need that fits, how "
            "they seem and whether Zeph knows why, and the Memory Categories "
            "that matter. The reply follows the Need’s “how to reply” and gets "
            "only those memories plus the always-included ones."
        ),
        prompt_key=UNDERSTANDING_PROMPT.key,
        model_key=UNDERSTANDING_MODEL.key,
        extra_prompt_keys=(SHARED_PHOTOS_MEMORY_DESCRIPTION.key,),
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
        prompt_key=PHOTO_DESCRIPTION_PROMPT.key,
        model_key=PHOTO_MODEL.key,
        extra_prompt_keys=(
            ASK_ABOUT_PHOTO_TOOL_DESCRIPTION.key,
            SEND_PHOTO_TOOL_DESCRIPTION.key,
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
        prompt_key=PERSONAL_STICKER_KEEPING_PROMPT.key,
        model_key=PERSONAL_STICKER_KEEPING_MODEL.key,
    ),
    CoreService(
        name="Check-ins",
        runs_when="Scheduler tick, for Users who are due",
        description=(
            "Decides whether to reach out to a User who opted in, which "
            "Check-in Kind to use and what to say, or to skip and give space, "
            "from their recent Conversation Summaries and Memory Items."
        ),
        prompt_key=CHECK_IN_PROMPT.key,
        model_key=CHECK_IN_MODEL.key,
    ),
)


EDITABLE_SETTINGS_BY_KEY: dict[str, EditableSetting] = {
    setting.key: setting for setting in EDITABLE_SETTINGS
}


@dataclass(frozen=True)
class DashboardContent:
    """Admin-managed wording and settings the Dashboard shows to Users.

    Attributes:
        ai_notice: The full AI notice.
        ai_notice_short: The short AI notice.
        user_memory_explanation: What User Memory is.
        photo_viewing_explanation: What Photo Viewing is.
        onboarding_reason_choices: The "What brings you here?" choices.
        message_retention_days: How many days messages are kept.
    """

    ai_notice: str
    ai_notice_short: str
    user_memory_explanation: str
    photo_viewing_explanation: str
    onboarding_reason_choices: list[str]
    message_retention_days: int


class InvalidSettingError(InvalidError):
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

    def dashboard_content(self) -> DashboardContent:
        """Read the Admin-managed wording the Dashboard shows to Users.

        Returns:
            The AI notices, explanations, onboarding choices and how long
            messages are kept.
        """
        settings = self._settings.load()
        return DashboardContent(
            ai_notice=settings.get(AI_NOTICE),
            ai_notice_short=settings.get(AI_NOTICE_SHORT),
            user_memory_explanation=settings.get(USER_MEMORY_EXPLANATION),
            photo_viewing_explanation=settings.get(PHOTO_VIEWING_EXPLANATION),
            onboarding_reason_choices=settings.get(ONBOARDING_REASON_CHOICES),
            message_retention_days=settings.get(MESSAGE_RETENTION_DAYS),
        )

    def model_choices(self) -> list[str]:
        """List the models Admins can pick for a core service.

        Returns:
            The model names.
        """
        return self._settings.load().get(AVAILABLE_MODELS)

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
