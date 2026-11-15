from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, insert, make_url, text

from companion.adapters.evals.in_process_companion import InProcessCompanion
from companion.adapters.postgres.database import (
    migrate,
    seed_check_in_kinds,
    seed_helplines,
    seed_memory_categories,
    seed_needs,
    seed_platform_settings,
)
from companion.adapters.postgres.tables import metadata, platform_settings
from companion.core.ports import ChatModel, Embedder, PhotoViewer


def create_database_if_missing(database_url: str) -> None:
    """Create a database on its Postgres server unless it is there already.

    Args:
        database_url: The database's URL.
    """
    url = make_url(database_url)
    server = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with server.connect() as connection:
            found = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).scalar()
            if not found:
                connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        server.dispose()


class PostgresEvalEnvironment:
    """The Eval database, apart from the app's, and the app built on it.

    Only made-up data is ever written here (ADR-0013).
    """

    def __init__(
        self,
        database_url: str,
        chat_model: ChatModel,
        photo_viewer: PhotoViewer,
        embedder: Embedder,
        seed_dir: Path,
    ) -> None:
        """Set up the environment.

        Args:
            database_url: The Eval database's URL; never the app's.
            chat_model: The real chat model.
            photo_viewer: The real photo viewer.
            embedder: The real embedder, loaded once.
            seed_dir: The app's seed folder, with the Eval test images in
                `evals/images`.
        """
        self._database_url = database_url
        self._engine: Engine = create_engine(database_url)
        self._chat_model = chat_model
        self._photo_viewer = photo_viewer
        self._embedder = embedder
        self._seed_dir = seed_dir

    def start_run(self) -> None:
        """Wipe the Eval database and bring its schema up to date."""
        with self._engine.begin() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
        migrate(self._database_url)

    def fresh_companion(self, platform_settings: dict[str, Any]) -> InProcessCompanion:
        """Empty the Eval database, seed it and build the app on it.

        Args:
            platform_settings: The Platform Settings to write into it, by
                key; settings missing here come from the seed.

        Returns:
            The app, ready for one case.
        """
        self._empty()
        self._store_platform_settings(platform_settings)
        seed_platform_settings(self._engine, self._seed_dir / "platform_settings.yaml")
        seed_helplines(self._engine, self._seed_dir / "helplines.yaml")
        seed_memory_categories(self._engine, self._seed_dir / "memory_categories.yaml")
        seed_check_in_kinds(self._engine, self._seed_dir / "check_in_kinds.yaml")
        seed_needs(self._engine, self._seed_dir / "needs.yaml")
        return InProcessCompanion(
            engine=self._engine,
            chat_model=self._chat_model,
            photo_viewer=self._photo_viewer,
            embedder=self._embedder,
            images_dir=self._seed_dir / "evals" / "images",
            knowledge_seed_file=self._seed_dir / "knowledge" / "knowledge.yaml",
        )

    def _empty(self) -> None:
        """Delete every row in the Eval database."""
        table_names = ", ".join(table.name for table in metadata.sorted_tables)
        with self._engine.begin() as connection:
            connection.execute(text(f"TRUNCATE {table_names} CASCADE"))

    def _store_platform_settings(self, values: dict[str, Any]) -> None:
        """Write Platform Settings into the empty Eval database.

        Seeding afterwards only adds keys still missing, so these values win.

        Args:
            values: Each setting's value by key.
        """
        if not values:
            return
        now = datetime.now(UTC)
        rows = [
            {"key": key, "value": value, "updated_at": now}
            for key, value in values.items()
        ]
        with self._engine.begin() as connection:
            connection.execute(insert(platform_settings).values(rows))
