#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src/crypto_quant_bot/data_governance"
CONFIG_PATH = ROOT / "config/data_governance/market_data_source_registry_v1.json"
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "httpx",
    "requests",
    "socket",
    "urllib",
    "websockets",
}


class ConnectivityBoundaryError(RuntimeError):
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


def validate() -> dict[str, object]:
    files = sorted(SOURCE_ROOT.rglob("*.py"))
    violations: list[str] = []
    for path in files:
        forbidden = sorted(imported_roots(path) & FORBIDDEN_IMPORT_ROOTS)
        if forbidden:
            violations.append(f"{path.relative_to(ROOT)} imports {forbidden}")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for source in config["sources"]:
        if source["enabled"] is not False or source["connection_status"] != "DISABLED":
            violations.append(f"{source['source_id']} is not disabled")
        if source["auth_mode"] != "NONE":
            violations.append(f"{source['source_id']} requests authentication")
    if violations:
        raise ConnectivityBoundaryError("; ".join(violations))
    return {
        "schema_version": "lot31-no-connectivity-validation-v1",
        "status": "PASS",
        "files_scanned": len(files),
        "source_count": len(config["sources"]),
        "forbidden_import_count": 0,
        "active_connection_count": 0,
        "authenticated_source_count": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (ConnectivityBoundaryError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"LOT31 CONNECTIVITY BOUNDARY: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
