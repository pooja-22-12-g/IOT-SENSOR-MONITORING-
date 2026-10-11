from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cache import RedisCache
from app.config import get_settings
from app.db import MongoStore
from app.replay import ReplayController
from app.routers import alerts, benchmark, health, readings, replay, sensors, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    if getattr(app.state, "preloaded", False):
        yield
        return
    mongo = MongoStore()
    cache = RedisCache()
    mongo.connect(settings)
    cache.connect(settings)
    app.state.mongo = mongo
    app.state.cache = cache
    app.state.replay = ReplayController(mongo, cache)
    yield
    mongo.close()
    cache.close()


app = FastAPI(
    title="Real-Time IoT Sensor Monitoring System",
    description="NoSQL monitoring API for the UCI Air Quality dataset.",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in settings.cors_origins.split(",") if item.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sensors.router)
app.include_router(readings.router)
app.include_router(stats.router)
app.include_router(alerts.router)
app.include_router(benchmark.router)
app.include_router(replay.router)


@app.get("/")
def root():
    return {
        "name": "Real-Time IoT Sensor Monitoring System",
        "docs": "/docs",
        "dataset": "UCI Air Quality",
    }
