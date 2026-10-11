"""Parse the official UCI Air Quality CSV (semicolon, comma decimals, -200 missing)."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from app.sensor_catalog import MISSING_SENTINEL, SENSORS


def parse_number(raw: str) -> float | None:
    text = (raw or "").strip()
    if not text:
        return None
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def parse_timestamp(date_str: str, time_str: str) -> datetime:
    # Original format: 10/03/2004 and 18.00.00
    return datetime.strptime(f"{date_str.strip()} {time_str.strip()}", "%d/%m/%Y %H.%M.%S")


def is_missing(value: float | None) -> bool:
    return value is None or value == MISSING_SENTINEL


def iter_station_rows(csv_path: str | Path) -> Iterator[dict[str, Any]]:
    path = Path(csv_path)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        header = next(reader)
        index = {name: i for i, name in enumerate(header)}
        required = ["Date", "Time", *[meta["column"] for meta in SENSORS.values()]]
        missing_cols = [col for col in required if col not in index]
        if missing_cols:
            raise ValueError(f"CSV is missing expected UCI columns: {missing_cols}")

        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue
            date_s = row[index["Date"]].strip()
            time_s = row[index["Time"]].strip()
            if not date_s or not time_s:
                continue
            timestamp = parse_timestamp(date_s, time_s)
            channels: dict[str, dict[str, Any]] = {}
            for sensor_id, meta in SENSORS.items():
                raw = row[index[meta["column"]]] if index[meta["column"]] < len(row) else ""
                number = parse_number(raw)
                missing = is_missing(number)
                channels[sensor_id] = {
                    "value": None if missing else number,
                    "is_missing": missing,
                    "raw": number,
                }
            yield {"timestamp": timestamp, "channels": channels}
