"""create scene_records table

Revision ID: 20260503_0004
Revises: 20260430_0003
Create Date: 2026-05-03

Brief 19 — Backend Authority Arc, Phase 2 Step 2.
Persistent record of resolved scenes with structured actions and arc-progression
contributions. Enables one-tag-per-scene enforcement at the backend, real
envelope counting per arc, and queryable scene history.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260503_0004"
down_revision = "20260430_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scene_records",
        sa.Column("scene_id", sa.Text(), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            sa.Text(),
            sa.ForeignKey("game_states.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resolved_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("scene_summary", sa.Text(), nullable=True),
        sa.Column(
            "scene_actions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("tag_advance_committed", sa.Text(), nullable=True),
        sa.Column(
            "arc_progressed_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("location_id", sa.Text(), nullable=True),
        sa.Column("turn_at_resolution", sa.Integer(), nullable=True),
        sa.Column(
            "time_at_resolution",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_scene_records_session_id", "scene_records", ["session_id"]
    )
    op.create_index(
        "idx_scene_records_session_resolved",
        "scene_records",
        ["session_id", "resolved_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_scene_records_session_resolved", table_name="scene_records")
    op.drop_index("idx_scene_records_session_id", table_name="scene_records")
    op.drop_table("scene_records")
