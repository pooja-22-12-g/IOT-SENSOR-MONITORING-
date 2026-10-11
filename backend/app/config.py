from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")

    mongodb_uri: str = "mongodb://127.0.0.1:27017"
    mongodb_db: str = "iot_air_quality"
    redis_url: str = "redis://127.0.0.1:6379/0"
    dataset_path: str = str(ROOT / "data" / "AirQualityUCI.csv")
    cache_ttl_seconds: int = 60
    replay_interval_seconds: int = 2
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    readings_collection: str = "sensor_readings"
    snapshots_collection: str = "station_snapshots"
    alerts_collection: str = "alerts"
    metadata_collection: str = "sensor_metadata"


def get_settings() -> Settings:
    return Settings()
