"""create arc transitions table

Revision ID: 20260430_0003
Revises: 20260430_0002
Create Date: 2026-04-30 21:16:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260430_0003"
down_revision = "20260430_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "arc_transitions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column(
            "arc_id",
            sa.Text(),
            sa.ForeignKey("arcs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("from_state", sa.Text(), nullable=False),
        sa.Column("to_state", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "transitioned_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "resolved_scenes_at_transition",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "locations_visited_at_transition",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("triggering_event", sa.Text(), nullable=True),
    )
    op.create_index("idx_arc_transitions_arc_id", "arc_transitions", ["arc_id"])
    op.create_index("idx_arc_transitions_session_id", "arc_transitions", ["session_id"])
    op.create_index(
        "idx_arc_transitions_transitioned_at",
        "arc_transitions",
        [sa.text("transitioned_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_arc_transitions_transitioned_at", table_name="arc_transitions")
    op.drop_index("idx_arc_transitions_session_id", table_name="arc_transitions")
    op.drop_index("idx_arc_transitions_arc_id", table_name="arc_transitions")
    op.drop_table("arc_transitions")