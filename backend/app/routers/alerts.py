from fastapi import APIRouter, Depends, Query, Request

from app.db import MongoStore
from app.deps import mongo_store, redis_cache
from app.queries import alerts as query_alerts

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts")
def alerts(
    request: Request,
    sensor_id: str | None = Query(default=None),
    limit: int = Query(default=40, ge=1, le=500),
    mongo: MongoStore = Depends(mongo_store),
):
    return {"alerts": query_alerts(mongo, redis_cache(request), sensor_id=sensor_id, limit=limit)}
