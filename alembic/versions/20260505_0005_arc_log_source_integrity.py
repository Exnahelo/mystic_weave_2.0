"""arc.log[].source integrity check (read-only fail-loud)

Revision ID: 20260505_0005
Revises: 20260503_0004
Create Date: 2026-05-05

Brief A — Stabilization Pass. Detects any arc.data->'log' entry whose
source value is outside the schema's valid set ('progress', 'transition').
Surfaced after the 2026-05-05 Phase 9b session, where a manual JSON patch
introduced a 'settlement_correction' source on arc-94f73453e294498e and
caused GET /arc/{session_id} to 500 on response validation.

The migration does not modify rows. It scans, fails loudly with the
offending arc_id / session_id / value, and points the operator at the
runbook. Automatic repair would lose operational meaning; the human picks
the right replacement source.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from api.models import ARC_BEAT_LOG_VALID_SOURCES

# revision identifiers, used by Alembic.
revision = "20260505_0005"
down_revision = "20260503_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Detect and fail loudly on any arc.log[].source value outside the
    valid set. Does not modify data; failure is the signal that operator
    repair is needed.
    """
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
            SELECT a.id AS arc_id,
                   a.session_id,
                   jsonb_array_elements(a.data->'log')->>'source' AS source_value
            FROM arcs a
            WHERE a.data ? 'log'
              AND jsonb_typeof(a.data->'log') = 'array'
            """
        )
    )
    invalid = [
        (row.arc_id, row.session_id, row.source_value)
        for row in result
        if row.source_value not in ARC_BEAT_LOG_VALID_SOURCES
    ]
    if invalid:
        details = "\n".join(
            f"  arc_id={a} session_id={s} bad_source={v!r}"
            for a, s, v in invalid
        )
        raise RuntimeError(
            f"arc.log[].source integrity check failed; "
            f"{len(invalid)} bad value(s) found.\n"
            f"Valid sources are {ARC_BEAT_LOG_VALID_SOURCES}.\n"
            f"Offending entries:\n{details}\n"
            f"Repair manually before re-running migration. "
            f"See docs/operations/arc-log-source-integrity.md for guidance."
        )


def downgrade() -> None:
    """No-op; this migration only validates."""
    pass
