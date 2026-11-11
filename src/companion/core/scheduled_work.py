import logging
from datetime import timedelta

from companion.core.ports import Clock, Repositories
from companion.core.post_conversation import PostConversationProcessor

logger = logging.getLogger(__name__)


class ScheduledWork:
    """The work the scheduler runs on every tick."""

    def __init__(
        self,
        repositories: Repositories,
        post_conversation: PostConversationProcessor,
        clock: Clock,
    ) -> None:
        """Set up the work.

        Args:
            repositories: Where Conversations and settings are stored.
            post_conversation: Processes each ended Conversation.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._post_conversation = post_conversation
        self._clock = clock

    def tick(self) -> None:
        """End Conversations past the quiet gap, then process each ended one.

        A Conversation whose processing fails stays unprocessed and is tried
        again on the next tick; the others still go ahead.
        """
        conversations = self._repositories.conversations
        quiet_gap = timedelta(
            minutes=self._repositories.platform_settings.get(
                "conversation_quiet_gap_minutes"
            )
        )
        now = self._clock.now()
        conversations.end_quiet(quiet_since=now - quiet_gap, ended_at=now)
        for conversation in conversations.list_ended_unprocessed():
            try:
                self._post_conversation.process(conversation)
            except Exception:
                logger.exception("Could not process an ended Conversation")
