"""Smoke tests for the StateRepository surface added in Brief 19.5.

Covers `get_state_full` and the `transaction()` context manager that yields a
TransactionalStateRepository. Uses fake pools/connections rather than a real
DB; the goal is to verify the wiring between repository methods and asyncpg
operations, not to re-test SQL.

Tests run async coroutines via `asyncio.run` to avoid taking on
`pytest-asyncio` as a new dependency.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import pytest

from api.repositories.state_repository import (
    FullState,
    StateRepository,
    TransactionalStateRepository,
)


# ---------------------------------------------------------------------------
# Async-context scaffolding
# ---------------------------------------------------------------------------

class _AcquireCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


class _TxCtx:
    """Records whether an exception passed through __aexit__ — i.e. rollback."""

    def __init__(self, conn):
        self._conn = conn
        self.exception_propagated: bool = False

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.exception_propagated = True
        # Don't suppress; let caller see the exception just like asyncpg.
        return False


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _AcquireCtx(self._conn)


class _FakeConn:
    """Stub asyncpg connection. Holds a single optional row keyed by session_id."""

    def __init__(self, *, row: dict[str, Any] | None = None):
        self._row = row
        self.tx: _TxCtx | None = None
        self.executed: list[tuple[str, tuple]] = []

    def transaction(self):
        self.tx = _TxCtx(self)
        return self.tx

    async def fetchrow(self, query: str, *args):
        if self._row is None:
            return None
        # Match either of the SELECT shapes the repo issues.
        return self._row

    async def execute(self, query: str, *args):
        self.executed.append((query, args))
        return "UPDATE 1"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_get_state_full_returns_composed_object() -> None:
    row = {
        "session_id": "sess1",
        "character": {"name": "Sylvara", "knowledge": {}},
        "world": {"location": "feywood", "turn": 4},
        "log": ["entry-1"],
        "updated_at": datetime(2026, 5, 3, tzinfo=timezone.utc),
    }
    repo = StateRepository(FakePool(_FakeConn(row=row)))

    state = asyncio.run(repo.get_state_full("sess1"))

    assert isinstance(state, FullState)
    assert state.session_id == "sess1"
    assert state.character == {"name": "Sylvara", "knowledge": {}}
    assert state.world == {"location": "feywood", "turn": 4}
    assert state.log == ["entry-1"]


@pytest.mark.unit
def test_get_state_full_returns_none_for_missing_session() -> None:
    repo = StateRepository(FakePool(_FakeConn(row=None)))

    state = asyncio.run(repo.get_state_full("missing"))

    assert state is None


@pytest.mark.unit
def test_transaction_context_yields_transactional_repo() -> None:
    row = {
        "session_id": "sess1",
        "character": {"name": "Sylvara"},
        "world": {"location": "feywood", "turn": 4},
        "log": [],
        "updated_at": datetime(2026, 5, 3, tzinfo=timezone.utc),
    }
    conn = _FakeConn(row=row)
    repo = StateRepository(FakePool(conn))

    async def run() -> None:
        async with repo.transaction() as txn:
            assert isinstance(txn, TransactionalStateRepository)
            state = await txn.get_state_full("sess1", lock=True)
            assert state is not None
            assert state.character["name"] == "Sylvara"

            await txn.update_character_with_log(
                "sess1",
                {"name": "Sylvara", "knowledge": {"athletics": {"tier": 2, "applications": {}}}},
                ["new entry"],
            )

    asyncio.run(run())

    assert any("UPDATE game_states" in q for q, _ in conn.executed)
    assert conn.tx is not None
    assert conn.tx.exception_propagated is False


@pytest.mark.unit
def test_transaction_propagates_exception_for_rollback() -> None:
    """A raised exception inside the context must propagate so asyncpg rolls back."""
    conn = _FakeConn(row=None)
    repo = StateRepository(FakePool(conn))

    async def run() -> None:
        async with repo.transaction() as txn:
            assert isinstance(txn, TransactionalStateRepository)
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(run())

    assert conn.tx is not None
    assert conn.tx.exception_propagated is True
