"""create arcs table

Revision ID: 20260430_0002
Revises: 20260410_0001
Create Date: 2026-04-30 20:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260430_0002"
down_revision = "20260410_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "arcs",
        sa.Column("id", sa.Text(), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            sa.Text(),
            sa.ForeignKey("game_states.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("primary_type", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("parent_arc_id", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_arcs_session_id", "arcs", ["session_id"])
    op.create_index("idx_arcs_session_state", "arcs", ["session_id", "state"])
    op.create_index(
        "idx_arcs_parent_arc_id",
        "arcs",
        ["parent_arc_id"],
        postgresql_where=sa.text("parent_arc_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_arcs_parent_arc_id", table_name="arcs")
    op.drop_index("idx_arcs_session_state", table_name="arcs")
    op.drop_index("idx_arcs_session_id", table_name="arcs")
    op.drop_table("arcs")