from fastapi.testclient import TestClient

from app.cache import RedisCache
from app.config import get_settings
from app.db import MongoStore
from app.main import app
from app.replay import ReplayController


def test_status_reports_real_disconnection_when_stores_are_down():
    mongo = MongoStore()
    cache = RedisCache()
    mongo.connected = False
    mongo.error = "simulated unreachable server"
    cache.connected = False
    cache.error = "simulated unreachable redis"
    app.state.preloaded = True
    app.state.settings = get_settings()
    app.state.mongo = mongo
    app.state.cache = cache
    app.state.replay = ReplayController(mongo, cache)
    with TestClient(app) as client:
        status = client.get("/api/status")
        assert status.status_code == 200
        body = status.json()
        assert body["mongo_connected"] is False
        assert body["redis_connected"] is False
        readings = client.get("/api/readings")
        assert readings.status_code == 503
        assert readings.json()["detail"]["mongo_connected"] is False
    app.state.preloaded = False
