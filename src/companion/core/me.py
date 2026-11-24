from dataclasses import dataclass

from companion.core.features import FeatureService
from companion.core.models import Feature, User


@dataclass(frozen=True)
class Me:
    """The signed-in User as the Dashboard shows them.

    Attributes:
        user: The User.
        user_memory_available: Whether the Admin side allows User Memory for
            them.
        photo_viewing_available: Whether the Admin side allows Photo Viewing
            for them.
        personal_stickers_available: Whether Personal Stickers works for
            them; they have no switch of their own.
        show_pattern_noticing_notice: Whether to show the notice saying Zeph now
            keeps quotes as evidence: Pattern noticing works for them and
            they haven't pressed "Got it" yet.
    """

    user: User
    user_memory_available: bool
    photo_viewing_available: bool
    personal_stickers_available: bool
    show_pattern_noticing_notice: bool


class MeService:
    """Describes the signed-in User, with which of their Features work."""

    def __init__(self, features: FeatureService) -> None:
        """Set up the service.

        Args:
            features: Says which Features are available for the User.
        """
        self._features = features

    def describe(self, user: User) -> Me:
        """Describe a User, with which of their Features are available.

        Args:
            user: The User.

        Returns:
            The User with their Feature availability.
        """
        return Me(
            user=user,
            user_memory_available=self._features.available_for(
                user.id, Feature.USER_MEMORY
            ),
            photo_viewing_available=self._features.available_for(
                user.id, Feature.PHOTO_VIEWING
            ),
            personal_stickers_available=self._features.works_for(
                user.id, Feature.PERSONAL_STICKERS
            ),
            show_pattern_noticing_notice=user.pattern_noticing_told_at is None
            and self._features.works_for(user.id, Feature.PATTERN_NOTICING),
        )
