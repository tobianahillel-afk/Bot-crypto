#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.risk_engine import RiskEngine

REGIME_5M = ROOT / "data" / "gold" / "btc_eur_5m_regime_lot6.jsonl"
REGIME_15M = ROOT / "data" / "gold" / "btc_eur_15m_regime_lot6.jsonl"
ALLOWED_REGIMES = {"unknown", "trend_up", "trend_down", "range", "compressed", "expanding", "volatile", "mixed"}
EXPECTED_CATALOG_IDS = {"btc_eur_5m_regime_lot6", "btc_eur_15m_regime_lot6"}
LOT6_FEATURES = [
    "direction_score",
    "trend_score",
    "range_score",
    "volatility_score",
    "regime_state",
    "regime_confidence_score",
]
def fail(message: str) -> int:
    print("LOT 6 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_lot6_catalog_ids() -> set[str]:
    records = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").load()
    if len(records) > 2000:
        raise ValueError("dataset catalog record count too large")
    matched_ids: set[str] = set()
    for record in records:
        dataset_id = record.get("dataset_id")
        if dataset_id in EXPECTED_CATALOG_IDS:
            matched_ids.add(dataset_id)
            if matched_ids == EXPECTED_CATALOG_IDS:
                break
    return matched_ids


def no_forbidden_fields(rows: list[dict]) -> bool:
    for row in rows:
        for key in row:
            lowered = key.lower()
            if lowered.startswith("future_") or lowered == "target" or lowered.startswith("target") or lowered == "label":
                return False
            value = row.get(key)
            if isinstance(value, str) and value.upper() in {"LONG", "SHORT"}:
                return False
    return True


def assert_score(value: object, name: str, lower: float, upper: float) -> str | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"{name} is not numeric"
    if not lower <= number <= upper:
        return f"{name} outside [{lower}, {upper}]"
    return None


def main() -> int:
    required_files = [
        ROOT / "src" / "crypto_quant_bot" / "contracts" / "regime.py",
        ROOT / "src" / "crypto_quant_bot" / "regime" / "__init__.py",
        ROOT / "src" / "crypto_quant_bot" / "regime" / "trend.py",
        ROOT / "src" / "crypto_quant_bot" / "regime" / "classifier.py",
        ROOT / "src" / "crypto_quant_bot" / "regime" / "confidence.py",
        ROOT / "src" / "crypto_quant_bot" / "regime" / "writer.py",
        ROOT / "scripts" / ("build_" + "lot6_" + "regime" + ".py"),
        ROOT / "config" / "regime.yaml",
        REGIME_5M,
        REGIME_15M,
        ROOT / "reports" / "lot_06_regime_report.md",
        ROOT / "docs" / "REGIME_ENGINE_POLICY.md",
        ROOT / "docs" / "TREND_RANGE_REGIME_POLICY.md",
        ROOT / "docs" / "ACCEPTANCE_CRITERIA_LOT_06.md",
        ROOT / "docs" / "LOT_06_REPORT.md",
    ]
    for path in required_files:
        if not path.exists():
            return fail(f"missing Lot 6 artifact: {path}")

    registry_text = (ROOT / "config" / "feature_registry.yaml").read_text(encoding="utf-8")
    for feature in LOT6_FEATURES:
        if feature not in registry_text:
            return fail(f"missing feature registry entry: {feature}")

    datasets = [(REGIME_5M, 36), (REGIME_15M, 12)]
    for path, expected in datasets:
        rows = read_jsonl(path)
        if len(rows) != expected:
            return fail(f"row count invalid for {path}: {len(rows)}")
        if not no_forbidden_fields(rows):
            return fail(f"forbidden field or signal in {path}")
        for row in rows:
            if row.get("used_for_decision") is not False:
                return fail("used_for_decision must be false")
            if row.get("regime_state") not in ALLOWED_REGIMES:
                return fail("invalid regime_state")
            if not isinstance(row.get("components"), dict):
                return fail("components must be a dict")
            if not row.get("available_at"):
                return fail("available_at missing")
            checks = [
                (row.get("direction_score"), "direction_score", -1.0, 1.0),
                (row.get("trend_score"), "trend_score", 0.0, 1.0),
                (row.get("range_score"), "range_score", 0.0, 1.0),
                (row.get("volatility_score"), "volatility_score", 0.0, 1.0),
                (row.get("confidence_score"), "confidence_score", 0.0, 1.0),
                (row.get("compression_score"), "compression_score", 0.0, 1.0),
                (row.get("expansion_score"), "expansion_score", 0.0, 1.0),
            ]
            for value, name, lower, upper in checks:
                error = assert_score(value, name, lower, upper)
                if error:
                    return fail(error)
        if rows[0].get("regime_state") != "unknown":
            return fail("first row should be unknown")

    if load_lot6_catalog_ids() != EXPECTED_CATALOG_IDS:
        return fail("dataset catalog missing Lot 6 entries")

    status_text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk_text = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    if "live_execution: DISABLED" not in status_text or "leverage: FORBIDDEN" not in status_text:
        return fail("module status safety invariant broken")
    if "trade_allowed_default: false" not in risk_text:
        return fail("risk default invariant broken")
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    if decision.trading_decision != "WAIT" or decision.system_decision != "BLOCK_TRADING" or decision.trade_allowed is not False:
        return fail("decision safety invariant broken")
    if risk.trade_allowed is not False:
        return fail("risk safety invariant broken")

    print("LOT 6 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
