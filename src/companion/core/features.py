from dataclasses import dataclass, replace
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
        on_by_default: Whether it is on for everyone before an Admin
            changes it.
        needs_stickers: Whether it works only while Stickers works too.
        in_reply_note: Whether replies are told when it isn't available,
            so they can say so if the User asks for it.
    """

    feature: Feature
    name: str
    description: str
    on_by_default: bool = True
    needs_stickers: bool = False
    in_reply_note: bool = True


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
    FeatureDetails(
        feature=Feature.CHECK_INS,
        name="Check-ins",
        description=(
            "Zeph can message a User first now and then. It works only while "
            "the User has Check-ins on too."
        ),
    ),
    FeatureDetails(
        feature=Feature.USER_MEMORY,
        name="User Memory",
        description=(
            "Zeph keeps and uses what matters about a User. It works only "
            "while the User has User Memory on too. Turning it off deletes "
            "nothing."
        ),
    ),
    FeatureDetails(
        feature=Feature.SETTINGS_IN_CHAT,
        name="Settings in Chat",
        description=(
            "A User can change their settings by asking Zeph in chat. Without "
            "it they change them on the Dashboard. Deleting their data in chat "
            "always works."
        ),
    ),
    FeatureDetails(
        feature=Feature.PHOTO_VIEWING,
        name="Photo Viewing",
        description=(
            "Zeph looks at the photos a User sends and can remember the ones "
            "that matter. It works only while the User has Photo Viewing on "
            "too. Every photo is still checked for safety either way."
        ),
    ),
    FeatureDetails(
        feature=Feature.PERSONAL_STICKERS,
        name="Personal Stickers",
        description=(
            "Zeph keeps stickers a User sends whose meaning is clear and can "
            "reply in them. It works only while Stickers works for the User. "
            "Turning it off deletes nothing."
        ),
        on_by_default=False,
        needs_stickers=True,
        in_reply_note=False,
    ),
)


class FeatureNotAvailableError(Exception):
    """Raised when a User changes their own switch while the Admin side has it off."""

    def __init__(self, feature: Feature) -> None:
        """Remember which Feature it was.

        Args:
            feature: The Feature that isn't available.
        """
        super().__init__(f"{feature_details(feature).name} isn't available")
        self.feature = feature


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
    Feature with no saved switch follows its default for everyone. A User's
    own switch, when "on" or "off", overrides the one for everyone.
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
        return self._status(user_id, feature).works

    def available_for(self, user_id: UUID, feature: Feature) -> bool:
        """Say whether the Admin side allows a Feature for a User.

        Args:
            user_id: The User.
            feature: The Feature.

        Returns:
            True if the Admin side allows it, whatever the User's own switch.
        """
        return self._status(user_id, feature).available

    def require_available(self, user_id: UUID, feature: Feature) -> None:
        """Make sure the Admin side allows a Feature for a User.

        Args:
            user_id: The User.
            feature: The Feature.

        Raises:
            FeatureNotAvailableError: If the Admin side has it off.
        """
        if not self.available_for(user_id, feature):
            raise FeatureNotAvailableError(feature)

    def unavailable_for(self, user_id: UUID) -> list[Feature]:
        """List the Features the Admin side has off for a User.

        Features the User turned off themselves aren't listed.

        Args:
            user_id: The User.

        Returns:
            The Features, in the order of `FEATURES`.
        """
        return [
            status.feature for status in self._statuses(user_id) if not status.available
        ]

    def unavailable_note(self, user_id: UUID) -> str:
        """Write the reply note naming the Features a User doesn't have.

        Features that aren't named in the reply note are left out.

        Args:
            user_id: The User being replied to.

        Returns:
            The Admin-managed note with the Features' names and the
            Dashboard's address filled in; "" when every Feature named in it
            works.
        """
        unavailable = [
            feature
            for feature in self.unavailable_for(user_id)
            if feature_details(feature).in_reply_note
        ]
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
                    on=details.on_by_default,
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

    def _status(self, user_id: UUID, feature: Feature) -> FeatureStatus:
        """Work out one Feature's status for a User.

        Args:
            user_id: The User.
            feature: The Feature.

        Returns:
            Its status.
        """
        return next(
            status for status in self._statuses(user_id) if status.feature == feature
        )

    def _statuses(self, user_id: UUID) -> list[FeatureStatus]:
        """Work out each Feature's status for a User, without checking they exist.

        A Feature that needs Stickers doesn't work while Stickers doesn't.

        Args:
            user_id: The User.

        Returns:
            One status per Feature, in the order of `FEATURES`.
        """
        user = self._repositories.users.get(user_id)
        user_switches = {
            switch.feature: switch
            for switch in self._repositories.feature_switches.list_for_user(user_id)
        }
        statuses = {
            everyone_switch.feature: status_for(
                everyone_switch,
                user_switches.get(everyone_switch.feature),
                own_switch_on(user, everyone_switch.feature),
            )
            for everyone_switch in self.list_for_everyone()
        }
        stickers_work = statuses[Feature.STICKERS].works
        return [
            stickers_off_applied(statuses[details.feature])
            if details.needs_stickers and not stickers_work
            else statuses[details.feature]
            for details in FEATURES
        ]


def own_switch_on(user: User | None, feature: Feature) -> bool | None:
    """Read the User's own switch for a Feature, where they have one.

    Args:
        user: The User; None if there is no such User.
        feature: The Feature.

    Returns:
        Whether the User has it on; None when the Feature has no switch of
        the User's own.
    """
    if user is None:
        return None
    if feature == Feature.USER_MEMORY:
        return user.user_memory_enabled
    if feature == Feature.CHECK_INS:
        return user.check_ins.enabled
    if feature == Feature.PHOTO_VIEWING:
        return user.photo_viewing_enabled
    return None


def status_for(
    everyone_switch: FeatureSwitch,
    user_switch: FeatureSwitch | None,
    own_switch: bool | None,
) -> FeatureStatus:
    """Apply the rule for whether a Feature works for a User, and why.

    The Admin side is the switch for this User if set, otherwise the one for
    everyone. The Feature works when the Admin side is on and the User's own
    switch, where they have one, is on too.

    Args:
        everyone_switch: The Feature's switch for everyone.
        user_switch: The Feature's switch for this User; None when "default".
        own_switch: The User's own switch; None when they have none.

    Returns:
        Whether the Feature works for the User, why, and their switch.
    """
    if user_switch is None:
        available = everyone_switch.on
        switch = UserFeatureSwitch.DEFAULT
        admin_reason = (
            FeatureReason.ON_FOR_EVERYONE
            if available
            else FeatureReason.OFF_FOR_EVERYONE
        )
    else:
        available = user_switch.on
        switch = UserFeatureSwitch.ON if available else UserFeatureSwitch.OFF
        admin_reason = (
            FeatureReason.ON_FOR_USER if available else FeatureReason.OFF_FOR_USER
        )
    turned_off_by_user = available and own_switch is False
    return FeatureStatus(
        feature=everyone_switch.feature,
        available=available,
        works=available and not turned_off_by_user,
        reason=FeatureReason.TURNED_OFF_BY_USER if turned_off_by_user else admin_reason,
        switch=switch,
        changed_by_email=user_switch.changed_by_email if user_switch else None,
        changed_at=user_switch.changed_at if user_switch else None,
    )


def stickers_off_applied(status: FeatureStatus) -> FeatureStatus:
    """Turn a Feature that needs Stickers off, because Stickers doesn't work.

    Args:
        status: The Feature's status from its own switches.

    Returns:
        The status marked as not working because Stickers is off; unchanged
        when it doesn't work anyway.
    """
    if not status.works:
        return status
    return replace(status, works=False, reason=FeatureReason.STICKERS_OFF)
