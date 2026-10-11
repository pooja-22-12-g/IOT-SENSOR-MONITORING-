from app.cache import DASHBOARD_KEY, LATEST_PREFIX


def test_redis_latest_and_alerts(cache, loaded):
    latest = cache.get_json(f"{LATEST_PREFIX}PT08_S1")
    assert latest is not None
    assert latest["sensor_id"] == "PT08_S1"
    summary = cache.get_json(DASHBOARD_KEY)
    assert summary["snapshot_count"] == 48
    alerts = cache.recent_alerts(5)
    assert isinstance(alerts, list)
