from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID

from companion.core.errors import InvalidError
from companion.core.models import Need, NeedDetails, User
from companion.core.needs import NeedService
from companion.core.platform_settings import (
    EDITABLE_SETTINGS,
    EditableSetting,
    PlatformSettingsService,
)

NEED_OVERRIDE_PREFIX = "need:"
NEED_FIELDS = ("name", "when_it_fits", "how_to_reply")


class InvalidOverrideError(InvalidError):
    """Raised when a Setting Override names no setting or Need, or is malformed."""


class OverriddenNeedGoneError(Exception):
    """Raised when a Variant changes a Need deleted before its run started.

    The case then ends as an Error with this message, so the Variant never
    quietly runs without its change.
    """


@dataclass(frozen=True)
class OverridableSetting:
    """A Platform Setting a Variant can override, with its live value.

    Attributes:
        setting: The setting and the rule its value must meet.
        value: Its live value.
    """

    setting: EditableSetting
    value: Any


@dataclass(frozen=True)
class OverrideChoices:
    """What a Variant can override, as the settings pages can change it.

    Attributes:
        settings: The Platform Settings Admins can edit, with live values.
        needs: The live Needs.
        models: The models a model setting can pick.
    """

    settings: list[OverridableSetting]
    needs: list[Need]
    models: list[str]


def need_override_key(need_id: UUID) -> str:
    """Name the override of a Need.

    Args:
        need_id: The Need's ID.

    Returns:
        The override's key, `need:<id>`.
    """
    return f"{NEED_OVERRIDE_PREFIX}{need_id}"


def need_values(need: Need | NeedDetails) -> dict[str, str]:
    """Write a Need's details as an override's value.

    Args:
        need: The Need, or its details.

    Returns:
        Its name, when it fits and how to reply.
    """
    return {
        "name": need.name,
        "when_it_fits": need.when_it_fits,
        "how_to_reply": need.how_to_reply,
    }


def overridden_need_id(key: str) -> UUID | None:
    """Read the Need an override changes, if it changes one.

    Args:
        key: The override's key.

    Returns:
        The Need's ID; None for a Platform Setting.

    Raises:
        InvalidOverrideError: If the key starts like a Need's but has no ID.
    """
    if not key.startswith(NEED_OVERRIDE_PREFIX):
        return None
    try:
        return UUID(key.removeprefix(NEED_OVERRIDE_PREFIX))
    except ValueError as error:
        raise InvalidOverrideError(f"'{key}' doesn't name a Need.") from error


def variant_settings(
    live_settings: Mapping[str, Any], overrides: Mapping[str, Any]
) -> dict[str, Any]:
    """Work out the Platform Settings a Variant runs with.

    Args:
        live_settings: The live Platform Settings, by key.
        overrides: The Variant's Setting Overrides.

    Returns:
        The live settings with the Variant's setting overrides on top;
        Need overrides are left out.
    """
    changed = {
        key: value
        for key, value in overrides.items()
        if not key.startswith(NEED_OVERRIDE_PREFIX)
    }
    return {**live_settings, **changed}


def variant_needs(
    live_needs: Sequence[Need], overrides: Mapping[str, Any]
) -> list[Need]:
    """Work out the Needs a Variant runs with.

    Args:
        live_needs: The live Needs, in order.
        overrides: The Variant's Setting Overrides.

    Returns:
        The live Needs, each with the Variant's changes to it.

    Raises:
        OverriddenNeedGoneError: If the Variant changes a Need that isn't
            among them.
    """
    live_keys = {need_override_key(need.id) for need in live_needs}
    gone = [
        key
        for key in overrides
        if key.startswith(NEED_OVERRIDE_PREFIX) and key not in live_keys
    ]
    if gone:
        raise OverriddenNeedGoneError(
            "This Variant changes a Need deleted before the run started."
        )
    return [
        replace(need, **overrides[need_override_key(need.id)])
        if need_override_key(need.id) in overrides
        else need
        for need in live_needs
    ]


def live_value(key: str, settings: Mapping[str, Any], needs: Sequence[Need]) -> Any:
    """Read the live value an override replaces.

    Args:
        key: The override's key.
        settings: The live Platform Settings, by key.
        needs: The live Needs.

    Returns:
        The setting's value, or the Need's details; None if there is none.
    """
    need_id = overridden_need_id(key)
    if need_id is None:
        return settings.get(key)
    need = next((need for need in needs if need.id == need_id), None)
    return need_values(need) if need is not None else None


