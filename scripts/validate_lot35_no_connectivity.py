#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "src/crypto_quant_bot/data_governance/candle_trade_book_reconciliation.py",
    ROOT / "src/crypto_quant_bot/data_governance/candle_trade_book_reconciliation_models.py",
    ROOT / "src/crypto_quant_bot/data_governance/candle_trade_book_reconciliation_validation.py",
)
FORBIDDEN_IMPORTS = {"socket", "requests", "httpx", "urllib", "websocket", "aiohttp", "ccxt"}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def main() -> int:
    offending = {
        str(path): sorted(imported_roots(path) & FORBIDDEN_IMPORTS)
        for path in TARGETS
    }
    offending = {path: names for path, names in offending.items() if names}
    if offending:
        print(f"LOT35 CONNECTIVITY VALIDATION: FAIL {offending}", file=sys.stderr)
        return 1
    print("LOT35 CONNECTIVITY VALIDATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
