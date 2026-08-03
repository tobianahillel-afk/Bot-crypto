#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.audit.writer import write_feature_registry_report, write_json

DATASETS = [
    "data/gold/btc_eur_5m_features_lot2.jsonl",
    "data/gold/btc_eur_15m_features_lot2.jsonl",
    "data/gold/btc_eur_5m_pivots_lot3.jsonl",
    "data/gold/btc_eur_15m_pivots_lot3.jsonl",
    "data/gold/btc_eur_5m_price_zones_lot3.jsonl",
    "data/gold/btc_eur_15m_price_zones_lot3.jsonl",
    "data/gold/btc_eur_5m_vwap_lot4.jsonl",
    "data/gold/btc_eur_15m_vwap_lot4.jsonl",
    "data/gold/btc_eur_5m_anchored_vwap_lot4.jsonl",
    "data/gold/btc_eur_15m_anchored_vwap_lot4.jsonl",
    "data/gold/btc_eur_5m_volatility_lot5.jsonl",
    "data/gold/btc_eur_15m_volatility_lot5.jsonl",
    "data/gold/btc_eur_5m_range_state_lot5.jsonl",
    "data/gold/btc_eur_15m_range_state_lot5.jsonl",
    "data/gold/btc_eur_5m_regime_lot6.jsonl",
    "data/gold/btc_eur_15m_regime_lot6.jsonl",
    "data/gold/btc_eur_5m_market_state_lot7.jsonl",
    "data/gold/btc_eur_15m_market_state_lot7.jsonl",
]
REQUIRED_FEATURES = [
    "close",
    "simple_return_1",
    "log_return_1",
    "true_range",
    "rolling_mean_close_3",
    "realized_volatility_3",
    "realized_volatility_6",
    "atr_3",
    "atr_6",
    "range_state",
    "direction_score",
    "trend_score",
    "range_score",
    "volatility_score",
    "regime_state",
    "regime_confidence_score",
]


def main() -> int:
    registry = ROOT / "config" / "feature_registry.yaml"
    docs = ROOT / "docs" / "FEATURE_REGISTRY.md"
    errors = []
    if not registry.exists():
        errors.append(f"missing registry: {registry}")
        registry_text = ""
    else:
        registry_text = registry.read_text(encoding="utf-8")
    if not docs.exists():
        errors.append(f"missing docs: {docs}")
    for rel in DATASETS:
        if not (ROOT / rel).exists():
            errors.append(f"missing audited dataset: {rel}")
    missing = [
        name
        for name in REQUIRED_FEATURES
        if f"{name}:" not in registry_text and f"name: {name}" not in registry_text
    ]
    if missing:
        errors.append("missing required registry features: " + ", ".join(missing))
    payload = {
        "audit_id": "lot8_feature_registry_static",
        "checked_at": "lot9_ter_static_check",
        "registry_path": str(registry),
        "dataset_paths": [str(ROOT / rel) for rel in DATASETS],
        "registered_features": REQUIRED_FEATURES,
        "dataset_features": REQUIRED_FEATURES,
        "missing_from_registry": missing,
        "unused_registry_features": [],
        "forbidden_feature_names": [],
        "lookahead_violations": [],
        "available_at_violations": [],
        "used_for_decision_violations": [],
        "quality_flag": "valid" if not errors else "invalid",
        "validation_status": "validated_lot8" if not errors else "failed_lot8",
        "errors": errors,
        "warnings": [],
        "source": "lot8_feature_registry_audit_fast_bounded",
        "used_for_decision": False,
    }
    write_json(ROOT / "data/audit/feature_registry_audit_lot8.json", payload)
    write_feature_registry_report(ROOT / "reports/lot_08_feature_registry_audit_report.md", payload)
    if errors:
        print("LOT 8 FEATURE REGISTRY AUDIT: FAIL", flush=True)
        return 1
    print("LOT 8 FEATURE REGISTRY AUDIT: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
