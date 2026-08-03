#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]



def fail(message: str) -> int:
    os.write(1, f"LOT 2 VALIDATION: FAIL\n{message}\n".encode())
    return 1


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def no_forbidden_text(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return "future_" not in text and "target" not in text and "label" not in text and '"LONG"' not in text and '"SHORT"' not in text


def main() -> int:
    required_counts = {
        "tests/fixtures/btc_eur_ohlcvt_1m_60.csv": 61,
        "data/silver/btc_eur_5m_ohlcvt_lot2.jsonl": 12,
        "data/silver/btc_eur_15m_ohlcvt_lot2.jsonl": 4,
        "data/gold/btc_eur_5m_features_lot2.jsonl": 12,
        "data/gold/btc_eur_15m_features_lot2.jsonl": 4,
    }
    for relative, expected in required_counts.items():
        path = ROOT / relative
        if not path.exists():
            return fail(f"missing {relative}")
        if line_count(path) != expected:
            return fail(f"invalid row count {relative}")
    required = [
        "src/crypto_quant_bot/timeframes/resampler.py",
        "src/crypto_quant_bot/features/basic.py",
        "src/crypto_quant_bot/features/registry.py",
        "config/feature_registry.yaml",
        "docs/FEATURE_REGISTRY.md",
        "reports/lot_02_multitimeframe_report.md",
        "reports/lot_02_feature_report.md",
    ]
    for relative in required:
        if not (ROOT / relative).exists():
            return fail(f"missing {relative}")
    for relative in ["data/gold/btc_eur_5m_features_lot2.jsonl", "data/gold/btc_eur_15m_features_lot2.jsonl"]:
        if not no_forbidden_text(ROOT / relative):
            return fail(f"forbidden trading or target field in {relative}")
    registry = (ROOT / "config" / "feature_registry.yaml").read_text(encoding="utf-8")
    for feature in ["simple_return_1", "log_return_1", "true_range", "rolling_mean_close_3"]:
        if feature not in registry:
            return fail(f"missing feature registry entry {feature}")
    status_text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk_text = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    if "live_execution: DISABLED" not in status_text or "leverage: FORBIDDEN" not in status_text:
        return fail("module status safety invariant broken")
    if "trade_allowed_default: false" not in risk_text:
        return fail("risk default invariant broken")
    os.write(1, b"LOT 2 VALIDATION: PASS\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
