"""Reloading a stored prompt from the seed without losing an Admin's edits.

A migration that changes a seed prompt calls `reload_prompt_unless_edited`
with the hash of the seed text it replaces. See the migrations guide,
`src/companion/adapters/postgres/migrations/README.md`.
"""

import hashlib
import logging

import sqlalchemy as sa

logger = logging.getLogger(__name__)


def prompt_hash(prompt: str) -> str:
    """Hash a prompt's text, the way a stored prompt is compared.

    Args:
        prompt: The prompt's text, as the seed loads it.

    Returns:
        The SHA-256 of the text as UTF-8, in hex.
    """
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def reload_prompt_unless_edited(
    connection: sa.Connection, key: str, previous_seed_hash: str
) -> None:
    """Remove a stored prompt still at the previous seed, so the new seed loads.

    A stored prompt that differs from the previous seed was edited by an
    Admin: it is kept, and a warning naming the setting is logged so the
    owner can merge the new seed text by hand. A prompt that isn't stored is
    left alone. The check and the removal are one statement, so backends
    migrating at the same time can't remove an edit.

    Args:
        connection: The migration's database connection (`op.get_bind()`).
        key: The Platform Setting key of the prompt.
        previous_seed_hash: `prompt_hash` of the seed text being replaced,
            written out in the migration.
    """
    connection.execute(
        sa.text(
            "DELETE FROM platform_settings WHERE key = :key "
            "AND encode(sha256(convert_to(value #>> '{}', 'UTF8')), 'hex') "
            "= :previous_seed_hash"
        ),
        {"key": key, "previous_seed_hash": previous_seed_hash},
    )
    still_stored = connection.execute(
        sa.text("SELECT 1 FROM platform_settings WHERE key = :key"), {"key": key}
    ).first()
    if still_stored:
        logger.warning(
            "Kept the Admin's edit of %s: the stored text differs from the "
            "previous seed, so the new seed text was not loaded. Merge the new "
            "seed text into it by hand on the Dashboard.",
            key,
        )
