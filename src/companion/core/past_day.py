from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from companion.core.models import UserSnapshot
from companion.core.platform_settings import MESSAGE_RETENTION_DAYS
from companion.core.ports import ChatTool, Repositories
from companion.core.recent_messages import to_recent_transcript
from companion.core.timing import day_span

PAST_DAY_TOOL_NAME = "past_day"
PAST_DAY_DESCRIPTION = (
    "Read every message you and the person sent on one past day, word for word. "
    "Use it when they ask about a day and its Day Summary isn't detailed enough. "
    "Messages are kept for a limited number of days; after that there are none."
)
PAST_DAY_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "date": {
            "type": "string",
            "description": "The day, in their time zone, as YYYY-MM-DD.",
        }
    },
    "required": ["date"],
}
DATE_NEEDED_NOTE = "Reading a past day needs its date as YYYY-MM-DD."
NO_EXACT_WORDS_NOTE = (
    "Answer from that day's Day Summary, if there is one, and don't claim to "
    "know their exact words."
)


def parse_day_argument(value: Any) -> date | None:
    """Read the day the model asked for.

    Args:
        value: The "date" argument, e.g. "2026-11-12".

    Returns:
        The day; None if it isn't a date written as YYYY-MM-DD.
    """
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


class PastDayTool:
    """Lets the Reply Plan read a past day's messages, within Message Retention."""

    def __init__(self, repositories: Repositories) -> None:
        """Set up the tool.

        Args:
            repositories: Where messages are stored.
        """
        self._repositories = repositories

    def tool_for(
        self, snapshot: UserSnapshot, on_read: Callable[[str], None]
    ) -> ChatTool:
        """Make the past-day tool for one Reply Plan.

        Args:
            snapshot: The User being answered; only their messages are read.
            on_read: Called with what each call of the tool read, so the
                reply can be given it too.

        Returns:
            The tool.
        """

        def run(arguments: dict[str, Any]) -> str:
            """Read the User's messages from the day the model asked for.

            Args:
                arguments: The model's arguments, with the "date".

            Returns:
                E.g. "14 messages from 12 Nov:" and the transcript; none for
                a day past Message Retention, with a note to answer from the
                Day Summary without claiming exact words.
            """
            day = parse_day_argument(arguments.get("date"))
            if day is None:
                return DATE_NEEDED_NOTE
            day_transcript = self.read_day(snapshot, day)
            on_read(day_transcript)
            return day_transcript

        return ChatTool(
            name=PAST_DAY_TOOL_NAME,
            description=PAST_DAY_DESCRIPTION,
            parameters=PAST_DAY_PARAMETERS,
            run=run,
        )

    def read_day(self, snapshot: UserSnapshot, day: date) -> str:
        """Write the User's messages from one day, as the Reply Plan reads them.

        A day wholly older than `message_retention_days` has no messages,
        even before the clean-up has deleted them. On the day retention
        reaches into, the start of the day may be gone, and it says so.

        Args:
            snapshot: The User being answered.
            day: The day, in their time zone.

        Returns:
            How many messages there were and their transcript, or that there
            are none.
        """
        short_day = f"{day.day} {day:%b}"
        retention = timedelta(days=snapshot.settings.get(MESSAGE_RETENTION_DAYS))
        time_zone = snapshot.user.time_zone
        if day < snapshot.today - retention:
            return (
                f"No messages from {short_day}: messages are only kept for "
                f"{retention.days} days. {NO_EXACT_WORDS_NOTE}"
            )
        messages = self._repositories.conversations.list_user_messages_between(
            snapshot.user.id, *day_span(day, time_zone)
        )
        if not messages:
            return f"No messages from {short_day}. {NO_EXACT_WORDS_NOTE}"
        how_many = "1 message" if len(messages) == 1 else f"{len(messages)} messages"
        transcript = to_recent_transcript(messages, time_zone)
        partly_deleted = (
            f"\n\nMessages are only kept for {retention.days} days, so the "
            f"start of {short_day} may already be gone."
            if day == snapshot.today - retention
            else ""
        )
        return f"{how_many} from {short_day}:\n{transcript}{partly_deleted}"
