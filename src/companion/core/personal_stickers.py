import json
import logging
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from companion.core.features import FeatureService
from companion.core.models import (
    ChannelSticker,
    ChatLine,
    ChatRole,
    ConversationMessage,
    Feature,
    MessageDirection,
    PersonalSticker,
    StickerImage,
)
from companion.core.ports import ChatChannel, Clock, Repositories
from companion.core.transcripts import to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)


class PersonalStickerNotFoundError(LookupError):
    """Raised when a User has no Personal Sticker with the given ID."""


@dataclass(frozen=True)
class SentSticker:
    """A sticker the User sent in a Conversation, and when they last sent it.

    Attributes:
        sticker: The sticker.
        sent_at: When they last sent it in the Conversation.
    """

    sticker: ChannelSticker
    sent_at: datetime


def list_sent_stickers(messages: list[ConversationMessage]) -> list[SentSticker]:
    """List the different stickers the User sent in a Conversation.

    Args:
        messages: The Conversation's messages, oldest first.

    Returns:
        Each sticker once, in the order first sent, with when it was last sent.
    """
    sent: dict[str, SentSticker] = {}
    for message in messages:
        if message.direction == MessageDirection.INCOMING and message.sticker:
            sent[message.sticker.file_unique_id] = SentSticker(
                sticker=message.sticker, sent_at=message.sent_at
            )
    return list(sent.values())


def read_stickers_to_keep(answer: str) -> list[Any]:
    """Read the stickers the keeping model picked from its JSON answer.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        The picks, as the model wrote them; [] if the answer can't be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return []
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return []
    picks = parsed.get("stickers_to_keep") if isinstance(parsed, dict) else None
    return picks if isinstance(picks, list) else []


def notes_for_valid_picks(
    picks: list[Any], stickers_by_number: dict[int, SentSticker]
) -> dict[int, str]:
    """Check the model's picks and read the note for each sticker it kept.

    A pick is skipped when it names an unknown sticker or has no note. When
    a sticker is picked twice, its last note is used.

    Args:
        picks: The picks, as the model wrote them.
        stickers_by_number: The stickers it was shown, by number.

    Returns:
        Each kept sticker's note, by number.
    """
    notes: dict[int, str] = {}
    for pick in picks:
        if not isinstance(pick, dict):
            continue
        number, note = pick.get("sticker"), pick.get("note")
        if (
            isinstance(number, int)
            and not isinstance(number, bool)
            and number in stickers_by_number
            and isinstance(note, str)
            and note.strip()
        ):
            notes[number] = note.strip()
    return notes


def plan_personal_stickers(
    notes: dict[int, str],
    stickers_by_number: dict[int, SentSticker],
    kept_by_unique_id: dict[str, PersonalSticker],
    user_id: UUID,
    now: datetime,
) -> list[PersonalSticker]:
    """Work out the Personal Stickers to save after a Conversation.

    A picked sticker is kept with its note, replacing the note of one kept
    already. A sticker kept already that the User sent again but wasn't
    picked keeps its note. Either way it was used when the User last sent it.

    Args:
        notes: Each picked sticker's note, by number.
        stickers_by_number: The stickers the User sent, by number.
        kept_by_unique_id: The User's Personal Stickers, by unchanging ID.
        user_id: The User.
        now: When they are being kept.

    Returns:
        The stickers to save.
    """
    planned: list[PersonalSticker] = []
    for number, sent in stickers_by_number.items():
        kept = kept_by_unique_id.get(sent.sticker.file_unique_id)
        note = notes.get(number) or (kept.note if kept else None)
        if note is None:
            continue
        planned.append(
            PersonalSticker(
                id=kept.id if kept else uuid4(),
                user_id=user_id,
                file_id=sent.sticker.file_id,
                file_unique_id=sent.sticker.file_unique_id,
                emoji=sent.sticker.emoji,
                set_name=sent.sticker.set_name,
                preview_file_id=sent.sticker.preview_file_id,
                note=note,
                kept_at=kept.kept_at if kept else now,
                last_used_at=sent.sent_at,
            )
        )
    return planned


def describe_stickers(
    messages: list[ConversationMessage],
    stickers_by_number: dict[int, SentSticker],
    kept_by_unique_id: dict[str, PersonalSticker],
) -> str:
    """Write what the keeping model is given.

    Args:
        messages: The Conversation's messages, oldest first.
        stickers_by_number: The stickers the User sent, by number.
        kept_by_unique_id: The User's Personal Stickers, by unchanging ID.

    Returns:
        The stickers the User sent, with the note of each one kept already,
        and the Conversation with each sticker marked by its number.
    """
    numbers = {
        sent.sticker.file_unique_id: number
        for number, sent in stickers_by_number.items()
    }
    sticker_lines = []
    for number, sent in stickers_by_number.items():
        line = f"[{number}] {sent.sticker.emoji or 'no emoji'}"
        kept = kept_by_unique_id.get(sent.sticker.file_unique_id)
        sticker_lines.append(f"{line} (kept already: {kept.note})" if kept else line)
    marked_messages = [
        replace(message, content=numbered_sticker_text(message.sticker, numbers))
        if message.direction == MessageDirection.INCOMING and message.sticker
        else message
        for message in messages
    ]
    return (
        "Stickers the person sent:\n" + "\n".join(sticker_lines) + "\n\n"
        f"The Conversation:\n{to_transcript_lines(marked_messages)}"
    )


def numbered_sticker_text(sticker: ChannelSticker, numbers: dict[str, int]) -> str:
    """Write a sticker in the Conversation with the number the model picks it by.

    Args:
        sticker: The sticker.
        numbers: Each sticker's number, by unchanging ID.

    Returns:
        E.g. "[sticker 1: 😂]", or "[sticker 1]" without an emoji.
    """
    number = numbers[sticker.file_unique_id]
    if sticker.emoji:
        return f"[sticker {number}: {sticker.emoji}]"
    return f"[sticker {number}]"


class PersonalStickerKeeper:
    """Keeps the stickers a User sent whose meaning was clear, when a Conversation ends.

    Personal Stickers aren't User Memory, so User Memory doesn't affect this.
    """

    def __init__(
        self,
        repositories: Repositories,
        features: FeatureService,
        chat_model: UsageRecordingChatModel,
        clock: Clock,
    ) -> None:
        """Set up the keeper.

        Args:
            repositories: Where Personal Stickers and settings are stored.
            features: Says whether Personal Stickers works for the User.
            chat_model: Picks the stickers to keep and writes their notes,
                and records the tokens used.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._features = features
        self._chat_model = chat_model
        self._clock = clock

    def keep_from(self, user_id: UUID, messages: list[ConversationMessage]) -> None:
        """Keep the stickers that fit from an ended Conversation.

        Nothing happens when Personal Stickers doesn't work for the User or
        they sent no stickers. Otherwise one model call picks the stickers
        with a clear meaning and writes a "when to use" note for each. Then
        the User's stickers over the limit are dropped, the one used longest
        ago first.

        Args:
            user_id: The User whose Conversation it was.
            messages: The Conversation's messages, oldest first.
        """
        if not self._features.works_for(user_id, Feature.PERSONAL_STICKERS):
            return
        stickers_by_number = dict(enumerate(list_sent_stickers(messages), start=1))
        if not stickers_by_number:
            return
        personal_stickers = self._repositories.personal_stickers
        kept_by_unique_id = {
            sticker.file_unique_id: sticker
            for sticker in personal_stickers.list_for_user(user_id)
        }
        settings = self._repositories.platform_settings
        answer = self._chat_model.generate(
            user_id=user_id,
            model=settings.get("personal_sticker_keeping_model"),
            instructions=settings.get("personal_sticker_keeping_prompt"),
            history=[
                ChatLine(
                    role=ChatRole.USER,
                    text=describe_stickers(
                        messages, stickers_by_number, kept_by_unique_id
                    ),
                )
            ],
        )
        notes = notes_for_valid_picks(read_stickers_to_keep(answer), stickers_by_number)
        personal_stickers.save_many(
            plan_personal_stickers(
                notes,
                stickers_by_number,
                kept_by_unique_id,
                user_id,
                self._clock.now(),
            )
        )
        personal_stickers.keep_most_recently_used(
            user_id, settings.get("personal_stickers_limit")
        )


