from fastapi import APIRouter, Depends, Request

from app.db import MongoStore
from app.deps import mongo_store, replay_controller

router = APIRouter(prefix="/api/replay", tags=["replay"])


@router.get("/status")
def status(request: Request, mongo: MongoStore = Depends(mongo_store)):
    return replay_controller(request).status()


@router.post("/start")
def start(request: Request, mongo: MongoStore = Depends(mongo_store)):
    return replay_controller(request).start()


@router.post("/stop")
def stop(request: Request, mongo: MongoStore = Depends(mongo_store)):
    return replay_controller(request).stop()


@router.post("/tick")
def tick(request: Request, mongo: MongoStore = Depends(mongo_store)):
    return replay_controller(request).tick()
