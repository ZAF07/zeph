from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID

from companion.core.errors import InvalidError
from companion.core.models import (
    CuriosityTreatment,
    Move,
    MoveDetails,
    Need,
    NeedDetails,
    User,
)
from companion.core.moves import MoveService
from companion.core.needs import NeedService
from companion.core.platform_settings import (
    EDITABLE_SETTINGS,
    EditableSetting,
    PlatformSettingsService,
)

NEED_OVERRIDE_PREFIX = "need:"
NEED_FIELDS = ("name", "when_it_fits", "how_to_reply")
MOVE_OVERRIDE_PREFIX = "move:"
MOVE_FIELDS = ("name", "when_it_fits", "how_to_do_it")


class InvalidOverrideError(InvalidError):
    """Raised when an override names no setting, Need or Move, or is malformed."""


class OverriddenNeedGoneError(Exception):
    """Raised when a Variant changes a Need deleted before its run started.

    The case then ends as an Error with this message, so the Variant never
    quietly runs without its change.
    """


class OverriddenMoveGoneError(Exception):
    """Raised when a Variant changes a Move deleted before its run started.

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
        moves: The live Moves.
        models: The models a model setting can pick.
    """

    settings: list[OverridableSetting]
    needs: list[Need]
    moves: list[Move]
    models: list[str]


def need_override_key(need_id: UUID) -> str:
    """Name the override of a Need.

    Args:
        need_id: The Need's ID.

    Returns:
        The override's key, `need:<id>`.
    """
    return f"{NEED_OVERRIDE_PREFIX}{need_id}"


def move_override_key(move_id: UUID) -> str:
    """Name the override of a Move.

    Args:
        move_id: The Move's ID.

    Returns:
        The override's key, `move:<id>`.
    """
    return f"{MOVE_OVERRIDE_PREFIX}{move_id}"


def need_values(need: Need | NeedDetails) -> dict[str, str]:
    """Write a Need's details as an override's value.

    Args:
        need: The Need, or its details.

    Returns:
        Its name, when it fits, how to reply and how Curiosities are
        treated.
    """
    return {
        "name": need.name,
        "when_it_fits": need.when_it_fits,
        "how_to_reply": need.how_to_reply,
        "curiosities": need.curiosities.value,
    }


def overridden_need(need: Need, value: Mapping[str, Any]) -> Need:
    """Apply a Variant's change to a Need.

    Args:
        need: The live Need.
        value: The override's value, as `need_values` wrote it; one saved
            before Needs said how Curiosities are treated has no such field.

    Returns:
        The Need with the override's texts and, if it names one, its way of
        treating Curiosities.
    """
    return replace(
        need,
        name=value["name"],
        when_it_fits=value["when_it_fits"],
        how_to_reply=value["how_to_reply"],
        curiosities=CuriosityTreatment(value.get("curiosities", need.curiosities)),
    )


def move_values(move: Move | MoveDetails) -> dict[str, str]:
    """Write a Move's text as an override's value.

    Args:
        move: The Move, or its details.

    Returns:
        Its name, when it fits and how to do it.
    """
    return {
        "name": move.name,
        "when_it_fits": move.when_it_fits,
        "how_to_do_it": move.how_to_do_it,
    }


def is_setting_key(key: str) -> bool:
    """Say whether an override changes a Platform Setting, not a Need or Move.

    Args:
        key: The override's key.

    Returns:
        True for a Platform Setting.
    """
    return not key.startswith((NEED_OVERRIDE_PREFIX, MOVE_OVERRIDE_PREFIX))


def overridden_id(key: str, prefix: str, kind: str) -> UUID | None:
    """Read the Need or Move an override changes, if it changes one of that kind.

    Args:
        key: The override's key.
        prefix: The start of that kind's keys, e.g. `need:`.
        kind: That kind's name for the message, e.g. "Need".

    Returns:
        The ID; None if the key isn't of that kind.

    Raises:
        InvalidOverrideError: If the key starts like that kind's but has no ID.
    """
    if not key.startswith(prefix):
        return None
    try:
        return UUID(key.removeprefix(prefix))
    except ValueError as error:
        raise InvalidOverrideError(f"'{key}' doesn't name a {kind}.") from error


def overridden_need_id(key: str) -> UUID | None:
    """Read the Need an override changes, if it changes one.

    Args:
        key: The override's key.

    Returns:
        The Need's ID; None for anything else.

    Raises:
        InvalidOverrideError: If the key starts like a Need's but has no ID.
    """
    return overridden_id(key, NEED_OVERRIDE_PREFIX, "Need")


