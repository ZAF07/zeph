import logging
from typing import Any
from uuid import UUID

from companion.core.features import FeatureService
from companion.core.models import (
    ChannelSticker,
    Feature,
    LibrarySticker,
    StickerImage,
)
from companion.core.ports import ChatChannel, ChatTool, Clock, Repositories

logger = logging.getLogger(__name__)

MAX_NOTE_LENGTH = 500
ALREADY_PICKED = "You already picked a sticker for this reply; only one is sent."
NO_SUCH_STICKER = "There is no sticker with that number. Pick one from the list."

STICKER_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "number": {"type": "integer", "description": "The sticker's number."}
    },
    "required": ["number"],
}


class StickerNotFoundError(LookupError):
    """Raised when no sticker in the Sticker Library has the given ID."""


class StickerSetNotFoundError(LookupError):
    """Raised when the chat channel has no sticker set with the given name."""


class StickerSetUnavailableError(Exception):
    """Raised when the chat channel can't be asked about a sticker set."""


class InvalidStickerError(ValueError):
    """Raised when a sticker set name or "when to use" note is not valid."""


def sticker_message_text(emoji: str | None) -> str:
    """Write a sticker as the Companion reads it in a Conversation.

    Args:
        emoji: The emoji the sticker stands for, if any.

    Returns:
        E.g. "[sticker: 😂]", or "[sticker]" without an emoji.
    """
    return f"[sticker: {emoji}]" if emoji else "[sticker]"


def sticker_tool_line(number: int, sticker: LibrarySticker) -> str:
    """Write one sticker as the sticker tool lists it.

    Args:
        number: The number the model picks it by.
        sticker: The sticker.

    Returns:
        E.g. "1. 🌱 Celebrating a small step forward".
    """
    parts = (f"{number}.", sticker.emoji, sticker.note)
    return " ".join(part for part in parts if part)


