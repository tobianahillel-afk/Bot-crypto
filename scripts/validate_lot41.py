#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.spread_depth_and_imbalance_engine import (  # noqa: E402
    AUDIT_PATH,
    FEATURE_PATH,
    STATE_PATH,
    build_lot41_artifacts,
)
from crypto_quant_bot.microstructure.spread_depth_and_imbalance_engine_validation import (  # noqa: E402
    Lot41ValidationError,
)

LOT42_FORBIDDEN = (
    ROOT / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine_models.py",
    ROOT / "scripts/run_lot42_liquidity_zones_walls_and_voids_engine.py",
    ROOT / "scripts/validate_lot42.py",
    ROOT / "docs/LOT_42_LIQUIDITY_ZONES_WALLS_AND_VOIDS_ENGINE.md",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot41ValidationError(message)


def _verify_checksum(payload: dict[str, Any], field: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    require(isinstance(actual, str), f"{label} checksum missing")
    require(canonical_checksum(body) == actual, f"{label} checksum mismatch")


def _verify_reference(feature: dict[str, Any]) -> None:
    require(feature["sequence_id"] == 1003, "Lot 41 reference sequence changed")
    require(feature["spread_absolute"] == "0.2", "Lot 41 reference spread changed")
    require(feature["mid_price"] == "50025", "Lot 41 reference mid changed")
    require(
        feature["spread_bps"] == "0.03998000999500249875062468766",
        "spread bps changed",
    )
    require(
        feature["microprice"] == "50025.01612903225806451612903",
        "microprice changed",
    )
    bands = feature["depth_bands"]
    require([item["band_bps"] for item in bands] == ["0.025", "0.05", "0.1"], "bands changed")
    require([item["bid_quantity"] for item in bands] == ["0.9", "0.9", "1.4"], "bid depth changed")
    require([item["ask_quantity"] for item in bands] == ["0.65", "1.75", "2.15"], "ask depth changed")
    require(feature["observed_depth_only"] is True, "observed-depth-only flag changed")
    require(feature["extrapolated"] is False, "Lot 41 may not extrapolate")


def _verify_safety(state: dict[str, Any]) -> None:
    safety = state["safety"]
    require(safety["analysis_only"] is True, "analysis_only changed")
    require(safety["used_for_decision"] is False, "used_for_decision changed")
    require(safety["trade_allowed"] is False, "trade_allowed changed")
    require(safety["execution_allowed"] is False, "execution_allowed changed")
    require(safety["approved_size"] == 0, "approved_size changed")


def _verify_persisted(expected: tuple[dict[str, Any], ...]) -> None:
    paths = (ROOT / STATE_PATH, ROOT / AUDIT_PATH, ROOT / FEATURE_PATH)
    for path, payload in zip(paths, expected, strict=True):
        require(path.exists(), f"persisted Lot 41 artifact missing: {path}")
        require(load_json_object(path) == payload, f"persisted Lot 41 artifact differs: {path}")


def validate(expected_code_commit: str, *, require_persisted: bool = False) -> dict[str, object]:
    first = build_lot41_artifacts(ROOT, expected_code_commit)
    second = build_lot41_artifacts(ROOT, expected_code_commit)
    require(first == second, "Lot 41 build is non-deterministic")
    state, audit, feature = (item.to_dict() for item in first)
    _verify_checksum(state, "output_checksum", "Lot 41 state")
    _verify_checksum(audit, "audit_checksum", "Lot 41 audit")
    _verify_checksum(feature, "feature_checksum", "BookFeatureStateV1")
    require(state["run_context"]["code_commit"] == expected_code_commit, "code commit mismatch")
    require(audit["state_output_checksum"] == state["output_checksum"], "audit/state link mismatch")
    require(audit["feature_checksum"] == feature["feature_checksum"], "audit/feature link mismatch")
    require(state["book_features"] == feature, "state/feature link mismatch")
    _verify_reference(feature)
    _verify_safety(state)
    for path in LOT42_FORBIDDEN:
        require(not path.exists(), f"Lot 42 must remain locked: {path}")
    payloads = state, audit, feature
    if require_persisted:
        _verify_persisted(payloads)
    result = {
        "schema_version": "lot41-validation-result-v1",
        "status": "PASS",
        "validation_state": state["validation_state"],
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "feature_checksum": feature["feature_checksum"],
        "spread_bps": feature["spread_bps"],
        "depth_bands_total": len(feature["depth_bands"]),
        "lot42_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate deterministic Lot 41 implementation")
    parser.add_argument("--expected-code-commit", required=True)
    parser.add_argument("--require-persisted", action="store_true")
    arguments = parser.parse_args()
    try:
        result = validate(arguments.expected_code_commit, require_persisted=arguments.require_persisted)
    except (Lot41ValidationError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT41 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
