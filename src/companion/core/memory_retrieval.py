import logging
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    ConversationSummary,
    MemoryCategory,
    MemoryItem,
)
from companion.core.ports import ChatModel, Repositories
from companion.core.response_composition import to_transcript_lines

logger = logging.getLogger(__name__)


def describe_message_for_picking(
    categories: list[MemoryCategory], messages: list[ConversationMessage]
) -> str:
    """Write what the memory retrieval model is given to pick categories.

    Args:
        categories: The Memory Categories it may pick from.
        messages: The Conversation so far, oldest first; the last one is the
            message being answered.

    Returns:
        The categories, the earlier Conversation and the latest message.
    """
    category_lines = "\n".join(
        f"- {category.name}: {category.description}" for category in categories
    )
    *earlier, latest = messages
    return (
        f"Memory Categories:\n{category_lines}\n\n"
        f"Earlier in the Conversation:\n"
        f"{to_transcript_lines(earlier) or 'Nothing yet.'}\n\n"
        f"Latest message:\nPerson: {latest.content}"
    )


def read_picked_categories(
    answer: str, categories: list[MemoryCategory]
) -> list[MemoryCategory]:
    """Read which categories the memory retrieval model picked.

    Each line of the answer may name one category, in any case and with
    bullets or punctuation around it; anything else is ignored.

    Args:
        answer: The model's answer.
        categories: The Memory Categories it could pick from.

    Returns:
        The picked categories, in their usual order.
    """
    picked_names = {line.strip(" -*•.,\"'").lower() for line in answer.splitlines()}
    return [
        category for category in categories if category.name.lower() in picked_names
    ]


def format_day(moment: datetime, time_zone: str | None) -> str:
    """Write a day like "9 Nov 2026" in the User's time zone.

    Args:
        moment: The moment.
        time_zone: The User's IANA time zone, if known; UTC otherwise.

    Returns:
        The day.
    """
    local = moment.astimezone(ZoneInfo(time_zone)) if time_zone else moment
    return f"{local.day} {local:%b %Y}"


def format_memory(
    categories: list[MemoryCategory],
    items: list[MemoryItem],
    summaries: list[ConversationSummary],
    time_zone: str | None,
    intro: str,
) -> str:
    """Write the User Memory part of the reply instructions.

    Args:
        intro: The Admin-set line that tells the model how to use memories.
        categories: The Memory Categories whose items go in, in order.
        items: The User's Memory Items.
        summaries: The newest Conversation Summaries, newest first.
        time_zone: The User's IANA time zone, for the summaries' days.

    Returns:
        The memory section, or "" if there is nothing to tell.
    """
    sections = []
    for category in categories:
        lines = [
            f"- {item.content}" for item in items if item.category_id == category.id
        ]
        if lines:
            sections.append(f"{category.name}:\n" + "\n".join(lines))
    if summaries:
        summary_lines = [
            f"- {format_day(summary.created_at, time_zone)}: {summary.summary} "
            f"They seemed {summary.mood}."
            for summary in summaries
        ]
        sections.append(
            "Recent Conversations, newest first:\n" + "\n".join(summary_lines)
        )
    if not sections:
        return ""
    return intro + "\n\n" + "\n\n".join(sections)


class MemoryRetrieval:
    """Finds the User Memory that matters for the message being answered."""

    def __init__(self, repositories: Repositories, chat_model: ChatModel) -> None:
        """Set up memory retrieval.

        Args:
            repositories: Where Users, Conversations, User Memory and
                settings are stored.
            chat_model: Picks the Memory Categories that matter.
        """
        self._repositories = repositories
        self._chat_model = chat_model

    def recall(self, user_id: UUID, conversation_id: UUID) -> str:
        """Write what the Companion remembers that matters for the newest message.

        Memory Items from every "always include" category go in, plus those
        from the categories a cheap model call picks for the message, plus
        the newest Conversation Summaries. Archived categories are left out.
        The call is skipped when no pickable category has items, and a
        failed call still leaves the "always include" items. Nothing is
        used when User Memory is off.

        Args:
            user_id: The User being answered.
            conversation_id: The Conversation the message is in.

        Returns:
            The memory section for the reply instructions; "" if none.
        """
        user = self._repositories.users.get(user_id)
        if user is None or not user.user_memory_enabled:
            return ""
        user_memory = self._repositories.user_memory
        items = user_memory.list_items(user_id)
        filled_category_ids = {item.category_id for item in items}
        active_categories = [
            category
            for category in self._repositories.memory_categories.list_all()
            if not category.archived
        ]
        pickable = [
            category
            for category in active_categories
            if not category.always_include and category.id in filled_category_ids
        ]
        picked_ids = {category.id for category in self._pick(pickable, conversation_id)}
        chosen = [
            category
            for category in active_categories
            if category.always_include or category.id in picked_ids
        ]
        settings = self._repositories.platform_settings
        summaries = user_memory.list_summaries(
            user_id, limit=settings.get("recent_conversation_summaries")
        )
        return format_memory(
            chosen,
            items,
            summaries,
            user.time_zone,
            settings.get("reply_memory_intro"),
        )

    def _pick(
        self, categories: list[MemoryCategory], conversation_id: UUID
    ) -> list[MemoryCategory]:
        """Ask the model which categories matter for the newest message.

        Args:
            categories: The categories it may pick from.
            conversation_id: The Conversation the message is in.

        Returns:
            The picked categories; none if there were none to pick from or
            the call failed.
        """
        if not categories:
            return []
        settings = self._repositories.platform_settings
        messages = self._repositories.conversations.list_messages(conversation_id)
        try:
            answer = self._chat_model.generate(
                model=settings.get("memory_retrieval_model"),
                instructions=settings.get("memory_retrieval_prompt"),
                history=[
                    ChatLine(
                        role=ChatRole.USER,
                        text=describe_message_for_picking(categories, messages),
                    )
                ],
            )
        except Exception:
            logger.exception("Memory retrieval could not pick Memory Categories")
            return []
        return read_picked_categories(answer, categories)
