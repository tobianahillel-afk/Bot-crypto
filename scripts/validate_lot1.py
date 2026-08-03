#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]



def fail(message: str) -> int:
    os.write(1, f"LOT 1 VALIDATION: FAIL\n{message}\n".encode())
    return 1


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def main() -> int:
    required = [
        "data/raw", "data/bronze", "data/silver", "data/gold", "data/audit",
        "tests/fixtures/btc_eur_ohlcvt_sample.csv",
        "tests/fixtures/btc_eur_ohlcvt_invalid.csv",
        "src/crypto_quant_bot/data/data_writer.py",
        "data/audit/dataset_catalog.json",
        "reports/lot_01_data_quality_report.md",
    ]
    for relative in required:
        if not (ROOT / relative).exists():
            return fail(f"missing {relative}")
    bronze_files = list((ROOT / "data" / "bronze").glob("*.jsonl"))
    if not bronze_files:
        return fail("missing bronze JSONL")
    if line_count(ROOT / "tests" / "fixtures" / "btc_eur_ohlcvt_sample.csv") < 7:
        return fail("valid fixture too small")
    catalog = (ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8")
    if "btc_eur_1m_ohlcvt_sample_lot1bis" not in catalog:
        return fail("dataset catalog missing Lot 1 dataset")
    status_text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk_text = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    if "live_execution: DISABLED" not in status_text or "leverage: FORBIDDEN" not in status_text:
        return fail("module status safety invariant broken")
    if "trade_allowed_default: false" not in risk_text:
        return fail("risk default invariant broken")
    os.write(1, b"LOT 1 VALIDATION: PASS\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
