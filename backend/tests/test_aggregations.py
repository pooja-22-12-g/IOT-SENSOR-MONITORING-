from datetime import datetime

from app.aggregations import aggregate_in_memory


def test_hourly_buckets_from_real_style_docs():
    hour = datetime(2004, 3, 10, 18, 0, 0)
    readings = [
        {
            "sensor_id": "PT08_S1",
            "hour_bucket": hour,
            "value": 1360.0,
            "is_missing": False,
            "anomaly": {"is_anomaly": False},
        },
        {
            "sensor_id": "PT08_S1",
            "hour_bucket": hour,
            "value": 1292.0,
            "is_missing": False,
            "anomaly": {"is_anomaly": True},
        },
        {
            "sensor_id": "PT08_S1",
            "hour_bucket": hour,
            "value": None,
            "is_missing": True,
            "anomaly": {"is_anomaly": True},
        },
    ]
    stats = aggregate_in_memory(readings, "hour_bucket")
    assert len(stats) == 1
    assert stats[0]["count"] == 2
    assert stats[0]["min"] == 1292.0
    assert stats[0]["max"] == 1360.0
    assert stats[0]["anomaly_count"] == 1
    assert stats[0]["avg"] == (1360.0 + 1292.0) / 2
