"""IoT NoSQL schema and MongoDB index definitions.

Time-oriented design:
- sensor_readings: one document per channel per hour (query by sensor_id + timestamp)
- station_snapshots: one document per hour with all channels together
- alerts: threshold / missing / drift events
"""

from __future__ import annotations

from typing import Any

INDEXES: dict[str, list[list[tuple[str, int]]]] = {
    "sensor_readings": [
        [("sensor_id", 1), ("timestamp", -1)],
        [("timestamp", -1)],
        [("sensor_id", 1), ("anomaly.is_anomaly", 1), ("timestamp", -1)],
        [("anomaly.is_anomaly", 1), ("timestamp", -1)],
        [("device_id", 1), ("timestamp", -1)],
    ],
    "station_snapshots": [
        [("timestamp", -1)],
        [("device_id", 1), ("timestamp", -1)],
    ],
    "alerts": [
        [("timestamp", -1)],
        [("sensor_id", 1), ("timestamp", -1)],
        [("severity", 1), ("timestamp", -1)],
    ],
    "sensor_metadata": [
        [("sensor_id", 1)],
    ],
}


def reading_document(
    *,
    sensor_id: str,
    timestamp,
    value: float | None,
    is_missing: bool,
    anomaly: dict[str, Any],
    meta: dict[str, Any],
    device_id: str,
    location: str,
) -> dict[str, Any]:
    hour = timestamp.replace(minute=0, second=0, microsecond=0)
    day = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "device_id": device_id,
        "location": location,
        "sensor_id": sensor_id,
        "sensor_name": meta["name"],
        "channel_type": meta["channel_type"],
        "target": meta["target"],
        "unit": meta["unit"],
        "timestamp": timestamp,
        "hour_bucket": hour,
        "day_bucket": day,
        "value": value,
        "is_missing": is_missing,
        "anomaly": anomaly,
    }


def snapshot_document(
    *,
    timestamp,
    device_id: str,
    location: str,
    channels: dict[str, dict[str, Any]],
    environment: dict[str, Any],
    anomaly_count: int,
) -> dict[str, Any]:
    return {
        "device_id": device_id,
        "location": location,
        "timestamp": timestamp,
        "hour_bucket": timestamp.replace(minute=0, second=0, microsecond=0),
        "day_bucket": timestamp.replace(hour=0, minute=0, second=0, microsecond=0),
        "channels": channels,
        "environment": environment,
        "anomaly_count": anomaly_count,
    }


def alert_document(
    *,
    timestamp,
    sensor_id: str,
    severity: str,
    reasons: list[str],
    value: float | None,
    device_id: str,
) -> dict[str, Any]:
    return {
        "timestamp": timestamp,
        "sensor_id": sensor_id,
        "severity": severity,
        "reasons": reasons,
        "value": value,
        "device_id": device_id,
    }
