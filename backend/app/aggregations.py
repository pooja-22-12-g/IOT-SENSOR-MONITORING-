"""Hourly and daily aggregation pipelines for MongoDB."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def time_bucket_pipeline(
    *,
    sensor_id: str | None,
    start: datetime | None,
    end: datetime | None,
    bucket_field: str,
) -> list[dict[str, Any]]:
    match: dict[str, Any] = {"is_missing": False, "value": {"$ne": None}}
    if sensor_id:
        match["sensor_id"] = sensor_id
    if start or end:
        match["timestamp"] = {}
        if start:
            match["timestamp"]["$gte"] = start
        if end:
            match["timestamp"]["$lte"] = end

    return [
        {"$match": match},
        {
            "$group": {
                "_id": {"sensor_id": "$sensor_id", "bucket": f"${bucket_field}"},
                "avg": {"$avg": "$value"},
                "min": {"$min": "$value"},
                "max": {"$max": "$value"},
                "count": {"$sum": 1},
                "anomaly_count": {
                    "$sum": {"$cond": [{"$eq": ["$anomaly.is_anomaly", True]}, 1, 0]}
                },
            }
        },
        {"$sort": {"_id.bucket": 1, "_id.sensor_id": 1}},
        {
            "$project": {
                "_id": 0,
                "sensor_id": "$_id.sensor_id",
                "bucket": "$_id.bucket",
                "avg": 1,
                "min": 1,
                "max": 1,
                "count": 1,
                "anomaly_count": 1,
            }
        },
    ]


def aggregate_in_memory(
    readings: list[dict[str, Any]],
    bucket_field: str,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, datetime], dict[str, Any]] = {}
    for row in readings:
        if row.get("is_missing") or row.get("value") is None:
            continue
        key = (row["sensor_id"], row[bucket_field])
        bucket = groups.setdefault(
            key,
            {"sensor_id": row["sensor_id"], "bucket": row[bucket_field], "values": [], "anomaly_count": 0},
        )
        bucket["values"].append(row["value"])
        if (row.get("anomaly") or {}).get("is_anomaly"):
            bucket["anomaly_count"] += 1

    out = []
    for (_sid, _ts), bucket in groups.items():
        values = bucket["values"]
        out.append(
            {
                "sensor_id": bucket["sensor_id"],
                "bucket": bucket["bucket"],
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values),
                "anomaly_count": bucket["anomaly_count"],
            }
        )
    out.sort(key=lambda item: (item["bucket"], item["sensor_id"]))
    return out
