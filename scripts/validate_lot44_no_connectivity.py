#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py",
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_validation.py",
    ROOT / "scripts/run_lot44_trades_and_aggressor_classification_schema.py",
    ROOT / "scripts/validate_lot44.py",
)
FORBIDDEN_ROOTS = {"socket", "requests", "httpx", "urllib", "websocket", "aiohttp", "ccxt"}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def main() -> int:
    for path in TARGETS:
        missing = FORBIDDEN_ROOTS & _imports(path)
        if missing:
            raise SystemExit(f"LOT44_CONNECTIVITY_FORBIDDEN:{path}:{sorted(missing)}")
    print("LOT44_NO_CONNECTIVITY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
