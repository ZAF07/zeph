from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Any

from companion.core.errors import InvalidError
from companion.core.models import (
    CheckInFrequency,
    PlatformSettings,
    Setting,
    StoredSetting,
    User,
)
from companion.core.ports import Clock, PlatformSettingsRepository

HELPLINES_PLACEHOLDER = "{helplines}"
FEATURES_PLACEHOLDER = "{features}"
DASHBOARD_URL_PLACEHOLDER = "{dashboard_url}"
CONFIRMATION_WORD_PLACEHOLDER = "{word}"


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


def read_days(value: Any) -> timedelta:
    """Read a stored setting that holds a number of days.

    Args:
        value: The stored value.

    Returns:
        That many days.
    """
    return timedelta(days=read_whole_number(value))


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


def read_on_off(value: Any) -> bool:
    """Read a stored on/off setting.

    Args:
        value: The stored value.

    Returns:
        True if it is on.

    Raises:
        TypeError: If the value is not true or false.
    """
    if not isinstance(value, bool):
        raise TypeError(f"Expected true or false, got {value!r}.")
    return value


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


def is_hours_by_frequency(value: Any, minimum: int, maximum: int) -> bool:
    """Tell whether a value gives every frequency, and only those, its hours.

    Args:
        value: The value to check, e.g. {"weekly": 168, ...}.
        minimum: The fewest hours allowed.
        maximum: The most hours allowed.

    Returns:
        True if each frequency has a whole number of hours in the range.
    """
    if not isinstance(value, dict):
        return False
    if set(value) != {frequency.value for frequency in CheckInFrequency}:
        return False
    return all(
        isinstance(hours, int)
        and not isinstance(hours, bool)
        and minimum <= hours <= maximum
        for hours in value.values()
    )


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
ONBOARDING_REASON_CHOICES = Setting("onboarding_reason_choices", read_text_list)
CONVERSATION_QUIET_GAP = Setting("conversation_quiet_gap_minutes", read_minutes)
MESSAGE_WAIT_SECONDS = Setting("message_wait_seconds", read_whole_number)
MESSAGE_WAIT_FINISHED_SECONDS = Setting(
    "message_wait_finished_seconds", read_whole_number
)
MESSAGE_WAIT_TRAILING_SECONDS = Setting(
    "message_wait_trailing_seconds", read_whole_number
)
MESSAGE_WAIT_CAP_SECONDS = Setting("message_wait_cap_seconds", read_whole_number)
MESSAGE_WAIT_LONG_TEXT_WORDS = Setting(
    "message_wait_long_text_words", read_whole_number
)
MESSAGE_WAIT_TRAILING_WORDS = Setting("message_wait_trailing_words", read_text_list)
MESSAGE_WAITS = (
    MESSAGE_WAIT_FINISHED_SECONDS,
    MESSAGE_WAIT_TRAILING_SECONDS,
    MESSAGE_WAIT_SECONDS,
)
TYPING_REPEAT_SECONDS = Setting("typing_repeat_seconds", read_whole_number)
MESSAGE_RETENTION_DAYS = Setting("message_retention_days", read_whole_number)
RECENT_MESSAGES_HOURS = Setting("recent_messages_hours", read_whole_number)
RECENT_MESSAGES_CAP = Setting("recent_messages_cap", read_whole_number)
TYPING_SECONDS_PER_CHARACTER = Setting("typing_seconds_per_character", read_number)
MIN_TYPING_SECONDS = Setting("min_typing_seconds", read_number)
MAX_TYPING_SECONDS = Setting("max_typing_seconds", read_number)
AVAILABLE_MODELS = Setting("available_models", read_text_list)
RESPONSE_MODEL = Setting("response_model", read_text)
RESPONSE_THINKING = Setting("response_thinking", read_on_off)
PERSONA = Setting("persona", read_text)
PERSONA_OUTLOOK = Setting("persona_outlook", read_text)
RESPONSE_PROMPT = Setting("response_prompt", read_text)
PHOTO_MODEL = Setting("photo_model", read_text)
PHOTO_THINKING = Setting("photo_thinking", read_on_off)
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
SAFEGUARD_THINKING = Setting("safeguard_thinking", read_on_off)
SAFEGUARD_PROMPT = Setting("safeguard_prompt", read_text)
CRISIS_REPLY = Setting("crisis_reply", read_text)
MEMORY_PROCESSING_MODEL = Setting("memory_processing_model", read_text)
MEMORY_PROCESSING_THINKING = Setting("memory_processing_thinking", read_on_off)
MEMORY_PROCESSING_PROMPT = Setting("memory_processing_prompt", read_text)
UNDERSTANDING_MODEL = Setting("understanding_model", read_text)
UNDERSTANDING_THINKING = Setting("understanding_thinking", read_on_off)
UNDERSTANDING_PROMPT = Setting("understanding_prompt", read_text)
REPLY_PLAN_MODEL = Setting("reply_plan_model", read_text)
REPLY_PLAN_THINKING = Setting("reply_plan_thinking", read_on_off)
REPLY_PLAN_PROMPT = Setting("reply_plan_prompt", read_text)
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
LIFE_THREADS_PER_REPLY = Setting("life_threads_per_reply", read_whole_number)
LIFE_THREADS_TEXTS_TO_SEARCH = Setting(
    "life_threads_texts_to_search", read_whole_number
)
LIFE_THREADS_CLOSENESS_PERCENT = Setting(
    "life_threads_closeness_percent", read_whole_number
)
MOVE_OUTCOMES_PER_UNDERSTANDING = Setting(
    "move_outcomes_per_understanding", read_whole_number
)
MOVE_OUTCOMES_CLOSENESS_PERCENT = Setting(
    "move_outcomes_closeness_percent", read_whole_number
)
LIFE_THREAD_BRUSHED_OFF_WAIT = Setting("life_thread_brushed_off_wait_days", read_days)
LIFE_THREAD_KEEPING_MODEL = Setting("life_thread_keeping_model", read_text)
LIFE_THREAD_KEEPING_THINKING = Setting("life_thread_keeping_thinking", read_on_off)
LIFE_THREAD_KEEPING_PROMPT = Setting("life_thread_keeping_prompt", read_text)
CURIOSITIES_PER_CONVERSATION = Setting(
    "curiosities_per_conversation", read_whole_number
)
CURIOSITIES_WAITING_LIMIT = Setting("curiosities_waiting_limit", read_whole_number)
CURIOSITY_REPLIES_BETWEEN = Setting("curiosity_replies_between", read_whole_number)
CURIOSITIES_PER_REPLY = Setting("curiosities_per_reply", read_whole_number)
CURIOSITY_HELD_WHEN_ASKING_WHY = Setting("curiosity_held_when_asking_why", read_on_off)
FOLLOW_UPS_PER_CONVERSATION = Setting("follow_ups_per_conversation", read_whole_number)
CURIOSITY_BRUSH_OFFS_TO_BACK_OFF = Setting(
    "curiosity_brush_offs_to_back_off", read_whole_number
)
CURIOSITY_BACK_OFF = Setting("curiosity_back_off_days", read_days)
CURIOSITY_CHECK_INS_PER_WEEK = Setting(
    "curiosity_check_ins_per_week", read_whole_number
)
CURIOSITY_KEEPING_MODEL = Setting("curiosity_keeping_model", read_text)
CURIOSITY_KEEPING_THINKING = Setting("curiosity_keeping_thinking", read_on_off)
CURIOSITY_KEEPING_PROMPT = Setting("curiosity_keeping_prompt", read_text)
MOVE_OUTCOME_KEEPING_MODEL = Setting("move_outcome_keeping_model", read_text)
MOVE_OUTCOME_KEEPING_THINKING = Setting("move_outcome_keeping_thinking", read_on_off)
MOVE_OUTCOME_KEEPING_PROMPT = Setting("move_outcome_keeping_prompt", read_text)
PATTERN_KEEPING_MODEL = Setting("pattern_keeping_model", read_text)
PATTERN_KEEPING_THINKING = Setting("pattern_keeping_thinking", read_on_off)
PATTERN_KEEPING_PROMPT = Setting("pattern_keeping_prompt", read_text)
PATTERN_KEEPING_THREADS = Setting("pattern_keeping_threads", read_whole_number)
PATTERN_KEEPING_DAYS = Setting("pattern_keeping_days", read_whole_number)
PATTERN_TAGGING_MODEL = Setting("pattern_tagging_model", read_text)
PATTERN_TAGGING_THINKING = Setting("pattern_tagging_thinking", read_on_off)
PATTERN_TAGGING_PROMPT = Setting("pattern_tagging_prompt", read_text)
PATTERN_WEAK_SIGN_POINTS = Setting("pattern_weak_sign_points", read_whole_number)
PATTERN_MODERATE_SIGN_POINTS = Setting(
    "pattern_moderate_sign_points", read_whole_number
)
PATTERN_STRONG_SIGN_POINTS = Setting("pattern_strong_sign_points", read_whole_number)
PATTERN_REAL_STORY_PERCENT = Setting("pattern_real_story_percent", read_whole_number)
PATTERN_REPORTED_HABIT_PERCENT = Setting(
    "pattern_reported_habit_percent", read_whole_number
)
PATTERN_WHAT_IF_PERCENT = Setting("pattern_what_if_percent", read_whole_number)
PATTERN_OWN_OPINION_PERCENT = Setting("pattern_own_opinion_percent", read_whole_number)
PATTERN_UNCLEAR_PERCENT = Setting("pattern_unclear_percent", read_whole_number)
PATTERN_HALF_LIFE_DAYS = Setting("pattern_half_life_days", read_whole_number)
PATTERN_PEOPLE_PER_SITUATION = Setting(
    "pattern_people_per_situation", read_whole_number
)
PATTERN_SUSPECTED_SITUATIONS = Setting(
    "pattern_suspected_situations", read_whole_number
)
PATTERN_SUSPECTED_POINTS = Setting("pattern_suspected_points", read_whole_number)
PATTERN_CLOSED_UNDER_POINTS = Setting("pattern_closed_under_points", read_whole_number)
PATTERN_PUSHED_BACK_WAIT = Setting("pattern_pushed_back_wait_days", read_days)
PATTERN_CLOSENESS_PERCENT = Setting("pattern_closeness_percent", read_whole_number)
PORTRAIT_MODEL = Setting("portrait_model", read_text)
PORTRAIT_THINKING = Setting("portrait_thinking", read_on_off)
PORTRAIT_PROMPT = Setting("portrait_prompt", read_text)
KNOWLEDGE_CHUNKS_PER_REPLY = Setting("knowledge_chunks_per_reply", read_whole_number)
KNOWLEDGE_CLOSENESS_PERCENT = Setting("knowledge_closeness_percent", read_whole_number)
KNOWLEDGE_WHEN_IT_HELPS_MODEL = Setting("knowledge_when_it_helps_model", read_text)
KNOWLEDGE_WHEN_IT_HELPS_THINKING = Setting(
    "knowledge_when_it_helps_thinking", read_on_off
)
KNOWLEDGE_WHEN_IT_HELPS_PROMPT = Setting("knowledge_when_it_helps_prompt", read_text)
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
DATA_DELETION_STARTED_NOTE = Setting("data_deletion_started_note", read_text)
MEMORY_OFF_CHAT_LINE = Setting("memory_off_chat_line", read_text)
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
PERSONAL_STICKER_KEEPING_THINKING = Setting(
    "personal_sticker_keeping_thinking", read_on_off
)
PERSONAL_STICKER_KEEPING_PROMPT = Setting("personal_sticker_keeping_prompt", read_text)
PERSONAL_STICKERS_LIMIT = Setting("personal_stickers_limit", read_whole_number)
CHECK_IN_MODEL = Setting("check_in_model", read_text)
CHECK_IN_THINKING = Setting("check_in_thinking", read_on_off)
CHECK_IN_PROMPT = Setting("check_in_prompt", read_text)
CHECK_IN_IGNORE_THRESHOLD = Setting("check_in_ignore_threshold", read_whole_number)
CHECK_IN_FEWER_MESSAGE = Setting("check_in_fewer_message", read_text)
CHECK_IN_GAPS = Setting("check_in_hours_between", read_check_in_gaps)
CHECK_IN_REPLY_WINDOW = Setting("check_in_reply_window_hours", read_hours)


