import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from companion.core.models import MessageKind, PlatformSettings
from companion.core.platform_settings import (
    MESSAGE_WAIT_FINISHED_SECONDS,
    MESSAGE_WAIT_LONG_TEXT_WORDS,
    MESSAGE_WAIT_SECONDS,
    MESSAGE_WAIT_TRAILING_SECONDS,
    MESSAGE_WAIT_TRAILING_WORDS,
)

TRAILING_ENDINGS = ("...", "…", ",")
FINISHED_ENDINGS = (".", "!")
EMOJI_JOINERS = {"‍", "️", "︎"}


class TextReads(StrEnum):
    """How a User's latest text reads, which decides how long Zeph waits for more."""

    FINISHED = "finished"
    TRAILING = "trailing"
    NEITHER = "neither"


@dataclass(frozen=True)
class MessageWait:
    """How long to wait for more after a User's latest text.

    Attributes:
        reads: How the text reads.
        seconds: How many seconds to wait.
    """

    reads: TextReads
    seconds: int


def ends_with_emoji(text: str) -> bool:
    """Say whether a text ends with an emoji.

    Args:
        text: The text, with no trailing spaces.

    Returns:
        True if its last character, past any skin tone or joiner, is an emoji.
    """
    for character in reversed(text):
        is_skin_tone = "\U0001f3fb" <= character <= "\U0001f3ff"
        if character in EMOJI_JOINERS or is_skin_tone:
            continue
        return unicodedata.category(character) == "So"
    return False


def how_text_reads(
    kind: MessageKind, text: str, trailing_words: list[str], long_text_words: int
) -> TextReads:
    """Decide whether a User's latest text reads finished, trails off, or neither.

    Args:
        kind: What kind of message it is.
        text: Its text, or a photo's caption; "" if none.
        trailing_words: Words that trail off when they end a text, and short
            openers that do when sent alone, lower-cased.
        long_text_words: How many words a text ending in a full stop, "!" or
            an emoji needs to read finished.

    Returns:
        Finished for a question or a long full thought; trailing for a text
        ending unfinished, a short opener alone or a photo with no caption;
        neither for anything else, a sticker included.
    """
    if kind == MessageKind.STICKER:
        return TextReads.NEITHER
    cleaned = text.strip().lower()
    if not cleaned:
        return TextReads.TRAILING if kind == MessageKind.PHOTO else TextReads.NEITHER
    if cleaned.endswith("?"):
        return TextReads.FINISHED
    words = cleaned.split()
    if (
        cleaned.endswith(TRAILING_ENDINGS)
        or words[-1] in trailing_words
        or " ".join(words) in trailing_words
    ):
        return TextReads.TRAILING
    is_long = len(words) >= long_text_words
    if is_long and (cleaned.endswith(FINISHED_ENDINGS) or ends_with_emoji(cleaned)):
        return TextReads.FINISHED
    return TextReads.NEITHER


def message_wait(
    kind: MessageKind, text: str, settings: PlatformSettings
) -> MessageWait:
    """Decide how long to wait for more after a User's latest text.

    Args:
        kind: What kind of message it is.
        text: Its text, or a photo's caption; "" if none.
        settings: The platform settings, which hold each wait and the rules.

    Returns:
        How the text reads and the seconds to wait.
    """
    reads = how_text_reads(
        kind,
        text,
        settings.get(MESSAGE_WAIT_TRAILING_WORDS),
        settings.get(MESSAGE_WAIT_LONG_TEXT_WORDS),
    )
    wait_setting = {
        TextReads.FINISHED: MESSAGE_WAIT_FINISHED_SECONDS,
        TextReads.TRAILING: MESSAGE_WAIT_TRAILING_SECONDS,
        TextReads.NEITHER: MESSAGE_WAIT_SECONDS,
    }[reads]
    return MessageWait(reads=reads, seconds=settings.get(wait_setting))
