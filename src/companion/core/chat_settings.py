from datetime import time
from typing import Any
from uuid import UUID

from companion.core.check_ins import CheckInService
from companion.core.features import FeatureNotAvailableError
from companion.core.memory_retrieval import format_day
from companion.core.models import (
    CheckInChanges,
    CheckInFrequency,
    Feature,
    LifeThread,
    MemoryItem,
    PauseLength,
    PlatformSettings,
    PreferenceChanges,
    User,
    UserSnapshot,
)
from companion.core.platform_settings import (
    CONFIRMATION_WORD_PLACEHOLDER,
    DATA_DELETION_STARTED_NOTE,
    MEMORY_OFF_CHAT_LINE,
    REPLY_DELETE_DATA_INSTRUCTIONS,
    REPLY_SETTINGS_INSTRUCTIONS,
)
from companion.core.ports import ChatTool, Repositories
from companion.core.reply_tools import ReplyContext, ReplyOffer
from companion.core.user_data import ChatDataDeletion
from companion.core.user_memory import MemoryNotFoundError, UserMemoryService
from companion.core.users import InvalidProfileError, UserService

DELETE_DATA_TOOL = "start_deleting_my_data"
TELL_THEM = "Tell them plainly what you changed."
NOTHING_CHANGED = "Nothing changed."
FREQUENCY_WORDS = {
    CheckInFrequency.WEEKLY: "at most once a week",
    CheckInFrequency.FEW_TIMES_A_WEEK: "at most a few times a week",
    CheckInFrequency.MOST_DAYS: "at most most days",
}
NO_ARGUMENTS: dict[str, Any] = {"type": "object", "properties": {}}
PAUSE_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "length": {
            "type": "string",
            "enum": [length.value for length in PauseLength],
            "description": "For a day, a week, or until they ask to resume.",
        }
    },
    "required": ["length"],
}
FREQUENCY_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "frequency": {
            "type": "string",
            "enum": [frequency.value for frequency in CheckInFrequency],
            "description": "Once a week, a few times a week, or most days.",
        }
    },
    "required": ["frequency"],
}
QUIET_HOURS_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "start": {
            "type": "string",
            "description": "When quiet hours begin, 24-hour, e.g. 22:00.",
        },
        "end": {
            "type": "string",
            "description": "When quiet hours end, 24-hour, e.g. 07:30.",
        },
    },
}
ON_OR_OFF_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {"on": {"type": "boolean", "description": "True for on."}},
    "required": ["on"],
}
FORGET_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "number": {
            "type": "integer",
            "description": "The memory's number from list_memories.",
        }
    },
    "required": ["number"],
}
TIME_ZONE_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "time_zone": {
            "type": "string",
            "description": 'The IANA time zone name, e.g. "Europe/London".',
        }
    },
    "required": ["time_zone"],
}


def parse_time(text: Any) -> time | None:
    """Read a 24-hour time like "21:30" the model passed.

    Args:
        text: The model's value.

    Returns:
        The time, or None if it isn't one.
    """
    try:
        return time.fromisoformat(str(text).strip())
    except ValueError:
        return None


def describe_listed_memory(memory: MemoryItem | LifeThread) -> str:
    """Write one line of what list_memories shows the model.

    Args:
        memory: A Memory Item or a Life Thread.

    Returns:
        The Memory Item's content, or the Life Thread's title and story.
    """
    if isinstance(memory, LifeThread):
        return f"A story in their life: {memory.title}. {memory.story}"
    return memory.content


