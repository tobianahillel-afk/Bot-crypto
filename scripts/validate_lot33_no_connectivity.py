#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src/crypto_quant_bot/data_governance"
CONFIG_PATH = ROOT / "config/data_governance/timestamp_clock_timezone_governance_v1.json"
FORBIDDEN_IMPORT_ROOTS = {"aiohttp", "httpx", "requests", "socket", "urllib", "websockets"}
FORBIDDEN_CONFIG_TOKENS = ("api_key", "secret", "password", "endpoint", "url", "token")


class Lot33ConnectivityBoundaryError(RuntimeError):
    pass


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def walk_keys(value: object) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.append(str(key).lower())
            keys.extend(walk_keys(nested))
    elif isinstance(value, list):
        for item in value:
            keys.extend(walk_keys(item))
    return keys


def validate() -> dict[str, object]:
    files = sorted(SOURCE_ROOT.rglob("*.py"))
    violations: list[str] = []
    for path in files:
        forbidden = sorted(imported_roots(path) & FORBIDDEN_IMPORT_ROOTS)
        if forbidden:
            violations.append(f"{path.relative_to(ROOT)} imports {forbidden}")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for key in walk_keys(config):
        if any(token in key for token in FORBIDDEN_CONFIG_TOKENS):
            violations.append(f"forbidden configuration key: {key}")
    if violations:
        raise Lot33ConnectivityBoundaryError("; ".join(violations))
    return {
        "schema_version": "lot33-no-connectivity-validation-v1",
        "status": "PASS",
        "files_scanned": len(files),
        "record_count": len(config["records"]),
        "forbidden_import_count": 0,
        "forbidden_configuration_key_count": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (Lot33ConnectivityBoundaryError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"LOT33 CONNECTIVITY BOUNDARY: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
