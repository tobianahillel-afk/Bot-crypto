#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]



def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def main() -> int:
    required = [
        "src/crypto_quant_bot/contracts/pivots.py",
        "src/crypto_quant_bot/contracts/zones.py",
        "src/crypto_quant_bot/pivots/fractal.py",
        "src/crypto_quant_bot/pivots/zones.py",
        "tests/fixtures/btc_eur_ohlcvt_1m_180_pivots.csv",
        "data/silver/btc_eur_5m_ohlcvt_lot3.jsonl",
        "data/silver/btc_eur_15m_ohlcvt_lot3.jsonl",
        "data/gold/btc_eur_5m_pivots_lot3.jsonl",
        "data/gold/btc_eur_15m_pivots_lot3.jsonl",
        "data/gold/btc_eur_5m_price_zones_lot3.jsonl",
        "data/gold/btc_eur_15m_price_zones_lot3.jsonl",
        "reports/lot_03_pivot_report.md",
        "reports/lot_03_zone_report.md",
    ]
    for relative in required:
        if not (ROOT / relative).exists():
            os.write(1, f"LOT 3 VALIDATION: FAIL\nmissing {relative}\n".encode())
            return 1
    expected_counts = {
        "data/silver/btc_eur_5m_ohlcvt_lot3.jsonl": 36,
        "data/silver/btc_eur_15m_ohlcvt_lot3.jsonl": 12,
        "data/gold/btc_eur_5m_pivots_lot3.jsonl": 6,
        "data/gold/btc_eur_15m_pivots_lot3.jsonl": 3,
        "data/gold/btc_eur_5m_price_zones_lot3.jsonl": 6,
        "data/gold/btc_eur_15m_price_zones_lot3.jsonl": 3,
    }
    for relative, expected in expected_counts.items():
        if line_count(ROOT / relative) != expected:
            os.write(1, f"LOT 3 VALIDATION: FAIL\ninvalid row count {relative}\n".encode())
            return 1
    text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    if "live_execution: DISABLED" not in text or "leverage: FORBIDDEN" not in text or "trade_allowed_default: false" not in risk:
        os.write(1, b"LOT 3 VALIDATION: FAIL\nsafety invariant broken\n")
        return 1
    os.write(1, b"LOT 3 VALIDATION: PASS\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
