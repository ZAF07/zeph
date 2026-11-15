"""Eval Runs: Eval Cases, runs, their Variants and Case Results (ADR-0013).

These tables hold no made-up data; that stays in the Eval database.

Revision ID: 0039
Revises: 0038
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0039"
down_revision: str | None = "0038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the Eval Case, Eval Run, Variant and Case Result tables."""
    op.create_table(
        "eval_cases",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column(
            "position", sa.BigInteger(), sa.Identity(), nullable=False, unique=True
        ),
        sa.Column("eval", sa.Text(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_eval_cases_eval", "eval_cases", ["eval"])
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position", sa.BigInteger(), sa.Identity(), nullable=False, unique=True
        ),
        sa.Column(
            "started_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("started_from", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("evals", postgresql.JSONB(), nullable=False),
        sa.Column("repeats", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("settings_snapshot", postgresql.JSONB()),
        sa.Column("judge_snapshot", postgresql.JSONB()),
        sa.Column("cases_snapshot", postgresql.JSONB()),
    )
    op.create_index("ix_eval_runs_state", "eval_runs", ["state"])
    op.create_table(
        "eval_variants",
        sa.Column(
            "run_id",
            sa.Uuid(),
            sa.ForeignKey("eval_runs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("letter", sa.Text(), primary_key=True),
        sa.Column(
            "setting_overrides",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
    )
    op.create_table(
        "eval_case_results",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position", sa.BigInteger(), sa.Identity(), nullable=False, unique=True
        ),
        sa.Column(
            "run_id",
            sa.Uuid(),
            sa.ForeignKey("eval_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("variant", sa.Text(), nullable=False),
        sa.Column("try_number", sa.Integer(), nullable=False),
        sa.Column("case_key", sa.Text(), nullable=False),
        sa.Column("eval", sa.Text(), nullable=False),
        sa.Column("case_content", postgresql.JSONB(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("checks", postgresql.JSONB(), nullable=False),
        sa.Column("facts", postgresql.JSONB(), nullable=False),
        sa.Column("notes", postgresql.JSONB(), nullable=False),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_eval_case_results_run_id", "eval_case_results", ["run_id"])


def downgrade() -> None:
    """Drop the Eval tables."""
    op.drop_table("eval_case_results")
    op.drop_table("eval_variants")
    op.drop_table("eval_runs")
    op.drop_table("eval_cases")
