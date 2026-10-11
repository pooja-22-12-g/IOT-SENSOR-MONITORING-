"""Redis cache for latest readings, dashboard stats, and recent alerts."""

from __future__ import annotations

import json
from typing import Any

import redis
from redis.exceptions import RedisError

from app.config import Settings

LATEST_PREFIX = "iot:latest:"
STATS_PREFIX = "iot:stats:"
ALERTS_KEY = "iot:alerts:recent"
DASHBOARD_KEY = "iot:dashboard:summary"
REPLAY_KEY = "iot:replay:state"


class RedisCache:
    def __init__(self) -> None:
        self.client: Any = None
        self.connected = False
        self.error: str | None = None

    def connect(self, settings: Settings, timeout: float = 0.8) -> None:
        self.connected = False
        self.error = None
        try:
            self.client = redis.Redis.from_url(
                settings.redis_url,
                socket_connect_timeout=timeout,
                decode_responses=True,
            )
            self.client.ping()
            self.connected = True
        except RedisError as exc:
            self.client = None
            self.connected = False
            self.error = str(exc)

    def close(self) -> None:
        if self.client is not None:
            try:
                self.client.close()
            except RedisError:
                pass
        self.client = None
        self.connected = False

    def set_json(self, key: str, value: Any, ttl: int | None = None) -> bool:
        if not self.connected or self.client is None:
            return False
        payload = json.dumps(value, default=str)
        if ttl:
            self.client.setex(key, ttl, payload)
        else:
            self.client.set(key, payload)
        return True

    def get_json(self, key: str) -> Any | None:
        if not self.connected or self.client is None:
            return None
        raw = self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def push_alert(self, alert: dict[str, Any], max_items: int = 50) -> None:
        if not self.connected or self.client is None:
            return
        self.client.lpush(ALERTS_KEY, json.dumps(alert, default=str))
        self.client.ltrim(ALERTS_KEY, 0, max_items - 1)

    def recent_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.connected or self.client is None:
            return []
        items = self.client.lrange(ALERTS_KEY, 0, limit - 1)
        return [json.loads(item) for item in items]


def attach_fake(cache: RedisCache, client: Any) -> RedisCache:
    cache.client = client
    cache.connected = True
    cache.error = None
    return cache