@dataclass(frozen=True)
class ModelPrice:
    """What one model costs in SGD per 1,000,000 tokens.

    Attributes:
        model: The model's name, e.g. "deepseek/deepseek-v4.1-flash".
        sgd_in: SGD per 1,000,000 tokens it reads.
        sgd_out: SGD per 1,000,000 tokens it writes.
    """

    model: str
    sgd_in: float
    sgd_out: float


def read_model_prices(value: Any) -> dict[str, ModelPrice]:
    """Read the stored Model Prices.

    Args:
        value: The stored value: SGD in and out by model, e.g.
            {"deepseek/deepseek-v4.1-flash": {"in": 0.38, "out": 1.54}}.

    Returns:
        Each priced model's price, by name.

    Raises:
        TypeError: If the value is not prices by model.
    """
    if not isinstance(value, dict):
        raise TypeError(f"Expected prices by model, got {value!r}.")
    return {
        model: ModelPrice(model, read_number(price["in"]), read_number(price["out"]))
        for model, price in value.items()
    }


MODEL_PRICES = Setting("model_prices", read_model_prices)
EVAL_RUN_TOKEN_LIMIT = Setting("eval_run_token_limit", read_whole_number)


class SettingKind(StrEnum):
    """What kind of value a setting holds, which decides how it is checked."""

    TEXT = "text"
    WHOLE_NUMBER = "whole_number"
    MODEL = "model"
    ON_OFF = "on_off"
    HOURS_BY_FREQUENCY = "hours_by_frequency"
    TEXT_LIST = "text_list"


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
        hint: One or two sentences shown under its label: what it is, what
            it serves, and which step reads it and when.
        minimum: The smallest allowed whole number, or number of hours for
            each frequency.
        maximum: The largest allowed whole number, or number of hours for
            each frequency.
        max_length: The longest allowed text.
        required_placeholders: The placeholders the text must keep.
    """

    key: str
    label: str
    kind: SettingKind
    hint: str
    minimum: int = 0
    maximum: int = 0
    max_length: int = 20_000
    required_placeholders: tuple[RequiredPlaceholder, ...] = ()


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
        thinking_key: The setting holding whether that model thinks first.
        extra_prompt_keys: Other text settings shown with its prompt, e.g.
            a tool description it uses.
        extra_prompt_groups: Other text settings shown with its prompt in
            named groups.
        limit_keys: Whole-number settings that limit what it is given,
            shown with its model and thinking switch.
    """

    name: str
    runs_when: str
    description: str
    prompt_key: str
    model_key: str
    thinking_key: str
    extra_prompt_keys: tuple[str, ...] = ()
    extra_prompt_groups: tuple[ExtraPromptGroup, ...] = ()
    limit_keys: tuple[str, ...] = ()