def need_details(
    key: str, value: Any, ruled_out_move_ids: frozenset[UUID]
) -> NeedDetails:
    """Read a Need override's value.

    Args:
        key: The override's key, for the message.
        value: Its value: a name, when it fits and how to reply.
        ruled_out_move_ids: The live Need's ruled-out Moves, which an
            override keeps.

    Returns:
        The details.

    Raises:
        InvalidOverrideError: If a field is missing or not text.
    """
    if not isinstance(value, dict) or not all(
        isinstance(value.get(name), str) for name in NEED_FIELDS
    ):
        raise InvalidOverrideError(
            f"The change to '{key}' needs a name, when it fits and how to reply."
        )
    return NeedDetails(
        name=value["name"],
        when_it_fits=value["when_it_fits"],
        how_to_reply=value["how_to_reply"],
        ruled_out_move_ids=ruled_out_move_ids,
    )


class SettingOverrideService:
    """Checks Setting Overrides, and saves them live, as the settings pages do.

    Platform Settings go through the Platform Settings save and Needs
    through the Need save, so an override is held to the same checks as an
    Admin's change on those pages.
    """

    def __init__(
        self, settings_service: PlatformSettingsService, need_service: NeedService
    ) -> None:
        """Set up the service.

        Args:
            settings_service: The Platform Settings save.
            need_service: The Need save.
        """
        self._settings_service = settings_service
        self._need_service = need_service

    def checked(self, overrides: Mapping[str, Any]) -> dict[str, Any]:
        """Check a Variant's Setting Overrides against the live settings' rules.

        Args:
            overrides: The overrides, by setting key or `need:<id>`.

        Returns:
            The same overrides, tidied as a save would tidy them.

        Raises:
            InvalidOverrideError: If a Need override is malformed.
            InvalidSettingError: If a setting can't be changed or its value
                is not valid.
            NeedNotFoundError: If a Need override names no live Need.
            InvalidNeedError: If a Need's new details are not valid.
        """
        checked: dict[str, Any] = {}
        for key, value in overrides.items():
            need_id = overridden_need_id(key)
            if need_id is None:
                checked[key] = self._settings_service.checked_value(key, value)
            else:
                checked[key] = need_values(
                    self._need_service.checked(
                        need_id, self._need_details(need_id, key, value)
                    )
                )
        return checked

    def _need_details(self, need_id: UUID, key: str, value: Any) -> NeedDetails:
        """Read a Need override's value, keeping the live Need's ruled-out Moves.

        Args:
            need_id: The overridden Need's ID.
            key: The override's key, for the message.
            value: Its value: a name, when it fits and how to reply.

        Returns:
            The details.

        Raises:
            InvalidOverrideError: If a field is missing or not text.
            NeedNotFoundError: If there is no such live Need.
        """
        details = need_details(key, value, frozenset())
        live = self._need_service.get(need_id)
        return replace(details, ruled_out_move_ids=live.ruled_out_move_ids)

    def choices(self) -> OverrideChoices:
        """List what a Variant can override, with each one's live value.

        Returns:
            The editable Platform Settings, the live Needs and the models.
        """
        live = {
            stored.key: stored.value
            for stored in self._settings_service.list_editable()
        }
        return OverrideChoices(
            settings=[
                OverridableSetting(setting, live.get(setting.key))
                for setting in EDITABLE_SETTINGS
            ],
            needs=self._need_service.list_all(),
            models=self._settings_service.model_choices(),
        )

    def save_live(self, admin: User, overrides: Mapping[str, Any]) -> None:
        """Save Setting Overrides as the live Platform Settings and Needs.

        Every override is checked first, so nothing is saved if any is
        refused.

        Args:
            admin: The Admin saving them.
            overrides: The overrides to save.

        Raises:
            InvalidOverrideError: As for `checked`.
            InvalidSettingError: As for `checked`.
            NeedNotFoundError: As for `checked`.
            InvalidNeedError: As for `checked`.
        """
        checked = self.checked(overrides)
        for key, value in checked.items():
            need_id = overridden_need_id(key)
            if need_id is not None:
                self._need_service.update(
                    need_id, self._need_details(need_id, key, value)
                )
        settings = {
            key: value
            for key, value in checked.items()
            if overridden_need_id(key) is None
        }
        if settings:
            self._settings_service.update(admin, settings)
