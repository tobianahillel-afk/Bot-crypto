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
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_engine import (  # noqa: E402
    AUDIT_PATH,
    STATE_PATH,
    ZONE_SET_PATH,
    build_lot42_artifacts,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_engine_validation import (  # noqa: E402
    DISPLAYED_WALL,
    LIQUIDITY_VOID,
    LOW_CONFIDENCE,
    PERSISTENT_ZONE,
    Lot42ValidationError,
)

LOT43_FORBIDDEN = (
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_validation.py",
    ROOT / "config/microstructure/book_resilience_and_replenishment_engine_v1.json",
    ROOT / "scripts/run_lot43_book_resilience_and_replenishment_engine.py",
    ROOT / "scripts/validate_lot43.py",
    ROOT / "tests/test_lot43_book_resilience_and_replenishment_engine.py",
    ROOT / "docs/LOT_43_BOOK_RESILIENCE_AND_REPLENISHMENT_ENGINE.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_43.md",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot42ValidationError(message)


def _verify_checksum(payload: dict[str, Any], field: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    require(isinstance(actual, str), f"{label} checksum missing")
    require(canonical_checksum(body) == actual, f"{label} checksum mismatch")


def _verify_reference(zone_set: dict[str, Any]) -> None:
    require(zone_set["sequence_id"] == 1003, "Lot 42 reference sequence changed")
    require(zone_set["history_sequence_ids"] == [1001, 1002, 1003], "history changed")
    require(zone_set["mid_price"] == "50025", "Lot 42 reference mid changed")
    require(zone_set["observed_book_only"] is True, "observed book boundary changed")
    require(zone_set["participant_intent_inferred"] is False, "intent inference enabled")
    zones = zone_set["zones"]
    voids = zone_set["voids"]
    require(len(zones) == 3, "reference active zone count changed")
    require(len(voids) == 1, "reference liquidity void count changed")
    require(all(DISPLAYED_WALL in zone["classifications"] for zone in zones), "wall set changed")
    require(
        sum(PERSISTENT_ZONE in zone["classifications"] for zone in zones) == 2,
        "persistent zone count changed",
    )
    require(
        sum(zone["confidence_status"] == LOW_CONFIDENCE for zone in zones) == 1,
        "low-confidence wall count changed",
    )
    require(voids[0]["side"] == "BID", "reference void side changed")
    require(voids[0]["classification"] == LIQUIDITY_VOID, "void classification changed")
    require(all(zone["participant_intent"] == "NOT_INFERRED" for zone in zones), "intent changed")
    require(all(item["participant_intent"] == "NOT_INFERRED" for item in voids), "void intent changed")


def _verify_safety(state: dict[str, Any]) -> None:
    safety = state["safety"]
    require(safety["analysis_only"] is True, "analysis_only changed")
    require(safety["used_for_decision"] is False, "used_for_decision changed")
    require(safety["trade_allowed"] is False, "trade_allowed changed")
    require(safety["execution_allowed"] is False, "execution_allowed changed")
    require(safety["approved_size"] == 0, "approved_size changed")
    require(safety["external_connectivity_allowed"] is False, "connectivity changed")
    require(safety["network_ingestion_allowed"] is False, "network ingestion changed")
    require(safety["real_credentials_allowed"] is False, "credentials boundary changed")


def _verify_links(
    state: dict[str, Any],
    audit: dict[str, Any],
    zone_set: dict[str, Any],
    expected_code_commit: str,
) -> None:
    require(state["run_context"]["code_commit"] == expected_code_commit, "code commit mismatch")
    require(audit["run_context"]["code_commit"] == expected_code_commit, "audit commit mismatch")
    require(audit["state_output_checksum"] == state["output_checksum"], "audit/state link mismatch")
    require(audit["zone_set_checksum"] == zone_set["zone_set_checksum"], "audit/zone link mismatch")
    require(state["liquidity_zones"] == zone_set, "state/zone-set link mismatch")
    require(state["lineage"] == audit["lineage"], "state/audit lineage mismatch")


def _verify_persisted(expected: tuple[dict[str, Any], ...]) -> None:
    paths = (ROOT / STATE_PATH, ROOT / AUDIT_PATH, ROOT / ZONE_SET_PATH)
    for path, payload in zip(paths, expected, strict=True):
        require(path.exists(), f"persisted Lot 42 artifact missing: {path}")
        require(load_json_object(path) == payload, f"persisted Lot 42 artifact differs: {path}")


def _verify_lot43_lock() -> None:
    for path in LOT43_FORBIDDEN:
        require(not path.exists(), f"Lot 43 must remain locked: {path}")


def validate(expected_code_commit: str, *, require_persisted: bool = False) -> dict[str, object]:
    first = build_lot42_artifacts(ROOT, expected_code_commit)
    second = build_lot42_artifacts(ROOT, expected_code_commit)
    require(first == second, "Lot 42 build is non-deterministic")
    state, audit, zone_set = (item.to_dict() for item in first)
    _verify_checksum(state, "output_checksum", "Lot 42 state")
    _verify_checksum(audit, "audit_checksum", "Lot 42 audit")
    _verify_checksum(zone_set, "zone_set_checksum", "LiquidityZoneSetV1")
    for zone in zone_set["zones"]:
        _verify_checksum(zone, "zone_checksum", "LiquidityZoneV1")
    for liquidity_void in zone_set["voids"]:
        _verify_checksum(liquidity_void, "void_checksum", "LiquidityVoidV1")
    _verify_links(state, audit, zone_set, expected_code_commit)
    _verify_reference(zone_set)
    _verify_safety(state)
    _verify_lot43_lock()
    payloads = state, audit, zone_set
    if require_persisted:
        _verify_persisted(payloads)
    metrics = state["metrics"]
    result = {
        "schema_version": "lot42-validation-result-v1",
        "status": "PASS",
        "validation_state": state["validation_state"],
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "zone_set_checksum": zone_set["zone_set_checksum"],
        "active_zones_total": metrics["lot_42_active_zones_total"],
        "displayed_walls_total": metrics["lot_42_displayed_walls_total"],
        "persistent_zones_total": metrics["lot_42_persistent_zones_total"],
        "low_confidence_walls_total": metrics["lot_42_low_confidence_walls_total"],
        "liquidity_voids_total": metrics["lot_42_liquidity_voids_total"],
        "lot43_status": "PLANNED_LOCKED",
        "participant_intent_inferred": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate deterministic Lot 42 implementation")
    parser.add_argument("--expected-code-commit", required=True)
    parser.add_argument("--require-persisted", action="store_true")
    arguments = parser.parse_args()
    try:
        result = validate(
            arguments.expected_code_commit,
            require_persisted=arguments.require_persisted,
        )
    except (Lot42ValidationError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT42 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
