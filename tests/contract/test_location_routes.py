import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import location


class _AcquireCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _AcquireCtx(self._conn)


class LocationConn:
    def __init__(self):
        self.locations = {"crossroads", "old-road", "river-ford"}
        self.edges = {("crossroads", "old-road"), ("crossroads", "river-ford")}
        self.deleted_edges: list[tuple[str, list[str]]] = []

    async def fetchval(self, query, *args):
        if "SELECT 1 FROM locations WHERE id = $1" in query:
            return 1 if args[0] in self.locations else None
        return None

    async def fetchrow(self, query, *args):
        if "INSERT INTO locations" in query and "RETURNING id, name, data, updated_at" in query:
            location_id = args[0]
            self.locations.add(location_id)
            return {
                "id": location_id,
                "name": args[1],
                "data": args[2],
                "updated_at": None,
            }
        return None

    async def fetch(self, query, *args):
        if "FROM locations" in query and "data->'connections'" in query:
            return []
        return []

    async def execute(self, query, *args):
        if "DELETE FROM world_graph" in query:
            source_id = args[0]
            keep_ids = set(args[1])
            self.deleted_edges.append((source_id, list(args[1])))
            self.edges = {
                edge for edge in self.edges
                if edge[0] != source_id or edge[1] in keep_ids
            }
            return "DELETE"

        if "INSERT INTO world_graph" in query:
            self.edges.add((args[0], args[1]))
            return "INSERT"

        return "OK"


def _make_app(pool) -> FastAPI:
    app = FastAPI()
    app.include_router(location.router)
    app.dependency_overrides[get_pool] = lambda: pool
    return app


@pytest.mark.contract
def test_location_update_deletes_stale_outbound_edges() -> None:
    conn = LocationConn()
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/location",
            json={
                "id": "crossroads",
                "name": "Crossroads",
                "type": "road",
                "description": "A split in the road.",
                "connections": ["river-ford"],
            },
        )

    assert response.status_code == 200
    assert conn.deleted_edges == [("crossroads", ["river-ford"])]
    assert ("crossroads", "old-road") not in conn.edges
    assert ("crossroads", "river-ford") in conn.edges