def overridden_move_id(key: str) -> UUID | None:
    """Read the Move an override changes, if it changes one.

    Args:
        key: The override's key.

    Returns:
        The Move's ID; None for anything else.

    Raises:
        InvalidOverrideError: If the key starts like a Move's but has no ID.
    """
    return overridden_id(key, MOVE_OVERRIDE_PREFIX, "Move")


def variant_settings(
    live_settings: Mapping[str, Any], overrides: Mapping[str, Any]
) -> dict[str, Any]:
    """Work out the Platform Settings a Variant runs with.

    Args:
        live_settings: The live Platform Settings, by key.
        overrides: The Variant's Setting Overrides.

    Returns:
        The live settings with the Variant's setting overrides on top;
        Need and Move overrides are left out.
    """
    changed = {key: value for key, value in overrides.items() if is_setting_key(key)}
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
        overridden_need(need, overrides[need_override_key(need.id)])
        if need_override_key(need.id) in overrides
        else need
        for need in live_needs
    ]


def variant_moves(
    live_moves: Sequence[Move], overrides: Mapping[str, Any]
) -> list[Move]:
    """Work out the Moves a Variant runs with.

    Args:
        live_moves: The live Moves, in order.
        overrides: The Variant's Setting Overrides.

    Returns:
        The live Moves, each with the Variant's changes to its text.

    Raises:
        OverriddenMoveGoneError: If the Variant changes a Move that isn't
            among them.
    """
    live_keys = {move_override_key(move.id) for move in live_moves}
    gone = [
        key
        for key in overrides
        if key.startswith(MOVE_OVERRIDE_PREFIX) and key not in live_keys
    ]
    if gone:
        raise OverriddenMoveGoneError(
            "This Variant changes a Move deleted before the run started."
        )
    return [
        replace(move, **overrides[move_override_key(move.id)])
        if move_override_key(move.id) in overrides
        else move
        for move in live_moves
    ]


def live_value(
    key: str,
    settings: Mapping[str, Any],
    needs: Sequence[Need],
    moves: Sequence[Move],
) -> Any:
    """Read the live value an override replaces.

    Args:
        key: The override's key.
        settings: The live Platform Settings, by key.
        needs: The live Needs.
        moves: The live Moves.

    Returns:
        The setting's value, or the Need's or Move's text; None if there is
        none.
    """
    need_id = overridden_need_id(key)
    if need_id is not None:
        need = next((need for need in needs if need.id == need_id), None)
        return need_values(need) if need is not None else None
    move_id = overridden_move_id(key)
    if move_id is not None:
        move = next((move for move in moves if move.id == move_id), None)
        return move_values(move) if move is not None else None
    return settings.get(key)


def has_text_fields(value: Any, names: Sequence[str]) -> bool:
    """Say whether an override's value holds each field as text.

    Args:
        value: The value.
        names: The fields it must hold.

    Returns:
        True if it is a mapping with each field as text.
    """
    return isinstance(value, dict) and all(
        isinstance(value.get(name), str) for name in names
    )


def check_need_override(key: str, value: Any) -> None:
    """Check a Need override's value has the right shape.

    Args:
        key: The override's key, for the message.
        value: Its value: a name, when it fits, how to reply and,
            optionally, how Curiosities are treated.

    Raises:
        InvalidOverrideError: If a text field is missing or not text, or
            the way of treating Curiosities isn't one of the choices.
    """
    if not has_text_fields(value, NEED_FIELDS):
        raise InvalidOverrideError(
            f"The change to '{key}' needs a name, when it fits and how to reply."
        )
    treatment = value.get("curiosities")
    choices = [choice.value for choice in CuriosityTreatment]
    if treatment is not None and treatment not in choices:
        raise InvalidOverrideError(
            f"The change to '{key}' has an unknown choice for Curiosities."
        )


def need_details(value: Mapping[str, Any], live: Need) -> NeedDetails:
    """Read a checked Need override's value.

    Args:
        value: Its value, as `check_need_override` passed it.
        live: The live Need, whose ruled-out Moves an override keeps, and
            whose way of treating Curiosities it keeps when it names none.

    Returns:
        The details.
    """
    changed = overridden_need(live, value)
    return NeedDetails(
        name=changed.name,
        when_it_fits=changed.when_it_fits,
        how_to_reply=changed.how_to_reply,
        ruled_out_move_ids=changed.ruled_out_move_ids,
        curiosities=changed.curiosities,
    )


