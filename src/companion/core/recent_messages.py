from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from uuid import UUID

from companion.core.memory_retrieval import format_day, format_time, summary_line
from companion.core.models import (
    ConversationMessage,
    DaySummary,
    MessageDirection,
    UserSnapshot,
)
from companion.core.platform_settings import (
    RECENT_MESSAGES_CAP,
    RECENT_MESSAGES_HOURS,
)
from companion.core.ports import Clock, Repositories
from companion.core.timing import users_today
from companion.core.transcripts import to_transcript_lines


@dataclass(frozen=True)
class RecentMessages:
    """Every message from the last hours, across Conversations, that a reply sees.

    Attributes:
        conversation_id: The Conversation being replied in.
        messages: The messages, oldest first; the User's messages at the end
            are the Message being answered.
        stand_ins: The Day Summaries standing in for the oldest messages
            left out past the cap, oldest day first; empty if none were.
    """

    conversation_id: UUID
    messages: list[ConversationMessage]
    stand_ins: Sequence[DaySummary] = field(default_factory=tuple)


def leave_out_past_cap(
    messages: list[ConversationMessage], cap: int
) -> tuple[list[ConversationMessage], list[ConversationMessage]]:
    """Split the messages into the newest that fit under the cap and the rest.

    Args:
        messages: The messages, oldest first.
        cap: The most messages to keep.

    Returns:
        The newest `cap` messages, and the older ones left out, each oldest
        first.
    """
    left_out = max(len(messages) - cap, 0)
    return messages[left_out:], messages[:left_out]


def starts_new_conversation(
    previous: ConversationMessage, message: ConversationMessage
) -> bool:
    """Say whether a message is the first of a later Conversation.

    Args:
        previous: The message before it.
        message: The message.

    Returns:
        True if the two are in different Conversations.
    """
    return message.conversation_id != previous.conversation_id


def split_off_latest_message(
    recent: RecentMessages,
) -> tuple[list[ConversationMessage], list[ConversationMessage]]:
    """Split the Recent Messages into what came before the latest Message and it.

    The latest Message is the User's texts in a row at the end of the
    Conversation being replied in; texts left unanswered at the end of an
    earlier Conversation are not part of it.

    Args:
        recent: The Recent Messages.

    Returns:
        The earlier messages and the latest Message's texts, each oldest
        first.
    """
    messages = recent.messages
    latest_start = len(messages)
    while latest_start > 0:
        message = messages[latest_start - 1]
        if (
            message.direction != MessageDirection.INCOMING
            or message.conversation_id != recent.conversation_id
        ):
            break
        latest_start -= 1
    return messages[:latest_start], messages[latest_start:]


def new_conversation_line(message: ConversationMessage, time_zone: str | None) -> str:
    """Write the line that marks where a later Conversation started.

    Args:
        message: The Conversation's first message among the Recent Messages.
        time_zone: The User's IANA time zone; UTC if they have none.

    Returns:
        E.g. "--- New Conversation, 12 Nov 2026 00:10 ---".
    """
    started = message.sent_at
    return (
        f"--- New Conversation, {format_day(started, time_zone)} "
        f"{format_time(started, time_zone)} ---"
    )


def to_recent_transcript(
    messages: list[ConversationMessage], time_zone: str | None
) -> str:
    """Write messages across Conversations as transcript lines for a model to read.

    Args:
        messages: The messages, oldest first.
        time_zone: The User's IANA time zone, for when each Conversation
            started.

    Returns:
        One "Person: ..." or "Companion: ..." line per message, with a line
        before each later Conversation saying when it started.
    """
    lines = []
    for number, message in enumerate(messages):
        if number and starts_new_conversation(messages[number - 1], message):
            lines.append(new_conversation_line(message, time_zone))
        lines.append(to_transcript_lines([message]))
    return "\n".join(lines)


def describe_stand_ins(stand_ins: Sequence[DaySummary]) -> str:
    """Write the Day Summaries standing in for messages left out past the cap.

    Args:
        stand_ins: The Day Summaries, oldest day first.

    Returns:
        A heading and one line per day; "" if there are none.
    """
    if not stand_ins:
        return ""
    lines = "\n".join(summary_line(summary) for summary in stand_ins)
    return f"Older messages left out on a long day, as their Day Summary:\n{lines}"


def describe_recent_messages(recent: RecentMessages, time_zone: str | None) -> str:
    """Write the Recent Messages for a model to read, ending with the latest Message.

    Args:
        recent: The Recent Messages.
        time_zone: The User's IANA time zone.

    Returns:
        The Day Summaries standing in, if any, then the earlier messages
        across Conversations, then the latest Message, with a line before it
        when it started a new Conversation.
    """
    earlier, latest = split_off_latest_message(recent)
    transcript = to_recent_transcript(earlier, time_zone) or "Nothing yet."
    latest_text = "\n".join(message.content for message in latest)
    latest_heading = (
        f"{new_conversation_line(latest[0], time_zone)}\nLatest message:"
        if earlier and latest and starts_new_conversation(earlier[-1], latest[0])
        else "Latest message:"
    )
    parts = [
        describe_stand_ins(recent.stand_ins),
        f"Earlier messages, across Conversations:\n{transcript}",
        f"{latest_heading}\nPerson: {latest_text}",
    ]
    return "\n\n".join(part for part in parts if part)


class RecentMessagesReader:
    """Reads the Recent Messages: every message from the last hours, all Conversations.

    The Understanding, the Reply Plan and the Reply all see them, so a new
    Conversation still has what was said earlier, even before midnight. On a
    very heavy day the oldest messages past an Admin-set cap are left out
    and the Day Summaries of their days stand in.
    """

    def __init__(self, repositories: Repositories, clock: Clock) -> None:
        """Set up the reader.

        Args:
            repositories: Where messages and Day Summaries are stored.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._clock = clock

    def read(self, snapshot: UserSnapshot, conversation_id: UUID) -> RecentMessages:
        """Read the Recent Messages for a reply in a Conversation.

        Args:
            snapshot: The User being answered.
            conversation_id: The Conversation being replied in.

        Returns:
            The messages from the last `recent_messages_hours`, at most
            `recent_messages_cap` of them, and the Day Summaries
            standing in for any left out.
        """
        settings = snapshot.settings
        now = self._clock.now()
        since = now - timedelta(hours=settings.get(RECENT_MESSAGES_HOURS))
        messages = self._repositories.conversations.list_user_messages_between(
            snapshot.user.id, since
        )
        kept, left_out = leave_out_past_cap(messages, settings.get(RECENT_MESSAGES_CAP))
        time_zone = snapshot.user.time_zone
        days = sorted({users_today(time_zone, message.sent_at) for message in left_out})
        stand_ins = (
            self._repositories.user_memory.list_summaries_for_days(
                snapshot.user.id, days
            )
            if days
            else []
        )
        return RecentMessages(
            conversation_id=conversation_id,
            messages=kept,
            stand_ins=tuple(sorted(stand_ins, key=lambda summary: summary.day)),
        )
