"""Reloading a stored Eval Case from the seed without losing an Admin's changes.

A migration that changes a seed Eval Case calls
`reload_eval_case_unless_edited` with the case's key. See the migrations
guide, `src/companion/adapters/postgres/migrations/README.md`.
"""

import logging

import sqlalchemy as sa

logger = logging.getLogger(__name__)


def reload_eval_case_unless_edited(connection: sa.Connection, key: str) -> None:
    """Remove a stored Eval Case no Admin changed, so the new seed case loads.

    A stored case an Admin edited or archived is kept, and a warning naming
    it is logged so the owner can change it by hand. A case that isn't stored
    is left alone. Past Case Results keep the case as it was when they ran.
    The removal checks for an Admin's change in the same statement, so
    backends migrating at the same time can't remove one.

    Args:
        connection: The migration's database connection (`op.get_bind()`).
        key: The Eval Case's key (its `id` in the seed file).
    """
    connection.execute(
        sa.text(
            "DELETE FROM eval_cases WHERE key = :key "
            "AND edited = false AND archived = false"
        ),
        {"key": key},
    )
    still_stored = connection.execute(
        sa.text("SELECT 1 FROM eval_cases WHERE key = :key"), {"key": key}
    ).first()
    if still_stored:
        logger.warning(
            "Kept the stored Eval Case %s: an Admin edited or archived it, so "
            "the new seed case was not loaded. Change it by hand on the "
            "Dashboard.",
            key,
        )