class SettingOverrideService:
    """Checks Setting Overrides, and saves them live, as the settings pages do.

    Platform Settings go through the Platform Settings save, Needs through
    the Need save and Moves through the Move save, so an override is held to
    the same checks as an Admin's change on those pages.
    """

    def __init__(
        self,
        settings_service: PlatformSettingsService,
        need_service: NeedService,
        move_service: MoveService,
    ) -> None:
        """Set up the service.

        Args:
            settings_service: The Platform Settings save.
            need_service: The Need save.
            move_service: The Move save.
        """
        self._settings_service = settings_service
        self._need_service = need_service
        self._move_service = move_service

    def checked(self, overrides: Mapping[str, Any]) -> dict[str, Any]:
        """Check a Variant's Setting Overrides against the live settings' rules.

        Args:
            overrides: The overrides, by setting key, `need:<id>` or
                `move:<id>`.

        Returns:
            The same overrides, tidied as a save would tidy them.

        Raises:
            InvalidOverrideError: If a Need or Move override is malformed.
            InvalidSettingError: If a setting can't be changed or its value
                is not valid.
            NeedNotFoundError: If a Need override names no live Need.
            InvalidNeedError: If a Need's new details are not valid.
            MoveNotFoundError: If a Move override names no live Move.
            InvalidMoveError: If a Move's new text is not valid.
            MoveNameTakenError: If a Move's new name is another Move's.
        """
        checked: dict[str, Any] = {}
        for key, value in overrides.items():
            need_id = overridden_need_id(key)
            move_id = overridden_move_id(key)
            if need_id is not None:
                checked[key] = need_values(
                    self._need_service.checked(
                        need_id, self._need_details(need_id, key, value)
                    )
                )
            elif move_id is not None:
                checked[key] = move_values(
                    self._move_service.checked(
                        move_id, self._move_details(move_id, key, value)
                    )
                )
            else:
                checked[key] = self._settings_service.checked_value(key, value)
        return checked

    def _need_details(self, need_id: UUID, key: str, value: Any) -> NeedDetails:
        """Read a Need override's value, keeping the live Need's ruled-out Moves.

        The value is read before the live Need is looked up, so a malformed
        value is refused as invalid even for a Need that doesn't exist.

        Args:
            need_id: The overridden Need's ID.
            key: The override's key, for the message.
            value: Its value: a name, when it fits, how to reply and,
                optionally, how Curiosities are treated.

        Returns:
            The details.

        Raises:
            InvalidOverrideError: If a field is missing or malformed.
            NeedNotFoundError: If there is no such live Need.
        """
        check_need_override(key, value)
        return need_details(value, self._need_service.get(need_id))

    def _move_details(self, move_id: UUID, key: str, value: Any) -> MoveDetails:
        """Read a Move override's value, keeping the live Move's other settings.

        Its needed Feature and whether it asks a question can't be overridden.

        The value is read before the live Move is looked up, so a malformed
        value is refused as invalid even for a Move that doesn't exist.

        Args:
            move_id: The overridden Move's ID.
            key: The override's key, for the message.
            value: Its value: a name, when it fits and how to do it.

        Returns:
            The details.

        Raises:
            InvalidOverrideError: If a field is missing or not text.
            MoveNotFoundError: If there is no such live Move.
        """
        if not has_text_fields(value, MOVE_FIELDS):
            raise InvalidOverrideError(
                f"The change to '{key}' needs a name, when it fits and how to do it."
            )
        live = self._move_service.get(move_id)
        return MoveDetails(
            name=value["name"],
            when_it_fits=value["when_it_fits"],
            how_to_do_it=value["how_to_do_it"],
            needed_feature=live.needed_feature,
            asks_a_question=live.asks_a_question,
        )

    def choices(self) -> OverrideChoices:
        """List what a Variant can override, with each one's live value.

        Returns:
            The editable Platform Settings, the live Needs and Moves, and the
            models.
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
            moves=self._move_service.list_all(),
            models=self._settings_service.model_choices(),
        )

    def save_live(self, admin: User, overrides: Mapping[str, Any]) -> None:
        """Save Setting Overrides as the live Platform Settings, Needs and Moves.

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
            MoveNotFoundError: As for `checked`.
            InvalidMoveError: As for `checked`.
            MoveNameTakenError: As for `checked`.
        """
        checked = self.checked(overrides)
        for key, value in checked.items():
            need_id = overridden_need_id(key)
            move_id = overridden_move_id(key)
            if need_id is not None:
                self._need_service.update(
                    need_id, self._need_details(need_id, key, value)
                )
            elif move_id is not None:
                self._move_service.update(
                    move_id, self._move_details(move_id, key, value)
                )
        settings = {key: value for key, value in checked.items() if is_setting_key(key)}
        if settings:
            self._settings_service.update(admin, settings)
