from fastapi import APIRouter, Depends, Query, Request

from app.db import MongoStore
from app.deps import mongo_store, redis_cache, replay_controller
from app.queries import bucket_stats, parse_iso

router = APIRouter(prefix="/api", tags=["stats"])


def _stats(request: Request, sensor_id, start, end, bucket_field, mongo):
    settings = request.app.state.settings
    end_dt = parse_iso(end) or replay_controller(request).current_time()
    return {
        "cache_ttl_seconds": settings.cache_ttl_seconds,
        "stats": bucket_stats(
            mongo,
            redis_cache(request),
            sensor_id=sensor_id,
            start=parse_iso(start),
            end=end_dt,
            bucket_field=bucket_field,
            ttl=settings.cache_ttl_seconds,
        ),
    }


@router.get("/stats/hourly")
def hourly(
    request: Request,
    sensor_id: str | None = Query(default=None),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    mongo: MongoStore = Depends(mongo_store),
):
    return _stats(request, sensor_id, start, end, "hour_bucket", mongo)


@router.get("/stats/daily")
def daily(
    request: Request,
    sensor_id: str | None = Query(default=None),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    mongo: MongoStore = Depends(mongo_store),
):
    return _stats(request, sensor_id, start, end, "day_bucket", mongo)
