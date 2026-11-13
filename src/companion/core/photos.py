import logging
from uuid import UUID

from companion.core.models import ChannelPhoto
from companion.core.ports import ChatChannel, Clock, PhotoViewer, Repositories
from companion.core.usage import UsageLimiter

logger = logging.getLogger(__name__)

RETRY_PAUSE_SECONDS = 1.0


def photo_message_text(
    caption: str, description: str | None, not_viewed_note: str
) -> str:
    """Write a photo message the way the Companion reads it.

    Args:
        caption: The photo's caption; "" if none.
        description: What the photo shows; None if it couldn't be viewed.
        not_viewed_note: What the Companion is told when it couldn't be viewed.

    Returns:
        "[photo: description] caption", or "[photo that didn't come through.
        note] caption" when it couldn't be viewed.
    """
    if description is None:
        marker = f"[photo that didn't come through. {not_viewed_note}]"
    else:
        marker = f"[photo: {description}]"
    return f"{marker} {caption.strip()}".strip()


class PhotoService:
    """Holds every photo rule: nothing else downloads or looks at images (ADR-0007).

    Photos are downloaded from the chat channel when needed and never kept.
    """

    def __init__(
        self,
        repositories: Repositories,
        chat_channel: ChatChannel,
        photo_viewer: PhotoViewer,
        usage_limiter: UsageLimiter,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where settings are stored.
            chat_channel: Downloads the photos.
            photo_viewer: Looks at each photo.
            usage_limiter: Records the tokens each look took.
            clock: Pauses between tries.
        """
        self._repositories = repositories
        self._chat_channel = chat_channel
        self._photo_viewer = photo_viewer
        self._usage_limiter = usage_limiter
        self._clock = clock

    def message_text(self, user_id: UUID, photo: ChannelPhoto, caption: str) -> str:
        """Describe a User's photo and write their message as the Companion reads it.

        Args:
            user_id: The User who sent it.
            photo: The photo.
            caption: Its caption; "" if none.

        Returns:
            The caption with the photo's description, or with the note that
            it didn't come through.
        """
        settings = self._repositories.platform_settings
        return photo_message_text(
            caption,
            self.describe(user_id, photo),
            settings.get("photo_not_viewed_note"),
        )

    def describe(self, user_id: UUID, photo: ChannelPhoto) -> str | None:
        """Download a photo and write a detailed description of it.

        A failed download or look is tried again up to `photo_retry_count`
        times, with a short pause. The tokens each look took go into the
        User's usage.

        Args:
            user_id: The User who sent it.
            photo: The photo.

        Returns:
            The description, or None if it still couldn't be viewed; the
            error is logged, never raised.
        """
        if photo.too_big_to_download:
            logger.error("Could not view a photo: it is too big to download")
            return None
        settings = self._repositories.platform_settings
        tries = 1 + settings.get("photo_retry_count")
        for attempt in range(1, tries + 1):
            try:
                image = self._chat_channel.download_photo(photo.file_id)
                answer = self._photo_viewer.look(
                    model=settings.get("photo_model"),
                    instructions=settings.get("photo_description_prompt"),
                    photo=image,
                )
            except Exception:
                logger.exception(
                    "Could not view a photo (try %d of %d)", attempt, tries
                )
            else:
                self._usage_limiter.record_tokens(
                    user_id, answer.tokens_in, answer.tokens_out
                )
                if answer.text.strip():
                    return answer.text.strip()
                logger.error(
                    "Could not view a photo: the description was empty (try %d of %d)",
                    attempt,
                    tries,
                )
            if attempt < tries:
                self._clock.sleep(RETRY_PAUSE_SECONDS)
        return None