class StickerLibraryService:
    """Lets Admins build the Sticker Library and edit when each sticker fits."""

    def __init__(
        self, repositories: Repositories, chat_channel: ChatChannel, clock: Clock
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where the Sticker Library is stored.
            chat_channel: Looks up sticker sets and sticker images.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_channel = chat_channel
        self._clock = clock

    def list_all(self) -> list[LibrarySticker]:
        """List every sticker in the order they were added.

        Returns:
            The stickers.
        """
        return self._repositories.stickers.list_all()

    def add_sent_sticker(self, sticker: ChannelSticker) -> bool:
        """Add a sticker an Admin sent the Companion, without a note.

        Args:
            sticker: The sticker.

        Returns:
            True if it was added; False if it was already in the library.
        """
        return self._repositories.stickers.add_new([sticker], self._clock.now()) == 1

    def import_set(self, set_name: str) -> int:
        """Add every sticker in a sticker set, without notes.

        Stickers already in the library are skipped and keep their notes.

        Args:
            set_name: The set's name, the part after t.me/addstickers/.

        Returns:
            How many stickers were added.

        Raises:
            InvalidStickerError: If the name is blank.
            StickerSetNotFoundError: If there is no such set.
            StickerSetUnavailableError: If the chat channel didn't answer.
        """
        name = set_name.strip()
        if not name:
            raise InvalidStickerError("Enter a sticker set name.")
        try:
            stickers = self._chat_channel.get_sticker_set(name)
        except Exception as error:
            logger.exception("Could not look up a sticker set")
            raise StickerSetUnavailableError(name) from error
        if stickers is None:
            raise StickerSetNotFoundError(name)
        return self._repositories.stickers.add_new(stickers, self._clock.now())

    def save_note(self, sticker_id: UUID, note: str) -> LibrarySticker:
        """Save when a sticker should be used.

        Args:
            sticker_id: The sticker's ID.
            note: The note; "" means the Companion won't send it.

        Returns:
            The saved sticker.

        Raises:
            InvalidStickerError: If the note is too long.
            StickerNotFoundError: If there is no such sticker.
        """
        tidy_note = note.strip()
        if len(tidy_note) > MAX_NOTE_LENGTH:
            raise InvalidStickerError(
                f"Keep the note under {MAX_NOTE_LENGTH} characters."
            )
        saved = self._repositories.stickers.save_note(sticker_id, tidy_note)
        if saved is None:
            raise StickerNotFoundError(sticker_id)
        return saved

    def remove(self, sticker_id: UUID) -> None:
        """Remove a sticker so the Companion no longer sends it.

        Args:
            sticker_id: The sticker's ID.

        Raises:
            StickerNotFoundError: If there is no such sticker.
        """
        if not self._repositories.stickers.delete(sticker_id):
            raise StickerNotFoundError(sticker_id)

    def get_image(self, sticker_id: UUID) -> StickerImage | None:
        """Get an image of a sticker for the Dashboard.

        Args:
            sticker_id: The sticker's ID.

        Returns:
            The image, or None if the sticker has none a browser can show or
            it couldn't be downloaded.

        Raises:
            StickerNotFoundError: If there is no such sticker.
        """
        sticker = self._repositories.stickers.get(sticker_id)
        if sticker is None:
            raise StickerNotFoundError(sticker_id)
        if sticker.preview_file_id is None:
            return None
        try:
            return self._chat_channel.get_sticker_image(sticker.preview_file_id)
        except Exception:
            logger.exception("Could not download a sticker image")
            return None


class StickerChoice:
    """The sticker tool for one reply, and the sticker it picked.

    Only stickers with a "when to use" note are offered, and at most one is
    picked per reply.
    """

    def __init__(self, stickers: list[LibrarySticker], description: str) -> None:
        """Set up the choice.

        Args:
            stickers: The stickers that have a note.
            description: The Admin-set tool description, put before the list.
        """
        self._stickers = stickers
        self._description = description
        self.picked: LibrarySticker | None = None

    @property
    def tools(self) -> list[ChatTool]:
        """The sticker tool, or none when no sticker has a note."""
        if not self._stickers:
            return []
        listed = "\n".join(
            sticker_tool_line(number, sticker)
            for number, sticker in enumerate(self._stickers, start=1)
        )
        return [
            ChatTool(
                name="send_sticker",
                description=f"{self._description}\n\n{listed}",
                parameters=STICKER_PARAMETERS,
                run=self._pick,
            )
        ]

    def _pick(self, arguments: dict[str, Any]) -> str:
        """Pick the sticker the model chose, if it is the first one.

        Args:
            arguments: The model's arguments, with the sticker's "number".

        Returns:
            What the model is told back.
        """
        if self.picked is not None:
            return ALREADY_PICKED
        try:
            number = int(arguments.get("number", 0))
        except (TypeError, ValueError):
            return NO_SUCH_STICKER
        if not 1 <= number <= len(self._stickers):
            return NO_SUCH_STICKER
        self.picked = self._stickers[number - 1]
        return f"Sticker {number} will be sent after your text. Now write your text."


class StickerTools:
    """Offers the Sticker Library to replies."""

    def __init__(self, repositories: Repositories, features: FeatureService) -> None:
        """Set up the sticker tools.

        Args:
            repositories: Where the Sticker Library and settings are stored.
            features: Says whether Stickers works for the User.
        """
        self._repositories = repositories
        self._features = features

    def offer(self, user_id: UUID) -> StickerChoice:
        """Start the sticker choice for one reply to a User.

        Args:
            user_id: The User being replied to.

        Returns:
            The choice, offering every sticker that has a note; none when
            Stickers doesn't work for the User.
        """
        if not self._features.works_for(user_id, Feature.STICKERS):
            return StickerChoice([], "")
        stickers = [
            sticker
            for sticker in self._repositories.stickers.list_all()
            if sticker.note
        ]
        return StickerChoice(
            stickers,
            self._repositories.platform_settings.get("sticker_tool_description"),
        )
