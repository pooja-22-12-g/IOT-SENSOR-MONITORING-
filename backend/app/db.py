"""MongoDB access. Connection success is reported only after a real ping."""

from __future__ import annotations

from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import Settings
from app.schema import INDEXES


class MongoStore:
    def __init__(self) -> None:
        self.client: MongoClient | None = None
        self.db: Any = None
        self.connected = False
        self.error: str | None = None

    def connect(self, settings: Settings, timeout_ms: int = 1500) -> None:
        self.connected = False
        self.error = None
        try:
            self.client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=timeout_ms)
            self.client.admin.command("ping")
            self.db = self.client[settings.mongodb_db]
            self.connected = True
        except PyMongoError as exc:
            self.client = None
            self.db = None
            self.connected = False
            self.error = str(exc)

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
        self.client = None
        self.db = None
        self.connected = False

    def require(self) -> Any:
        if not self.connected or self.db is None:
            raise RuntimeError(self.error or "MongoDB is not connected")
        return self.db

    def ensure_indexes(self) -> dict[str, int]:
        db = self.require()
        created: dict[str, int] = {}
        for collection, specs in INDEXES.items():
            coll = db[collection]
            before = {idx["name"] for idx in coll.list_indexes()}
            for spec in specs:
                coll.create_index(spec)
            after = {idx["name"] for idx in coll.list_indexes()}
            created[collection] = len(after - before)
        return created


def attach_mock(store: MongoStore, database: Any) -> MongoStore:
    """Used by tests with mongomock. Not used to fake a live server."""
    store.client = None
    store.db = database
    store.connected = True
    store.error = None
    return store
