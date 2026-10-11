"""Load the UCI CSV into MongoDB and warm Redis. Fails loudly if Mongo is down."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cache import RedisCache  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import MongoStore  # noqa: E402
from app.ingest import ingest_csv  # noqa: E402


def main() -> None:
    settings = get_settings()
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(settings.dataset_path)
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

    mongo = MongoStore()
    cache = RedisCache()
    mongo.connect(settings)
    if not mongo.connected:
        print(json.dumps({"ok": False, "mongo_connected": False, "error": mongo.error}, indent=2))
        sys.exit(1)
    cache.connect(settings)
    mongo.ensure_indexes()
    result = ingest_csv(str(csv_path), mongo, cache, ttl=settings.cache_ttl_seconds, limit=limit)
    result["ok"] = True
    result["mongo_connected"] = True
    result["redis_connected"] = cache.connected
    result["redis_error"] = cache.error
    print(json.dumps(result, indent=2, default=str))
    mongo.close()
    cache.close()


if __name__ == "__main__":
    main()
