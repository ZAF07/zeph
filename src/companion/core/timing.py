from datetime import datetime, timedelta

from companion.core.models import Conversation
from companion.core.ports import PlatformSettingsRepository


def quiet_gap(settings: PlatformSettingsRepository) -> timedelta:
    """Read how long with no message ends a Conversation.

    Args:
        settings: Holds the Admin-set quiet gap.

    Returns:
        The quiet gap.
    """
    return timedelta(minutes=settings.get("conversation_quiet_gap_minutes"))


def check_in_reply_window(settings: PlatformSettingsRepository) -> timedelta:
    """Read how long after a Check-in the User's first message is its reply.

    Args:
        settings: Holds the reply window.

    Returns:
        The reply window.
    """
    return timedelta(hours=settings.get("check_in_reply_window_hours"))


def is_open(conversation: Conversation, now: datetime, gap: timedelta) -> bool:
    """Tell whether a new message would join a Conversation.

    A Conversation is open until it is ended or the quiet gap passes.

    Args:
        conversation: The Conversation.
        now: The current time.
        gap: How long with no message ends a Conversation.

    Returns:
        True if it is still open.
    """
    return conversation.ended_at is None and now - conversation.last_message_at < gap
