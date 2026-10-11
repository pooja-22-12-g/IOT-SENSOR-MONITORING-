from __future__ import annotations

from datetime import datetime
from typing import Any

from app.aggregations import time_bucket_pipeline
from app.cache import DASHBOARD_KEY, LATEST_PREFIX, RedisCache
from app.db import MongoStore
from app.health import health_report
from app.sensor_catalog import SENSORS, sensor_list
from app.serialize import public_doc, public_list


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", ""))


def latest_readings(mongo: MongoStore, cache: RedisCache) -> list[dict[str, Any]]:
    out = []
    db = mongo.require()
    for sensor_id in SENSORS:
        cached = cache.get_json(f"{LATEST_PREFIX}{sensor_id}")
        if cached:
            cached["cache_hit"] = True
            out.append(cached)
            continue
        doc = db["sensor_readings"].find_one({"sensor_id": sensor_id}, sort=[("timestamp", -1)])
        item = public_doc(doc)
        if item:
            item["cache_hit"] = False
            cache.set_json(f"{LATEST_PREFIX}{sensor_id}", item)
            out.append(item)
    return out


def list_readings(
    mongo: MongoStore,
    *,
    sensor_id: str | None,
    start: datetime | None,
    end: datetime | None,
    limit: int,
) -> list[dict[str, Any]]:
    query: dict[str, Any] = {}
    if sensor_id:
        query["sensor_id"] = sensor_id
    if start or end:
        query["timestamp"] = {}
        if start:
            query["timestamp"]["$gte"] = start
        if end:
            query["timestamp"]["$lte"] = end
    docs = (
        mongo.require()["sensor_readings"]
        .find(query)
        .sort("timestamp", -1)
        .limit(limit)
    )
    return public_list(list(docs))


def bucket_stats(
    mongo: MongoStore,
    cache: RedisCache,
    *,
    sensor_id: str | None,
    start: datetime | None,
    end: datetime | None,
    bucket_field: str,
    ttl: int,
) -> list[dict[str, Any]]:
    cache_key = (
        f"iot:stats:{bucket_field}:{sensor_id or 'all'}:"
        f"{start.isoformat() if start else ''}:"
        f"{end.isoformat() if end else ''}"
    )
    cached = cache.get_json(cache_key)
    if cached is not None:
        return cached
    pipeline = time_bucket_pipeline(
        sensor_id=sensor_id, start=start, end=end, bucket_field=bucket_field
    )
    rows = list(mongo.require()["sensor_readings"].aggregate(pipeline))
    payload = public_list(rows)
    cache.set_json(cache_key, payload, ttl)
    return payload


def alerts(
    mongo: MongoStore,
    cache: RedisCache,
    *,
    sensor_id: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    if not sensor_id:
        cached = cache.recent_alerts(limit)
        if cached:
            return cached
    query: dict[str, Any] = {}
    if sensor_id:
        query["sensor_id"] = sensor_id
    docs = mongo.require()["alerts"].find(query).sort("timestamp", -1).limit(limit)
    return public_list(list(docs))


def sensor_health(mongo: MongoStore, sensor_id: str, cap_time: datetime | None = None) -> dict[str, Any]:
    query: dict[str, Any] = {"sensor_id": sensor_id}
    if cap_time:
        query["timestamp"] = {"$lte": cap_time}
    docs = list(
        mongo.require()["sensor_readings"].find(query).sort("timestamp", -1).limit(168)
    )
    report = health_report(docs)
    report["sensor_id"] = sensor_id
    report["name"] = SENSORS[sensor_id]["name"]
    return report


def dashboard_summary(mongo: MongoStore, cache: RedisCache, cap_time: datetime | None = None) -> dict[str, Any]:
    cached = cache.get_json(DASHBOARD_KEY) if cap_time is None else None
    db = mongo.require()
    snap_query: dict[str, Any] = {}
    if cap_time:
        snap_query["timestamp"] = {"$lte": cap_time}
    latest_snap = db["station_snapshots"].find_one(snap_query, sort=[("timestamp", -1)])
    alert_query: dict[str, Any] = {}
    if cap_time:
        alert_query["timestamp"] = {"$lte": cap_time}
    alert_count = db["alerts"].count_documents(alert_query)
    reading_count = db["sensor_readings"].count_documents(
        {"timestamp": {"$lte": cap_time}} if cap_time else {}
    )
    health = [sensor_health(mongo, sensor_id, cap_time) for sensor_id in SENSORS]
    payload = {
        "latest_snapshot": public_doc(latest_snap),
        "alert_count": alert_count,
        "reading_count": reading_count,
        "sensor_catalog": sensor_list(),
        "health": health,
        "cache_meta": cached,
        "virtual_now": cap_time.isoformat() if cap_time else None,
    }
    return payload
