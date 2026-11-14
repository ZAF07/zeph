import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from companion.core.models import (
    ConversationSummary,
    Feature,
    MemoryCategory,
    MemoryItem,
    SharedPhoto,
    UserSnapshot,
)
from companion.core.platform_settings import (
    OLDER_SUMMARIES_CLOSENESS_PERCENT,
    OLDER_SUMMARIES_PER_REPLY,
    RECENT_CONVERSATION_SUMMARIES,
    REPLY_MEMORY_INTRO,
    SHARED_PHOTOS_MEMORY_DESCRIPTION,
)
from companion.core.ports import Embedder, Repositories

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
    """Make the "Shared Photos" group the Understanding picks like a category.

    Shared Photos have no Memory Category, so they are offered to the
    Understanding as one extra category, after the real ones.

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


def shared_photo_line(
    photo: SharedPhoto, time_zone: str | None, bullet: str = "-"
) -> str:
    """Write one Shared Photo as the reply's memory section lists it.

    Args:
        photo: The Shared Photo.
        time_zone: The User's IANA time zone, for the day it was sent.
        bullet: What the line starts with, e.g. "-" or a number like "1.".

    Returns:
        E.g. '- 10 Nov 2026: A ginger cat… They said: "this is Miso". Why it
        matters: Miso is their cat.'
    """
    line = f"{bullet} {format_day(photo.sent_at, time_zone)}: {photo.description}"
    if photo.caption:
        line += f' They said: "{photo.caption}".'
    return f"{line} Why it matters: {photo.note}"


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


def summary_line(summary: ConversationSummary, time_zone: str | None) -> str:
    """Write one Conversation Summary as the reply's memory section lists it.

    Args:
        summary: The Conversation Summary.
        time_zone: The User's IANA time zone, for the day it was written.

    Returns:
        E.g. "- 9 Nov 2026: Talked about a new job. They seemed excited."
    """
    return (
        f"- {format_day(summary.created_at, time_zone)}: {summary.summary} "
        f"They seemed {summary.mood}."
    )


def format_memory(
    categories: list[MemoryCategory],
    items: list[MemoryItem],
    summaries: list[ConversationSummary],
    time_zone: str | None,
    intro: str,
    shared_photos: Sequence[SharedPhoto] = (),
    older_summaries: Sequence[ConversationSummary] = (),
) -> str:
    """Write the User Memory part of the reply instructions.

    Args:
        intro: The Admin-set line that tells the model how to use memories.
        categories: The Memory Categories whose items go in, in order.
        items: The User's Memory Items.
        summaries: The newest Conversation Summaries, newest first.
        time_zone: The User's IANA time zone, for the days.
        shared_photos: The Shared Photos that matter for the message.
        older_summaries: Older Conversation Summaries found by meaning,
            closest first.

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
        summary_lines = [summary_line(summary, time_zone) for summary in summaries]
        sections.append(
            "Recent Conversations, newest first:\n" + "\n".join(summary_lines)
        )
    if older_summaries:
        older_lines = [summary_line(summary, time_zone) for summary in older_summaries]
        sections.append(
            "Older Conversations that may matter:\n" + "\n".join(older_lines)
        )
    if shared_photos:
        photo_lines = [shared_photo_line(photo, time_zone) for photo in shared_photos]
        sections.append(
            "Photos they shared with you, newest first:\n" + "\n".join(photo_lines)
        )
    if not sections:
        return ""
    return intro + "\n\n" + "\n\n".join(sections)


@dataclass(frozen=True)
class SavedMemory:
    """What the Companion has saved about a User, read once for a reply.

    Attributes:
        categories: The active Memory Categories, in order.
        items: The User's Memory Items.
        summaries: The newest Conversation Summaries, newest first.
        shared_photos: The User's Shared Photos; empty when Photo Viewing
            doesn't work for them.
        pickable: The categories the Understanding may pick: active ones
            with items that aren't "always include", then the "Shared
            Photos" group when the User has Shared Photos.
    """

    categories: list[MemoryCategory]
    items: list[MemoryItem]
    summaries: list[ConversationSummary]
    shared_photos: list[SharedPhoto]
    pickable: list[MemoryCategory]

    def items_in(self, category_name: str) -> list[MemoryItem]:
        """List the Memory Items in one category, found by name ignoring case.

        Args:
            category_name: The category's name, e.g. "Goals".

        Returns:
            Its items; none if there is no such active category.
        """
        category_ids = {
            category.id
            for category in self.categories
            if category.name.lower() == category_name.lower()
        }
        return [item for item in self.items if item.category_id in category_ids]


