from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, exists, select
from sqlalchemy.dialects.postgresql import insert

from companion.adapters.pattern_catalog_seed import read_pattern_catalog_seed
from companion.adapters.postgres.repositories import (
    PostgresCopyRepository,
    PostgresPatternCatalogRepository,
)
from companion.adapters.postgres.tables import (
    check_in_kinds,
    helplines,
    memory_categories,
    moves,
    need_ruled_out_moves,
    needs,
    platform_settings,
    thought_experiments,
)
from companion.core.models import (
    CopySeedSlot,
    CuriositySensitivity,
    CuriosityTreatment,
)
from companion.core.pattern_catalog import PatternCatalogService

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def migrate(database_url: str) -> None:
    """Bring the database schema up to date.

    Args:
        database_url: SQLAlchemy URL of the database.
    """
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")


def seed_platform_settings(engine: Engine, seed_file: Path) -> None:
    """Load seed platform settings, keeping any value already in the database.

    Only keys that are missing get added, so Admin edits are never overwritten
    and settings added by later releases still appear on existing installs.

    Args:
        engine: The database engine.
        seed_file: YAML file mapping setting keys to their starting values.
    """
    seed_values = yaml.safe_load(seed_file.read_text())
    now = datetime.now(UTC)
    rows = [
        {"key": key, "value": value, "updated_at": now}
        for key, value in seed_values.items()
    ]
    with engine.begin() as connection:
        connection.execute(
            insert(platform_settings).values(rows).on_conflict_do_nothing()
        )


def read_copy_seed(seed_file: Path) -> list[CopySeedSlot]:
    """Read the Copy seed file.

    Args:
        seed_file: YAML file listing tabs in order, each with a `tab` key, a
            `name` and its `slots` in page order. A slot has a `key`, `name`,
            `max_length`, `text` and optional `placeholders`.

    Returns:
        Every slot the file defines.
    """
    tabs = yaml.safe_load(seed_file.read_text())
    return [
        CopySeedSlot(
            key=slot["key"],
            tab=tab["tab"],
            tab_name=tab["name"],
            tab_order=tab_order,
            slot_order=slot_order,
            name=slot["name"],
            text=slot["text"],
            max_length=slot["max_length"],
            placeholders=tuple(slot.get("placeholders", [])),
        )
        for tab_order, tab in enumerate(tabs)
        for slot_order, slot in enumerate(tab["slots"])
    ]


def seed_copy(engine: Engine, seed_file: Path) -> None:
    """Make the stored Copy follow the seed file, keeping Admin-edited text.

    New slots are added with the seed text, and slots taken out of the seed
    are removed. A stored slot keeps its text, but its name, tab, order, max
    length and placeholders always come from the seed.

    Args:
        engine: The database engine.
        seed_file: The Copy seed file.
    """
    PostgresCopyRepository(engine).sync_with_seed(
        read_copy_seed(seed_file), datetime.now(UTC)
    )


def load_pattern_catalog(engine: Engine, seed_dir: Path) -> None:
    """Make the stored Pattern Catalog follow its files (ADR-0025).

    Args:
        engine: The database engine.
        seed_dir: The folder holding one YAML file per Pattern Type.

    Raises:
        InvalidPatternCatalogError: If a file is not valid, or a Pattern Type
            changed while keeping a version already stored; nothing is loaded.
    """
    PatternCatalogService(PostgresPatternCatalogRepository(engine)).load(
        read_pattern_catalog_seed(seed_dir), datetime.now(UTC)
    )


def seed_helplines(engine: Engine, seed_file: Path) -> None:
    """Load the seed Helplines and international fallback on first run.

    Nothing is loaded once any Helpline exists, so a Helpline an Admin removed
    never comes back.

    Args:
        engine: The database engine.
        seed_file: YAML file with `countries` (country code to a list of
            Helplines) and one `international_fallback`.
    """
    seed = yaml.safe_load(seed_file.read_text())
    fallback = seed["international_fallback"]
    rows = [
        {
            "id": uuid4(),
            "country": None,
            "name": fallback["name"],
            "number": str(fallback["number"]),
            "hours": fallback.get("hours"),
            "sort_order": 0,
        }
    ]
    for country, country_helplines in seed["countries"].items():
        rows.extend(
            {
                "id": uuid4(),
                "country": country,
                "name": helpline["name"],
                "number": str(helpline["number"]),
                "hours": helpline.get("hours"),
                "sort_order": sort_order,
            }
            for sort_order, helpline in enumerate(country_helplines)
        )
    with engine.begin() as connection:
        if connection.execute(select(exists().select_from(helplines))).scalar():
            return
        connection.execute(insert(helplines).values(rows))


def seed_memory_categories(engine: Engine, seed_file: Path) -> None:
    """Load the starting Memory Categories on first run.

    Nothing is loaded once any Memory Category exists, so Admin changes are
    never overwritten.

    Args:
        engine: The database engine.
        seed_file: YAML file listing categories with `name`, `description`
            and `always_include`, in the order to show them.
    """
    seed = yaml.safe_load(seed_file.read_text())
    rows = [
        {
            "id": uuid4(),
            "name": category["name"],
            "description": category["description"],
            "always_include": category["always_include"],
            "archived": False,
            "sort_order": sort_order,
        }
        for sort_order, category in enumerate(seed)
    ]
    with engine.begin() as connection:
        if connection.execute(select(exists().select_from(memory_categories))).scalar():
            return
        connection.execute(insert(memory_categories).values(rows))


