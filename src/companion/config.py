from collections.abc import Mapping

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class MissingSettingsError(Exception):
    """Raised when required keys are missing from `.env`."""

    def __init__(self, missing_keys: list[str]) -> None:
        """Build the error message naming every missing key.

        Args:
            missing_keys: The environment variable names that are missing.
        """
        self.missing_keys = missing_keys
        super().__init__(
            "Missing required setting(s) in .env: " + ", ".join(missing_keys)
        )


class Settings(BaseSettings):
    """Secrets, adapter choices and addresses read from the environment.

    Everything else about how the Companion behaves is admin-managed data in
    the database (ADR-0004). Keys used only by later issues are optional
    until those issues land.
    """

    model_config = SettingsConfigDict(extra="ignore", env_ignore_empty=True)

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    clerk_secret_key: str

    telegram_bot_token: str
    telegram_bot_username: str
    telegram_webhook_secret: str
    telegram_webhook_register: bool = True

    webhook_base_url: str
    dashboard_url: str

    deepseek_api_key: str
    tavily_api_key: str
    initial_admin_emails: str = ""

    chat_channel_adapter: str = "telegram"
    auth_verifier_adapter: str = "clerk"
    repositories_adapter: str = "postgres"
    clock_adapter: str = "system"
    chat_model_adapter: str = "deepseek"
    embedder_adapter: str = "fastembed"
    vector_store_adapter: str = "pgvector"
    text_extractor_adapter: str = "pypdf"
    web_search_adapter: str = "tavily"
    scheduler_adapter: str = "in_process"

    model_call_developer_logs: bool = False

    @property
    def initial_admin_email_set(self) -> frozenset[str]:
        """Split the comma-separated initial Admin emails.

        Returns:
            The emails in lower case, without blanks.
        """
        emails = (
            email.strip().lower() for email in self.initial_admin_emails.split(",")
        )
        return frozenset(email for email in emails if email)

    @property
    def database_url(self) -> str:
        """Build the SQLAlchemy URL for Postgres.

        Returns:
            The database URL.
        """
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def load_settings(environment: Mapping[str, str] | None = None) -> Settings:
    """Read settings, failing with the names of any missing required keys.

    Args:
        environment: Variables to read instead of the process environment;
            used by tests.

    Returns:
        The settings.

    Raises:
        MissingSettingsError: If any required key is missing.
    """
    try:
        if environment is None:
            return Settings()
        lowercase_environment = {
            key.lower(): value for key, value in environment.items()
        }
        return Settings.model_validate(lowercase_environment)
    except ValidationError as error:
        missing_keys = [
            str(problem["loc"][0]).upper()
            for problem in error.errors()
            if problem["type"] == "missing"
        ]
        if not missing_keys:
            raise
        raise MissingSettingsError(missing_keys) from error
