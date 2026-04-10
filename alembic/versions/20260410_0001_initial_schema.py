"""initial schema

Revision ID: 20260410_0001
Revises:
Create Date: 2026-04-10 10:26:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260410_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "game_states",
        sa.Column("session_id", sa.Text(), primary_key=True, nullable=False),
        sa.Column("character", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("world", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "log",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=True, server_default=sa.text("now()")),
    )

    op.create_table(
        "locations",
        sa.Column("id", sa.Text(), primary_key=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=True, server_default=sa.text("now()")),
    )

    op.create_table(
        "world_graph",
        sa.Column("from_id", sa.Text(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("to_id", sa.Text(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("traversal", sa.Text(), nullable=True),
        sa.Column("distance", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("from_id", "to_id"),
    )


def downgrade() -> None:
    op.drop_table("world_graph")
    op.drop_table("locations")
    op.drop_table("game_states")
