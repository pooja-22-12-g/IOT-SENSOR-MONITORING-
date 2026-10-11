"""Describe the UCI Air Quality CSV without requiring MongoDB or Redis."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.parser import iter_station_rows  # noqa: E402
from app.sensor_catalog import SENSORS  # noqa: E402


def percentile(sorted_vals: list[float], p: float) -> float | None:
    if not sorted_vals:
        return None
    idx = int(round((p / 100) * (len(sorted_vals) - 1)))
    return sorted_vals[idx]


def main() -> None:
    settings = get_settings()
    path = Path(settings.dataset_path)
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    values: dict[str, list[float]] = defaultdict(list)
    missing: dict[str, int] = defaultdict(int)
    rows = 0
    first = last = None
    for row in iter_station_rows(path):
        rows += 1
        first = first or row["timestamp"]
        last = row["timestamp"]
        for sensor_id, channel in row["channels"].items():
            if channel["is_missing"]:
                missing[sensor_id] += 1
            else:
                values[sensor_id].append(channel["value"])

    report = {
        "file": str(path),
        "hourly_rows": rows,
        "first_timestamp": first.isoformat() if first else None,
        "last_timestamp": last.isoformat() if last else None,
        "channels": {},
    }
    for sensor_id, meta in SENSORS.items():
        vals = sorted(values[sensor_id])
        report["channels"][sensor_id] = {
            "column": meta["column"],
            "valid": len(vals),
            "missing": missing[sensor_id],
            "min": vals[0] if vals else None,
            "p50": percentile(vals, 50),
            "p95": percentile(vals, 95),
            "p99": percentile(vals, 99),
            "max": vals[-1] if vals else None,
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
