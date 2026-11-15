"""Eval Run cost control, picked cases, re-runs and full traces.

Eval Runs keep the case keys they run, a cancel request, their token limit
and the run they re-run; Case Results keep tokens by model; Eval model
calls hold each Case Result's full trace, apart from the Model Call Log.

Revision ID: 0044
Revises: 0043
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0044"
down_revision: str | None = "0043"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the new Eval Run and Case Result columns and the Eval model calls."""
    op.add_column(
        "eval_runs",
        sa.Column("case_keys", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "eval_runs",
        sa.Column(
            "cancel_requested", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column("eval_runs", sa.Column("token_limit", sa.Integer()))
    op.add_column(
        "eval_runs",
        sa.Column(
            "rerun_of", sa.Uuid(), sa.ForeignKey("eval_runs.id", ondelete="SET NULL")
        ),
    )
    op.add_column(
        "eval_case_results",
        sa.Column(
            "tokens_by_model", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
    )
    op.create_index("ix_eval_case_results_case_key", "eval_case_results", ["case_key"])
    op.create_table(
        "eval_model_calls",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position", sa.BigInteger(), sa.Identity(), nullable=False, unique=True
        ),
        sa.Column(
            "case_result_id",
            sa.Uuid(),
            sa.ForeignKey("eval_case_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("made_up_user_id", sa.Uuid(), nullable=False),
        sa.Column("trace_id", sa.Uuid(), nullable=False),
        sa.Column("trace_kind", sa.Text(), nullable=False),
        sa.Column("step", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("thinking", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text()),
        sa.Column("tools_called", postgresql.JSONB(), nullable=False),
        sa.Column("content", postgresql.JSONB()),
        sa.Column("understanding_shape", postgresql.JSONB()),
    )
    op.create_index(
        "ix_eval_model_calls_case_result_id", "eval_model_calls", ["case_result_id"]
    )


def downgrade() -> None:
    """Drop the Eval model calls and the new columns."""
    op.drop_table("eval_model_calls")
    op.drop_index("ix_eval_case_results_case_key", "eval_case_results")
    op.drop_column("eval_case_results", "tokens_by_model")
    op.drop_column("eval_runs", "rerun_of")
    op.drop_column("eval_runs", "token_limit")
    op.drop_column("eval_runs", "cancel_requested")
    op.drop_column("eval_runs", "case_keys")
