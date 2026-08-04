#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRM = ROOT / "src" / "crypto_quant_bot" / "market_analysis" / "trend_range_momentum.py"
READINESS = ROOT / "scripts" / "validate_pre_lot26_readiness.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text and old not in text:
        return
    if old not in text:
        raise RuntimeError(f"expected source not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    replace_once(
        TRM,
        '    if "INSUFFICIENT_DATA" in {trend_state, range_state, momentum_state}:\n',
        '    if any(\n'
        '        "INSUFFICIENT_DATA" in state\n'
        '        for state in (trend_state, range_state, momentum_state)\n'
        '    ):\n',
    )
    replace_once(
        READINESS,
        '        "src/crypto_quant_bot/core/enums.py",\n',
        '        "src/crypto_quant_bot/core/enums.py",\n'
        '        "src/crypto_quant_bot/market_analysis/trend_range_momentum.py",\n',
    )
    print("P0.6 TRM insufficient-data fix applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
