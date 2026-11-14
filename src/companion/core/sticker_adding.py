import logging
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from companion.core.models import ChannelSticker, IncomingMessage, User, UserRole
from companion.core.ports import ChatChannel, ChatTool, Repositories, Timer
from companion.core.stickers import (
    StickerLibraryService,
    StickerSetNotFoundError,
    StickerSetUnavailableError,
)

logger = logging.getLogger(__name__)

ADDING_TOOL = "start_adding_stickers"
ADDED_REACTION = "👍"
QUIET_GAP_SETTING = "sticker_adding_quiet_gap_minutes"
SUMMARY_SETTING = "sticker_adding_summary_reply"
NOT_WORDS = re.compile(r"[^\w\s]")


class AddingChoice(StrEnum):
    """What each sticker an Admin sends adds to the Sticker Library."""

    SINGLE_STICKERS = "single_stickers"
    WHOLE_SETS = "whole_sets"


CHOICE_WORDS = {
    AddingChoice.SINGLE_STICKERS: "single stickers",
    AddingChoice.WHOLE_SETS: "whole sets",
}
ADD_THIS_PHRASES = {
    "add this": AddingChoice.SINGLE_STICKERS,
    "add it": AddingChoice.SINGLE_STICKERS,
    "add this sticker": AddingChoice.SINGLE_STICKERS,
    "add this set": AddingChoice.WHOLE_SETS,
    "add the set": AddingChoice.WHOLE_SETS,
    "add this whole set": AddingChoice.WHOLE_SETS,
    "add the whole set": AddingChoice.WHOLE_SETS,
}
ADDING_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "choice": {
            "type": "string",
            "enum": [choice.value for choice in AddingChoice],
            "description": (
                "single_stickers adds each sticker they send; whole_sets adds "
                "every sticker in the set of each sticker they send."
            ),
        }
    },
    "required": ["choice"],
}


@dataclass
class StickerTally:
    """What an Admin added to the Sticker Library in chat.

    Attributes:
        added: How many stickers were added.
        already_there: How many were already in the library and skipped.
        sets: The sticker sets added whole.
    """

    added: int = 0
    already_there: int = 0
    sets: set[str] = field(default_factory=set)


@dataclass
class AddingMode:
    """One Admin's adding mode: what each sticker adds, and what was added.

    Attributes:
        choice: Whether each sticker adds itself or its whole set.
        chat_id: The chat the stickers come from; None until the first one.
        tally: What was added so far.
    """

    choice: AddingChoice
    chat_id: int | None = None
    tally: StickerTally = field(default_factory=StickerTally)


def add_request(text: str) -> AddingChoice | None:
    """Read whether a reply to a sticker asks to add it, or its set.

    Args:
        text: The reply's text.

    Returns:
        The choice for "add this" or "add this set" (any case, any
        punctuation or emoji); None for anything else.
    """
    phrase = " ".join(NOT_WORDS.sub("", text).lower().split())
    return ADD_THIS_PHRASES.get(phrase)


def added_summary(tally: StickerTally) -> str:
    """Write what was added, as the Admin is told.

    Args:
        tally: What was added.

    Returns:
        E.g. "Added 33 stickers from 1 set (2 were already there)."
    """
    stickers = "1 sticker" if tally.added == 1 else f"{tally.added} stickers"
    summary = f"Added {stickers}"
    if tally.sets:
        summary += f" from {len(tally.sets)} set{'' if len(tally.sets) == 1 else 's'}"
    if tally.already_there:
        verb = "was" if tally.already_there == 1 else "were"
        summary += f" ({tally.already_there} {verb} already there)"
    return f"{summary}."