class ReplySettingsTools:
    """The settings tools for one reply to one User.

    Each tool reads the User afresh, so several changes in one reply build
    on each other, and calls the same core service the Dashboard API uses,
    marked as made in chat.
    """

    def __init__(
        self,
        user_id: UUID,
        repositories: Repositories,
        users: UserService,
        check_ins: CheckInService,
        user_memory: UserMemoryService,
        data_deletion: ChatDataDeletion,
        settings: PlatformSettings,
        offer: ReplyOffer,
    ) -> None:
        """Set up the tools for one reply.

        Args:
            user_id: The User being replied to.
            repositories: Where Users are stored.
            users: Changes User Memory, Photo Viewing and the time zone.
            check_ins: Changes Check-in settings.
            user_memory: Lists and forgets Memory Items and Life Threads.
            data_deletion: Asks to delete the User's data.
            settings: The platform settings, read once for the reply.
            offer: The reply's offer, given the fixed line that closes the
                reply once User Memory is turned off.
        """
        self._user_id = user_id
        self._settings = settings
        self._offer = offer
        self._repositories = repositories
        self._users = users
        self._check_ins = check_ins
        self._user_memory = user_memory
        self._data_deletion = data_deletion
        self._listed_memories: list[MemoryItem | LifeThread] = []

    @property
    def tools(self) -> list[ChatTool]:
        """Every settings tool a User may use in chat."""
        return [
            ChatTool(
                name="pause_check_ins",
                description=(
                    "Pause the person's Check-ins for a day, a week, or until "
                    "they ask to resume, when they clearly ask for a break."
                ),
                parameters=PAUSE_PARAMETERS,
                run=self._pause,
            ),
            ChatTool(
                name="resume_check_ins",
                description="End a pause on the person's Check-ins.",
                parameters=NO_ARGUMENTS,
                run=self._resume,
            ),
            ChatTool(
                name="change_check_in_frequency",
                description="Change how often, at most, you may check in.",
                parameters=FREQUENCY_PARAMETERS,
                run=self._change_frequency,
            ),
            ChatTool(
                name="change_quiet_hours",
                description=(
                    "Change the person's quiet hours, when you never check in, "
                    "in their local time. Give the start, the end, or both."
                ),
                parameters=QUIET_HOURS_PARAMETERS,
                run=self._change_quiet_hours,
            ),
            ChatTool(
                name="turn_user_memory_on_or_off",
                description=(
                    "Turn your memory of the person on or off. Off deletes "
                    "nothing: you still use what you remember but stop "
                    "learning anything new."
                ),
                parameters=ON_OR_OFF_PARAMETERS,
                run=self._turn_user_memory_on_or_off,
            ),
            ChatTool(
                name="turn_photo_viewing_on_or_off",
                description=(
                    "Turn on or off whether you look at the person's photos. "
                    "Off means you don't look at, keep or use their photos; "
                    "every photo is still checked for safety."
                ),
                parameters=ON_OR_OFF_PARAMETERS,
                run=self._turn_photo_viewing_on_or_off,
            ),
            ChatTool(
                name="list_memories",
                description=(
                    "List what you remember about the person and the stories "
                    "in their life you follow, by number, to find the one "
                    "they want you to forget."
                ),
                parameters=NO_ARGUMENTS,
                run=self._list_memories,
            ),
            ChatTool(
                name="forget_memory",
                description=(
                    "Forget one memory or story the person named, by its "
                    "number from list_memories. Only the one they clearly meant."
                ),
                parameters=FORGET_PARAMETERS,
                run=self._forget_memory,
            ),
            ChatTool(
                name="change_time_zone",
                description="Change the person's time zone.",
                parameters=TIME_ZONE_PARAMETERS,
                run=self._change_time_zone,
            ),
            ChatTool(
                name=DELETE_DATA_TOOL,
                description=(
                    "Start deleting the person's data when they clearly ask to "
                    "delete their data. Nothing is deleted until they reply "
                    "with the confirmation word."
                ),
                parameters=NO_ARGUMENTS,
                run=self._start_deleting_data,
            ),
        ]

    def _user(self) -> User:
        """Read the User as they are now.

        Returns:
            The User.

        Raises:
            LookupError: If the User no longer exists.
        """
        user = self._repositories.users.get(self._user_id)
        if user is None:
            raise LookupError
        return user

    def _pause(self, arguments: dict[str, Any]) -> str:
        """Pause the User's Check-ins.

        Args:
            arguments: The model's arguments, with the pause "length".

        Returns:
            What the model is told back.
        """
        user = self._user()
        if not user.check_ins.enabled:
            return (
                "Their Check-ins are off, so there is nothing to pause. "
                f"{NOTHING_CHANGED}"
            )
        try:
            length = PauseLength(str(arguments.get("length")))
        except ValueError:
            return f"The length must be day, week or until_resumed. {NOTHING_CHANGED}"
        settings = self._check_ins.pause(user, length, in_chat=True).check_ins
        if settings.paused_until is None:
            return f"Check-ins are paused until they ask to resume. {TELL_THEM}"
        until = format_day(settings.paused_until, user.time_zone)
        return f"Check-ins are paused until {until}. {TELL_THEM}"

    def _resume(self, arguments: dict[str, Any]) -> str:
        """End the pause on the User's Check-ins.

        Args:
            arguments: The model's arguments; none are needed.

        Returns:
            What the model is told back.
        """
        user = self._user()
        if not self._check_ins.is_paused(user):
            return f"Their Check-ins aren't paused. {NOTHING_CHANGED}"
        self._check_ins.resume(user, in_chat=True)
        return f"Check-ins are resumed. {TELL_THEM}"

    def _change_frequency(self, arguments: dict[str, Any]) -> str:
        """Change how often, at most, Check-ins may be sent.

        Args:
            arguments: The model's arguments, with the "frequency".

        Returns:
            What the model is told back.
        """
        try:
            frequency = CheckInFrequency(str(arguments.get("frequency")))
        except ValueError:
            return (
                "The frequency must be weekly, few_times_a_week or most_days. "
                f"{NOTHING_CHANGED}"
            )
        self._check_ins.change_settings(
            self._user(), CheckInChanges(frequency=frequency), in_chat=True
        )
        return f"Check-ins are now {FREQUENCY_WORDS[frequency]}. {TELL_THEM}"

    def _change_quiet_hours(self, arguments: dict[str, Any]) -> str:
        """Change when the User's quiet hours start or end.

        Args:
            arguments: The model's arguments, with the "start", "end" or both.

        Returns:
            What the model is told back.
        """
        start = parse_time(arguments["start"]) if "start" in arguments else None
        end = parse_time(arguments["end"]) if "end" in arguments else None
        given_but_unreadable = ("start" in arguments and start is None) or (
            "end" in arguments and end is None
        )
        if given_but_unreadable or (start is None and end is None):
            return (
                "Give the start or end as a 24-hour time like 22:00. Ask them "
                f"if you aren't sure. {NOTHING_CHANGED}"
            )
        settings = self._check_ins.change_settings(
            self._user(),
            CheckInChanges(quiet_hours_start=start, quiet_hours_end=end),
            in_chat=True,
        ).check_ins
        return (
            f"Quiet hours are now {settings.quiet_hours_start:%H:%M} to "
            f"{settings.quiet_hours_end:%H:%M}, their time. {TELL_THEM}"
        )

    def _turn_user_memory_on_or_off(self, arguments: dict[str, Any]) -> str:
        """Turn User Memory on or off.

        Turning it off closes the reply with the Admin-set line saying
        nothing is deleted, so the User is always told; turning it back on
        in the same reply drops that line.

        Args:
            arguments: The model's arguments, with "on".

        Returns:
            What the model is told back.
        """
        turn_on = arguments.get("on")
        if not isinstance(turn_on, bool):
            return f"Say true for on or false for off. {NOTHING_CHANGED}"
        try:
            self._users.update_preferences(
                self._user(),
                PreferenceChanges(user_memory_enabled=turn_on),
                in_chat=True,
            )
        except FeatureNotAvailableError:
            return (
                "User Memory isn't available on their account, so it can't be "
                f"turned on or off. {NOTHING_CHANGED} Tell them so plainly."
            )
        if turn_on:
            self._offer.closing_text = ""
            return f"Your memory of them is on. {TELL_THEM}"
        self._offer.closing_text = self._settings.get(MEMORY_OFF_CHAT_LINE)
        return (
            "Your memory of them is off: you won't learn anything new, but you "
            "still use what you already know. Nothing was deleted. A fixed line "
            "saying so is sent after your reply, so don't repeat it. "
            f"{TELL_THEM}"
        )

    def _turn_photo_viewing_on_or_off(self, arguments: dict[str, Any]) -> str:
        """Turn Photo Viewing on or off.

        Args:
            arguments: The model's arguments, with "on".

        Returns:
            What the model is told back.
        """
        turn_on = arguments.get("on")
        if not isinstance(turn_on, bool):
            return f"Say true for on or false for off. {NOTHING_CHANGED}"
        try:
            self._users.update_preferences(
                self._user(),
                PreferenceChanges(photo_viewing_enabled=turn_on),
                in_chat=True,
            )
        except FeatureNotAvailableError:
            return (
                "Photo Viewing isn't available on their account, so it can't be "
                f"turned on or off. {NOTHING_CHANGED} Tell them so plainly."
            )
        if turn_on:
            return f"Photo Viewing is on: you look at the photos they send. {TELL_THEM}"
        return (
            "Photo Viewing is off: you won't look at, keep or use their photos "
            "until they turn it on. Every photo is still checked for safety, "
            f"and their Shared Photos weren't deleted. {TELL_THEM}"
        )

    def _list_memories(self, arguments: dict[str, Any]) -> str:
        """List the User's Memory Items, then their Life Threads, by number.

        Args:
            arguments: The model's arguments; none are needed.

        Returns:
            The numbered Memory Items and Life Threads, or that there are none.
        """
        groups = self._user_memory.list_groups(self._user_id)
        items = [item for group in groups for item in group.items]
        threads = self._user_memory.list_threads(self._user_id)
        self._listed_memories = [*items, *threads]
        if not self._listed_memories:
            return "You remember nothing about them."
        return "\n".join(
            f"{number}. {describe_listed_memory(memory)}"
            for number, memory in enumerate(self._listed_memories, start=1)
        )

    def _forget_memory(self, arguments: dict[str, Any]) -> str:
        """Forget one of the listed Memory Items or Life Threads.

        Args:
            arguments: The model's arguments, with the memory's "number".

        Returns:
            What the model is told back.
        """
        if not self._listed_memories:
            return f"Call list_memories first to see the numbers. {NOTHING_CHANGED}"
        try:
            number = int(arguments.get("number", 0))
        except (TypeError, ValueError):
            number = 0
        if not 1 <= number <= len(self._listed_memories):
            return f"There is no memory with that number. {NOTHING_CHANGED}"
        memory = self._listed_memories[number - 1]
        try:
            if isinstance(memory, LifeThread):
                self._user_memory.delete_thread(self._user_id, memory.id)
                forgotten = memory.title
            else:
                self._user_memory.delete_item(self._user_id, memory.id)
                forgotten = memory.content
        except MemoryNotFoundError:
            return f"That memory is already gone. {NOTHING_CHANGED}"
        return f'You forgot "{forgotten}". {TELL_THEM}'

    def _change_time_zone(self, arguments: dict[str, Any]) -> str:
        """Change the User's time zone.

        Args:
            arguments: The model's arguments, with the "time_zone".

        Returns:
            What the model is told back.
        """
        time_zone = str(arguments.get("time_zone", "")).strip()
        try:
            self._users.update_preferences(
                self._user(), PreferenceChanges(time_zone=time_zone), in_chat=True
            )
        except InvalidProfileError:
            return (
                f'"{time_zone}" isn\'t a known time zone. Ask them which city '
                f"they're in. {NOTHING_CHANGED}"
            )
        return f"Their time zone is now {time_zone}. {TELL_THEM}"

    def _start_deleting_data(self, arguments: dict[str, Any]) -> str:
        """Ask for the confirmation word before deleting the User's data.

        Args:
            arguments: The model's arguments; none are needed.

        Returns:
            What the model is told back, with the confirmation word.
        """
        self._data_deletion.ask(self._user())
        word = self._data_deletion.confirmation_word(self._settings)
        note = self._settings.get(DATA_DELETION_STARTED_NOTE)
        return note.replace(CONFIRMATION_WORD_PLACEHOLDER, word)


