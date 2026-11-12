from datetime import timedelta

from companion.core.ports import Clock, ConversationEngine, Repositories

RETENTION_DAYS_SETTING = "message_retention_days"


class MessageRetention:
    """Deletes raw messages once they are older than the Admin-set retention period.

    Conversation Summaries and Memory Items are kept until the User deletes
    them.
    """

    def __init__(
        self,
        repositories: Repositories,
        conversation_engine: ConversationEngine,
        clock: Clock,
    ) -> None:
        """Set up the cleanup.

        Args:
            repositories: Where messages and settings are stored.
            conversation_engine: Forgets what it saved for a User.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._conversation_engine = conversation_engine
        self._clock = clock

    def delete_expired(self) -> None:
        """Delete messages older than the retention period.

        What the conversation engine saved for each User with old messages is
        deleted first, as it holds copies of their messages. If that fails,
        the messages stay too, so the next tick tries again.
        """
        retention = timedelta(
            days=self._repositories.platform_settings.get(RETENTION_DAYS_SETTING)
        )
        cutoff = self._clock.now() - retention
        conversations = self._repositories.conversations
        for user_id in conversations.list_users_with_messages_sent_before(cutoff):
            self._conversation_engine.forget_user(user_id)
        conversations.delete_messages_sent_before(cutoff)
