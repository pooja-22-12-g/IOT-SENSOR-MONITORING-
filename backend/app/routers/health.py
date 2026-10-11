from fastapi import APIRouter, Request

from app.sensor_catalog import sensor_list

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/status")
def api_status(request: Request):
    mongo = request.app.state.mongo
    cache = request.app.state.cache
    return {
        "mongo_connected": mongo.connected,
        "mongo_error": mongo.error,
        "redis_connected": cache.connected,
        "redis_error": cache.error,
        "sensor_count": len(sensor_list()),
    }