class PersonalStickerService:
    """Lets a User see and remove their Personal Stickers, and Admins count them.

    This works whether or not Personal Stickers works for the User.
    """

    def __init__(self, repositories: Repositories, chat_channel: ChatChannel) -> None:
        """Set up the service.

        Args:
            repositories: Where Personal Stickers are stored.
            chat_channel: Downloads sticker images.
        """
        self._repositories = repositories
        self._chat_channel = chat_channel

    def list_for(self, user_id: UUID) -> list[PersonalSticker]:
        """List a User's Personal Stickers, most recently used first.

        Args:
            user_id: The User.

        Returns:
            The stickers.
        """
        return self._repositories.personal_stickers.list_for_user(user_id)

    def count_for(self, user_id: UUID) -> int:
        """Count a User's Personal Stickers.

        Args:
            user_id: The User.

        Returns:
            How many they have.
        """
        return self._repositories.personal_stickers.count_for_user(user_id)

    def get_image(self, user_id: UUID, sticker_id: UUID) -> StickerImage | None:
        """Get an image of one of a User's Personal Stickers for the Dashboard.

        Args:
            user_id: The User it must belong to.
            sticker_id: The sticker's ID.

        Returns:
            The image, or None if the sticker has none a browser can show or
            it couldn't be downloaded.

        Raises:
            PersonalStickerNotFoundError: If the User has no such sticker.
        """
        sticker = self._repositories.personal_stickers.get(user_id, sticker_id)
        if sticker is None:
            raise PersonalStickerNotFoundError(sticker_id)
        if sticker.preview_file_id is None:
            return None
        try:
            return self._chat_channel.get_sticker_image(sticker.preview_file_id)
        except Exception:
            logger.exception("Could not download a Personal Sticker image")
            return None

    def remove(self, user_id: UUID, sticker_id: UUID) -> None:
        """Remove one of a User's Personal Stickers.

        Args:
            user_id: The User it must belong to.
            sticker_id: The sticker's ID.

        Raises:
            PersonalStickerNotFoundError: If the User has no such sticker.
        """
        if not self._repositories.personal_stickers.delete(user_id, sticker_id):
            raise PersonalStickerNotFoundError(sticker_id)
