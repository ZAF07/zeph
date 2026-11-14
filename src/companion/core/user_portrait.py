import logging
from collections.abc import Sequence
from datetime import datetime

from companion.core.life_threads import describe_thread
from companion.core.memory_retrieval import (
    format_day,
    format_items_by_category,
    summary_line,
)
from companion.core.model_call_log import start_trace
from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationSummary,
    LifeThread,
    MemoryCategory,
    MemoryItem,
    ModelStep,
    PlatformSettings,
    TraceKind,
    UserPortrait,
    UserSnapshot,
)
from companion.core.platform_settings import PORTRAIT_MODEL, PORTRAIT_PROMPT
from companion.core.ports import Clock, Repositories
from companion.core.usage import UsageRecordingChatModel
from companion.core.user_snapshot import UserSnapshotLoader

logger = logging.getLogger(__name__)

SUMMARIES_FOR_PORTRAIT = 10


def describe_user_memory(
    categories: Sequence[MemoryCategory],
    items: Sequence[MemoryItem],
    threads: Sequence[LifeThread],
    summaries: Sequence[ConversationSummary],
    now: datetime,
    time_zone: str | None,
) -> str:
    """Write what the Portrait model is given: the User Memory, never the old Portrait.

    Args:
        categories: Every Memory Category, archived ones included.
        items: The User's Memory Items.
        threads: The User's Life Threads, open first.
        summaries: Their newest Conversation Summaries, newest first.
        now: The current time.
        time_zone: The User's IANA time zone, for the days.

    Returns:
        Today's date, the Memory Items by category, the Life Threads and the
        recent Conversations.
    """
    item_sections = format_items_by_category(categories, items)
    thread_lines = "\n".join(
        f"- {describe_thread(thread, time_zone)}" for thread in threads
    )
    summary_lines = "\n".join(summary_line(summary, time_zone) for summary in summaries)
    item_text = "\n\n".join(item_sections)
    return (
        f"Today: {format_day(now, time_zone)}\n\n"
        f"What Zeph remembers:\n{item_text or 'Nothing yet.'}\n\n"
        f"Life Threads:\n{thread_lines or 'None yet.'}\n\n"
        f"Recent Conversations, newest first:\n{summary_lines or 'None yet.'}"
    )


class PortraitWriter:
    """Writes each User's User Portrait from their User Memory.

    It is written from their Memory Items, Life Threads and newest
    Conversation Summaries only, never from the old Portrait, so something
    they deleted is gone from the next one.
    """

    def __init__(
        self,
        repositories: Repositories,
        user_snapshots: UserSnapshotLoader,
        chat_model: UsageRecordingChatModel,
        clock: Clock,
    ) -> None:
        """Set up the writer.

        Args:
            repositories: Where User Memory, Life Threads and Portraits are
                stored.
            user_snapshots: Reads a User and their Features for a rewrite.
            chat_model: Writes the Portrait and records the tokens used.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._user_snapshots = user_snapshots
        self._chat_model = chat_model
        self._clock = clock

    def write(self, snapshot: UserSnapshot) -> None:
        """Write the User's Portrait again from what is saved now.

        An empty answer changes nothing. The Portrait isn't saved if it was
        cleared, or another was saved, after its User Memory was read.

        Args:
            snapshot: The User.
        """
        read_at = self._clock.now()
        text = self._ask(snapshot, read_at)
        if not text:
            logger.warning("The User Portrait model gave an empty answer")
            return
        self._repositories.user_portraits.save(
            UserPortrait(user_id=snapshot.user.id, text=text, written_at=read_at)
        )

    def rewrite_requested(self, settings: PlatformSettings) -> None:
        """Write again the Portraits a deletion asked for, without what was deleted.

        This runs whatever User Memory says, since it only forgets. A User
        with no Portrait gets none. When a rewrite fails or the answer is
        empty, the Portrait is cleared instead, so the deleted thing is never
        used again. Clearing also stops any Portrait written from older User
        Memory from landing later.

        Args:
            settings: The platform settings, read once for the tick.
        """
        portraits = self._repositories.user_portraits
        for user_id in portraits.list_rewrite_requests():
            snapshot = self._user_snapshots.find(
                user_id, settings, start_trace(TraceKind.PORTRAIT_REWRITE)
            )
            if snapshot is None:
                continue
            read_at = self._clock.now()
            text = ""
            if portraits.find(user_id) is not None:
                try:
                    text = self._ask(snapshot, read_at)
                except Exception:
                    logger.exception("Could not rewrite a User Portrait; clearing it")
            if text:
                portraits.save(
                    UserPortrait(user_id=user_id, text=text, written_at=read_at)
                )
            else:
                portraits.clear(user_id, read_at)

    def _ask(self, snapshot: UserSnapshot, read_at: datetime) -> str:
        """Ask the model for the Portrait, from the User Memory saved now.

        Args:
            snapshot: The User.
            read_at: When their User Memory is being read.

        Returns:
            The Portrait; "" if the answer was empty.
        """
        user_id = snapshot.user.id
        description = describe_user_memory(
            self._repositories.memory_categories.list_all(),
            self._repositories.user_memory.list_items(user_id),
            self._repositories.life_threads.list_for_user(user_id),
            self._repositories.user_memory.list_summaries(
                user_id, limit=SUMMARIES_FOR_PORTRAIT
            ),
            read_at,
            snapshot.user.time_zone,
        )
        settings = snapshot.settings
        return self._chat_model.generate(
            snapshot=snapshot,
            step=ModelStep.PORTRAIT,
            model=settings.get(PORTRAIT_MODEL),
            instructions=settings.get(PORTRAIT_PROMPT),
            history=[ChatLine(role=ChatRole.USER, text=description)],
        ).strip()
