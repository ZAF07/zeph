from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import MIGRATIONS_DIR, migrate, seed_moves
from tests.conftest import MOVES_SEED_FILE, NEEDS_SEED_FILE
from tests.test_moves import (
    STARTER_MOVES,
    how_to_do_it,
    stored_rule_outs,
    when_it_fits,
)
from tests.test_understanding import how_to_reply, need_when_it_fits

OLD_ACCOUNTABILITY_HOW_TO_REPLY = (
    "Hold them to what they said they want, kindly but honestly. Name the "
    "progress or the slip without lecturing, ask what got in the way or what "
    "the next small step is, and remind them why it matters to them."
)
OLD_BE_HEARD_WHEN_IT_FITS = (
    "They are venting or sharing something painful or frustrating, and want it "
    "to land with someone, not to be fixed, and it isn't mainly about one of "
    "their Goals. A slip on a Goal mentioned beside real pain (say, their mum "
    "in hospital) is still Be heard."
)
OLD_JUST_CHATTING_WHEN_IT_FITS = (
    "Small talk, banter, a greeting, a passing update or something fun, with "
    "nothing heavy underneath."
)
RELOADED_SETTINGS = (
    "persona",
    "understanding_prompt",
    "web_search_tool_description",
    "reply_web_search_instructions",
)


def downgrade_to(database_url: str, revision: str) -> None:
    """Take the database back to an earlier revision."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, revision)


def upgrade_to(database_url: str, revision: str) -> None:
    """Bring the database forward to a revision before the newest."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, revision)


def downgrade_to_before_moves(database_url: str) -> None:
    """Take the database back to the revision before Moves."""
    downgrade_to(database_url, "0049")


def move_names(engine: Engine) -> list[str]:
    """The stored Moves' names, in order."""
    with engine.connect() as connection:
        return list(
            connection.execute(text("SELECT name FROM moves ORDER BY sort_order"))
            .scalars()
            .all()
        )


def test_the_migration_adds_the_starter_moves_and_rule_outs_to_existing_needs(
    engine: Engine, database_url: str
) -> None:
    downgrade_to_before_moves(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE needs SET how_to_reply = :old WHERE name = :name"),
                {"old": OLD_ACCOUNTABILITY_HOW_TO_REPLY, "name": "Accountability"},
            )
    finally:
        migrate(database_url)

    assert move_names(engine) == STARTER_MOVES
    rule_outs = stored_rule_outs(engine)
    assert rule_outs["Be heard"] == {
        "Reframe",
        "Suggest",
        "Plan steps",
        "Push",
        "Research",
    }
    assert rule_outs["Ask more"] == set(STARTER_MOVES)
    with engine.connect() as connection:
        accountability = connection.execute(
            text("SELECT how_to_reply FROM needs WHERE name = 'Accountability'")
        ).scalar_one()
        reloaded = connection.execute(
            text("SELECT key FROM platform_settings WHERE key = ANY(:keys)"),
            {"keys": list(RELOADED_SETTINGS)},
        ).all()
    assert accountability == how_to_reply("Accountability").strip()
    assert reloaded == []


def test_the_migration_adds_no_moves_to_a_database_without_needs(
    engine: Engine, database_url: str
) -> None:
    downgrade_to_before_moves(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE needs CASCADE"))
    finally:
        migrate(database_url)

    assert move_names(engine) == []


def test_seeding_adds_nothing_once_moves_exist(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM moves WHERE name = 'Push'"))

    seed_moves(engine, MOVES_SEED_FILE, NEEDS_SEED_FILE)

    assert move_names(engine) == [name for name in STARTER_MOVES if name != "Push"]
    assert "Push" not in stored_rule_outs(engine)["Be heard"]


def test_seeding_reads_whether_a_move_asks_a_question(
    engine: Engine, tmp_path: Path
) -> None:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE moves CASCADE"))
    moves_seed_file = tmp_path / "moves.yaml"
    moves_seed_file.write_text(
        "- name: Wonder\n"
        "  when_it_fits: They mention their day.\n"
        "  how_to_do_it: Ask one light question.\n"
        "  asks_a_question: true\n"
        "- name: Cheer\n"
        "  when_it_fits: Good news.\n"
        "  how_to_do_it: Cheer them on.\n"
    )
    needs_seed_file = tmp_path / "needs.yaml"
    needs_seed_file.write_text("[]\n")

    seed_moves(engine, moves_seed_file, needs_seed_file)

    with engine.connect() as connection:
        ticked = dict(
            connection.execute(text("SELECT name, asks_a_question FROM moves")).all()
        )
    assert ticked == {"Wonder": True, "Cheer": False}


def test_the_migration_says_research_needs_web_search(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0051")
    try:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE moves SET name = 'research' WHERE name = 'Research'")
            )
    finally:
        migrate(database_url)

    with engine.connect() as connection:
        needed = dict(
            connection.execute(text("SELECT name, needed_feature FROM moves")).all()
        )
    assert needed == {
        **{name: None for name in STARTER_MOVES if name != "Research"},
        "research": "web_search",
    }


def test_the_next_move_migration_reloads_the_understanding_prompt(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0053")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = to_jsonb('Old prompt'::text) "
                    "WHERE key = 'understanding_prompt'"
                )
            )
    finally:
        migrate(database_url)

    with engine.connect() as connection:
        prompt = connection.execute(
            text(
                "SELECT value FROM platform_settings WHERE key = 'understanding_prompt'"
            )
        ).all()
        next_moves = connection.execute(
            text("SELECT next_move, next_move_why FROM reply_plans")
        ).all()
    assert prompt == []
    assert next_moves == []


def test_the_unmade_next_move_migration_reloads_the_curiosity_keeping_prompt(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0054")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = to_jsonb('Old prompt'::text) "
                    "WHERE key = 'curiosity_keeping_prompt'"
                )
            )
    finally:
        migrate(database_url)

    with engine.connect() as connection:
        prompt = connection.execute(
            text(
                "SELECT value FROM platform_settings "
                "WHERE key = 'curiosity_keeping_prompt'"
            )
        ).all()
    assert prompt == []


