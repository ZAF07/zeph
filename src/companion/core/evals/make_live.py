from collections.abc import Collection
from uuid import UUID

from companion.core.errors import ConflictError, InvalidError, NotFoundError
from companion.core.evals.models import (
    EvalRun,
    EvalRunState,
    LiveChange,
    Variant,
)
from companion.core.evals.ports import EvalRunRepository
from companion.core.evals.runs import EvalRunNotFoundError
from companion.core.evals.setting_overrides import SettingOverrides, live_value
from companion.core.models import User
from companion.core.ports import Clock, NeedRepository, PlatformSettingsRepository


class VariantNotFoundError(NotFoundError):
    """Raised when a run has no Variant with that letter."""

    shown_message = "This run has no such Variant."


class RunNotFinishedError(ConflictError):
    """Raised when making live a Variant of a run that didn't finish."""

    shown_message = "Only a Finished run can be made live."


class AlreadyMadeLiveError(ConflictError):
    """Raised when making live a Variant that was made live already."""

    shown_message = "This Variant was made live already."


class NoOverridesError(InvalidError):
    """Raised when making live a Variant that has no Setting Overrides."""

    shown_message = "This Variant runs the live settings; there's nothing to make live."


def variant_of(run: EvalRun | None, letter: str) -> Variant:
    """Find a run's Variant by its letter.

    Args:
        run: The run; None if it is gone.
        letter: The Variant's letter.

    Returns:
        The Variant.

    Raises:
        VariantNotFoundError: If there is no such Variant.
    """
    variants = run.variants if run else []
    variant = next((variant for variant in variants if variant.letter == letter), None)
    if variant is None:
        raise VariantNotFoundError()
    return variant


class MakeLiveService:
    """Applies a Variant's Setting Overrides to the live settings: Make Live.

    The overrides go through the same saves as the settings pages, so
    Make Live can't save something those pages would refuse. A setting whose
    live value changed since the run started is applied only if the Admin
    confirms it.
    """

    def __init__(
        self,
        runs: EvalRunRepository,
        overrides: SettingOverrides,
        live_settings: PlatformSettingsRepository,
        live_needs: NeedRepository,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            runs: Where Eval Runs are stored.
            overrides: Saves Setting Overrides as live settings.
            live_settings: The live Platform Settings, to compare with.
            live_needs: The live Needs, to compare with.
            clock: Tells the time.
        """
        self._runs = runs
        self._overrides = overrides
        self._live_settings = live_settings
        self._live_needs = live_needs
        self._clock = clock

    def changes_since_run(self, run_id: UUID, letter: str) -> list[LiveChange]:
        """List the Variant's overridden settings changed live since the run.

        Args:
            run_id: The run.
            letter: The Variant's letter.

        Returns:
            Each such setting with its value then, now and the override; an
            empty list when Make Live needs no confirming.

        Raises:
            EvalRunNotFoundError: If there is no such run.
            VariantNotFoundError: If the run has no such Variant.
            RunNotFinishedError: If the run didn't finish.
            AlreadyMadeLiveError: If the Variant was made live already.
            NoOverridesError: If the Variant has no overrides.
        """
        run, variant = self._variant_to_make_live(run_id, letter)
        return self._changes(run, variant)

    def make_live(
        self, run_id: UUID, letter: str, admin: User, confirmed_keys: Collection[str]
    ) -> Variant:
        """Apply the Variant's Setting Overrides to the live settings.

        Overrides whose live value is as it was when the run started are
        applied straight away; changed ones only if confirmed, and are left
        out otherwise. The Variant records who, when, and what was applied
        or left out, and can't be made live again.

        Args:
            run_id: The run.
            letter: The Variant's letter.
            admin: The Admin making it live.
            confirmed_keys: The changed settings the Admin chose to apply.

        Returns:
            The Variant, made live.

        Raises:
            EvalRunNotFoundError: If there is no such run.
            VariantNotFoundError: If the run has no such Variant.
            RunNotFinishedError: If the run didn't finish.
            AlreadyMadeLiveError: If the Variant was made live already.
            NoOverridesError: If the Variant has no overrides.
            InvalidError: If the settings save refuses an override.
            NotFoundError: If an override's Need was deleted since.
        """
        run, variant = self._variant_to_make_live(run_id, letter)
        changed = {change.key for change in self._changes(run, variant)}
        left_out = [
            key
            for key in variant.setting_overrides
            if key in changed and key not in confirmed_keys
        ]
        applied = {
            key: value
            for key, value in variant.setting_overrides.items()
            if key not in left_out
        }
        self._overrides.save_live(admin, applied)
        self._runs.mark_made_live(
            run_id, letter, admin.id, self._clock.now(), list(applied), left_out
        )
        return variant_of(self._runs.get(run_id), letter)

    def _variant_to_make_live(
        self, run_id: UUID, letter: str
    ) -> tuple[EvalRun, Variant]:
        """Find a Variant and check that it can be made live.

        Args:
            run_id: The run.
            letter: The Variant's letter.

        Returns:
            The run and the Variant.

        Raises:
            EvalRunNotFoundError: If there is no such run.
            VariantNotFoundError: If the run has no such Variant.
            RunNotFinishedError: If the run didn't finish.
            AlreadyMadeLiveError: If the Variant was made live already.
            NoOverridesError: If the Variant has no overrides.
        """
        run = self._runs.get(run_id)
        if run is None:
            raise EvalRunNotFoundError()
        variant = variant_of(run, letter)
        if run.state != EvalRunState.FINISHED:
            raise RunNotFinishedError()
        if variant.made_live is not None:
            raise AlreadyMadeLiveError()
        if not variant.setting_overrides:
            raise NoOverridesError()
        return run, variant

    def _changes(self, run: EvalRun, variant: Variant) -> list[LiveChange]:
        """Compare each overridden setting's live value then and now.

        Args:
            run: The run, with its snapshot.
            variant: The Variant.

        Returns:
            The settings whose live value changed since the run started.
        """
        snapshot = run.snapshot
        then_settings = snapshot.settings if snapshot else {}
        then_needs = snapshot.needs if snapshot else []
        now_settings = self._live_settings.load().values
        now_needs = self._live_needs.list_all()
        changes = []
        for key, override in variant.setting_overrides.items():
            then = live_value(key, then_settings, then_needs)
            now = live_value(key, now_settings, now_needs)
            if then != now:
                changes.append(LiveChange(key, then, now, override))
        return changes
