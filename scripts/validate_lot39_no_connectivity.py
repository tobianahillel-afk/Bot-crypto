#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor.py",
    "src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor_models.py",
    "src/crypto_quant_bot/microstructure/order_book_delta_sequence_reconstructor.py",
    "src/crypto_quant_bot/microstructure/order_book_delta_sequence_reconstructor_models.py",
    "src/crypto_quant_bot/microstructure/order_book_delta_sequence_reconstructor_validation.py",
    "scripts/run_lot39_order_book_delta_and_sequence_reconstructor.py",
    "scripts/run_lot39_order_book_delta_sequence_reconstructor.py",
    "scripts/validate_lot39.py",
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


def _import_name(node: ast.Import | ast.ImportFrom) -> str:
    if isinstance(node, ast.Import):
        return node.names[0].name
    return node.module or ""


def validate_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in FORBIDDEN_TEXT:
        if marker in text:
            raise RuntimeError(f"LOT39_FORBIDDEN_TEXT:{path}:{marker}")
    tree = ast.parse(text, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            imported = _import_name(node)
            forbidden = any(
                imported == root or imported.startswith(root + ".")
                for root in FORBIDDEN_IMPORT_ROOTS
            )
            if forbidden:
                raise RuntimeError(f"LOT39_FORBIDDEN_IMPORT:{path}:{imported}")
        if isinstance(node, ast.Call):
            func = node.func
            name: str | None = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name in FORBIDDEN_CALL_NAMES:
                raise RuntimeError(f"LOT39_FORBIDDEN_CALL:{path}:{name}")


def main() -> int:
    try:
        for relative in FILES:
            path = ROOT / relative
            if not path.exists():
                raise RuntimeError(f"LOT39_REQUIRED_FILE_MISSING:{relative}")
            validate_file(path)
        print("LOT39_NO_CONNECTIVITY_VALIDATED")
    except (OSError, SyntaxError, RuntimeError) as exc:
        print(f"LOT39 NO CONNECTIVITY: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
