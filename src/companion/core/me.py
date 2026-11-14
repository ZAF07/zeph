from dataclasses import dataclass

from companion.core.features import FeatureService
from companion.core.models import Feature, User
from companion.core.ports import Repositories
from companion.core.user_memory import UserMemoryService


@dataclass(frozen=True)
class Me:
    """The signed-in User as the Dashboard shows them.

    Attributes:
        user: The User.
        user_memory_available: Whether the Admin side allows User Memory for
            them.
        memory_note: The Admin-managed note saying User Memory is off and
            why; "" when it works.
        photo_viewing_available: Whether the Admin side allows Photo Viewing
            for them.
        personal_stickers_available: Whether Personal Stickers works for
            them; they have no switch of their own.
    """

    user: User
    user_memory_available: bool
    memory_note: str
    photo_viewing_available: bool
    personal_stickers_available: bool


class MeService:
    """Describes the signed-in User, with which of their Features work."""

    def __init__(
        self,
        repositories: Repositories,
        features: FeatureService,
        user_memory_service: UserMemoryService,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where platform settings are stored.
            features: Says which Features are available for the User.
            user_memory_service: Picks the note saying User Memory is off.
        """
        self._repositories = repositories
        self._features = features
        self._user_memory_service = user_memory_service

    def describe(self, user: User) -> Me:
        """Describe a User, with which of their Features are available.

        Args:
            user: The User.

        Returns:
            The User with their Feature availability and memory note.
        """
        settings = self._repositories.platform_settings.load()
        return Me(
            user=user,
            user_memory_available=self._features.available_for(
                user.id, Feature.USER_MEMORY
            ),
            memory_note=self._user_memory_service.memory_note(user, settings),
            photo_viewing_available=self._features.available_for(
                user.id, Feature.PHOTO_VIEWING
            ),
            personal_stickers_available=self._features.works_for(
                user.id, Feature.PERSONAL_STICKERS
            ),
        )
