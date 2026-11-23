import logging
from collections.abc import Mapping

from pydantic_settings import BaseSettings, SettingsConfigDict

LOAD_TEST_ADAPTER = "load_test"
LOAD_TEST_LOGGER_NAME = "companion.adapters.load_test"


class LoadTestNotAllowedError(Exception):
    """Raised when `.env` picks a load-test adapter outside a load test."""

    def __init__(self, setting_key: str) -> None:
        """Build the error message naming the setting.

        Args:
            setting_key: The environment variable that picked the adapter.
        """
        super().__init__(
            f"{setting_key}={LOAD_TEST_ADAPTER} only works in a load test "
            "(make load-test), which sets LOAD_TEST_RUN=true"
        )


class LoadTestSwitch(BaseSettings):
    """Whether this backend runs for a load test.

    Only `docker-compose.load-test.yml` sets `LOAD_TEST_RUN`; the main
    Compose file never passes it, so `.env` alone can't turn the load-test
    adapters on.
    """

    model_config = SettingsConfigDict(extra="ignore", env_ignore_empty=True)

    load_test_run: bool = False


def allow_load_test_adapter(
    setting_key: str, environment: Mapping[str, str] | None = None
) -> None:
    """Check a load-test adapter may be used, and show the load-test logs.

    The load-test adapters log each send, search and tick at INFO, which
    `make load-test` reads, so their logger gets its own handler.

    Args:
        setting_key: The environment variable that picked the adapter.
        environment: Variables to read instead of the process environment;
            used by tests.

    Raises:
        LoadTestNotAllowedError: If this backend isn't running a load test.
    """
    switch = (
        LoadTestSwitch()
        if environment is None
        else LoadTestSwitch.model_validate(
            {key.lower(): value for key, value in environment.items()}
        )
    )
    if not switch.load_test_run:
        raise LoadTestNotAllowedError(setting_key)
    logger = logging.getLogger(LOAD_TEST_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
