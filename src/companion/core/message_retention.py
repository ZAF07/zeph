from datetime import timedelta

from companion.core.models import PlatformSettings
from companion.core.platform_settings import MESSAGE_RETENTION_DAYS
from companion.core.ports import Clock, Repositories


class MessageRetention:
    """Deletes raw messages once they are older than the Admin-set retention period.

    Model Call Log entries go with them. Conversation Summaries and Memory
    Items are kept until the User deletes them.
    """

    def __init__(
        self,
        repositories: Repositories,
        clock: Clock,
    ) -> None:
        """Set up the cleanup.

        Args:
            repositories: Where messages and settings are stored.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._clock = clock

    def delete_expired(self, settings: PlatformSettings) -> None:
        """Delete messages and Model Call Log entries older than the retention period.

        Args:
            settings: Holds the retention period, read once for the tick.
        """
        retention = timedelta(days=settings.get(MESSAGE_RETENTION_DAYS))
        cutoff = self._clock.now() - retention
        self._repositories.conversations.delete_messages_sent_before(cutoff)
        self._repositories.model_calls.delete_started_before(cutoff)
