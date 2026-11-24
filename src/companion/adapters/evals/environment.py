from collections.abc import Sequence
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
    seed_moves,
    seed_needs,
    seed_platform_settings,
)
from companion.adapters.postgres.tables import (
    metadata,
    need_ruled_out_moves,
    platform_settings,
)
from companion.adapters.postgres.tables import moves as moves_table
from companion.adapters.postgres.tables import needs as needs_table
from companion.core.evals.models import EvalImage
from companion.core.models import Move, Need
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
            seed_dir: The app's seed folder.
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

    def fresh_companion(
        self,
        platform_settings: dict[str, Any],
        needs: Sequence[Need],
        moves: Sequence[Move],
        images: Sequence[EvalImage],
    ) -> InProcessCompanion:
        """Empty the Eval database, seed it and build the app on it.

        Args:
            platform_settings: The Platform Settings to write into it, by
                key; settings missing here come from the seed.
            needs: The Needs to write into it, with their ruled-out Moves;
                the seed's when empty.
            moves: The Moves to write into it; the seed's when empty.
            images: The test images the case sends, by name.

        Returns:
            The app, ready for one case.
        """
        self._empty()
        self._store_platform_settings(platform_settings)
        self._store_needs(needs)
        self._store_moves(moves, needs)
        seed_platform_settings(self._engine, self._seed_dir / "platform_settings.yaml")
        seed_helplines(self._engine, self._seed_dir / "helplines.yaml")
        seed_memory_categories(self._engine, self._seed_dir / "memory_categories.yaml")
        seed_check_in_kinds(self._engine, self._seed_dir / "check_in_kinds.yaml")
        seed_needs(self._engine, self._seed_dir / "needs.yaml")
        seed_moves(
            self._engine,
            self._seed_dir / "moves.yaml",
            self._seed_dir / "needs.yaml",
        )
        return InProcessCompanion(
            engine=self._engine,
            chat_model=self._chat_model,
            photo_viewer=self._photo_viewer,
            embedder=self._embedder,
            images=images,
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

    def _store_needs(self, needs: Sequence[Need]) -> None:
        """Write Needs into the empty Eval database.

        Seeding afterwards adds Needs only when there are none, so these win.

        Args:
            needs: The Needs, with their IDs and order.
        """
        if not needs:
            return
        rows = [
            {
                "id": need.id,
                "name": need.name,
                "when_it_fits": need.when_it_fits,
                "how_to_reply": need.how_to_reply,
                "sort_order": need.sort_order,
                "is_fallback": need.is_fallback,
                "curiosities": need.curiosities,
            }
            for need in needs
        ]
        with self._engine.begin() as connection:
            connection.execute(insert(needs_table).values(rows))

    def _store_moves(self, moves: Sequence[Move], needs: Sequence[Need]) -> None:
        """Write Moves, and each Need's ruled-out Moves, into the Eval database.

        Seeding afterwards adds Moves only when there are none, so these win.

        Args:
            moves: The Moves, with their IDs and order.
            needs: The Needs already written, with their ruled-out Moves.
        """
        if not moves:
            return
        move_rows = [
            {
                "id": move.id,
                "name": move.name,
                "when_it_fits": move.when_it_fits,
                "how_to_do_it": move.how_to_do_it,
                "sort_order": move.sort_order,
                "needed_feature": (
                    None if move.needed_feature is None else move.needed_feature.value
                ),
                "asks_a_question": move.asks_a_question,
            }
            for move in moves
        ]
        rule_out_rows = [
            {"need_id": need.id, "move_id": move_id}
            for need in needs
            for move_id in need.ruled_out_move_ids
        ]
        with self._engine.begin() as connection:
            connection.execute(insert(moves_table).values(move_rows))
            if rule_out_rows:
                connection.execute(insert(need_ruled_out_moves).values(rule_out_rows))