class SettingsTools:
    """Offers replies the tools to change a User's settings in chat (ADR-0006).

    When Settings in Chat doesn't work for the User, only the tool to delete
    their data is offered: deleting their data never depends on a Feature.
    """

    def __init__(
        self,
        repositories: Repositories,
        users: UserService,
        check_ins: CheckInService,
        user_memory: UserMemoryService,
        data_deletion: ChatDataDeletion,
    ) -> None:
        """Set up the settings tools.

        Args:
            repositories: Where Users and settings are stored.
            users: Changes User Memory, Photo Viewing and the time zone.
            check_ins: Changes Check-in settings.
            user_memory: Lists and forgets Memory Items and Life Threads.
            data_deletion: Asks to delete the User's data.
        """
        self._repositories = repositories
        self._users = users
        self._check_ins = check_ins
        self._user_memory = user_memory
        self._data_deletion = data_deletion

    def offer(self, snapshot: UserSnapshot, context: ReplyContext) -> ReplyOffer:
        """Pick the settings tools for a reply to a User.

        Deleting the account, changing country and disconnecting Telegram
        have no tool: they are only on the Dashboard.

        Args:
            snapshot: The User being replied to.
            context: What the reply is answering; not needed here.

        Returns:
            The tools and their reply instructions; only the tool to delete
            their data, with its own instructions, when Settings in Chat
            doesn't work for them.
        """
        offer = ReplyOffer()
        reply_tools = ReplySettingsTools(
            snapshot.user.id,
            self._repositories,
            self._users,
            self._check_ins,
            self._user_memory,
            self._data_deletion,
            snapshot.settings,
            offer,
        )
        if snapshot.works(Feature.SETTINGS_IN_CHAT):
            offer.tools = reply_tools.tools
            instructions = REPLY_SETTINGS_INSTRUCTIONS
        else:
            offer.tools = [
                tool for tool in reply_tools.tools if tool.name == DELETE_DATA_TOOL
            ]
            instructions = REPLY_DELETE_DATA_INSTRUCTIONS
        offer.instructions = snapshot.settings.get(instructions)
        return offer
