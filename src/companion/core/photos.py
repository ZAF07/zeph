import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID

from companion.core.errors import NotFoundError
from companion.core.models import (
    ChannelPhoto,
    Feature,
    PhotoImage,
    SharedPhoto,
    UserSnapshot,
)
from companion.core.platform_settings import (
    ASK_ABOUT_PHOTO_TOOL_DESCRIPTION,
    PHOTO_ALBUM_MAX_PHOTOS,
    PHOTO_DESCRIPTION_PROMPT,
    PHOTO_MODEL,
    PHOTO_NOT_VIEWED_NOTE,
    PHOTO_RETRY_COUNT,
    PHOTO_VIEWING_OFF_NOTE,
    SEND_PHOTO_TOOL_DESCRIPTION,
)
from companion.core.ports import (
    ChatChannel,
    ChatTool,
    Clock,
    Repositories,
)
from companion.core.reply_tools import ReplyContext, ReplyOffer
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

RETRY_PAUSE_SECONDS = 1.0
MAX_PHOTO_LINE_CHARACTERS = 300
NO_SUCH_PHOTO = "There is no photo with that number. Pick one from the list."
MISSING_QUESTION = "Looking at a photo again needs a question about it."
LOOK_AGAIN_FAILED = (
    "You couldn't look at the photo again just now. Answer from its "
    "description if you can; if not, say plainly that you couldn't look again."
)


NO_SUCH_SHARED_PHOTO = (
    "There is no Shared Photo with that number. Pick one from the list, or send none."
)
PHOTO_ALREADY_PICKED = (
    "A photo is already being sent with this reply, and only one can be. Now "
    "write your text."
)


class SharedPhotoNotFoundError(NotFoundError):
    """Raised when a User has no Shared Photo with that ID."""

    shown_message = "Shared Photo not found"


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


SEND_PHOTO_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "photo": {"type": "integer", "description": "The photo's number."},
    },
    "required": ["photo"],
}


@dataclass(frozen=True)
class PhotoMessage:
    """A User's photo message as the Companion reads it.

    Attributes:
        text: The caption with each photo's description, or with the note
            that it didn't come through or wasn't looked at.
        photos: The photos looked at, each marked as viewed and holding its
            description when the reply may see it.
        safeguard_text: The caption with each photo's description, for the
            Safeguard alone, when Photo Viewing is off; None when it is the
            same as `text`.
    """

    text: str
    photos: tuple[ChannelPhoto, ...]
    safeguard_text: str | None = None


def photo_marker(
    description: str | None,
    not_viewed_note: str,
    number: int | None = None,
    viewing_off_note: str | None = None,
) -> str:
    """Write one photo the way the Companion reads it.

    Args:
        description: What the photo shows; None if it couldn't be viewed.
        not_viewed_note: What the Companion is told when it couldn't be viewed.
        number: The photo's place in an album; None for a photo sent alone.
        viewing_off_note: What the Companion is told when Photo Viewing is
            off; None when it is on.

    Returns:
        "[photo: description]", "[photo 2: description]" in an album,
        "[photo that didn't come through. note]" when it couldn't be viewed,
        or "[photo you didn't look at. note]" when Photo Viewing is off.
    """
    name = "photo" if number is None else f"photo {number}"
    if viewing_off_note is not None:
        return f"[{name} you didn't look at. {viewing_off_note}]"
    if description is None:
        return f"[{name} that didn't come through. {not_viewed_note}]"
    return f"[{name}: {description}]"


def photo_message_text(
    caption: str,
    descriptions: Sequence[str | None],
    not_viewed_note: str,
    photos_not_looked_at: int = 0,
    viewing_off_note: str | None = None,
) -> str:
    """Write a photo message the way the Companion reads it.

    Args:
        caption: The caption; "" if none.
        descriptions: What each photo shows, in order; None for one that
            couldn't be viewed.
        not_viewed_note: What the Companion is told when one couldn't be
            viewed.
        photos_not_looked_at: How many more photos came in the album that
            weren't looked at.
        viewing_off_note: What the Companion is told when Photo Viewing is
            off, in place of every description; None when it is on.

    Returns:
        "[photo: description] caption" for one photo, or "[photo 1: …]
        [photo 2: …] caption" for an album, ending with a note to mention
        any photos that weren't looked at.
    """
    if len(descriptions) == 1 and not photos_not_looked_at:
        markers = [
            photo_marker(
                descriptions[0], not_viewed_note, viewing_off_note=viewing_off_note
            )
        ]
    else:
        markers = [
            photo_marker(
                description,
                not_viewed_note,
                number,
                viewing_off_note=viewing_off_note,
            )
            for number, description in enumerate(descriptions, start=1)
        ]
    parts = [*markers, caption.strip()]
    if photos_not_looked_at:
        parts.append(not_looked_at_note(photos_not_looked_at, len(descriptions)))
    return " ".join(part for part in parts if part)


