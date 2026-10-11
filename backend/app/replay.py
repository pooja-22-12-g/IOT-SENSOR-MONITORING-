"""Replay stored historical hours as a moving 'virtual now' cursor."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.cache import REPLAY_KEY, RedisCache
from app.db import MongoStore


class ReplayController:
    def __init__(self, mongo: MongoStore, cache: RedisCache) -> None:
        self.mongo = mongo
        self.cache = cache
        self.state: dict[str, Any] = {
            "running": False,
            "index": 0,
            "virtual_now": None,
            "total_hours": 0,
        }

    def _hours(self) -> list[datetime]:
        db = self.mongo.require()
        return [doc["timestamp"] for doc in db["station_snapshots"].find({}, {"timestamp": 1}).sort("timestamp", 1)]

    def start(self) -> dict[str, Any]:
        hours = self._hours()
        self.state = {
            "running": True,
            "index": 0,
            "virtual_now": hours[0].isoformat() if hours else None,
            "total_hours": len(hours),
        }
        self._persist()
        return self.status()

    def stop(self) -> dict[str, Any]:
        self.state["running"] = False
        self._persist()
        return self.status()

    def tick(self) -> dict[str, Any]:
        hours = self._hours()
        if not hours:
            self.state["virtual_now"] = None
            self.state["total_hours"] = 0
            self._persist()
            return self.status()
        if not self.state["running"]:
            self.state["running"] = True
        nxt = min(self.state["index"] + 1, len(hours) - 1)
        self.state["index"] = nxt
        self.state["virtual_now"] = hours[nxt].isoformat()
        self.state["total_hours"] = len(hours)
        self._persist()
        return self.status()

    def current_time(self) -> datetime | None:
        hours = self._hours()
        if not hours:
            return None
        if not self.state.get("running"):
            return hours[-1]
        idx = min(int(self.state.get("index") or 0), len(hours) - 1)
        return hours[idx]

    def status(self) -> dict[str, Any]:
        return dict(self.state)

    def _persist(self) -> None:
        if self.cache.connected:
            self.cache.set_json(REPLAY_KEY, self.state)