MODEL_HINT = (
    "Which model this step calls. A larger model is slower and costs more per Message."
)
THINKING_HINT = (
    "Lets the model reason before it answers. Slower, and better on steps that decide."
)

EDITABLE_SETTINGS: tuple[EditableSetting, ...] = (
    EditableSetting(
        PERSONA.key,
        "Voice",
        SettingKind.TEXT,
        hint=(
            "How Zeph speaks: its tone, values and boundaries. The Reply reads this "
            "before every message, and so does a Check-in sent on its own."
        ),
    ),
    EditableSetting(
        PERSONA_OUTLOOK.key,
        "Outlook",
        SettingKind.TEXT,
        hint=(
            "How Zeph sees people and what helps them grow, in plain prose. Zeph "
            "forms its Read of each User from this before every reply."
        ),
    ),
    EditableSetting(
        SAFEGUARD_PROMPT.key,
        "Safeguard prompt",
        SettingKind.TEXT,
        hint=(
            "Tells the Safeguard what counts as a crisis. The Safeguard reads each "
            "text as it arrives, before any reply is written."
        ),
    ),
    EditableSetting(
        SAFEGUARD_MODEL.key,
        "Safeguard model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        SAFEGUARD_THINKING.key,
        "Safeguard thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        CRISIS_REPLY.key,
        "Crisis Reply",
        SettingKind.TEXT,
        max_length=4_000,
        required_placeholders=(
            RequiredPlaceholder(HELPLINES_PLACEHOLDER, "where the Helplines go"),
        ),
        hint=(
            "Sent at once, instead of a normal reply, when the Safeguard finds a "
            "crisis. {helplines} becomes the Helplines for the User’s country."
        ),
    ),
    EditableSetting(
        RESPONSE_PROMPT.key,
        "Response composition prompt",
        SettingKind.TEXT,
        hint=(
            "The Reply’s own instructions for writing Zeph’s texts. Combined with the "
            "Persona and the priority order on every reply."
        ),
    ),
    EditableSetting(
        RESPONSE_MODEL.key,
        "Response composition model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        RESPONSE_THINKING.key,
        "Response composition thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        STICKER_TOOL_DESCRIPTION.key,
        "send_sticker tool description",
        SettingKind.TEXT,
        max_length=4_000,
        hint=(
            "Tells the Reply when to use the send_sticker tool. Offered on every reply "
            "while Stickers works for the User."
        ),
    ),
    EditableSetting(
        WEB_SEARCH_TOOL_DESCRIPTION.key,
        "web_search tool description",
        SettingKind.TEXT,
        max_length=4_000,
        hint=(
            "Tells the Reply when to use the web_search tool. Offered on every reply "
            "while Web Search works for the User."
        ),
    ),
    EditableSetting(
        PAGE_FETCH_TOOL_DESCRIPTION.key,
        "fetch_page tool description",
        SettingKind.TEXT,
        max_length=4_000,
        hint=(
            "Tells the Reply when to use the fetch_page tool to read a web page. "
            "Offered together with web_search."
        ),
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
            "Used instead of the web search instructions once the User has reached "
            "their Web Search Limit for the day."
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
            "Added to the reply instructions, so the reply can change the User’s "
            "settings when they ask in chat."
        ),
    ),
    EditableSetting(
        REPLY_DELETE_DATA_INSTRUCTIONS.key,
        "Delete data instructions",
        SettingKind.TEXT,
        max_length=4_000,
        hint=(
            "Used instead of the Settings in Chat instructions when Settings in Chat "
            "doesn’t work for the User."
        ),
    ),
    EditableSetting(
        DATA_DELETION_STARTED_NOTE.key,
        "Data deletion started note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "What the reply is told once the User asks in chat to delete their data, "
            "so it can explain and ask for the confirmation word."
        ),
        required_placeholders=(
            RequiredPlaceholder(CONFIRMATION_WORD_PLACEHOLDER, "the confirmation word"),
        ),
    ),
    EditableSetting(
        REPLY_DATA_DELETION_CANCELLED_NOTE.key,
        "Data deletion cancelled note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Added when the User’s message cancelled their request to delete their "
            "data."
        ),
    ),
    EditableSetting(
        REPLY_DATA_DELETION_WORD_NOT_ALONE_NOTE.key,
        "Data deletion word-not-alone note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Added instead when the User sent the confirmation word together with "
            "other texts in one Message, so it didn’t count."
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
            "Added when a Feature doesn’t work for the User. {features} becomes those "
            "Features’ names and {dashboard_url} the Dashboard’s address."
        ),
    ),
    EditableSetting(
        MEMORY_PROCESSING_PROMPT.key,
        "Post-conversation processing prompt",
        SettingKind.TEXT,
        hint=(
            "Tells the first Conversation-end step how to rewrite the day’s Day "
            "Summary and mood, change Memory Items and keep Shared Photos. Runs when a "
            "Conversation ends after the quiet gap."
        ),
    ),
    EditableSetting(
        MEMORY_PROCESSING_MODEL.key,
        "Post-conversation processing model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        MEMORY_PROCESSING_THINKING.key,
        "Post-conversation processing thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        UNDERSTANDING_PROMPT.key,
        "Understanding prompt",
        SettingKind.TEXT,
        hint=(
            "What the Understanding is told to read. It runs first on every Message, "
            "and its answer goes to the Reply Plan."
        ),
    ),
    EditableSetting(
        UNDERSTANDING_MODEL.key,
        "Understanding model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        UNDERSTANDING_THINKING.key,
        "Understanding thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        REPLY_PLAN_PROMPT.key,
        "Reply Plan prompt",
        SettingKind.TEXT,
        hint=(
            "How the Reply Plan weighs what a reply could do. It runs after the "
            "Understanding, and the Reply follows what it picks."
        ),
        max_length=40_000,
    ),
    EditableSetting(
        REPLY_PLAN_MODEL.key,
        "Reply Plan model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        REPLY_PLAN_THINKING.key,
        "Reply Plan thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        REPLY_ASK_WHY_NOTE.key,
        "“Gently ask why” note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Added when the Reply Plan says to gently ask why the User feels as they "
            "do and Zeph doesn’t know why, unless the previous reply already asked."
        ),
    ),
    EditableSetting(
        SHARED_PHOTOS_MEMORY_DESCRIPTION.key,
        "Shared Photos description for the Reply Plan",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Describes the User’s Shared Photos to the Reply Plan, which picks them "
            "like a Memory Category before each reply. When picked, the Reply can send "
            "one back."
        ),
    ),
    EditableSetting(
        PHOTO_DESCRIPTION_PROMPT.key,
        "Photo description prompt",
        SettingKind.TEXT,
        hint=(
            "Tells Photo viewing how to describe each photo a User sends. Runs on "
            "every photo, before the Safeguard."
        ),
    ),
    EditableSetting(
        PHOTO_MODEL.key,
        "Photo viewing model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        PHOTO_THINKING.key,
        "Photo viewing thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        ASK_ABOUT_PHOTO_TOOL_DESCRIPTION.key,
        "ask_about_photo tool description",
        SettingKind.TEXT,
        max_length=4_000,
        hint=(
            "Tells the Reply when to use the ask_about_photo tool to look at a photo "
            "again with a question. Offered when the Conversation has a viewed photo."
        ),
    ),
    EditableSetting(
        SEND_PHOTO_TOOL_DESCRIPTION.key,
        "send_photo tool description",
        SettingKind.TEXT,
        max_length=4_000,
        hint=(
            "Tells the Reply when to use the send_photo tool to send back one of the "
            "User’s Shared Photos. Offered when the Reply Plan picked Shared "
            "Photos."
        ),
    ),
    EditableSetting(
        PHOTO_NOT_VIEWED_NOTE.key,
        "“Didn’t come through” note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Added to the Message the Safeguard and the Reply read when a photo "
            "couldn’t be downloaded or looked at, so Zeph says so honestly."
        ),
    ),
    EditableSetting(
        PHOTO_VIEWING_OFF_NOTE.key,
        "“Photo Viewing off” note",
        SettingKind.TEXT,
        max_length=2_000,
        hint=(
            "Added to the Message the Reply reads while Photo Viewing is off for the "
            "User, so Zeph says plainly it didn’t look at the photo."
        ),
    ),
    EditableSetting(
        PHOTO_RETRY_COUNT.key,
        "Photo retries",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=5,
        hint=(
            "Extra tries Photo viewing makes when a photo fails to download or be "
            "looked at, before Zeph says it didn’t come through."
        ),
    ),
    EditableSetting(
        PHOTO_ALBUM_MAX_PHOTOS.key,
        "Most photos per album",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=10,
        hint=(
            "How many photos in one album Photo viewing looks at. The Reply mentions "
            "any it didn’t look at."
        ),
    ),
    EditableSetting(
        LIFE_THREAD_KEEPING_PROMPT.key,
        "Life Thread keeping prompt",
        SettingKind.TEXT,
        hint=(
            "Tells Life Thread keeping how to start and add to the User’s Life "
            "Threads, with the commitments they agreed to. Runs when a Conversation "
            "ends, after the Day Summary."
        ),
    ),
    EditableSetting(
        LIFE_THREAD_KEEPING_MODEL.key,
        "Life Thread keeping model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        LIFE_THREAD_KEEPING_THINKING.key,
        "Life Thread keeping thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        PORTRAIT_PROMPT.key,
        "User Portrait prompt",
        SettingKind.TEXT,
        hint=(
            "Tells the User Portrait step how to write a short picture of the User, "
            "which every Understanding, Reply Plan and reply sees. Runs last when "
            "a Conversation ends, and after the User deletes something."
        ),
    ),
    EditableSetting(
        PORTRAIT_MODEL.key,
        "User Portrait model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        PORTRAIT_THINKING.key,
        "User Portrait thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        CURIOSITY_KEEPING_PROMPT.key,
        "Curiosity keeping prompt",
        SettingKind.TEXT,
        hint=(
            "Tells Curiosity keeping what Zeph should ask the User later, including "
            "how a commitment went. Runs when a Conversation ends, after Life Thread "
            "keeping."
        ),
    ),
    EditableSetting(
        CURIOSITY_KEEPING_MODEL.key,
        "Curiosity keeping model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        CURIOSITY_KEEPING_THINKING.key,
        "Curiosity keeping thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        MOVE_OUTCOME_KEEPING_PROMPT.key,
        "Move Outcome keeping prompt",
        SettingKind.TEXT,
        hint=(
            "Tells Move Outcome keeping how to write whether each Move Zeph made "
            "helped, and why. Runs when a Conversation ends in which a Move was made."
        ),
    ),
    EditableSetting(
        MOVE_OUTCOME_KEEPING_MODEL.key,
        "Move Outcome keeping model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        MOVE_OUTCOME_KEEPING_THINKING.key,
        "Move Outcome keeping thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        PATTERN_TAGGING_PROMPT.key,
        "Pattern tagging prompt",
        SettingKind.TEXT,
        hint=(
            "How to read a Conversation into the Pattern Catalog as Observations, "
            "which code then checks. It runs once a Conversation ends, after Life "
            "Threads, while Pattern noticing works."
        ),
    ),
    EditableSetting(
        PATTERN_TAGGING_MODEL.key,
        "Pattern tagging model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        PATTERN_TAGGING_THINKING.key,
        "Pattern tagging thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        PATTERN_KEEPING_PROMPT.key,
        "Pattern keeping prompt",
        SettingKind.TEXT,
        hint=(
            "What counts as a Pattern. It runs once a Conversation ends, after Life "
            "Threads are kept."
        ),
    ),
    EditableSetting(
        PATTERN_KEEPING_MODEL.key,
        "Pattern keeping model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        PATTERN_KEEPING_THINKING.key,
        "Pattern keeping thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        PATTERN_KEEPING_THREADS.key,
        "Closest Threads to include",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=50,
        hint=(
            "How many of the User’s other Threads, closest in meaning, Pattern "
            "keeping is given."
        ),
    ),
    EditableSetting(
        PATTERN_KEEPING_DAYS.key,
        "Days of evidence to include",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=60,
        hint=(
            "How many days behind the evidence Pattern keeping reads, as messages "
            "or Day Summaries."
        ),
    ),
    EditableSetting(
        PERSONAL_STICKER_KEEPING_PROMPT.key,
        "Personal Sticker keeping prompt",
        SettingKind.TEXT,
        hint=(
            "Tells Personal Sticker keeping which of the User’s stickers to keep and "
            "when to use each. Runs when a Conversation ends in which the User sent "
            "stickers."
        ),
    ),
    EditableSetting(
        PERSONAL_STICKER_KEEPING_MODEL.key,
        "Personal Sticker keeping model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        PERSONAL_STICKER_KEEPING_THINKING.key,
        "Personal Sticker keeping thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        KNOWLEDGE_WHEN_IT_HELPS_PROMPT.key,
        "Knowledge “when it helps” prompt",
        SettingKind.TEXT,
        hint=(
            "Tells the drafting step how to write a Knowledge document’s “when it "
            "helps”, which the Reply Plan reads to pick documents. Runs when a "
            "document is made ready without one."
        ),
    ),
    EditableSetting(
        KNOWLEDGE_WHEN_IT_HELPS_MODEL.key,
        "Knowledge “when it helps” model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        KNOWLEDGE_WHEN_IT_HELPS_THINKING.key,
        "Knowledge “when it helps” thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        PERSONAL_STICKERS_LIMIT.key,
        "Most Personal Stickers per User",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=200,
        hint=(
            "Most stickers Personal Sticker keeping keeps from one User. When it would "
            "keep more, it drops the one used longest ago."
        ),
    ),
    EditableSetting(
        STICKER_ADDING_QUIET_GAP.key,
        "Sticker adding quiet gap",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=60,
        hint=(
            "Minutes without a sticker before adding stickers in chat ends and the "
            "Reply says what was added."
        ),
    ),
    EditableSetting(
        CHECK_IN_PROMPT.key,
        "Check-in prompt",
        SettingKind.TEXT,
        hint=(
            "Tells the Check-ins step whether to reach out, with which Check-in Kind "
            "and what to say, or to give space. Runs on the scheduler tick for Users "
            "who are due."
        ),
    ),
    EditableSetting(
        CHECK_IN_MODEL.key,
        "Check-in model",
        SettingKind.MODEL,
        hint=MODEL_HINT,
    ),
    EditableSetting(
        CHECK_IN_THINKING.key,
        "Check-in thinking",
        SettingKind.ON_OFF,
        hint=THINKING_HINT,
    ),
    EditableSetting(
        CHECK_IN_GAPS.key,
        "Check-in gaps",
        SettingKind.HOURS_BY_FREQUENCY,
        minimum=1,
        maximum=720,
        hint=(
            "Fewest hours between two Check-ins, for each frequency a User can pick. "
            "The scheduler checks it before a User is due."
        ),
    ),
    EditableSetting(
        CHECK_IN_IGNORE_THRESHOLD.key,
        "Ignore threshold",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=10,
        hint=(
            "Unanswered Check-ins in a row before the scheduler pauses a User’s "
            "Check-ins and asks once about fewer."
        ),
    ),
    EditableSetting(
        CHECK_IN_FEWER_MESSAGE.key,
        "“Would you like fewer?” message",
        SettingKind.TEXT,
        max_length=1_000,
        hint=(
            "Sent once by the Check-ins scheduler when a User reaches the ignore "
            "threshold, asking whether they’d like fewer Check-ins."
        ),
    ),
    EditableSetting(
        OLDER_SUMMARIES_PER_REPLY.key,
        "Most older Conversations per reply",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=10,
        hint=(
            "When the Understanding asks to look up the past, how many older Day "
            "Summaries Recall may add beyond the newest ones."
        ),
    ),
    EditableSetting(
        OLDER_SUMMARIES_CLOSENESS_PERCENT.key,
        "Older Conversation closeness bar",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
        hint=(
            "How close in meaning an older Day Summary must be to what the "
            "Understanding looks up for Recall to add it. Real matches score about "
            "70–80; unrelated ones up to about 65."
        ),
    ),
    EditableSetting(
        LIFE_THREADS_PER_REPLY.key,
        "Most Life Threads in mind",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=30,
        hint=(
            "How many Life Threads the Reply Plan can have in mind at once: those "
            "the message brings to mind first, then earlier ones in the "
            "Conversation. Set high; it is only there to protect cost."
        ),
    ),
    EditableSetting(
        LIFE_THREADS_TEXTS_TO_SEARCH.key,
        "Texts searched for Life Threads",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=30,
        hint=(
            "How many of the User’s latest texts Recall searches Life Threads and "
            "Patterns on, together with what the Understanding says they mean."
        ),
    ),
    EditableSetting(
        LIFE_THREADS_CLOSENESS_PERCENT.key,
        "Life Thread closeness bar",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
        hint=(
            "How close in meaning a Thread’s story must be to what the User means "
            "and their latest texts for Recall to bring it to mind. A Thread naming "
            "someone or something they mention always counts."
        ),
    ),
    EditableSetting(
        MOVE_OUTCOMES_PER_UNDERSTANDING.key,
        "Most Move Outcomes per Reply Plan",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=10,
        hint=(
            "How many of the User’s past Move Outcomes, closest first, the "
            "Reply Plan sees before each reply."
        ),
    ),
    EditableSetting(
        MOVE_OUTCOMES_CLOSENESS_PERCENT.key,
        "Move Outcome closeness bar",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
        hint=(
            "How close in meaning a Move Outcome must be to the User’s last few texts "
            "for the Reply Plan to see it. Real matches score about 75–85; "
            "unrelated ones up to about 62."
        ),
    ),
    EditableSetting(
        LIFE_THREAD_BRUSHED_OFF_WAIT.key,
        "Wait after a brushed-off Life Thread",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=365,
        hint=(
            "Days before the Reply Plan may bring up a Life Thread again after the "
            "User brushed it off. One they asked to drop is never brought up again."
        ),
    ),
    EditableSetting(
        PATTERN_CLOSENESS_PERCENT.key,
        "Pattern closeness bar",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
        hint=(
            "How close in meaning a Pattern must be to what the User means and "
            "their latest texts for Recall to bring it to mind with no Thread. "
            "Fits score about 47–66 and small talk up to about 61, so a low bar "
            "brings in some noise."
        ),
    ),
    EditableSetting(
        PATTERN_WEAK_SIGN_POINTS.key,
        "Points for a weak sign",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=1000,
        hint=(
            "What an Observation matching a weak sign of its Pattern Type is "
            "worth, before its kind of evidence and fading. Scoring runs at "
            "Conversation end after tagging, and when Observations are deleted."
        ),
    ),
    EditableSetting(
        PATTERN_MODERATE_SIGN_POINTS.key,
        "Points for a moderate sign",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=1000,
        hint=(
            "What an Observation matching a moderate sign is worth, before its "
            "kind of evidence and fading."
        ),
    ),
    EditableSetting(
        PATTERN_STRONG_SIGN_POINTS.key,
        "Points for a strong sign",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=1000,
        hint=(
            "What an Observation matching a strong sign is worth, before its "
            "kind of evidence and fading."
        ),
    ),
    EditableSetting(
        PATTERN_REAL_STORY_PERCENT.key,
        "Real story counts",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
        hint=(
            "How much of its sign's points an Observation from something that "
            "really happened keeps."
        ),
    ),
    EditableSetting(
        PATTERN_REPORTED_HABIT_PERCENT.key,
        "Reported habit counts",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
        hint=(
            "How much of its sign's points an Observation keeps when the User "
            "says what they usually do."
        ),
    ),
    EditableSetting(
        PATTERN_WHAT_IF_PERCENT.key,
        "“What if” answer counts",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
        hint=(
            "How much of its sign's points an Observation keeps when it answers "
            "a made-up situation."
        ),
    ),
    EditableSetting(
        PATTERN_OWN_OPINION_PERCENT.key,
        "Own opinion counts",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
        hint=(
            "How much of its sign's points an Observation keeps when it is the "
            "User's opinion of themselves."
        ),
    ),
    EditableSetting(
        PATTERN_UNCLEAR_PERCENT.key,
        "Unclear counts",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
        hint=(
            "How much an unclear Observation, naming two look-alike Pattern "
            "Types, keeps toward each of them."
        ),
    ),
    EditableSetting(
        PATTERN_HALF_LIFE_DAYS.key,
        "Pattern evidence half-life",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=3650,
        hint=(
            "After this many days an Observation counts half, and a quarter "
            "after twice as long, so Patterns keep up with who the User is now."
        ),
    ),
    EditableSetting(
        PATTERN_PEOPLE_PER_SITUATION.key,
        "Most people per situation",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=50,
        hint=(
            "Within one Life Thread only the strongest Observation per person "
            "counts, for and against apart; this many people at most add "
            "weight."
        ),
    ),
    EditableSetting(
        PATTERN_SUSPECTED_SITUATIONS.key,
        "Situations to be suspected",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=50,
        hint=(
            "How many situations (Life Threads; with none, the same person and "
            "setting) a noticed Pattern must show in to become suspected."
        ),
    ),
    EditableSetting(
        PATTERN_SUSPECTED_POINTS.key,
        "Score to be suspected",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=10000,
        hint=(
            "The lowest score, in points, at which a noticed Pattern seen in "
            "enough situations becomes suspected. Under it, a suspected one "
            "goes back to noticed."
        ),
    ),
    EditableSetting(
        PATTERN_CLOSED_UNDER_POINTS.key,
        "Score that closes a Pattern",
        SettingKind.WHOLE_NUMBER,
        minimum=-10000,
        maximum=0,
        hint=(
            "A noticed or suspected Pattern whose score falls under this, in "
            "points, is closed. One whose score comes back over it is noticed "
            "again."
        ),
    ),
    EditableSetting(
        PATTERN_PUSHED_BACK_WAIT.key,
        "Wait after a pushed-back Pattern",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=365,
        hint=(
            "Days before a Pattern the User pushed back on comes to mind for the "
            "Reply Plan again, so Zeph doesn't offer the same view too soon. A "
            "closed Pattern never comes back."
        ),
    ),
    EditableSetting(
        CURIOSITIES_PER_CONVERSATION.key,
        "Most Curiosities raised per Conversation",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=5,
        hint=(
            "How many Curiosities can be raised in one Conversation; until then, due "
            "ones are offered to the Reply Plan before each reply. 0 means none."
        ),
    ),
    EditableSetting(
        CURIOSITIES_PER_REPLY.key,
        "Most Curiosities per reply",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=5,
        hint=(
            "How many Curiosities one reply may ask. Most Curiosities raised per "
            "Conversation still caps it."
        ),
    ),
    EditableSetting(
        CURIOSITY_HELD_WHEN_ASKING_WHY.key,
        "Hold a Curiosity when the reply asks why",
        SettingKind.ON_OFF,
        hint=(
            "When on, a reply that asks why they feel as they do asks no "
            "Curiosity too, and it stays due. When off, the reply can ask both."
        ),
    ),
    EditableSetting(
        CURIOSITIES_WAITING_LIMIT.key,
        "Most Curiosities waiting at once",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=50,
        hint=(
            "Most Curiosities waiting at once. When a Conversation’s end makes more, "
            "Curiosity keeping closes the oldest."
        ),
    ),
    EditableSetting(
        CURIOSITY_REPLIES_BETWEEN.key,
        "Fewest replies between Curiosities",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=50,
        hint=(
            "How many replies must pass after a Curiosity is raised, in any "
            "Conversation, before another is offered to the Reply Plan."
        ),
    ),
    EditableSetting(
        FOLLOW_UPS_PER_CONVERSATION.key,
        "Most follow-up questions per Conversation",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=10,
        hint=(
            "How many replies in one Conversation may make a Move that asks a "
            "question, such as Get curious. These don't use the Curiosity limit."
        ),
    ),
    EditableSetting(
        CURIOSITY_BRUSH_OFFS_TO_BACK_OFF.key,
        "Brush-offs before backing off",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=10,
        hint=(
            "After this many Curiosities brushed off in a row, none is offered for "
            "the rest of the Conversation and the spacing doubles. One engaged "
            "answer ends it."
        ),
    ),
    EditableSetting(
        CURIOSITY_BACK_OFF.key,
        "Days of doubled spacing",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=60,
        hint=(
            "How long the fewest replies between Curiosities stays doubled after "
            "Zeph backs off, counted from the last brush-off."
        ),
    ),
    EditableSetting(
        CURIOSITY_CHECK_INS_PER_WEEK.key,
        "Most Curiosity Check-ins per week",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=7,
        hint=(
            "How many “Something I’ve been wondering” Check-ins the Check-ins step may "
            "send a User in any 7 days; 0 means none."
        ),
    ),
    EditableSetting(
        KNOWLEDGE_CLOSENESS_PERCENT.key,
        "Knowledge closeness bar",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=100,
        hint=(
            "How close in meaning a passage must be, inside the Knowledge documents "
            "the Reply Plan chose, for the Reply to get it. Fitting passages score "
            "about 65–75; unrelated ones about 50."
        ),
    ),
    EditableSetting(
        CONVERSATION_QUIET_GAP.key,
        "Conversation quiet gap",
        SettingKind.WHOLE_NUMBER,
        minimum=5,
        maximum=1440,
        hint=(
            "Minutes of silence before a Conversation ends and the Conversation-end "
            "steps run."
        ),
    ),
    EditableSetting(
        MESSAGE_WAIT_FINISHED_SECONDS.key,
        "Wait after a finished text",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=60,
        hint=(
            "Seconds Zeph waits for more when the User’s last text reads finished "
            "(a question, or a long text ending in a full stop, “!” or an emoji). "
            "Shorter means quicker replies, with more chance of cutting the User off."
        ),
    ),
    EditableSetting(
        MESSAGE_WAIT_TRAILING_SECONDS.key,
        "Wait after a trailing text",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=60,
        hint=(
            "Seconds Zeph waits for more when the User’s last text ends unfinished "
            "(“and…”, “so”, “wait”, a photo with no caption). Longer means fewer "
            "cut-offs but slower replies."
        ),
    ),
    EditableSetting(
        MESSAGE_WAIT_SECONDS.key,
        "Wait after any other text",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=60,
        hint=(
            "Seconds Zeph waits for more when the User’s last text reads neither "
            "finished nor trailing, or is a sticker. Longer gathers more texts into "
            "one reply but makes every reply slower."
        ),
    ),
    EditableSetting(
        MESSAGE_WAIT_CAP_SECONDS.key,
        "Wait cap",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=60,
        hint=(
            "Most seconds Zeph waits from the first text of a Message, however many "
            "texts follow, and never less than the longest wait. Shorter means a "
            "long burst of texts is answered sooner, with more chance of cutting "
            "the User off."
        ),
    ),
    EditableSetting(
        MESSAGE_WAIT_LONG_TEXT_WORDS.key,
        "Long text",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=100,
        hint=(
            "How many words a text ending in a full stop, “!” or an emoji needs to "
            "read finished and get the short wait. Fewer words means more texts are "
            "answered quickly."
        ),
    ),
    EditableSetting(
        MESSAGE_WAIT_TRAILING_WORDS.key,
        "Trailing words",
        SettingKind.TEXT_LIST,
        hint=(
            "Words that make a text trail off when they end it, and short openers "
            "(“ok so”, “hmm”) that do when sent alone, separated by commas. Adding "
            "a word makes Zeph wait longer after texts that end with it."
        ),
    ),
    EditableSetting(
        RECENT_MESSAGES_HOURS.key,
        "Recent messages",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=72,
        hint=(
            "Hours of messages, across Conversations, that the Understanding, Reply "
            "Plan and Reply see word for word. More hours remember more and cost "
            "more per Message."
        ),
    ),
    EditableSetting(
        RECENT_MESSAGES_CAP.key,
        "Recent messages cap",
        SettingKind.WHOLE_NUMBER,
        minimum=4,
        maximum=2000,
        hint=(
            "On a very heavy day, the oldest messages past this many are left out "
            "of the Recent Messages and their Day Summary stands in, to keep the cost "
            "fixed."
        ),
    ),
    EditableSetting(
        TYPING_REPEAT_SECONDS.key,
        "Typing repeat",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=5,
        hint=(
            "How often the Reply shows “typing” again while it is being written, since "
            "Telegram hides it after about 5 seconds."
        ),
    ),
    EditableSetting(
        DAILY_MESSAGE_LIMIT.key,
        "Daily message limit",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=10_000,
        hint=(
            "Messages a User can send per day before the Reply gate stops replying and "
            "sends the Limit-reached reply. Safety replies never count toward it."
        ),
    ),
    EditableSetting(
        DAILY_LIMIT_REPLY.key,
        "Limit-reached reply",
        SettingKind.TEXT,
        max_length=1_000,
        hint=(
            "Sent in Telegram by the Reply gate when a User hits the daily message "
            "limit."
        ),
    ),
    EditableSetting(
        ONBOARDING_UNFINISHED_REPLY.key,
        "“Finish onboarding first” reply",
        SettingKind.TEXT,
        max_length=1_000,
        required_placeholders=(
            RequiredPlaceholder(DASHBOARD_URL_PLACEHOLDER, "the link to the Dashboard"),
        ),
        hint=(
            "Sent by the Telegram connection step when someone uses a connection link "
            "before finishing onboarding. {dashboard_url} becomes the Dashboard’s "
            "address."
        ),
    ),
    EditableSetting(
        MESSAGE_RETENTION_DAYS.key,
        "Message retention",
        SettingKind.WHOLE_NUMBER,
        minimum=1,
        maximum=365,
        hint=(
            "Days messages are kept before the Message Retention clean-up deletes "
            "them; Day Summaries stay. Shown to Users on Account & privacy."
        ),
    ),
    EditableSetting(
        WEB_SEARCH_DAILY_LIMIT.key,
        "Per-user daily web search limit",
        SettingKind.WHOLE_NUMBER,
        minimum=0,
        maximum=1000,
        hint=(
            "Web searches and page reads the Reply may make for one User per day, "
            "reset at their midnight. After that the Web Search Limit reached note is "
            "used instead."
        ),
    ),
    EditableSetting(
        MEMORY_OFF_CHAT_LINE.key,
        "“Memory off” line in chat",
        SettingKind.TEXT,
        max_length=1_000,
        hint=(
            "Sent by Settings in Chat as its own message after the reply, when a User "
            "turns memory off in chat."
        ),
    ),
    EditableSetting(
        DATA_DELETED_REPLY.key,
        "“Data deleted” reply",
        SettingKind.TEXT,
        max_length=1_000,
        hint=(
            "Sent by Delete My Data in chat once the User’s data is deleted, after "
            "they sent the confirmation word."
        ),
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
        thinking_key=SAFEGUARD_THINKING.key,
    ),
    CoreService(
        name="Understanding",
        runs_when="Every Message · first",
        description=(
            "Reads each Message: what the User said and means, how they feel, "
            "and what they want. It reads only and decides nothing."
        ),
        prompt_key=UNDERSTANDING_PROMPT.key,
        model_key=UNDERSTANDING_MODEL.key,
        thinking_key=UNDERSTANDING_THINKING.key,
    ),
    CoreService(
        name="Reply Plan",
        runs_when="Every Message · after the Understanding",
        description=(
            "Decides what the reply should do: the Need, the Moves, which "
            "Threads to bring up, whether a Check-in fits, and Zeph’s Read."
        ),
        prompt_key=REPLY_PLAN_PROMPT.key,
        model_key=REPLY_PLAN_MODEL.key,
        thinking_key=REPLY_PLAN_THINKING.key,
        extra_prompt_keys=(SHARED_PHOTOS_MEMORY_DESCRIPTION.key,),
    ),
    CoreService(
        name="Response composition",
        runs_when="Every reply",
        description=(
            "Writes Zeph’s reply from the Persona, the relevant memories, recent "
            "Day Summaries, Knowledge and the Conversation so far."
        ),
        prompt_key=RESPONSE_PROMPT.key,
        model_key=RESPONSE_MODEL.key,
        thinking_key=RESPONSE_THINKING.key,
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
                    DATA_DELETION_STARTED_NOTE.key,
                    REPLY_DATA_DELETION_CANCELLED_NOTE.key,
                    REPLY_DATA_DELETION_WORD_NOT_ALONE_NOTE.key,
                ),
            ),
            ExtraPromptGroup(
                "Memory and Knowledge",
                (REPLY_MEMORY_INTRO.key, REPLY_KNOWLEDGE_INTRO.key),
            ),
            ExtraPromptGroup("Reply Plan", (REPLY_ASK_WHY_NOTE.key,)),
            ExtraPromptGroup("Features", (REPLY_FEATURES_UNAVAILABLE_NOTE.key,)),
            ExtraPromptGroup("Stickers", (STICKER_TOOL_DESCRIPTION.key,)),
        ),
    ),
    CoreService(
        name="Post-conversation processing",
        runs_when="After quiet gap",
        description=(
            "After a Conversation goes quiet, rewrites the day's Day Summary "
            "and mood, and adds, updates or removes Memory Items by category."
        ),
        prompt_key=MEMORY_PROCESSING_PROMPT.key,
        model_key=MEMORY_PROCESSING_MODEL.key,
        thinking_key=MEMORY_PROCESSING_THINKING.key,
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
        thinking_key=PHOTO_THINKING.key,
        extra_prompt_keys=(
            ASK_ABOUT_PHOTO_TOOL_DESCRIPTION.key,
            SEND_PHOTO_TOOL_DESCRIPTION.key,
        ),
    ),
    CoreService(
        name="Life Thread keeping",
        runs_when="After quiet gap, while User Memory works",
        description=(
            "Starts and adds to the User’s Life Threads: the ongoing stories "
            "in their life, open or settled, with the people or things in "
            "them. Records how the User took each Thread Zeph brought up, so "
            "it isn’t raised again too soon, or at all once they asked to "
            "drop it."
        ),
        prompt_key=LIFE_THREAD_KEEPING_PROMPT.key,
        model_key=LIFE_THREAD_KEEPING_MODEL.key,
        thinking_key=LIFE_THREAD_KEEPING_THINKING.key,
    ),
    CoreService(
        name="Curiosity keeping",
        runs_when="After quiet gap, while User Memory and Curiosities work",
        description=(
            "Writes the things Zeph wants to ask the User later, each with why, "
            "a “not before” day and how sensitive it is. Records how the User "
            "took the ones Zeph asked, closes ones no longer relevant, and "
            "closes the oldest waiting ones over the limit."
        ),
        prompt_key=CURIOSITY_KEEPING_PROMPT.key,
        model_key=CURIOSITY_KEEPING_MODEL.key,
        thinking_key=CURIOSITY_KEEPING_THINKING.key,
    ),
    CoreService(
        name="Move Outcome keeping",
        runs_when="After quiet gap, while User Memory works",
        description=(
            "Writes what Zeph learned about each Move it made: the situation, "
            "how the User felt, whether it helped, didn’t or was mixed, and "
            "why. Runs only when the Conversation’s Reply Plans made a "
            "Move. Users see these under “What helps you”."
        ),
        prompt_key=MOVE_OUTCOME_KEEPING_PROMPT.key,
        model_key=MOVE_OUTCOME_KEEPING_MODEL.key,
        thinking_key=MOVE_OUTCOME_KEEPING_THINKING.key,
    ),
    CoreService(
        name="User Portrait",
        runs_when="After quiet gap while User Memory works, and after a deletion",
        description=(
            "Writes a short picture of the User from their Memory Items, Life "
            "Threads, Move Outcomes and newest Day Summaries: who "
            "they are, what’s going on now, recurring themes, what helps and "
            "what doesn’t, and where they stand on their Goals. Every "
            "Understanding, Reply Plan and reply sees it. When the User deletes "
            "a Memory Item, Life Thread, Move Outcome or Summary, it is written "
            "again without it."
        ),
        prompt_key=PORTRAIT_PROMPT.key,
        model_key=PORTRAIT_MODEL.key,
        thinking_key=PORTRAIT_THINKING.key,
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
        thinking_key=PERSONAL_STICKER_KEEPING_THINKING.key,
    ),
    CoreService(
        name="Knowledge “when it helps”",
        runs_when="When a Knowledge document is made ready without one",
        description=(
            "Drafts a Knowledge document’s “when it helps” description from "
            "its details and text. The Reply Plan reads these to decide "
            "whether any document fits. Admins can rewrite it on the "
            "document’s page."
        ),
        prompt_key=KNOWLEDGE_WHEN_IT_HELPS_PROMPT.key,
        model_key=KNOWLEDGE_WHEN_IT_HELPS_MODEL.key,
        thinking_key=KNOWLEDGE_WHEN_IT_HELPS_THINKING.key,
    ),
    CoreService(
        name="Check-ins",
        runs_when=(
            "Scheduler tick, for Users who are due; after a reply offered a "
            "Woven-in Check-in"
        ),
        description=(
            "Decides whether to reach out to a User who opted in, which "
            "Check-in Kind to use and what to say, or to skip and give space, "
            "from their recent Day Summaries and Memory Items. When one "
            "comes due mid-Conversation, the Reply Plan weighs it instead; "
            "this model, without thinking, then checks whether the reply "
            "brought it up, so it is logged only when sent."
        ),
        prompt_key=CHECK_IN_PROMPT.key,
        model_key=CHECK_IN_MODEL.key,
        thinking_key=CHECK_IN_THINKING.key,
    ),
    CoreService(
        name="Pattern tagging",
        runs_when="Conversation end · after Life Threads, while Pattern noticing works",
        description=(
            "Reads the Conversation into the Pattern Catalog: each Observation "
            "with its Pattern Type and sign, for or against, the User’s exact "
            "quote and its situation tags. Code drops any whose Pattern Type, "
            "sign, quote or tags don’t check out. Nothing reaches a reply."
        ),
        prompt_key=PATTERN_TAGGING_PROMPT.key,
        model_key=PATTERN_TAGGING_MODEL.key,
        thinking_key=PATTERN_TAGGING_THINKING.key,
    ),
    CoreService(
        name="Pattern keeping",
        runs_when="Conversation end · after Life Threads",
        description=(
            "Looks across Life Threads for the same way of thinking, feeling or "
            "acting, and keeps it as a Pattern."
        ),
        prompt_key=PATTERN_KEEPING_PROMPT.key,
        model_key=PATTERN_KEEPING_MODEL.key,
        thinking_key=PATTERN_KEEPING_THINKING.key,
        limit_keys=(PATTERN_KEEPING_THREADS.key, PATTERN_KEEPING_DAYS.key),
    ),
)


