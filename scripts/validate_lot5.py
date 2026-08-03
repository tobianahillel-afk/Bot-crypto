#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VOL_5M = ROOT / "data" / "gold" / "btc_eur_5m_volatility_lot5.jsonl"
VOL_15M = ROOT / "data" / "gold" / "btc_eur_15m_volatility_lot5.jsonl"
RANGE_5M = ROOT / "data" / "gold" / "btc_eur_5m_range_state_lot5.jsonl"
RANGE_15M = ROOT / "data" / "gold" / "btc_eur_15m_range_state_lot5.jsonl"
CATALOG = ROOT / "data" / "audit" / "dataset_catalog.json"
MAX_JSONL_BYTES = 1_000_000
MAX_JSONL_ROWS = 200
MAX_CATALOG_BYTES = 2_000_000
ALLOWED_RANGE_STATES = {"unknown", "compressed", "normal", "expanding"}
LOT5_DATASET_IDS = {
    "btc_eur_5m_volatility_lot5",
    "btc_eur_15m_volatility_lot5",
    "btc_eur_5m_range_state_lot5",
    "btc_eur_15m_range_state_lot5",
}
LOT5_FEATURES = [
    "realized_volatility_3",
    "realized_volatility_6",
    "true_range",
    "atr_3",
    "atr_6",
    "rolling_high_6",
    "rolling_low_6",
    "rolling_range_6",
    "rolling_mid_6",
    "close_position_in_range_6",
    "range_width_pct",
    "compression_score",
    "expansion_score",
    "range_state",
]


def fail(message: str) -> int:
    print("LOT 5 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def read_jsonl(path: Path, expected_rows: int) -> list[dict[str, Any]]:
    if path.stat().st_size > MAX_JSONL_BYTES:
        raise ValueError(f"jsonl file too large: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number > MAX_JSONL_ROWS:
                raise ValueError(f"too many jsonl rows in {path}")
            stripped = line.strip()
            if stripped:
                payload = json.loads(stripped)
                if not isinstance(payload, dict):
                    raise ValueError(f"non-object jsonl row in {path}")
                rows.append(payload)
    if len(rows) != expected_rows:
        raise ValueError(f"row count invalid for {path}")
    return rows


def load_catalog_ids(path: Path) -> set[str]:
    if not path.exists():
        raise ValueError(f"missing dataset catalog: {path}")
    if path.stat().st_size > MAX_CATALOG_BYTES:
        raise ValueError(f"dataset catalog too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("dataset catalog must be a list")
    dataset_ids: set[str] = set()
    for record in payload:
        if isinstance(record, dict):
            dataset_id = record.get("dataset_id")
            if isinstance(dataset_id, str):
                dataset_ids.add(dataset_id)
    return dataset_ids


def no_forbidden_fields(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        for key in row:
            if key.startswith("future_") or key.startswith("target") or key == "target" or key == "label":
                return False
    return True


def main() -> int:
    required_files = [
        ROOT / "src" / "crypto_quant_bot" / "contracts" / "volatility.py",
        ROOT / "src" / "crypto_quant_bot" / "contracts" / "range_state.py",
        ROOT / "src" / "crypto_quant_bot" / "volatility" / "realized.py",
        ROOT / "src" / "crypto_quant_bot" / "volatility" / "atr.py",
        ROOT / "src" / "crypto_quant_bot" / "volatility" / "range_state.py",
        ROOT / "src" / "crypto_quant_bot" / "volatility" / "writer.py",
        ROOT / "scripts" / ("build_" + "lot5_" + "volatility" + ".py"),
        VOL_5M,
        VOL_15M,
        RANGE_5M,
        RANGE_15M,
        ROOT / "reports" / "lot_05_volatility_report.md",
        ROOT / "reports" / "lot_05_range_state_report.md",
        ROOT / "docs" / "VOLATILITY_ENGINE_POLICY.md",
        ROOT / "docs" / "ATR_POLICY.md",
        ROOT / "docs" / "RANGE_STATE_POLICY.md",
        ROOT / "docs" / "ACCEPTANCE_CRITERIA_LOT_05.md",
        ROOT / "docs" / "LOT_05_REPORT.md",
        ROOT / "config" / "feature_registry.yaml",
        CATALOG,
    ]
    for path in required_files:
        if not path.exists():
            return fail(f"missing Lot 5 artifact: {path}")

    registry_text = (ROOT / "config" / "feature_registry.yaml").read_text(encoding="utf-8")
    for feature in LOT5_FEATURES:
        if feature not in registry_text:
            return fail(f"missing feature registry entry: {feature}")

    datasets = [(VOL_5M, 36), (VOL_15M, 12), (RANGE_5M, 36), (RANGE_15M, 12)]
    rows_by_path: list[tuple[Path, list[dict[str, Any]]]] = []
    try:
        for path, expected in datasets:
            rows = read_jsonl(path, expected)
            rows_by_path.append((path, rows))
            if not no_forbidden_fields(rows):
                return fail(f"forbidden target/label/future field in {path}")
            for row in rows:
                if row.get("used_for_decision") is not False:
                    return fail(f"used_for_decision must be false in {path}")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return fail(str(exc))

    for path, rows in rows_by_path[:2]:
        for row in rows:
            for key in ["true_range", "hl_range", "oc_range", "close_to_close_abs_return", "realized_volatility_3", "realized_volatility_6", "atr_3", "atr_6"]:
                if key not in row:
                    return fail(f"missing volatility field {key} in {path}")
        if rows[0]["true_range"] is None:
            return fail("first true_range must not be null")
        if rows[0]["atr_3"] is not None or rows[1]["atr_3"] is not None or rows[0]["realized_volatility_3"] is not None:
            return fail("early rolling volatility/ATR fields must be null")
        if rows[2]["atr_3"] is None:
            return fail("atr_3 should be available on third row")

    for path, rows in rows_by_path[2:]:
        for row in rows:
            for key in ["rolling_high_6", "rolling_low_6", "rolling_range_6", "rolling_mid_6", "close_position_in_range_6", "range_width_pct", "compression_score", "expansion_score", "range_state"]:
                if key not in row:
                    return fail(f"missing range field {key} in {path}")
            if row.get("range_state") not in ALLOWED_RANGE_STATES:
                return fail("invalid range_state")
            for score_name in ("compression_score", "expansion_score"):
                value = row.get(score_name)
                if value is not None and not (0 <= float(value) <= 1):
                    return fail(f"{score_name} outside [0,1]")
        if any(rows[i]["rolling_range_6"] is not None for i in range(min(5, len(rows)))):
            return fail("first five rolling range values must be null")
        if len(rows) >= 6 and rows[5]["rolling_range_6"] is None:
            return fail("rolling range should be available on sixth row")

    try:
        catalog_ids = load_catalog_ids(CATALOG)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return fail(str(exc))
    missing_ids = sorted(LOT5_DATASET_IDS - catalog_ids)
    if missing_ids:
        return fail(f"missing dataset catalog entries: {', '.join(missing_ids)}")

    status_text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk_text = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    if "live_execution: DISABLED" not in status_text or "leverage: FORBIDDEN" not in status_text:
        return fail("module status safety invariant broken")
    if "trade_allowed_default: false" not in risk_text:
        return fail("risk default invariant broken")

    print("LOT 5 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
