import logging

from companion.core.check_ins import CheckInService
from companion.core.message_retention import MessageRetention
from companion.core.platform_settings import CONVERSATION_QUIET_GAP
from companion.core.ports import Clock, Repositories
from companion.core.post_conversation import PostConversationProcessor
from companion.core.user_data import UserDataService

logger = logging.getLogger(__name__)


class ScheduledWork:
    """The work the scheduler runs on every tick."""

    def __init__(
        self,
        repositories: Repositories,
        post_conversation: PostConversationProcessor,
        check_ins: CheckInService,
        message_retention: MessageRetention,
        user_data: UserDataService,
        clock: Clock,
    ) -> None:
        """Set up the work.

        Args:
            repositories: Where Conversations and settings are stored.
            post_conversation: Processes each ended Conversation.
            check_ins: Sends the Check-ins that are due.
            message_retention: Deletes messages older than the retention
                period.
            user_data: Deletes the auth accounts still to delete.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._post_conversation = post_conversation
        self._check_ins = check_ins
        self._message_retention = message_retention
        self._user_data = user_data
        self._clock = clock

    def tick(self) -> None:
        """Process quiet Conversations, send Check-ins, delete old data.

        Old data is messages past the retention period and auth accounts still
        to delete. A Conversation whose processing fails, or an auth account
        whose deletion fails, is tried again on the next tick; the others still
        go ahead. The platform settings are read once, at the start, for the
        whole tick.
        """
        settings = self._repositories.platform_settings.load()
        conversations = self._repositories.conversations
        now = self._clock.now()
        conversations.end_quiet(
            quiet_since=now - settings.get(CONVERSATION_QUIET_GAP), ended_at=now
        )
        for conversation in conversations.list_ended_unprocessed():
            try:
                self._post_conversation.process(conversation, settings)
            except Exception:
                logger.exception("Could not process an ended Conversation")
        self._check_ins.send_due(settings)
        self._message_retention.delete_expired(settings)
        self._user_data.delete_pending_auth_accounts()
