#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src/crypto_quant_bot/data_governance"
CONFIG_PATH = ROOT / "config/data_governance/instrument_symbol_contract_normalization_v1.json"
SOURCE_REGISTRY_PATH = ROOT / "data/audit/source_registry_lot31.json"
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "httpx",
    "requests",
    "socket",
    "urllib",
    "websockets",
}
FORBIDDEN_CONFIG_KEYS = {
    "api_key",
    "api_secret",
    "auth_token",
    "credentials",
    "endpoint_url",
    "password",
    "private_key",
}


class Lot32ConnectivityBoundaryError(RuntimeError):
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


def walk_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = {str(key).lower() for key in value}
        for nested in value.values():
            keys.update(walk_keys(nested))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for nested in value:
            keys.update(walk_keys(nested))
        return keys
    return set()


def validate() -> dict[str, object]:
    files = sorted(SOURCE_ROOT.rglob("*.py"))
    violations: list[str] = []
    for path in files:
        forbidden = sorted(imported_roots(path) & FORBIDDEN_IMPORT_ROOTS)
        if forbidden:
            violations.append(f"{path.relative_to(ROOT)} imports {forbidden}")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    forbidden_keys = sorted(walk_keys(config) & FORBIDDEN_CONFIG_KEYS)
    if forbidden_keys:
        violations.append(f"Lot 32 config contains forbidden keys: {forbidden_keys}")
    source_registry = json.loads(SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    for source in source_registry["sources"]:
        if source["enabled"] is not False or source["connection_status"] != "DISABLED":
            violations.append(f"{source['source_id']} is not disabled")
        if source["auth_mode"] != "NONE":
            violations.append(f"{source['source_id']} requests authentication")
    if violations:
        raise Lot32ConnectivityBoundaryError("; ".join(violations))
    return {
        "schema_version": "lot32-no-connectivity-validation-v1",
        "status": "PASS",
        "files_scanned": len(files),
        "instrument_count": len(config["instruments"]),
        "source_count": len(source_registry["sources"]),
        "forbidden_import_count": 0,
        "forbidden_config_key_count": 0,
        "active_connection_count": 0,
        "authenticated_source_count": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (
        Lot32ConnectivityBoundaryError,
        OSError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        print(f"LOT32 CONNECTIVITY BOUNDARY: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
