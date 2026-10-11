from __future__ import annotations

from fastapi import HTTPException, Request

from app.cache import RedisCache
from app.db import MongoStore
from app.replay import ReplayController


def mongo_store(request: Request) -> MongoStore:
    store: MongoStore = request.app.state.mongo
    if not store.connected:
        raise HTTPException(
            status_code=503,
            detail={
                "mongo_connected": False,
                "error": store.error or "MongoDB is not connected",
            },
        )
    return store


def redis_cache(request: Request) -> RedisCache:
    return request.app.state.cache


def replay_controller(request: Request) -> ReplayController:
    return request.app.state.replay