class MemoryRetrieval:
    """Finds the User Memory that matters for the message being answered."""

    def __init__(self, repositories: Repositories, embedder: Embedder) -> None:
        """Set up memory retrieval.

        Args:
            repositories: Where User Memory and Memory Categories are stored.
            embedder: Embeds the phrases older Summaries are searched with.
        """
        self._repositories = repositories
        self._embedder = embedder

    def read(self, snapshot: UserSnapshot) -> SavedMemory:
        """Read what the Companion has saved about the User, once per reply.

        Archived categories are left out. What is saved is used even while
        User Memory is off, since off only stops learning; no Shared Photo
        is used when Photo Viewing doesn't work.

        Args:
            snapshot: The User being answered.

        Returns:
            Their saved memory, and the categories the Understanding may pick.
        """
        user_id = snapshot.user.id
        settings = snapshot.settings
        user_memory = self._repositories.user_memory
        items = user_memory.list_items(user_id)
        shared_photos = (
            user_memory.list_shared_photos(user_id)
            if snapshot.works(Feature.PHOTO_VIEWING)
            else []
        )
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
        if shared_photos:
            pickable.append(
                shared_photos_group(settings.get(SHARED_PHOTOS_MEMORY_DESCRIPTION))
            )
        return SavedMemory(
            categories=active_categories,
            items=items,
            summaries=user_memory.list_summaries(
                user_id, limit=settings.get(RECENT_CONVERSATION_SUMMARIES)
            ),
            shared_photos=shared_photos,
            pickable=pickable,
        )

    def recall(
        self,
        snapshot: UserSnapshot,
        saved: SavedMemory,
        picked_categories: Sequence[str],
        look_up_past: Sequence[str] = (),
    ) -> RecalledMemory:
        """Pick out what the Companion remembers that matters for the message.

        Memory Items from every "always include" category go in, plus those
        from the categories the Understanding picked, plus the newest
        Conversation Summaries, plus older Summaries found by meaning. All
        the User's Shared Photos go in when the Understanding picked "Shared
        Photos". A picked name that isn't one of the pickable categories is
        ignored.

        Args:
            snapshot: The User being answered.
            saved: Their saved memory, read for this reply.
            picked_categories: The names of the categories the Understanding
                picked, in any case.
            look_up_past: The Understanding's phrases to search older
                Summaries with; none searches nothing.

        Returns:
            The memory section for the reply instructions and the Shared
            Photos that matter.
        """
        picked_names = {name.strip().lower() for name in picked_categories}
        picked = [
            category
            for category in saved.pickable
            if category.name.lower() in picked_names
        ]
        picked_ids = {category.id for category in picked}
        relevant_photos = (
            saved.shared_photos
            if any(category.name == SHARED_PHOTOS_GROUP_NAME for category in picked)
            else []
        )
        chosen = [
            category
            for category in saved.categories
            if category.always_include or category.id in picked_ids
        ]
        return RecalledMemory(
            text=format_memory(
                chosen,
                saved.items,
                saved.summaries,
                snapshot.user.time_zone,
                snapshot.settings.get(REPLY_MEMORY_INTRO),
                relevant_photos,
                self._find_older_summaries(snapshot, saved, look_up_past),
            ),
            shared_photo_ids=tuple(photo.id for photo in relevant_photos),
        )

    def _find_older_summaries(
        self,
        snapshot: UserSnapshot,
        saved: SavedMemory,
        look_up_past: Sequence[str],
    ) -> list[ConversationSummary]:
        """Find the User's older Summaries closest in meaning to the phrases.

        Only the User's own Summaries are searched, leaving out the newest
        ones already given. Only those at least as close as the Admin-set
        bar count, up to the Admin-set number. If the search fails the reply
        goes ahead without them.

        Args:
            snapshot: The User being answered.
            saved: Their saved memory, read for this reply.
            look_up_past: The phrases to search with.

        Returns:
            The older Summaries, closest first; none if no phrase was given.
        """
        settings = snapshot.settings
        limit = settings.get(OLDER_SUMMARIES_PER_REPLY)
        if not look_up_past or limit < 1:
            return []
        try:
            return self._repositories.user_memory.find_summaries_by_meaning(
                snapshot.user.id,
                [self._embedder.embed_query(phrase) for phrase in look_up_past],
                min_closeness=settings.get(OLDER_SUMMARIES_CLOSENESS_PERCENT) / 100,
                limit=limit,
                leave_out=[summary.id for summary in saved.summaries],
            )
        except Exception:
            logger.exception("Could not search older Conversation Summaries")
            return []
