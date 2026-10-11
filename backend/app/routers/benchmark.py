from fastapi import APIRouter, Request

from app.benchmark import run_benchmarks

router = APIRouter(prefix="/api", tags=["benchmark"])


@router.get("/benchmark")
def benchmark(request: Request):
    return run_benchmarks(request.app.state.mongo)
