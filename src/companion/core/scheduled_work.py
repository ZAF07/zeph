import logging

from companion.core.check_ins import CheckInService
from companion.core.message_retention import MessageRetention
from companion.core.ports import Clock, Repositories
from companion.core.post_conversation import PostConversationProcessor
from companion.core.timing import quiet_gap

logger = logging.getLogger(__name__)


class ScheduledWork:
    """The work the scheduler runs on every tick."""

    def __init__(
        self,
        repositories: Repositories,
        post_conversation: PostConversationProcessor,
        check_ins: CheckInService,
        message_retention: MessageRetention,
        clock: Clock,
    ) -> None:
        """Set up the work.

        Args:
            repositories: Where Conversations and settings are stored.
            post_conversation: Processes each ended Conversation.
            check_ins: Sends the Check-ins that are due.
            message_retention: Deletes messages older than the retention
                period.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._post_conversation = post_conversation
        self._check_ins = check_ins
        self._message_retention = message_retention
        self._clock = clock

    def tick(self) -> None:
        """End and process quiet Conversations, send Check-ins, delete old messages.

        A Conversation whose processing fails stays unprocessed and is tried
        again on the next tick; the others still go ahead.
        """
        conversations = self._repositories.conversations
        now = self._clock.now()
        conversations.end_quiet(
            quiet_since=now - quiet_gap(self._repositories.platform_settings),
            ended_at=now,
        )
        for conversation in conversations.list_ended_unprocessed():
            try:
                self._post_conversation.process(conversation)
            except Exception:
                logger.exception("Could not process an ended Conversation")
        self._check_ins.send_due()
        self._message_retention.delete_expired()
