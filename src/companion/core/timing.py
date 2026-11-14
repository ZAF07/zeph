from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from companion.core.models import Conversation


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


def users_today(time_zone: str | None, now: datetime) -> date:
    """Work out today's date where a User lives.

    Args:
        time_zone: The User's time zone name, e.g. "Asia/Singapore"; None if
            they have none.
        now: The current time.

    Returns:
        Today's date in their time zone, or in UTC if they have none.
    """
    return (now.astimezone(ZoneInfo(time_zone)) if time_zone else now).date()


def local_now(time_zone: str | None, now: datetime) -> datetime:
    """Turn a time into the User's local time.

    Args:
        time_zone: The User's IANA time zone; UTC if they have none.
        now: The time, timezone-aware.

    Returns:
        The same moment in the User's time zone.
    """
    return now.astimezone(ZoneInfo(time_zone or "UTC"))
