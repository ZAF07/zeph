from dataclasses import dataclass
from datetime import datetime

from companion.core.check_ins import CheckInService, RecentCheckIn
from companion.core.memory_categories import HOME_GOALS_CATEGORY_SETTING
from companion.core.models import MemoryItem, TelegramConnection, User
from companion.core.ports import Repositories

RECENTLY_REMEMBERED_LIMIT = 3


@dataclass(frozen=True)
class RememberedItem:
    """A Memory Item and the name of its Memory Category.

    Attributes:
        item: The Memory Item.
        category: Its Memory Category's name.
    """

    item: MemoryItem
    category: str


@dataclass(frozen=True)
class Home:
    """What the Dashboard home shows a User. Never a next Check-in time.

    Attributes:
        telegram_connection: The User's Telegram Connection, if they have one.
        last_conversation_at: When the newest message in their newest
            Conversation was sent, if they have had one.
        check_ins_paused: Whether their Check-ins are paused right now.
        last_check_in: The newest Check-in sent to them, if any.
        goals: Their Memory Items in the Goals Memory Category, newest first;
            empty while User Memory is off.
        recently_remembered: Their newest Memory Items, newest first; empty
            while User Memory is off.
    """

    telegram_connection: TelegramConnection | None
    last_conversation_at: datetime | None
    check_ins_paused: bool
    last_check_in: RecentCheckIn | None
    goals: list[MemoryItem]
    recently_remembered: list[RememberedItem]


class HomeService:
    """Gathers what the Dashboard home shows, from data that already exists."""

    def __init__(
        self, repositories: Repositories, check_in_service: CheckInService
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where connections, Conversations, User Memory,
                Memory Categories and settings are stored.
            check_in_service: Tells whether Check-ins are paused and which
                was sent last.
        """
        self._repositories = repositories
        self._check_in_service = check_in_service

    def get(self, user: User) -> Home:
        """Gather a User's Dashboard home.

        Args:
            user: The signed-in User.

        Returns:
            Their Telegram Connection, Check-in status and, if User Memory is
            on, their Goals and newest Memory Items.
        """
        latest_conversation = self._repositories.conversations.get_latest_for_user(
            user.id
        )
        goals, recently_remembered = (
            self._goals_and_recently_remembered(user)
            if user.user_memory_enabled
            else ([], [])
        )
        return Home(
            telegram_connection=self._repositories.telegram_connections.get_by_user(
                user.id
            ),
            last_conversation_at=(
                latest_conversation.last_message_at if latest_conversation else None
            ),
            check_ins_paused=self._check_in_service.is_paused(user),
            last_check_in=self._check_in_service.last_sent(user),
            goals=goals,
            recently_remembered=recently_remembered,
        )

    def _goals_and_recently_remembered(
        self, user: User
    ) -> tuple[list[MemoryItem], list[RememberedItem]]:
        """Pick a User's Goals and newest Memory Items.

        Args:
            user: The User.

        Returns:
            Their Memory Items in the Goals Memory Category, and their
            newest few Memory Items with category names, each newest first.
        """
        category_names = {
            category.id: category.name
            for category in self._repositories.memory_categories.list_all()
        }
        goals_name = self._repositories.platform_settings.get(
            HOME_GOALS_CATEGORY_SETTING
        )
        newest_first = sorted(
            self._repositories.user_memory.list_items(user.id),
            key=lambda item: item.updated_at,
            reverse=True,
        )
        goals = [
            item
            for item in newest_first
            if category_names.get(item.category_id) == goals_name
        ]
        recently_remembered = [
            RememberedItem(item=item, category=category_names[item.category_id])
            for item in newest_first[:RECENTLY_REMEMBERED_LIMIT]
        ]
        return goals, recently_remembered
