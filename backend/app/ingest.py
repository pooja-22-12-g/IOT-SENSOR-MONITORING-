"""Ingest UCI Air Quality rows into MongoDB and warm Redis."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import median
from typing import Any

from app.anomaly import evaluate_reading
from app.cache import DASHBOARD_KEY, LATEST_PREFIX, RedisCache
from app.db import MongoStore
from app.parser import iter_station_rows
from app.schema import alert_document, reading_document, snapshot_document
from app.sensor_catalog import DEVICE_ID, LOCATION, SENSORS


def _mad(values: list[float], center: float) -> float:
    if not values:
        return 0.0
    deviations = [abs(v - center) for v in values]
    return median(deviations)


def compute_ratio_baselines(csv_path: str) -> dict[str, dict[str, float]]:
    ratios: dict[str, list[float]] = defaultdict(list)
    for row in iter_station_rows(csv_path):
        channels = row["channels"]
        for sensor_id, meta in SENSORS.items():
            ref_id = meta.get("reference_sensor_id")
            if not ref_id:
                continue
            sensor_val = channels[sensor_id]["value"]
            ref_val = channels[ref_id]["value"]
            if sensor_val is None or ref_val is None or ref_val == 0:
                continue
            if meta.get("inverse_to_reference"):
                if sensor_val == 0:
                    continue
                ratios[sensor_id].append((1.0 / sensor_val) / ref_val)
            else:
                ratios[sensor_id].append(sensor_val / ref_val)
    baselines: dict[str, dict[str, float]] = {}
    for sensor_id, values in ratios.items():
        center = median(values)
        baselines[sensor_id] = {"median": center, "mad": _mad(values, center), "pairs": len(values)}
    return baselines


def ingest_csv(
    csv_path: str,
    mongo: MongoStore,
    cache: RedisCache | None = None,
    ttl: int = 60,
    limit: int | None = None,
) -> dict[str, Any]:
    db = mongo.require()
    readings = db["sensor_readings"]
    snapshots = db["station_snapshots"]
    alerts = db["alerts"]
    metadata = db["sensor_metadata"]

    baselines = compute_ratio_baselines(csv_path)
    previous: dict[str, float | None] = {sid: None for sid in SENSORS}
    inserted_readings = 0
    inserted_snapshots = 0
    inserted_alerts = 0
    last_timestamp: datetime | None = None
    latest_by_sensor: dict[str, dict[str, Any]] = {}

    for index, row in enumerate(iter_station_rows(csv_path)):
        if limit is not None and index >= limit:
            break
        timestamp = row["timestamp"]
        last_timestamp = timestamp
        channels_out: dict[str, dict[str, Any]] = {}
        anomaly_count = 0
        hour_docs = []
        alert_docs = []

        for sensor_id, meta in SENSORS.items():
            channel = row["channels"][sensor_id]
            ref_id = meta.get("reference_sensor_id")
            ref_val = row["channels"][ref_id]["value"] if ref_id else None
            baseline = baselines.get(sensor_id, {})
            anomaly = evaluate_reading(
                sensor_id,
                channel["value"],
                channel["is_missing"],
                previous_value=previous[sensor_id],
                reference_value=ref_val,
                ratio_median=baseline.get("median"),
                ratio_mad=baseline.get("mad"),
            )
            if not channel["is_missing"]:
                previous[sensor_id] = channel["value"]
            if anomaly["is_anomaly"]:
                anomaly_count += 1
                alert_docs.append(
                    alert_document(
                        timestamp=timestamp,
                        sensor_id=sensor_id,
                        severity=anomaly["severity"],
                        reasons=anomaly["reasons"],
                        value=channel["value"],
                        device_id=DEVICE_ID,
                    )
                )
            doc = reading_document(
                sensor_id=sensor_id,
                timestamp=timestamp,
                value=channel["value"],
                is_missing=channel["is_missing"],
                anomaly=anomaly,
                meta=meta,
                device_id=DEVICE_ID,
                location=LOCATION,
            )
            hour_docs.append(doc)
            latest_by_sensor[sensor_id] = doc
            channels_out[sensor_id] = {
                "value": channel["value"],
                "is_missing": channel["is_missing"],
                "unit": meta["unit"],
                "anomaly": anomaly,
            }

        readings.insert_many(hour_docs)
        inserted_readings += len(hour_docs)
        snapshots.insert_one(
            snapshot_document(
                timestamp=timestamp,
                device_id=DEVICE_ID,
                location=LOCATION,
                channels=channels_out,
                environment={
                    "T": channels_out["T"]["value"],
                    "RH": channels_out["RH"]["value"],
                    "AH": channels_out["AH"]["value"],
                },
                anomaly_count=anomaly_count,
            )
        )
        inserted_snapshots += 1
        if alert_docs:
            alerts.insert_many(alert_docs)
            inserted_alerts += len(alert_docs)
            if cache and cache.connected:
                for alert in alert_docs:
                    cache.push_alert(alert)

    for sensor_id, meta in SENSORS.items():
        metadata.replace_one(
            {"sensor_id": sensor_id},
            {
                "sensor_id": sensor_id,
                **meta,
                "drift_baseline": baselines.get(sensor_id),
                "last_ingested_at": last_timestamp,
            },
            upsert=True,
        )

    if cache and cache.connected:
        for sensor_id, doc in latest_by_sensor.items():
            cache.set_json(f"{LATEST_PREFIX}{sensor_id}", doc, ttl)
        cache.set_json(
            DASHBOARD_KEY,
            {
                "last_timestamp": last_timestamp,
                "reading_count": inserted_readings,
                "snapshot_count": inserted_snapshots,
                "alert_count": inserted_alerts,
            },
            ttl,
        )

    return {
        "readings": inserted_readings,
        "snapshots": inserted_snapshots,
        "alerts": inserted_alerts,
        "last_timestamp": last_timestamp.isoformat() if last_timestamp else None,
        "drift_baselines": {k: {**v, "median": v["median"], "mad": v["mad"]} for k, v in baselines.items()},
        "source": str(csv_path),
    }
