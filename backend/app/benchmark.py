"""Query timing against the live or injected MongoDB database.

Timings are measured with time.perf_counter around real collection operations.
This module never invents durations.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from app.aggregations import time_bucket_pipeline
from app.db import MongoStore


def _time_call(name: str, fn: Callable[[], Any]) -> dict[str, Any]:
    started = time.perf_counter()
    result = fn()
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    count = result if isinstance(result, int) else len(result)
    return {"name": name, "elapsed_ms": round(elapsed_ms, 3), "result_count": count}


def run_benchmarks(mongo: MongoStore) -> dict[str, Any]:
    if not mongo.connected:
        return {
            "mongo_connected": False,
            "error": mongo.error or "MongoDB is not connected",
            "results": [],
        }

    db = mongo.require()
    readings = db["sensor_readings"]
    alerts = db["alerts"]

    def latest_one() -> list:
        return list(readings.find({"sensor_id": "PT08_S1"}).sort("timestamp", -1).limit(1))

    def range_query() -> list:
        return list(
            readings.find({"sensor_id": "PT08_S1"}).sort("timestamp", -1).limit(168)
        )

    def anomaly_query() -> list:
        return list(alerts.find({}).sort("timestamp", -1).limit(50))

    def hourly_agg() -> list:
        pipeline = time_bucket_pipeline(
            sensor_id="PT08_S1",
            start=None,
            end=None,
            bucket_field="hour_bucket",
        )
        return list(readings.aggregate(pipeline))

    def daily_agg() -> list:
        pipeline = time_bucket_pipeline(
            sensor_id="PT08_S1",
            start=None,
            end=None,
            bucket_field="day_bucket",
        )
        return list(readings.aggregate(pipeline))

    results = [
        _time_call("latest_reading_by_sensor", latest_one),
        _time_call("last_168_hours_by_sensor", range_query),
        _time_call("recent_alerts", anomaly_query),
        _time_call("hourly_aggregation_PT08_S1", hourly_agg),
        _time_call("daily_aggregation_PT08_S1", daily_agg),
    ]
    return {"mongo_connected": True, "error": None, "results": results}