def test_the_fallback_migration_adds_a_column_that_defaults_to_not_fallback(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0055")
    migrate(database_url)

    with engine.connect() as connection:
        column = connection.execute(
            text(
                "SELECT is_nullable, column_default FROM information_schema.columns "
                "WHERE table_name = 'understandings' AND column_name = 'is_fallback'"
            )
        ).one()
    assert tuple(column) == ("NO", "false")


def test_the_asks_a_question_migration_leaves_existing_moves_unticked(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0058")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = to_jsonb('Old prompt'::text) "
                    "WHERE key = 'woven_check_in_prompt'"
                )
            )
    finally:
        migrate(database_url)

    with engine.connect() as connection:
        ticked = dict(
            connection.execute(text("SELECT name, asks_a_question FROM moves")).all()
        )
        prompt = connection.execute(
            text(
                "SELECT value FROM platform_settings "
                "WHERE key = 'woven_check_in_prompt'"
            )
        ).all()
    assert ticked == {name: False for name in STARTER_MOVES}
    assert prompt == []


def stored_when_it_fits(engine: Engine) -> dict[str, str]:
    """Each stored Need's "when it fits", by name."""
    with engine.connect() as connection:
        return dict(
            connection.execute(text("SELECT name, when_it_fits FROM needs")).all()
        )


def test_the_get_curious_migration_adds_it_last_ticked_with_its_rule_outs(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0060")
    try:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM moves WHERE name = 'Get curious'"))
            connection.execute(
                text("UPDATE needs SET when_it_fits = :old WHERE name = 'Be heard'"),
                {"old": OLD_BE_HEARD_WHEN_IT_FITS},
            )
            connection.execute(
                text(
                    "UPDATE needs SET when_it_fits = :old WHERE name = 'Just chatting'"
                ),
                {"old": OLD_JUST_CHATTING_WHEN_IT_FITS},
            )
    finally:
        migrate(database_url)

    assert move_names(engine) == STARTER_MOVES
    with engine.connect() as connection:
        get_curious = connection.execute(
            text(
                "SELECT when_it_fits, how_to_do_it, asks_a_question, needed_feature "
                "FROM moves WHERE name = 'Get curious'"
            )
        ).one()
    assert tuple(get_curious) == (
        when_it_fits("Get curious"),
        how_to_do_it("Get curious"),
        True,
        None,
    )
    ruled_out_by = {
        need
        for need, moves in stored_rule_outs(engine).items()
        if "Get curious" in moves
    }
    assert ruled_out_by == {"Ask more", "Get it done"}
    wording = stored_when_it_fits(engine)
    assert wording["Be heard"] == need_when_it_fits("Be heard")
    assert wording["Just chatting"] == need_when_it_fits("Just chatting")


def test_the_get_curious_migration_leaves_an_existing_one_and_edited_wording_alone(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0060")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE moves SET name = 'get Curious', when_it_fits = 'Mine', "
                    "asks_a_question = false WHERE name = 'Get curious'"
                )
            )
            connection.execute(
                text(
                    "DELETE FROM need_ruled_out_moves WHERE move_id = "
                    "(SELECT id FROM moves WHERE name = 'get Curious')"
                )
            )
            connection.execute(
                text(
                    "UPDATE needs SET when_it_fits = 'My own wording' "
                    "WHERE name IN ('Be heard', 'Just chatting')"
                )
            )
    finally:
        migrate(database_url)

    with engine.connect() as connection:
        moves = connection.execute(
            text(
                "SELECT name, when_it_fits, asks_a_question FROM moves "
                "WHERE lower(name) = 'get curious'"
            )
        ).all()
    assert [tuple(move) for move in moves] == [("get Curious", "Mine", False)]
    assert all(
        "get Curious" not in moves for moves in stored_rule_outs(engine).values()
    )
    wording = stored_when_it_fits(engine)
    assert wording["Be heard"] == "My own wording"
    assert wording["Just chatting"] == "My own wording"


def test_the_get_curious_migration_adds_no_move_to_a_database_without_moves(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0060")
    try:
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE moves CASCADE"))
    finally:
        migrate(database_url)

    assert move_names(engine) == []
