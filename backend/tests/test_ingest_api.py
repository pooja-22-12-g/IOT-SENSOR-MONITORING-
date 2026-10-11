from app.sensor_catalog import SENSORS


def test_ingest_sample_counts(loaded):
    # 48 hours * 13 channels
    assert loaded["snapshots"] == 48
    assert loaded["readings"] == 48 * len(SENSORS)
    assert loaded["last_timestamp"] == "2004-03-12T17:00:00"


def test_status_with_injected_stores(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    body = response.json()
    assert body["mongo_connected"] is True
    assert body["redis_connected"] is True


def test_dashboard_and_filters(client):
    sensors = client.get("/api/sensors")
    assert sensors.status_code == 200
    assert len(sensors.json()["sensors"]) == 13

    latest = client.get("/api/sensors/latest")
    assert latest.status_code == 200
    assert len(latest.json()["readings"]) == 13

    readings = client.get("/api/readings", params={"sensor_id": "PT08_S1", "limit": 10})
    assert readings.status_code == 200
    rows = readings.json()["readings"]
    assert len(rows) == 10
    assert all(row["sensor_id"] == "PT08_S1" for row in rows)

    hourly = client.get("/api/stats/hourly", params={"sensor_id": "PT08_S1"})
    assert hourly.status_code == 200
    assert len(hourly.json()["stats"]) >= 1

    daily = client.get("/api/stats/daily", params={"sensor_id": "PT08_S1"})
    assert daily.status_code == 200
    assert len(daily.json()["stats"]) >= 1

    alerts = client.get("/api/alerts")
    assert alerts.status_code == 200
    assert "alerts" in alerts.json()

    health = client.get("/api/sensors/PT08_S1/health")
    assert health.status_code == 200
    assert health.json()["sensor_id"] == "PT08_S1"
    assert health.json()["sample_count"] > 0


def test_replay_advances_virtual_now(client):
    started = client.post("/api/replay/start")
    assert started.status_code == 200
    assert started.json()["running"] is True
    assert started.json()["virtual_now"] == "2004-03-10T18:00:00"

    ticked = client.post("/api/replay/tick")
    assert ticked.json()["virtual_now"] == "2004-03-10T19:00:00"

    stopped = client.post("/api/replay/stop")
    assert stopped.json()["running"] is False


def test_compare_two_sensors(client):
    response = client.get("/api/compare", params={"sensor_ids": "PT08_S1,CO_GT", "limit": 20})
    assert response.status_code == 200
    series = response.json()["series"]
    assert "PT08_S1" in series and "CO_GT" in series
    assert len(series["PT08_S1"]) == 20


def test_benchmark_runs_against_injected_mongo(client):
    response = client.get("/api/benchmark")
    assert response.status_code == 200
    body = response.json()
    assert body["mongo_connected"] is True
    names = {item["name"] for item in body["results"]}
    assert "hourly_aggregation_PT08_S1" in names
    for item in body["results"]:
        assert "elapsed_ms" in item
        assert item["elapsed_ms"] >= 0
