from dataclasses import dataclass
from uuid import UUID

from companion.core.admin_users import UserNotFoundError
from companion.core.models import (
    Feature,
    FeatureReason,
    FeatureStatus,
    FeatureSwitch,
    User,
    UserFeatureSwitch,
)
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
    FeatureDetails(
        feature=Feature.STICKERS,
        name="Stickers",
        description=(
            "Zeph can add a sticker from the Sticker Library to a reply. "
            "Zeph still reads the stickers a User sends either way."
        ),
    ),
    FeatureDetails(
        feature=Feature.KNOWLEDGE,
        name="Knowledge",
        description=(
            "Zeph gets philosophy and mindfulness passages from the Knowledge "
            "library that may fit the message."
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
    Feature with no saved switch is on for everyone. A User's own switch, when
    "on" or "off", overrides the one for everyone.
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
        return [
            status.feature for status in self._statuses(user_id) if not status.works
        ]

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

    def statuses_for(self, user_id: UUID) -> list[FeatureStatus]:
        """Say for each Feature whether it works for a User, and why.

        Args:
            user_id: The User.

        Returns:
            One status per Feature, in the order of `FEATURES`.

        Raises:
            UserNotFoundError: If there is no such User.
        """
        self._require_user(user_id)
        return self._statuses(user_id)

    def set_for_user(
        self, user_id: UUID, feature: Feature, switch: UserFeatureSwitch, admin: User
    ) -> FeatureStatus:
        """Set a Feature to default, on or off for one User.

        "Default" removes the User's switch, so they follow everyone's.

        Args:
            user_id: The User.
            feature: The Feature.
            switch: The new switch for this User.
            admin: The Admin making the change.

        Returns:
            The Feature's status for the User after the change.

        Raises:
            UserNotFoundError: If there is no such User.
        """
        self._require_user(user_id)
        if switch == UserFeatureSwitch.DEFAULT:
            self._repositories.feature_switches.remove_for_user(user_id, feature)
        else:
            self._repositories.feature_switches.save_for_user(
                user_id,
                feature,
                switch == UserFeatureSwitch.ON,
                self._clock.now(),
                admin.id,
            )
        return next(
            status for status in self._statuses(user_id) if status.feature == feature
        )

    def _require_user(self, user_id: UUID) -> None:
        """Make sure a User exists.

        Args:
            user_id: The User.

        Raises:
            UserNotFoundError: If there is no such User.
        """
        if self._repositories.users.get(user_id) is None:
            raise UserNotFoundError(user_id)

    def _statuses(self, user_id: UUID) -> list[FeatureStatus]:
        """Work out each Feature's status for a User, without checking they exist.

        Args:
            user_id: The User.

        Returns:
            One status per Feature, in the order of `FEATURES`.
        """
        user_switches = {
            switch.feature: switch
            for switch in self._repositories.feature_switches.list_for_user(user_id)
        }
        return [
            status_for(everyone_switch, user_switches.get(everyone_switch.feature))
            for everyone_switch in self.list_for_everyone()
        ]


def status_for(
    everyone_switch: FeatureSwitch, user_switch: FeatureSwitch | None
) -> FeatureStatus:
    """Apply the rule: the User's switch if set, otherwise the one for everyone.

    Args:
        everyone_switch: The Feature's switch for everyone.
        user_switch: The Feature's switch for this User; None when "default".

    Returns:
        Whether the Feature works for the User, why, and their switch.
    """
    if user_switch is None:
        return FeatureStatus(
            feature=everyone_switch.feature,
            works=everyone_switch.on,
            reason=(
                FeatureReason.ON_FOR_EVERYONE
                if everyone_switch.on
                else FeatureReason.OFF_FOR_EVERYONE
            ),
            switch=UserFeatureSwitch.DEFAULT,
            changed_by_email=None,
            changed_at=None,
        )
    return FeatureStatus(
        feature=everyone_switch.feature,
        works=user_switch.on,
        reason=FeatureReason.ON_FOR_USER
        if user_switch.on
        else FeatureReason.OFF_FOR_USER,
        switch=UserFeatureSwitch.ON if user_switch.on else UserFeatureSwitch.OFF,
        changed_by_email=user_switch.changed_by_email,
        changed_at=user_switch.changed_at,
    )
