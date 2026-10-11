from fastapi import APIRouter, Depends, Query, Request

from app.db import MongoStore
from app.deps import mongo_store, redis_cache, replay_controller
from app.queries import dashboard_summary, latest_readings, sensor_health
from app.sensor_catalog import SENSORS, sensor_list

router = APIRouter(prefix="/api", tags=["sensors"])


@router.get("/sensors")
def list_sensors():
    return {"sensors": sensor_list()}


@router.get("/sensors/latest")
def latest(request: Request, mongo: MongoStore = Depends(mongo_store)):
    return {"readings": latest_readings(mongo, redis_cache(request))}


@router.get("/sensors/{sensor_id}/health")
def one_health(
    sensor_id: str,
    request: Request,
    mongo: MongoStore = Depends(mongo_store),
):
    if sensor_id not in SENSORS:
        return {"error": "unknown sensor_id", "sensor_id": sensor_id}
    cap = replay_controller(request).current_time()
    return sensor_health(mongo, sensor_id, cap)


@router.get("/dashboard")
def dashboard(
    request: Request,
    use_replay: bool = Query(default=True),
    mongo: MongoStore = Depends(mongo_store),
):
    cap = replay_controller(request).current_time() if use_replay else None
    return dashboard_summary(mongo, redis_cache(request), cap)