def not_looked_at_note(photos_not_looked_at: int, photos_looked_at: int) -> str:
    """Tell the Companion that some photos in an album weren't looked at.

    Args:
        photos_not_looked_at: How many weren't looked at.
        photos_looked_at: How many were.

    Returns:
        E.g. "[The album had 3 more photos that you didn't look at, because
        you look at only the first 5 in an album. They came through fine.
        Mention briefly that you only looked at the first 5.]"
    """
    if photos_not_looked_at == 1:
        more, came_through = "1 more photo", "It came through"
    else:
        more, came_through = f"{photos_not_looked_at} more photos", "They came through"
    return (
        f"[The album had {more} that you didn't look at, because you look at "
        f"only the first {photos_looked_at} in an album. {came_through} "
        f"fine. Mention briefly that you only looked at the first "
        f"{photos_looked_at}.]"
    )


def sent_shared_photo_text(description: str) -> str:
    """Write a Shared Photo the Companion sent back, as its Conversation keeps it.

    It reads as a note of what was done, not as words to send, so later
    replies don't copy it out as text.

    Args:
        description: What the photo shows.

    Returns:
        E.g. "[You sent them back their own photo with the send_photo tool.
        It shows: A ginger cat…]".
    """
    return (
        "[You sent them back their own photo with the send_photo tool. "
        f"It shows: {description}]"
    )


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


def photo_tool_line(number: int, description: str) -> str:
    """Write one photo as the ask_about_photo tool lists it.

    Args:
        number: The number the model picks it by.
        description: What the photo shows.

    Returns:
        E.g. "1. A ginger cat asleep…", shortened if long.
    """
    if len(description) > MAX_PHOTO_LINE_CHARACTERS:
        description = description[: MAX_PHOTO_LINE_CHARACTERS - 1] + "…"
    return f"{number}. {description}"


