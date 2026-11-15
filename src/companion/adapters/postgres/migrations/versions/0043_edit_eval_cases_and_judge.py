"""Admins edit Eval Cases and the Judge: case authors, test images, Judge settings.

Stored cases are rewritten once into the shape the case forms write:
Persona messages as `{text, photo, shows}`, rules as `{id, check}`, Memory
Items as `{category, contents}` and earlier lines as `{who, text}`. Run
snapshots keep the cases as they were.

Revision ID: 0043
Revises: 0042
Create Date: 2026-11-15
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0043"
down_revision: str | None = "0042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def rules_list(rules: Any) -> Any:
    """Write rules given by ID as a list of `{id, check}`.

    Args:
        rules: The rules as stored.

    Returns:
        The list; unchanged if already one.
    """
    if isinstance(rules, dict):
        return [{"id": rule, "check": check} for rule, check in rules.items()]
    return rules


def memory_item_list(items: Any) -> Any:
    """Write Memory Items given by category as a list of `{category, contents}`.

    Args:
        items: The Memory Items as stored.

    Returns:
        The list; unchanged if already one.
    """
    if isinstance(items, dict):
        return [
            {"category": category, "contents": contents}
            for category, contents in items.items()
        ]
    return items or []


def persona_message(message: Any) -> Any:
    """Write a Persona message as `{text, photo, shows}`.

    Args:
        message: Plain text, or `{photo, shows, caption}`.

    Returns:
        The message.
    """
    if isinstance(message, str):
        return {"text": message, "photo": None, "shows": ""}
    if "caption" in message or "text" not in message:
        return {
            "text": message.get("caption", ""),
            "photo": message.get("photo"),
            "shows": message.get("shows", ""),
        }
    return message


def earlier_line(line: dict[str, str]) -> dict[str, str]:
    """Write an earlier line as `{who, text}`.

    Args:
        line: `{person: <text>}`, `{zeph: <text>}` or already `{who, text}`.

    Returns:
        The line.
    """
    if "person" in line:
        return {"who": "person", "text": line["person"]}
    if "zeph" in line:
        return {"who": "zeph", "text": line["zeph"]}
    return line


def regular_content(eval_name: str, content: dict[str, Any]) -> dict[str, Any]:
    """Rewrite one case's content into the shape the case forms write.

    Args:
        eval_name: The case's Eval.
        content: Its content as stored.

    Returns:
        The content in the regular shape.
    """
    if eval_name == "persona":
        return {
            **content,
            "messages": [persona_message(m) for m in content["messages"]],
            "rules": rules_list(content.get("rules", {})),
        }
    if eval_name == "settings":
        return {**content, "memories": memory_item_list(content.get("memories"))}
    if eval_name == "understanding":
        memory = content.get("memory", {})
        return {
            **content,
            "memory": {**memory, "items": memory_item_list(memory.get("items"))},
            "earlier": [earlier_line(line) for line in content.get("earlier", [])],
            "rules": rules_list(content.get("rules", {})),
        }
    return content


def upgrade() -> None:
    """Add who wrote each case and whether it was edited, images and the Judge."""
    op.add_column(
        "eval_cases",
        sa.Column("edited", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "eval_cases",
        sa.Column(
            "created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
    )
    op.add_column(
        "eval_cases",
        sa.Column(
            "updated_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
    )
    op.create_table(
        "eval_images",
        sa.Column("name", sa.Text(), primary_key=True),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("media_type", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "eval_judge_settings",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "updated_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
    )
    eval_cases = sa.table(
        "eval_cases",
        sa.column("key", sa.Text()),
        sa.column("eval", sa.Text()),
        sa.column("content", postgresql.JSONB()),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(eval_cases.c.key, eval_cases.c.eval, eval_cases.c.content)
    ).all()
    for key, eval_name, content in rows:
        connection.execute(
            sa.update(eval_cases)
            .where(eval_cases.c.key == key)
            .values(content=regular_content(eval_name, content))
        )


def downgrade() -> None:
    """Drop the Judge settings, the images and the case authors.

    Cases stay in the regular shape.
    """
    op.drop_table("eval_judge_settings")
    op.drop_table("eval_images")
    op.drop_column("eval_cases", "updated_by")
    op.drop_column("eval_cases", "created_by")
    op.drop_column("eval_cases", "edited")
