from __future__ import annotations

from datetime import datetime
from typing import Any


def public_doc(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if doc is None:
        return None
    out = dict(doc)
    if "_id" in out:
        out["_id"] = str(out["_id"])
    for key, value in list(out.items()):
        if isinstance(value, datetime):
            out[key] = value.isoformat()
    return out


def public_list(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in (public_doc(doc) for doc in docs) if item is not None]