class PhotoService:
    """Holds every photo rule: nothing else downloads or looks at images (ADR-0007).

    Photos are downloaded from the chat channel when needed and never kept.
    """

    def __init__(
        self,
        repositories: Repositories,
        chat_channel: ChatChannel,
        chat_model: UsageRecordingChatModel,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where settings and Shared Photos are stored.
            chat_channel: Downloads the photos.
            chat_model: Looks at each photo and records the look.
            clock: Pauses between tries.
        """
        self._repositories = repositories
        self._chat_channel = chat_channel
        self._chat_model = chat_model
        self._clock = clock

    def read_message(
        self, snapshot: UserSnapshot, photos: Sequence[ChannelPhoto], caption: str
    ) -> PhotoMessage:
        """Describe a User's photos and write their message as the Companion reads it.

        At most `photo_album_max_photos` are looked at; the Companion is told
        how many more there were. Every photo is described for the Safeguard.
        When Photo Viewing doesn't work for the User, the descriptions go to
        the Safeguard alone: the Companion reads only the caption and the
        "Photo Viewing off" note, and no photo is marked as viewed.

        Args:
            snapshot: The User who sent them.
            photos: The photo, or an album's photos in the order sent.
            caption: The caption; "" if none.

        Returns:
            The message text and the photos looked at, each marked as viewed,
            holding its description if the reply may see it, and the caption;
            with Photo Viewing off, the Safeguard's own text too.
        """
        settings = snapshot.settings
        looked_at = photos[: settings.get(PHOTO_ALBUM_MAX_PHOTOS)]
        descriptions = [self.describe(snapshot, photo) for photo in looked_at]
        described_text = photo_message_text(
            caption,
            descriptions,
            settings.get(PHOTO_NOT_VIEWED_NOTE),
            photos_not_looked_at=len(photos) - len(looked_at),
        )
        if not snapshot.works(Feature.PHOTO_VIEWING):
            return PhotoMessage(
                text=photo_message_text(
                    caption,
                    descriptions,
                    settings.get(PHOTO_NOT_VIEWED_NOTE),
                    viewing_off_note=settings.get(PHOTO_VIEWING_OFF_NOTE),
                ),
                photos=tuple(
                    replace(photo, caption=caption.strip()) for photo in looked_at
                ),
                safeguard_text=described_text,
            )
        return PhotoMessage(
            text=described_text,
            photos=tuple(
                replace(
                    photo,
                    viewed=description is not None,
                    description=description or "",
                    caption=caption.strip(),
                )
                for photo, description in zip(looked_at, descriptions, strict=True)
            ),
        )

    def describe(self, snapshot: UserSnapshot, photo: ChannelPhoto) -> str | None:
        """Download a photo and write a detailed description of it.

        A failed download or look is tried again up to `photo_retry_count`
        times, with a short pause. The tokens each look took go into the
        User's usage.

        Args:
            snapshot: The User who sent it.
            photo: The photo.

        Returns:
            The description, or None if it still couldn't be viewed; the
            error is logged, never raised.
        """
        if photo.too_big_to_download:
            logger.error("Could not view a photo: it is too big to download")
            return None
        settings = snapshot.settings
        return self._look(
            snapshot,
            photo,
            settings.get(PHOTO_DESCRIPTION_PROMPT),
            log_action="view a photo",
        )

    def ask(
        self, snapshot: UserSnapshot, photo: ChannelPhoto, question: str
    ) -> str | None:
        """Look at a User's photo again to answer a question about it.

        Retries and usage work as for `describe`.

        Args:
            snapshot: The User who sent it.
            photo: The photo.
            question: What to look for.

        Returns:
            The answer, or None if it still couldn't be looked at; the
            error is logged, never raised.
        """
        settings = snapshot.settings
        return self._look(
            snapshot,
            photo,
            photo_question_instructions(
                settings.get(PHOTO_DESCRIPTION_PROMPT), question
            ),
            log_action="look at a photo again",
        )

    def list_shared(self, user_id: UUID) -> list[SharedPhoto]:
        """List a User's Shared Photos, newest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Shared Photos.
        """
        return self._repositories.user_memory.list_shared_photos(user_id)

    def delete_shared(self, user_id: UUID, photo_id: UUID) -> None:
        """Delete one of a User's Shared Photos.

        Args:
            user_id: The User's ID.
            photo_id: The Shared Photo's ID.

        Raises:
            SharedPhotoNotFoundError: If the User has no such Shared Photo.
        """
        if not self._repositories.user_memory.delete_shared_photo(user_id, photo_id):
            raise SharedPhotoNotFoundError(photo_id)

    def shared_photo_image(self, user_id: UUID, photo_id: UUID) -> PhotoImage | None:
        """Download one of a User's Shared Photos for the Dashboard.

        Args:
            user_id: The User's ID.
            photo_id: The Shared Photo's ID.

        Returns:
            The image, or None if it couldn't be downloaded; the error is
            logged, never raised.

        Raises:
            SharedPhotoNotFoundError: If the User has no such Shared Photo.
        """
        photo = self._repositories.user_memory.get_shared_photo(user_id, photo_id)
        if photo is None:
            raise SharedPhotoNotFoundError(photo_id)
        try:
            return self._chat_channel.download_photo(photo.file_id)
        except Exception:
            logger.exception("Could not download a Shared Photo")
            return None

    def _look(
        self,
        snapshot: UserSnapshot,
        photo: ChannelPhoto,
        instructions: str,
        log_action: str,
    ) -> str | None:
        """Download a photo and look at it, trying again when that fails.

        Args:
            snapshot: The User who sent the photo, for usage and the Model Call
                Log.
            photo: The photo.
            instructions: What to write about the photo.
            log_action: What is being done, for the error log, e.g.
                "view a photo".

        Returns:
            What the photo viewer wrote, or None after the last failed try.
        """
        settings = snapshot.settings
        tries = 1 + settings.get(PHOTO_RETRY_COUNT)
        for attempt in range(1, tries + 1):
            try:
                image = self._chat_channel.download_photo(photo.file_id)
                answer = self._chat_model.look(
                    snapshot=snapshot,
                    model=settings.get(PHOTO_MODEL),
                    instructions=instructions,
                    photo=image,
                )
            except Exception:
                logger.exception(
                    "Could not %s (try %d of %d)", log_action, attempt, tries
                )
            else:
                if answer.strip():
                    return answer.strip()
                logger.error(
                    "Could not %s: the answer was empty (try %d of %d)",
                    log_action,
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

    def offer(self, snapshot: UserSnapshot, context: ReplyContext) -> ReplyOffer:
        """Pick the photo tools for a reply in a Conversation.

        The ask_about_photo tool lists the photos in the Conversation that
        were viewed, by number and description, under the Admin-set tool
        description. A photo saved before descriptions were kept on it is
        listed with its message's text.

        Args:
            snapshot: The User being replied to.
            context: What the reply is answering, with its Conversation.

        Returns:
            The offer with the ask_about_photo tool; no tool when no photo in
            the Conversation was viewed or Photo Viewing doesn't work for the
            User.
        """
        if not snapshot.works(Feature.PHOTO_VIEWING):
            return ReplyOffer()
        messages = self._repositories.conversations.list_messages(
            context.conversation_id
        )
        viewed = [
            (photo, photo.description or message.content)
            for message in messages
            for photo in message.photos
            if photo.viewed
        ]
        if not viewed:
            return ReplyOffer()

        def run_ask(arguments: dict[str, Any]) -> str:
            """Look at the photo the model picked again, with its question.

            Args:
                arguments: The model's arguments, with the "photo" number
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
            answer = self._photo_service.ask(snapshot, photo, question)
            if answer is None:
                return LOOK_AGAIN_FAILED
            return f"Looking again at photo {number}: {answer}"

        listed = "\n".join(
            photo_tool_line(number, photo_description)
            for number, (_, photo_description) in enumerate(viewed, start=1)
        )
        description = snapshot.settings.get(ASK_ABOUT_PHOTO_TOOL_DESCRIPTION)
        return ReplyOffer(
            tools=[
                ChatTool(
                    name="ask_about_photo",
                    description=f"{description}\n\n{listed}",
                    parameters=ASK_ABOUT_PHOTO_PARAMETERS,
                    run=run_ask,
                )
            ]
        )


def send_photo_offer(shared_photos: list[SharedPhoto], description: str) -> ReplyOffer:
    """Offer the send_photo tool for one reply; it picks at most one photo.

    Args:
        shared_photos: The User's own Shared Photos it may send.
        description: The Admin-set tool description, put before the list.

    Returns:
        The offer with the send_photo tool, which sets `picked` when the model
        picks a Shared Photo; no tool when there is no Shared Photo to send.
    """
    offer = ReplyOffer()
    if not shared_photos:
        return offer

    def pick(arguments: dict[str, Any]) -> str:
        """Pick the Shared Photo the model chose, if it is the first one.

        Args:
            arguments: The model's arguments, with the photo's "number".

        Returns:
            What the model is told back.
        """
        if offer.picked is not None:
            return PHOTO_ALREADY_PICKED
        number = arguments.get("photo")
        if not isinstance(number, int) or isinstance(number, bool):
            return NO_SUCH_SHARED_PHOTO
        if not 1 <= number <= len(shared_photos):
            return NO_SUCH_SHARED_PHOTO
        offer.picked = shared_photos[number - 1]
        return f"Photo {number} will be sent after your text. Now write your text."

    listed = "\n".join(
        photo_tool_line(number, photo.description)
        for number, photo in enumerate(shared_photos, start=1)
    )
    offer.tools.append(
        ChatTool(
            name="send_photo",
            description=f"{description}\n\n{listed}",
            parameters=SEND_PHOTO_PARAMETERS,
            run=pick,
        )
    )
    return offer


class SendPhotoTools:
    """Offers the send_photo tool to replies."""

    def __init__(self, repositories: Repositories) -> None:
        """Set up the send_photo tools.

        Args:
            repositories: Where Shared Photos and settings are stored.
        """
        self._repositories = repositories

    def offer(self, snapshot: UserSnapshot, context: ReplyContext) -> ReplyOffer:
        """Offer the send_photo tool for one reply to a User.

        Each Shared Photo is looked up by the User's own ID, so another
        User's photo can never be offered or sent.

        Args:
            snapshot: The User being replied to.
            context: What the reply is answering, with the Shared Photos that
                matter for the message, as the Understanding picked them.

        Returns:
            The offer, listing those of the User's Shared Photos that still
            exist; no tool when there are none.
        """
        user_memory = self._repositories.user_memory
        found = (
            user_memory.get_shared_photo(snapshot.user.id, photo_id)
            for photo_id in context.shared_photo_ids
        )
        shared_photos = [photo for photo in found if photo is not None]
        return send_photo_offer(
            shared_photos,
            snapshot.settings.get(SEND_PHOTO_TOOL_DESCRIPTION),
        )
