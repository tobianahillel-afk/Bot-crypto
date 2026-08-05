from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5


class Lot26ValidationError(ValueError):
    """Fail-closed validation error for Lot 26."""


def canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def checksum(payload: object) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def parse_utc(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise Lot26ValidationError(f"MTF_TIMEZONE_INVALID:{field_name}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise Lot26ValidationError(f"MTF_TIMEZONE_INVALID:{field_name}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise Lot26ValidationError(f"MTF_TIMEZONE_INVALID:{field_name}")
    return parsed


def load_json_object(path: Path | str) -> dict[str, Any]:
    target = Path(path)
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Lot26ValidationError(f"expected JSON object: {target}")
    return payload


def require_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise Lot26ValidationError(f"{key} must be a mapping")
    return value


def stable_id(kind: str, payload: object) -> str:
    return str(uuid5(NAMESPACE_URL, f"lot26:{kind}:{checksum(payload)}"))
