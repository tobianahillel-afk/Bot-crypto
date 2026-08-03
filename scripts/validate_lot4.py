#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.core.config_loader import ConfigLoader
from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.risk_engine import RiskEngine

MAX_JSONL_BYTES = 1_000_000
MAX_JSONL_ROWS = 300
MAX_CATALOG_BYTES = 2_000_000
MAX_FORBIDDEN_FIELD_NODES = 5_000
CATALOG = ROOT / "data" / "audit" / "dataset_catalog.json"
LOT4_DATASET_IDS = {
    "btc_eur_5m_volume_profile_lot4",
    "btc_eur_15m_volume_profile_lot4",
    "btc_eur_5m_vwap_lot4",
    "btc_eur_15m_vwap_lot4",
    "btc_eur_5m_anchored_vwap_lot4",
    "btc_eur_15m_anchored_vwap_lot4",
}


def fail(message: str) -> int:
    print("LOT 4 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def read_jsonl(path: Path, max_rows: int = MAX_JSONL_ROWS) -> list[dict[str, Any]]:
    if path.stat().st_size > MAX_JSONL_BYTES:
        raise ValueError(f"jsonl file too large: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number > max_rows:
                raise ValueError(f"too many jsonl rows in {path}")
            stripped = line.strip()
            if stripped:
                payload = json.loads(stripped)
                if not isinstance(payload, dict):
                    raise ValueError(f"non-object jsonl row in {path}")
                rows.append(payload)
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
    stack: list[object] = list(rows)
    visited_nodes = 0
    while stack:
        visited_nodes += 1
        if visited_nodes > MAX_FORBIDDEN_FIELD_NODES:
            return False
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if key in {"target", "label"} or key.startswith("future_"):
                    return False
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    return True


def main() -> int:
    required = [
        ROOT / "src" / "crypto_quant_bot" / "contracts" / "volume_profile.py",
        ROOT / "src" / "crypto_quant_bot" / "contracts" / "vwap.py",
        ROOT / "src" / "crypto_quant_bot" / "volume" / "profile.py",
        ROOT / "src" / "crypto_quant_bot" / "volume" / "vwap.py",
        ROOT / "src" / "crypto_quant_bot" / "volume" / "anchors.py",
        ROOT / "data" / "gold" / "btc_eur_5m_volume_profile_lot4.jsonl",
        ROOT / "data" / "gold" / "btc_eur_15m_volume_profile_lot4.jsonl",
        ROOT / "data" / "gold" / "btc_eur_5m_volume_profile_summary_lot4.jsonl",
        ROOT / "data" / "gold" / "btc_eur_15m_volume_profile_summary_lot4.jsonl",
        ROOT / "data" / "gold" / "btc_eur_5m_vwap_lot4.jsonl",
        ROOT / "data" / "gold" / "btc_eur_15m_vwap_lot4.jsonl",
        ROOT / "data" / "gold" / "btc_eur_5m_anchor_points_lot4.jsonl",
        ROOT / "data" / "gold" / "btc_eur_15m_anchor_points_lot4.jsonl",
        ROOT / "data" / "gold" / "btc_eur_5m_anchored_vwap_lot4.jsonl",
        ROOT / "data" / "gold" / "btc_eur_15m_anchored_vwap_lot4.jsonl",
        ROOT / "reports" / "lot_04_volume_profile_report.md",
        ROOT / "reports" / "lot_04_vwap_report.md",
        ROOT / "docs" / "VOLUME_PROFILE_POLICY.md",
        ROOT / "docs" / "VWAP_POLICY.md",
        ROOT / "docs" / "ANCHORED_VWAP_POLICY.md",
        CATALOG,
    ]
    for path in required:
        if not path.exists():
            return fail(f"missing Lot 4 artifact: {path}")

    try:
        vp_5m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_5m_volume_profile_lot4.jsonl")
        vp_15m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_15m_volume_profile_lot4.jsonl")
        summaries_5m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_5m_volume_profile_summary_lot4.jsonl")
        summaries_15m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_15m_volume_profile_summary_lot4.jsonl")
        vwap_5m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_5m_vwap_lot4.jsonl")
        vwap_15m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_15m_vwap_lot4.jsonl")
        anchors_5m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_5m_anchor_points_lot4.jsonl")
        anchors_15m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_15m_anchor_points_lot4.jsonl")
        anchored_5m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_5m_anchored_vwap_lot4.jsonl")
        anchored_15m = read_jsonl(ROOT / "data" / "gold" / "btc_eur_15m_anchored_vwap_lot4.jsonl")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return fail(str(exc))

    if len(vp_5m) != 25 or len(vp_15m) != 25:
        return fail("volume profile bin counts invalid")
    if len(summaries_5m) != 1 or len(summaries_15m) != 1:
        return fail("volume profile summary counts invalid")
    if len(vwap_5m) != 36 or len(vwap_15m) != 12:
        return fail("VWAP row counts invalid")
    if len(anchors_5m) < 3 or len(anchors_15m) < 1:
        return fail("anchor row counts invalid")
    if len(anchored_5m) < 36 or len(anchored_15m) < 12:
        return fail("anchored VWAP row counts invalid")
    if not any(row.get("is_poc") is True for row in vp_5m + vp_15m):
        return fail("POC missing")

    all_rows = vp_5m + vp_15m + summaries_5m + summaries_15m + vwap_5m + vwap_15m + anchors_5m + anchors_15m + anchored_5m + anchored_15m
    if not no_forbidden_fields(all_rows):
        return fail("forbidden target/label/future field in Lot 4 data")
    for row in all_rows:
        if row.get("used_for_decision") is not False:
            return fail("used_for_decision must be false in Lot 4 data")
    for row in vwap_5m + vwap_15m:
        if row.get("available_at", "") < row.get("timestamp", ""):
            return fail("VWAP available_at before timestamp")
    anchors = {row.get("anchor_id"): row for row in anchors_5m + anchors_15m}
    for row in anchored_5m + anchored_15m:
        anchor = anchors.get(row.get("anchor_id"))
        if anchor is None:
            return fail("anchored VWAP references unknown anchor")
        if row.get("available_at", "") < anchor.get("usable_from", ""):
            return fail("anchored VWAP emitted before anchor usable_from")

    try:
        catalog_ids = load_catalog_ids(CATALOG)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return fail(str(exc))
    missing_ids = sorted(LOT4_DATASET_IDS - catalog_ids)
    if missing_ids:
        return fail(f"missing dataset catalog entries: {', '.join(missing_ids)}")

    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    if decision.trading_decision != "WAIT" or decision.trade_allowed is not False:
        return fail("Decision Engine invariant broken")
    if risk.trade_allowed is not False:
        return fail("Risk Engine invariant broken")
    statuses = ConfigLoader(ROOT / "config").load("module_status_matrix")
    if statuses.get("live_execution") != "DISABLED" or statuses.get("leverage") != "FORBIDDEN":
        return fail("module status safety invariant broken")

    print("LOT 4 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