EDITABLE_SETTINGS_BY_KEY: dict[str, EditableSetting] = {
    setting.key: setting for setting in EDITABLE_SETTINGS
}


@dataclass(frozen=True)
class DashboardContent:
    """Admin-managed settings the Dashboard shows to Users.

    The words around them are Copy (ADR-0019).

    Attributes:
        onboarding_reason_choices: The "What brings you here?" choices.
        message_retention_days: How many days messages are kept.
    """

    onboarding_reason_choices: list[str]
    message_retention_days: int


class InvalidSettingError(InvalidError):
    """Raised when a setting change is not allowed or its value is not valid."""


def checked_text_list(setting: EditableSetting, value: Any) -> list[str]:
    """Check a new list of words, trimming and lower-casing each.

    Args:
        setting: The list setting.
        value: The new value.

    Returns:
        The words, trimmed and lower-cased, with blank ones left out.

    Raises:
        InvalidSettingError: If the value is not a list of texts, or has no
            words in it.
    """
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise InvalidSettingError(f"The {setting.label} must be a list of words.")
    words = [item.strip().lower() for item in value if item.strip()]
    if not words:
        raise InvalidSettingError(f"The {setting.label} needs at least one word.")
    return words


def check_waits_fit_under_the_cap(
    settings: PlatformSettings, values: Mapping[str, Any]
) -> None:
    """Check the Message wait cap is at least as long as each wait, after a change.

    Only a change to a wait or the cap is checked, so other settings can
    always be saved.

    Args:
        settings: The platform settings before the change.
        values: The checked new value for each setting key being changed.

    Raises:
        InvalidSettingError: If the cap would be shorter than any of the
            three waits.
    """
    keys_checked = {wait.key for wait in MESSAGE_WAITS} | {MESSAGE_WAIT_CAP_SECONDS.key}
    if not keys_checked & values.keys():
        return
    longest_wait = max(
        values.get(wait.key, settings.get(wait)) for wait in MESSAGE_WAITS
    )
    cap = values.get(
        MESSAGE_WAIT_CAP_SECONDS.key, settings.get(MESSAGE_WAIT_CAP_SECONDS)
    )
    if cap < longest_wait:
        raise InvalidSettingError(
            f"The Wait cap must be at least the longest wait ({longest_wait} seconds)."
        )


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
        """Read the Admin-managed settings the Dashboard shows to Users.

        Returns:
            The onboarding choices and how long messages are kept.
        """
        settings = self._settings.load()
        return DashboardContent(
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
            InvalidSettingError: If a key may not be changed, a value is not
                valid, or the Message wait cap would be shorter than a wait;
                nothing is saved.
        """
        validated_values = {
            key: self.checked_value(key, value) for key, value in values.items()
        }
        check_waits_fit_under_the_cap(self._settings.load(), validated_values)
        if validated_values:
            self._settings.save_many(validated_values, self._clock.now(), admin.id)
        return self.list_editable()

    def checked_value(self, key: str, value: Any) -> Any:
        """Check one new value against its setting's rule, without saving it.

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
        if setting.kind == SettingKind.ON_OFF:
            if not isinstance(value, bool):
                raise InvalidSettingError(f"The {setting.label} must be on or off.")
            return value
        if setting.kind == SettingKind.TEXT_LIST:
            return checked_text_list(setting, value)
        if setting.kind == SettingKind.HOURS_BY_FREQUENCY:
            if not is_hours_by_frequency(value, setting.minimum, setting.maximum):
                raise InvalidSettingError(
                    f"The {setting.label} must give each frequency a whole "
                    f"number of hours from {setting.minimum} to {setting.maximum}."
                )
            return value
        if value not in self.model_choices():
            raise InvalidSettingError(
                f"The {setting.label} must be one of the listed models."
            )
        return value