def seed_check_in_kinds(engine: Engine, seed_file: Path) -> None:
    """Load the starting Check-in Kinds on first run.

    Nothing is loaded once any Check-in Kind exists, so Admin changes are
    never overwritten.

    Args:
        engine: The database engine.
        seed_file: YAML file listing Kinds with `name`, `description` and
            optional `sends_shared_photo`, `raises_curiosity` and
            `shares_pattern`, in the
            order to show them.
    """
    seed = yaml.safe_load(seed_file.read_text())
    rows = [
        {
            "id": uuid4(),
            "name": kind["name"],
            "description": kind["description"],
            "sort_order": sort_order,
            "sends_shared_photo": kind.get("sends_shared_photo", False),
            "raises_curiosity": kind.get("raises_curiosity", False),
            "shares_pattern": kind.get("shares_pattern", False),
        }
        for sort_order, kind in enumerate(seed)
    ]
    with engine.begin() as connection:
        if connection.execute(select(exists().select_from(check_in_kinds))).scalar():
            return
        connection.execute(insert(check_in_kinds).values(rows))


def seed_needs(engine: Engine, seed_file: Path) -> None:
    """Load the starting Needs on first run.

    Nothing is loaded once any Need exists, so Admin changes are never
    overwritten.

    Args:
        engine: The database engine.
        seed_file: YAML file listing Needs with `name`, `when_it_fits`,
            `how_to_reply`, an optional `fallback` and an optional
            `curiosities` (how Curiosities are treated while it is picked;
            only if they fit, when left out), in the order to show them.
    """
    seed = yaml.safe_load(seed_file.read_text())
    rows = [
        {
            "id": uuid4(),
            "name": need["name"],
            "when_it_fits": need["when_it_fits"],
            "how_to_reply": need["how_to_reply"],
            "sort_order": sort_order,
            "is_fallback": need.get("fallback", False),
            "curiosities": CuriosityTreatment(
                need.get("curiosities", CuriosityTreatment.ONLY_IF_IT_FITS)
            ),
        }
        for sort_order, need in enumerate(seed)
    ]
    with engine.begin() as connection:
        if connection.execute(select(exists().select_from(needs))).scalar():
            return
        connection.execute(insert(needs).values(rows))


def seed_thought_experiments(engine: Engine, seed_file: Path) -> None:
    """Add each seeded Thought Experiment whose key isn't stored yet.

    One already stored with its key is left as it is, edited, switched off
    or archived, so a seed never overwrites an Admin's change and never
    brings back an archived one. New ones keep the file's order.

    Args:
        engine: The database engine.
        seed_file: YAML file listing Thought Experiments with `key`,
            `wording`, `pattern_types` (the two it tells apart),
            `sensitivity` and an optional `starter`, in order.
    """
    seed = yaml.safe_load(seed_file.read_text())
    now = datetime.now(UTC)
    rows = [
        {
            "id": uuid4(),
            "seed_key": entry["key"],
            "wording": " ".join(entry["wording"].split()),
            "pattern_type_id": entry["pattern_types"][0],
            "other_pattern_type_id": entry["pattern_types"][1],
            "sensitivity": CuriositySensitivity(entry["sensitivity"]),
            "starter": entry.get("starter", False),
            "is_on": True,
            "created_at": now + timedelta(microseconds=order),
            "updated_at": now,
        }
        for order, entry in enumerate(seed)
    ]
    with engine.begin() as connection:
        stored = set(
            connection.execute(select(thought_experiments.c.seed_key)).scalars()
        )
        new_rows = [row for row in rows if row["seed_key"] not in stored]
        if new_rows:
            connection.execute(insert(thought_experiments).values(new_rows))


def seed_moves(engine: Engine, moves_seed_file: Path, needs_seed_file: Path) -> None:
    """Load the starting Moves and each starting Need's ruled-out Moves on first run.

    Nothing is loaded once any Move exists, so Admin changes are never
    overwritten. Load the Needs first: rule-outs go to the stored Needs that
    have a seeded Need's name, ignoring case.

    Args:
        engine: The database engine.
        moves_seed_file: YAML file listing Moves with `name`, `when_it_fits`,
            `how_to_do_it`, an optional `needed_feature` and an optional
            `asks_a_question`, in the order to show them.
        needs_seed_file: YAML file listing Needs, each with an optional
            `ruled_out_moves` list of Move names.
    """
    moves_seed = yaml.safe_load(moves_seed_file.read_text())
    needs_seed = yaml.safe_load(needs_seed_file.read_text())
    move_ids = {move["name"].lower(): uuid4() for move in moves_seed}
    move_rows = [
        {
            "id": move_ids[move["name"].lower()],
            "name": move["name"],
            "when_it_fits": move["when_it_fits"],
            "how_to_do_it": move["how_to_do_it"],
            "sort_order": sort_order,
            "needed_feature": move.get("needed_feature"),
            "asks_a_question": move.get("asks_a_question", False),
        }
        for sort_order, move in enumerate(moves_seed)
    ]
    with engine.begin() as connection:
        if connection.execute(select(exists().select_from(moves))).scalar():
            return
        connection.execute(insert(moves).values(move_rows))
        need_ids = {
            name.lower(): need_id
            for need_id, name in connection.execute(select(needs.c.id, needs.c.name))
        }
        rule_out_rows = [
            {
                "need_id": need_ids[need["name"].lower()],
                "move_id": move_ids[move.lower()],
            }
            for need in needs_seed
            if need["name"].lower() in need_ids
            for move in need.get("ruled_out_moves", [])
        ]
        if rule_out_rows:
            connection.execute(insert(need_ruled_out_moves).values(rule_out_rows))
