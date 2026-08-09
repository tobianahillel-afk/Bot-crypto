#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ROOT / "src/crypto_quant_bot/microstructure/order_book_l2_snapshot_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/order_book_l2_snapshot_engine_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/order_book_l2_snapshot_engine_validation.py",
    ROOT / "scripts/run_lot38_order_book_l2_snapshot_engine.py",
    ROOT / "scripts/validate_lot38.py",
)
FORBIDDEN_ROOTS = {"aiohttp", "http", "httpx", "requests", "socket", "urllib", "websockets"}


def imported_root(node: ast.AST) -> str | None:
    if isinstance(node, ast.Import):
        return node.names[0].name.split(".")[0] if node.names else None
    if isinstance(node, ast.ImportFrom) and node.module:
        return node.module.split(".")[0]
    return None


def validate() -> None:
    for path in FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            root = imported_root(node)
            if root in FORBIDDEN_ROOTS:
                raise RuntimeError(f"forbidden network import in {path.relative_to(ROOT)}: {root}")


def main() -> int:
    try:
        validate()
    except (OSError, SyntaxError, RuntimeError) as exc:
        print(f"LOT38 CONNECTIVITY VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    print("LOT38 CONNECTIVITY VALIDATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
