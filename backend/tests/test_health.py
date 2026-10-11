from app.health import health_report


def test_empty_window_is_unknown():
    report = health_report([])
    assert report["status"] == "unknown"
    assert report["health_score"] is None


def test_healthy_complete_series():
    readings = [
        {"is_missing": False, "value": 10.0, "anomaly": {"is_anomaly": False, "reasons": []}}
        for _ in range(20)
    ]
    report = health_report(readings)
    assert report["health_score"] == 100.0
    assert report["status"] == "healthy"


def test_missing_and_drift_lower_score():
    readings = [
        {
            "is_missing": True,
            "value": None,
            "anomaly": {"is_anomaly": True, "reasons": ["missing_value_sentinel", "sensor_drift"]},
        }
        for _ in range(20)
    ]
    report = health_report(readings)
    assert report["status"] == "degraded"
    assert report["health_score"] < 60
