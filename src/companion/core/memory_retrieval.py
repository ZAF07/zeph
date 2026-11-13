import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from companion.core.features import FeatureService
from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    ConversationSummary,
    Feature,
    MemoryCategory,
    MemoryItem,
    SharedPhoto,
)
from companion.core.ports import Repositories
from companion.core.transcripts import to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

SHARED_PHOTOS_GROUP_NAME = "Shared Photos"


@dataclass(frozen=True)
class RecalledMemory:
    """What the Companion remembers that matters for the message being answered.

    Attributes:
        text: The memory section for the reply instructions; "" if none.
        shared_photo_ids: The User's Shared Photos that matter for the
            message, which the reply may send back; empty if none.
    """

    text: str
    shared_photo_ids: tuple[UUID, ...] = ()


def shared_photos_group(description: str) -> MemoryCategory:
    """Make the "Shared Photos" group that memory retrieval picks like a category.

    Shared Photos have no Memory Category, so they are offered to the
    picking call as one extra category, after the real ones.

    Args:
        description: The Admin-set description of Shared Photos.

    Returns:
        The group, as a Memory Category that is never stored.
    """
    return MemoryCategory(
        id=uuid4(),
        name=SHARED_PHOTOS_GROUP_NAME,
        description=description,
        always_include=False,
        archived=False,
        sort_order=0,
    )


def shared_photo_line(photo: SharedPhoto, time_zone: str | None) -> str:
    """Write one Shared Photo as the reply's memory section lists it.

    Args:
        photo: The Shared Photo.
        time_zone: The User's IANA time zone, for the day it was sent.

    Returns:
        E.g. '- 10 Nov 2026: A ginger cat… They said: "this is Miso". Why it
        matters: Miso is their cat.'
    """
    line = f"- {format_day(photo.sent_at, time_zone)}: {photo.description}"
    if photo.caption:
        line += f' They said: "{photo.caption}".'
    return f"{line} Why it matters: {photo.note}"


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
    shared_photos: Sequence[SharedPhoto] = (),
) -> str:
    """Write the User Memory part of the reply instructions.

    Args:
        intro: The Admin-set line that tells the model how to use memories.
        categories: The Memory Categories whose items go in, in order.
        items: The User's Memory Items.
        summaries: The newest Conversation Summaries, newest first.
        time_zone: The User's IANA time zone, for the days.
        shared_photos: The Shared Photos that matter for the message.

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
    if shared_photos:
        photo_lines = [shared_photo_line(photo, time_zone) for photo in shared_photos]
        sections.append(
            "Photos they shared with you, newest first:\n" + "\n".join(photo_lines)
        )
    if not sections:
        return ""
    return intro + "\n\n" + "\n\n".join(sections)


class MemoryRetrieval:
    """Finds the User Memory that matters for the message being answered."""

    def __init__(
        self,
        repositories: Repositories,
        features: FeatureService,
        chat_model: UsageRecordingChatModel,
    ) -> None:
        """Set up memory retrieval.

        Args:
            repositories: Where Users, Conversations, User Memory and
                settings are stored.
            features: Says whether User Memory works for the User.
            chat_model: Picks the Memory Categories that matter and records
                the tokens used.
        """
        self._repositories = repositories
        self._features = features
        self._chat_model = chat_model

    def recall(self, user_id: UUID, conversation_id: UUID) -> RecalledMemory:
        """Find what the Companion remembers that matters for the newest message.

        Memory Items from every "always include" category go in, plus those
        from the categories a cheap model call picks for the message, plus
        the newest Conversation Summaries. The User's Shared Photos are
        offered to the same call as one more category, "Shared Photos", and
        all of them go in when it is picked. Archived categories are left
        out. The call is skipped when there is nothing to pick, and a failed
        call still leaves the "always include" items. Nothing is used when
        User Memory doesn't work for the User.

        Args:
            user_id: The User being answered.
            conversation_id: The Conversation the message is in.

        Returns:
            The memory section for the reply instructions and the Shared
            Photos that matter.
        """
        user = self._repositories.users.get(user_id)
        if user is None or not self._features.works_for(user_id, Feature.USER_MEMORY):
            return RecalledMemory(text="")
        settings = self._repositories.platform_settings
        user_memory = self._repositories.user_memory
        items = user_memory.list_items(user_id)
        shared_photos = user_memory.list_shared_photos(user_id)
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
        photos_group = shared_photos_group(
            settings.get("shared_photos_memory_description")
        )
        if shared_photos:
            pickable.append(photos_group)
        picked = self._pick(pickable, user_id, conversation_id)
        picked_ids = {category.id for category in picked}
        relevant_photos = shared_photos if photos_group in picked else []
        chosen = [
            category
            for category in active_categories
            if category.always_include or category.id in picked_ids
        ]
        summaries = user_memory.list_summaries(
            user_id, limit=settings.get("recent_conversation_summaries")
        )
        return RecalledMemory(
            text=format_memory(
                chosen,
                items,
                summaries,
                user.time_zone,
                settings.get("reply_memory_intro"),
                relevant_photos,
            ),
            shared_photo_ids=tuple(photo.id for photo in relevant_photos),
        )

    def _pick(
        self,
        categories: list[MemoryCategory],
        user_id: UUID,
        conversation_id: UUID,
    ) -> list[MemoryCategory]:
        """Ask the model which categories matter for the newest message.

        Args:
            categories: The categories it may pick from.
            user_id: The User being answered.
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
                user_id=user_id,
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
