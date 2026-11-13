import logging
from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID

from companion.core.models import ChannelPhoto
from companion.core.ports import (
    ChatChannel,
    ChatTool,
    Clock,
    PhotoViewer,
    Repositories,
)
from companion.core.usage import UsageLimiter

logger = logging.getLogger(__name__)

RETRY_PAUSE_SECONDS = 1.0
MAX_PHOTO_LINE_CHARACTERS = 300
NO_SUCH_PHOTO = "There is no photo with that number. Pick one from the list."
MISSING_QUESTION = "Looking at a photo again needs a question about it."
LOOK_AGAIN_FAILED = (
    "You couldn't look at the photo again just now. Answer from its "
    "description if you can; if not, say plainly that you couldn't look again."
)

ASK_ABOUT_PHOTO_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "photo": {"type": "integer", "description": "The photo's number."},
        "question": {
            "type": "string",
            "description": "What to look for in the photo.",
        },
    },
    "required": ["photo", "question"],
}


@dataclass(frozen=True)
class PhotoMessage:
    """A User's photo message as the Companion reads it.

    Attributes:
        text: The caption with the photo's description, or with the note
            that it didn't come through.
        photo: The photo, marked as viewed when it was described.
    """

    text: str
    photo: ChannelPhoto


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


def photo_question_instructions(description_prompt: str, question: str) -> str:
    """Write the instructions for looking at a photo again with a question.

    The description prompt comes first, so its rules (only what is really
    there, no secrets, no guesses at who people are) still apply.

    Args:
        description_prompt: The Admin-set photo description prompt.
        question: What the Companion wants to know about the photo.

    Returns:
        The instructions, ending with the question.
    """
    return (
        f"{description_prompt}\n\nThis time, instead of a full description, "
        f"answer only this question about the photo, following the rules "
        f"above: {question}"
    )


def photo_tool_line(number: int, message_text: str) -> str:
    """Write one photo as the ask_about_photo tool lists it.

    Args:
        number: The number the model picks it by.
        message_text: The text of the message it came with.

    Returns:
        E.g. "1. [photo: A ginger cat…] meet Biscuit", shortened if long.
    """
    if len(message_text) > MAX_PHOTO_LINE_CHARACTERS:
        message_text = message_text[: MAX_PHOTO_LINE_CHARACTERS - 1] + "…"
    return f"{number}. {message_text}"


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

    def read_message(
        self, user_id: UUID, photo: ChannelPhoto, caption: str
    ) -> PhotoMessage:
        """Describe a User's photo and write their message as the Companion reads it.

        Args:
            user_id: The User who sent it.
            photo: The photo.
            caption: Its caption; "" if none.

        Returns:
            The message text and the photo, marked as viewed if it was
            described.
        """
        settings = self._repositories.platform_settings
        description = self.describe(user_id, photo)
        return PhotoMessage(
            text=photo_message_text(
                caption, description, settings.get("photo_not_viewed_note")
            ),
            photo=replace(photo, viewed=description is not None),
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
        return self._look(
            user_id,
            photo,
            settings.get("photo_description_prompt"),
            "view a photo",
        )

    def ask(self, user_id: UUID, photo: ChannelPhoto, question: str) -> str | None:
        """Look at a User's photo again to answer a question about it.

        Retries and usage work as for `describe`.

        Args:
            user_id: The User who sent it.
            photo: The photo.
            question: What to look for.

        Returns:
            The answer, or None if it still couldn't be looked at; the
            error is logged, never raised.
        """
        settings = self._repositories.platform_settings
        return self._look(
            user_id,
            photo,
            photo_question_instructions(
                settings.get("photo_description_prompt"), question
            ),
            "look at a photo again",
        )

    def _look(
        self, user_id: UUID, photo: ChannelPhoto, instructions: str, action: str
    ) -> str | None:
        """Download a photo and look at it, trying again when that fails.

        Args:
            user_id: The User whose usage the tokens go into.
            photo: The photo.
            instructions: What to write about the photo.
            action: What is being done, for the error log, e.g. "view a photo".

        Returns:
            What the photo viewer wrote, or None after the last failed try.
        """
        settings = self._repositories.platform_settings
        tries = 1 + settings.get("photo_retry_count")
        for attempt in range(1, tries + 1):
            try:
                image = self._chat_channel.download_photo(photo.file_id)
                answer = self._photo_viewer.look(
                    model=settings.get("photo_model"),
                    instructions=instructions,
                    photo=image,
                )
            except Exception:
                logger.exception("Could not %s (try %d of %d)", action, attempt, tries)
            else:
                self._usage_limiter.record_tokens(
                    user_id, answer.tokens_in, answer.tokens_out
                )
                if answer.text.strip():
                    return answer.text.strip()
                logger.error(
                    "Could not %s: the answer was empty (try %d of %d)",
                    action,
                    attempt,
                    tries,
                )
            if attempt < tries:
                self._clock.sleep(RETRY_PAUSE_SECONDS)
        return None


class PhotoTools:
    """Offers the ask_about_photo tool to replies."""

    def __init__(self, repositories: Repositories, photo_service: PhotoService) -> None:
        """Set up the photo tools.

        Args:
            repositories: Where Conversations and settings are stored.
            photo_service: Looks at a photo again.
        """
        self._repositories = repositories
        self._photo_service = photo_service

    def offer(self, user_id: UUID, conversation_id: UUID) -> list[ChatTool]:
        """Pick the photo tools for a reply in a Conversation.

        The ask_about_photo tool lists the photos in the Conversation that
        were viewed, by number, under the Admin-set tool description.

        Args:
            user_id: The User being replied to.
            conversation_id: The Conversation being replied in.

        Returns:
            The ask_about_photo tool, or none when no photo in the
            Conversation was viewed.
        """
        messages = self._repositories.conversations.list_messages(conversation_id)
        viewed = [
            (photo, message.content)
            for message in messages
            for photo in message.photos
            if photo.viewed
        ]
        if not viewed:
            return []

        def run_ask(arguments: dict[str, Any]) -> str:
            """Look at the photo the model picked again, with its question.

            Args:
                arguments: The model's arguments, with the photo's "number"
                    and the "question".

            Returns:
                The answer, or why there is none.
            """
            try:
                number = int(arguments.get("photo", 0))
            except (TypeError, ValueError):
                return NO_SUCH_PHOTO
            if not 1 <= number <= len(viewed):
                return NO_SUCH_PHOTO
            question = str(arguments.get("question", "")).strip()
            if not question:
                return MISSING_QUESTION
            photo, _ = viewed[number - 1]
            answer = self._photo_service.ask(user_id, photo, question)
            if answer is None:
                return LOOK_AGAIN_FAILED
            return f"Looking again at photo {number}: {answer}"

        listed = "\n".join(
            photo_tool_line(number, text)
            for number, (_, text) in enumerate(viewed, start=1)
        )
        description = self._repositories.platform_settings.get(
            "ask_about_photo_tool_description"
        )
        return [
            ChatTool(
                name="ask_about_photo",
                description=f"{description}\n\n{listed}",
                parameters=ASK_ABOUT_PHOTO_PARAMETERS,
                run=run_ask,
            )
        ]
