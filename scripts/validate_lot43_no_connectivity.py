#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine.py",
    "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_models.py",
    "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_validation.py",
    "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_analysis.py",
    "scripts/run_lot43_book_resilience_and_replenishment_engine.py",
    "scripts/validate_lot43.py",
)
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "boto3",
    "ccxt",
    "http.client",
    "httpx",
    "requests",
    "socket",
    "urllib" + ".request",
    "urllib3",
    "websocket",
    "websockets",
}
FORBIDDEN_CALL_NAMES = {
    "connect",
    "create_connection",
    "getaddrinfo",
    "request",
    "socket",
    "urlopen",
}
FORBIDDEN_TEXT = (
    "http" + "://",
    "https" + "://",
    "wss" + "://",
    "API_KEY",
    "API_SECRET",
    "KRAKEN_KEY",
    "KRAKEN_SECRET",
)


def _import_names(node: ast.Import | ast.ImportFrom) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    return (node.module or "",)


def validate_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in FORBIDDEN_TEXT:
        if marker in text:
            raise RuntimeError(f"LOT43_FORBIDDEN_TEXT:{path}:{marker}")
    tree = ast.parse(text, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            for imported in _import_names(node):
                if any(
                    imported == root or imported.startswith(root + ".")
                    for root in FORBIDDEN_IMPORT_ROOTS
                ):
                    raise RuntimeError(f"LOT43_FORBIDDEN_IMPORT:{path}:{imported}")
        if isinstance(node, ast.Call):
            function = node.func
            name: str | None = None
            if isinstance(function, ast.Name):
                name = function.id
            elif isinstance(function, ast.Attribute):
                name = function.attr
            if name in FORBIDDEN_CALL_NAMES:
                raise RuntimeError(f"LOT43_FORBIDDEN_CALL:{path}:{name}")


def main() -> int:
    try:
        for relative in FILES:
            path = ROOT / relative
            if not path.exists():
                raise RuntimeError(f"LOT43_REQUIRED_FILE_MISSING:{relative}")
            validate_file(path)
        print("LOT43_NO_CONNECTIVITY_VALIDATED")
    except (OSError, SyntaxError, RuntimeError) as exc:
        print(f"LOT43 NO CONNECTIVITY: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
