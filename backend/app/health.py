"""Sensor health and drift scores from recent readings (0-100)."""

from __future__ import annotations

from typing import Any, Iterable


def _safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def health_report(readings: Iterable[dict[str, Any]], window: int = 168) -> dict[str, Any]:
    """Compute completeness, stability, drift, and overall health.

    window default is 168 hourly samples = 7 days.
    """
    items = list(readings)[:window]
    total = len(items)
    if total == 0:
        return {
            "sample_count": 0,
            "completeness": None,
            "stability": None,
            "drift_penalty": None,
            "health_score": None,
            "missing_rate": None,
            "anomaly_rate": None,
            "drift_rate": None,
            "status": "unknown",
        }

    missing = sum(1 for row in items if row.get("is_missing"))
    anomalies = sum(1 for row in items if (row.get("anomaly") or {}).get("is_anomaly"))
    drift = sum(
        1
        for row in items
        if "sensor_drift" in ((row.get("anomaly") or {}).get("reasons") or [])
    )
    completeness = 1.0 - (missing / total)
    stability = 1.0 - (anomalies / total)
    drift_penalty = drift / total
    score = max(0.0, min(100.0, 100.0 * (0.45 * completeness + 0.40 * stability + 0.15 * (1.0 - drift_penalty))))

    if score >= 80:
        status = "healthy"
    elif score >= 60:
        status = "watch"
    else:
        status = "degraded"

    return {
        "sample_count": total,
        "completeness": round(completeness, 4),
        "stability": round(stability, 4),
        "drift_penalty": round(drift_penalty, 4),
        "health_score": round(score, 2),
        "missing_rate": round(missing / total, 4),
        "anomaly_rate": round(anomalies / total, 4),
        "drift_rate": round(drift / total, 4),
        "status": status,
        "mean_value": _safe_mean([row["value"] for row in items if row.get("value") is not None]),
    }
