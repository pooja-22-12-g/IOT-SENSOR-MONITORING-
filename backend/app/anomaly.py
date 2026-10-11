"""Threshold, missing-value, spike, and drift checks."""

from __future__ import annotations

from typing import Any

from app.sensor_catalog import SENSORS

SPIKE_FACTOR = 0.45


def classify_threshold(sensor_id: str, value: float | None, is_missing: bool) -> dict[str, Any]:
    reasons: list[str] = []
    severity = "ok"
    if is_missing or value is None:
        return {
            "is_anomaly": True,
            "severity": "critical",
            "reasons": ["missing_value_sentinel"],
        }

    meta = SENSORS[sensor_id]
    if meta.get("crit_high") is not None and value >= meta["crit_high"]:
        reasons.append("above_critical_high")
        severity = "critical"
    elif meta.get("warn_high") is not None and value >= meta["warn_high"]:
        reasons.append("above_warning_high")
        severity = "warning"

    if meta.get("crit_low") is not None and value <= meta["crit_low"]:
        reasons.append("below_critical_low")
        severity = "critical"
    elif meta.get("warn_low") is not None and value <= meta["warn_low"]:
        if severity == "ok":
            severity = "warning"
        reasons.append("below_warning_low")

    return {
        "is_anomaly": bool(reasons),
        "severity": severity,
        "reasons": reasons,
    }


def detect_spike(previous: float | None, current: float | None) -> bool:
    if previous is None or current is None:
        return False
    baseline = abs(previous)
    if baseline < 1e-9:
        return False
    return abs(current - previous) / baseline >= SPIKE_FACTOR


def detect_drift(
    sensor_id: str,
    sensor_value: float | None,
    reference_value: float | None,
    ratio_median: float | None,
    ratio_mad: float | None,
) -> bool:
    """Flag drift when the sensor/reference ratio is far from the historical median.

    PT08.S3 is inversely related to NOx in this device, so the ratio uses 1/sensor.
    """
    meta = SENSORS[sensor_id]
    if sensor_value is None or reference_value is None or reference_value == 0:
        return False
    if ratio_median is None or ratio_mad is None:
        return False
    if meta.get("inverse_to_reference"):
        if sensor_value == 0:
            return False
        ratio = (1.0 / sensor_value) / reference_value
    else:
        ratio = sensor_value / reference_value
    scale = max(ratio_mad, abs(ratio_median) * 0.05, 1e-9)
    return abs(ratio - ratio_median) > 6.0 * scale


def evaluate_reading(
    sensor_id: str,
    value: float | None,
    is_missing: bool,
    previous_value: float | None = None,
    reference_value: float | None = None,
    ratio_median: float | None = None,
    ratio_mad: float | None = None,
) -> dict[str, Any]:
    result = classify_threshold(sensor_id, value, is_missing)
    reasons = list(result["reasons"])
    severity = result["severity"]

    if detect_spike(previous_value, value):
        reasons.append("sudden_spike")
        if severity == "ok":
            severity = "warning"

    if detect_drift(sensor_id, value, reference_value, ratio_median, ratio_mad):
        reasons.append("sensor_drift")
        if severity != "critical":
            severity = "warning"

    return {
        "is_anomaly": bool(reasons),
        "severity": "ok" if not reasons else severity,
        "reasons": reasons,
    }
