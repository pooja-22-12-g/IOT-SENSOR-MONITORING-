from __future__ import annotations

import sys
from pathlib import Path

import fakeredis
import mongomock
import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.cache import RedisCache, attach_fake  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import MongoStore, attach_mock  # noqa: E402
from app.ingest import ingest_csv  # noqa: E402
from app.main import app  # noqa: E402
from app.replay import ReplayController  # noqa: E402

SAMPLE_CSV = ROOT / "data" / "sample_48h.csv"


@pytest.fixture
def sample_csv() -> Path:
    return SAMPLE_CSV


@pytest.fixture
def mongo() -> MongoStore:
    store = MongoStore()
    return attach_mock(store, mongomock.MongoClient().iot_air_quality)


@pytest.fixture
def cache() -> RedisCache:
    fake = fakeredis.FakeRedis(decode_responses=True)
    return attach_fake(RedisCache(), fake)


@pytest.fixture
def loaded(mongo: MongoStore, cache: RedisCache, sample_csv: Path):
    mongo.ensure_indexes()
    summary = ingest_csv(str(sample_csv), mongo, cache, ttl=60)
    return summary


@pytest.fixture
def client(mongo: MongoStore, cache: RedisCache, loaded) -> TestClient:
    app.state.preloaded = True
    app.state.settings = get_settings()
    app.state.mongo = mongo
    app.state.cache = cache
    app.state.replay = ReplayController(mongo, cache)
    with TestClient(app) as test_client:
        yield test_client
    app.state.preloaded = False