class StickerAdding:
    """Lets Admins add stickers to the Sticker Library from the chat.

    An Admin asks the Companion in plain words, which starts adding mode
    through a tool (like ADR-0006's settings tools). In the mode each sticker
    they send is added, or its whole set, and gets a reaction instead of a
    reply. The mode ends on their first message that isn't a sticker, or
    after a quiet gap, and they are told what was added. An Admin can also
    reply "add this" or "add this set" to a sticker in the chat. Adding modes
    live in memory only, so a restart ends them.

    One lock guards every adding mode and is held while a sticker is added
    and reacted to, so the summary never comes before a sticker's reaction.
    Only Admins in adding mode ever wait on it.
    """

    def __init__(
        self,
        repositories: Repositories,
        sticker_library: StickerLibraryService,
        chat_channel: ChatChannel,
        deliver_notice: Callable[[UUID, int, str], None],
        timer: Timer,
        dashboard_url: str,
    ) -> None:
        """Set up sticker adding.

        Args:
            repositories: Where Users and settings are stored.
            sticker_library: Adds stickers and looks up sticker sets.
            chat_channel: Reacts to stickers.
            deliver_notice: Sends the summary to an Admin's chat and saves it
                in their Conversation, so the next reply knows what was added.
            timer: Ends adding mode after the quiet gap.
            dashboard_url: The Dashboard's address, put into the summary.
        """
        self._repositories = repositories
        self._sticker_library = sticker_library
        self._chat_channel = chat_channel
        self._deliver_notice = deliver_notice
        self._timer = timer
        self._dashboard_url = dashboard_url
        self._modes: dict[UUID, AddingMode] = {}
        self._guard = threading.Lock()

    def tools(self, user: User) -> list[ChatTool]:
        """Offer the tool that starts adding mode, to Admins only.

        Args:
            user: The User being replied to.

        Returns:
            The tool for an Admin; none for anyone else.
        """
        if user.role != UserRole.ADMIN:
            return []
        return [
            ChatTool(
                name=ADDING_TOOL,
                description=(
                    "Start adding stickers to the Sticker Library, when this "
                    "Admin asks to add stickers or sticker sets. Adding is "
                    "off right now, whatever was said earlier: it ends as "
                    "soon as they send anything that isn't a sticker. So call "
                    "this every time they ask, and never tell them to send "
                    "stickers, or say adding is on, without calling it first. "
                    "Ask whether they mean single stickers or whole sets only "
                    "if it isn't clear."
                ),
                parameters=ADDING_PARAMETERS,
                run=lambda arguments: self._start(user.id, arguments),
            )
        ]

    def add_if_adding(self, user_id: UUID, message: IncomingMessage) -> bool:
        """Add a sticker an Admin sent, if they are in adding mode.

        The sticker, or its whole set, is added and gets a reaction, and the
        quiet gap starts again. In whole-sets mode a set already added in
        this mode isn't looked up again, and a sticker whose set can't be
        found is added on its own. A reaction the chat channel refuses is
        logged; the sticker still counts.

        Args:
            user_id: The User who sent it.
            message: The sticker message.

        Returns:
            True if they were in adding mode and it was added; False if they
            weren't, so it is just chat.
        """
        sticker = message.sticker
        with self._guard:
            mode = self._modes.get(user_id)
            if mode is None or sticker is None:
                return False
            mode.chat_id = message.chat_id
            whole_set = mode.choice == AddingChoice.WHOLE_SETS
            set_already_added = (
                sticker.set_name is not None and sticker.set_name in mode.tally.sets
            )
            if not (whole_set and set_already_added):
                self._add(mode.tally, sticker, whole_set)
            self._restart_quiet_gap(user_id)
            self._react(message)
        return True

    def add_if_asked(self, user_id: UUID, message: IncomingMessage) -> bool:
        """Add the sticker an Admin replied "add this" or "add this set" to.

        The Admin is told what was added.

        Args:
            user_id: The User who sent the message.
            message: The message.

        Returns:
            True if it was such a reply from an Admin and the sticker, or its
            set, was added; False if the message is just chat.
        """
        choice = add_request(message.text)
        sticker = message.replied_sticker
        if sticker is None or choice is None or not self._is_admin(user_id):
            return False
        tally = StickerTally()
        self._add(tally, sticker, choice == AddingChoice.WHOLE_SETS)
        self._send_summary(user_id, message.chat_id, tally)
        return True

    def finish(self, user_id: UUID) -> None:
        """End a User's adding mode, if on, and tell them what was added.

        Nothing is sent if no sticker was sent in the mode.

        Args:
            user_id: The User.
        """
        with self._guard:
            mode = self._modes.pop(user_id, None)
        if mode is not None and mode.chat_id is not None:
            self._send_summary(user_id, mode.chat_id, mode.tally)

    def _start(self, user_id: UUID, arguments: dict[str, Any]) -> str:
        """Start adding mode for an Admin, as the model asked.

        Args:
            user_id: The Admin.
            arguments: The model's arguments, with the "choice".

        Returns:
            What the model is told back.
        """
        try:
            choice = AddingChoice(str(arguments.get("choice")))
        except ValueError:
            return "The choice must be single_stickers or whole_sets. Nothing started."
        with self._guard:
            self._modes[user_id] = AddingMode(choice=choice)
            self._restart_quiet_gap(user_id)
        return (
            f"Adding mode is on for {CHOICE_WORDS[choice]}. Tell them in a few "
            f"words to send the stickers over. Each one gets a {ADDED_REACTION} "
            "instead of a reply. When they send something that isn't a "
            "sticker, they are told what was added."
        )

    def _add(
        self, tally: StickerTally, sticker: ChannelSticker, whole_set: bool
    ) -> None:
        """Add one sticker, or its whole set, and count it.

        Args:
            tally: Where to count what was added.
            sticker: The sticker.
            whole_set: True to add every sticker in its set when it has one
                that can be found.
        """
        stickers = [sticker]
        if whole_set and sticker.set_name is not None:
            try:
                stickers = self._sticker_library.find_set(sticker.set_name)
                tally.sets.add(sticker.set_name)
            except (StickerSetNotFoundError, StickerSetUnavailableError):
                stickers = [sticker]
        result = self._sticker_library.add_stickers(stickers)
        tally.added += result.added
        tally.already_there += result.already_there

    def _react(self, message: IncomingMessage) -> None:
        """Put the "added" reaction on a sticker, logging a refusal.

        Args:
            message: The sticker message.
        """
        try:
            self._chat_channel.react(
                message.chat_id, message.message_id, ADDED_REACTION
            )
        except Exception:
            logger.exception("Could not react to an added sticker")

    def _restart_quiet_gap(self, user_id: UUID) -> None:
        """Start the wait after which adding mode ends, again.

        Args:
            user_id: The Admin in adding mode.
        """
        minutes = self._repositories.platform_settings.get(QUIET_GAP_SETTING)
        self._timer.start(
            f"sticker-adding:{user_id}", minutes * 60, lambda: self.finish(user_id)
        )

    def _send_summary(self, user_id: UUID, chat_id: int, tally: StickerTally) -> None:
        """Tell the Admin what was added, with a reminder to write notes.

        The reminder is left out when nothing new was added.

        Args:
            user_id: The Admin.
            chat_id: The chat to send it in.
            tally: What was added.
        """
        summary = added_summary(tally)
        if tally.added:
            template = self._repositories.platform_settings.get(SUMMARY_SETTING)
            summary = template.replace("{added}", summary).replace(
                "{dashboard_url}", self._dashboard_url
            )
        self._deliver_notice(user_id, chat_id, summary)

    def _is_admin(self, user_id: UUID) -> bool:
        """Tell whether a User is an Admin right now.

        Args:
            user_id: The User.

        Returns:
            True if they are an Admin.
        """
        user = self._repositories.users.get(user_id)
        return user is not None and user.role == UserRole.ADMIN
