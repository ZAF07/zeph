from dataclasses import dataclass
from uuid import UUID

from companion.core.models import Feature, FeatureSwitch, User
from companion.core.ports import Clock, Repositories

UNAVAILABLE_NOTE_SETTING = "reply_features_unavailable_note"


@dataclass(frozen=True)
class FeatureDetails:
    """How Admins see a Feature.

    Attributes:
        feature: The Feature.
        name: Its name.
        description: A short line on what it does.
    """

    feature: Feature
    name: str
    description: str


FEATURES: tuple[FeatureDetails, ...] = (
    FeatureDetails(
        feature=Feature.WEB_SEARCH,
        name="Web Search",
        description=(
            "Zeph can look things up on the web and read pages when a "
            "conversation needs a fact."
        ),
    ),
)


def feature_details(feature: Feature) -> FeatureDetails:
    """Find how Admins see a Feature.

    Args:
        feature: The Feature.

    Returns:
        Its name and description.
    """
    return next(details for details in FEATURES if details.feature == feature)


class FeatureService:
    """Answers whether a Feature works for a User, and keeps its switches.

    Other core services ask this instead of reading switches themselves. A
    Feature with no saved switch is on for everyone.
    """

    def __init__(
        self, repositories: Repositories, clock: Clock, dashboard_url: str
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where switches and settings are stored.
            clock: Tells the current time, for each change.
            dashboard_url: The Dashboard's address, put into the note about
                Features that aren't available.
        """
        self._repositories = repositories
        self._clock = clock
        self._dashboard_url = dashboard_url

    def works_for(self, user_id: UUID, feature: Feature) -> bool:
        """Say whether a Feature works for a User right now.

        Args:
            user_id: The User.
            feature: The Feature.

        Returns:
            True if the Feature works for them.
        """
        return feature not in self.unavailable_for(user_id)

    def unavailable_for(self, user_id: UUID) -> list[Feature]:
        """List the Features that don't work for a User right now.

        Args:
            user_id: The User.

        Returns:
            The Features, in the order of `FEATURES`.
        """
        return [switch.feature for switch in self.list_for_everyone() if not switch.on]

    def unavailable_note(self, user_id: UUID) -> str:
        """Write the reply note naming the Features a User doesn't have.

        Args:
            user_id: The User being replied to.

        Returns:
            The Admin-managed note with the Features' names and the
            Dashboard's address filled in; "" when every Feature works.
        """
        unavailable = self.unavailable_for(user_id)
        if not unavailable:
            return ""
        names = ", ".join(feature_details(feature).name for feature in unavailable)
        note: str = self._repositories.platform_settings.get(UNAVAILABLE_NOTE_SETTING)
        return note.replace("{features}", names).replace(
            "{dashboard_url}", self._dashboard_url
        )

    def list_for_everyone(self) -> list[FeatureSwitch]:
        """List every Feature's switch for everyone with its last change.

        Returns:
            One switch per Feature, in the order of `FEATURES`.
        """
        saved = {
            switch.feature: switch
            for switch in self._repositories.feature_switches.list_for_everyone()
        }
        return [
            saved.get(
                details.feature,
                FeatureSwitch(
                    feature=details.feature,
                    on=True,
                    changed_by_email=None,
                    changed_at=None,
                ),
            )
            for details in FEATURES
        ]

    def set_for_everyone(
        self, feature: Feature, on: bool, admin: User
    ) -> FeatureSwitch:
        """Turn a Feature on or off for everyone.

        Args:
            feature: The Feature.
            on: Whether it should be on.
            admin: The Admin making the change.

        Returns:
            The Feature's switch after the change.
        """
        self._repositories.feature_switches.save_for_everyone(
            feature, on, self._clock.now(), admin.id
        )
        return next(
            switch for switch in self.list_for_everyone() if switch.feature == feature
        )
