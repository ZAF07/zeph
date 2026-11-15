from collections.abc import Mapping
from typing import Any

from companion.core.evals.case_shapes import FormShape, InvalidFormError, find_problems
from companion.core.evals.judge import judge_shape
from companion.core.evals.ports import JudgeSettingsRepository
from companion.core.models import User
from companion.core.platform_settings import AVAILABLE_MODELS
from companion.core.ports import Clock, PlatformSettingsRepository


class InvalidJudgeSettingsError(InvalidFormError):
    """Raised when the Judge's settings don't fit their form."""


class JudgeSettingsService:
    """Lets Admins set the Judge's model, thinking and prompts (ADR-0004).

    The settings are kept apart from the Platform Settings, so a Variant's
    Setting Overrides never change the Judge. A change applies from the
    next run; each run keeps the Judge settings it used.
    """

    def __init__(
        self,
        judge_settings: JudgeSettingsRepository,
        platform_settings: PlatformSettingsRepository,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            judge_settings: Where the Judge's settings are stored.
            platform_settings: The Platform Settings, for the models Admins
                can pick.
            clock: Tells the time.
        """
        self._judge_settings = judge_settings
        self._platform_settings = platform_settings
        self._clock = clock

    def shape(self) -> FormShape:
        """Describe the Judge's settings as a form.

        Returns:
            The shape, with the models Admins can pick.
        """
        return judge_shape(self._platform_settings.load().get(AVAILABLE_MODELS))

    def values(self) -> dict[str, Any]:
        """Read the Judge's settings.

        Returns:
            Each setting's value by name.
        """
        return self._judge_settings.load()

    def save(self, admin: User, values: Mapping[str, Any]) -> dict[str, Any]:
        """Check and save the Judge's settings, all together or not at all.

        Args:
            admin: The Admin changing them.
            values: Every setting's new value by name.

        Returns:
            The settings after the change.

        Raises:
            InvalidJudgeSettingsError: If a value doesn't fit, with a message per
                field; nothing is saved.
        """
        shape = self.shape()
        problems = find_problems(shape, values)
        if problems:
            raise InvalidJudgeSettingsError(
                "The Judge's settings have problems; see each field.", problems
            )
        self._judge_settings.save(
            {
                field.name: values.get(field.name, field.default)
                for field in shape.fields
            },
            self._clock.now(),
            admin.id,
        )
        return self.values()
