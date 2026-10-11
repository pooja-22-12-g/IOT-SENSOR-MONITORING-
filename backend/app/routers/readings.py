from fastapi import APIRouter, Depends, Query, Request

from app.db import MongoStore
from app.deps import mongo_store, replay_controller
from app.queries import list_readings, parse_iso

router = APIRouter(prefix="/api", tags=["readings"])


@router.get("/compare")
def compare(
    request: Request,
    sensor_ids: str = Query(..., description="Comma-separated sensor IDs"),
    limit: int = Query(default=168, ge=1, le=2000),
    mongo: MongoStore = Depends(mongo_store),
):
    end_dt = replay_controller(request).current_time()
    series = {}
    for sensor_id in [item.strip() for item in sensor_ids.split(",") if item.strip()]:
        series[sensor_id] = list_readings(
            mongo, sensor_id=sensor_id, start=None, end=end_dt, limit=limit
        )
    return {"series": series}


@router.get("/readings")
def readings(
    request: Request,
    sensor_id: str | None = Query(default=None),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    limit: int = Query(default=240, ge=1, le=2000),
    mongo: MongoStore = Depends(mongo_store),
):
    end_dt = parse_iso(end) or replay_controller(request).current_time()
    return {
        "readings": list_readings(
            mongo,
            sensor_id=sensor_id,
            start=parse_iso(start),
            end=end_dt,
            limit=limit,
        )
    }
