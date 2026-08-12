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
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine import (  # noqa: E402
    AUDIT_PATH,
    RESILIENCE_PATH,
    STATE_PATH,
    build_lot43_artifacts,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (  # noqa: E402
    Lot43ValidationError,
)

LOT44_FORBIDDEN = (
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py",
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py",
    ROOT / "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_validation.py",
    ROOT / "config/microstructure/trades_and_aggressor_classification_schema_v1.json",
    ROOT / "scripts/run_lot44_trades_and_aggressor_classification_schema.py",
    ROOT / "scripts/validate_lot44.py",
    ROOT / "tests/test_lot44_trades_and_aggressor_classification_schema.py",
    ROOT / "docs/LOT_44_TRADES_AND_AGGRESSOR_CLASSIFICATION_SCHEMA.md",
    ROOT / "docs/ACCEPTANCE_CRITERIA_LOT_44.md",
)
SCHEMAS = (
    ROOT / "contracts/schemas/book_resilience_state_v1.schema.json",
    ROOT / "contracts/schemas/book_resilience_replenishment_engine_state_v1.schema.json",
    ROOT / "contracts/schemas/book_resilience_replenishment_engine_audit_v1.schema.json",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot43ValidationError(message)


def _verify_checksum(payload: dict[str, Any], field: str, label: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    require(isinstance(actual, str), f"{label} checksum missing")
    require(canonical_checksum(body) == actual, f"{label} checksum mismatch")


def _verify_reference(resilience: dict[str, Any]) -> None:
    require(resilience["sequence_id"] == 1003, "Lot 43 reference sequence changed")
    require(resilience["history_sequence_ids"] == [1001, 1002, 1003], "history changed")
    require(resilience["resilience_horizons_us"] == [10000, 25000], "horizon set changed")
    require(resilience["volatility_measure_bps"] == "0", "volatility measure changed")
    require(resilience["volatility_regime"] == "QUIET", "volatility regime changed")
    require(resilience["volatility_method"] == "OBSERVED_BOOK_MID_MAX_ABS_MOVE_BPS", "method changed")
    require(resilience["observed_book_only"] is True, "observed-book boundary changed")
    require(resilience["participant_intent_inferred"] is False, "intent inference enabled")
    events = resilience["depletion_events"]
    require(len(events) == 1, "reference depletion-event count changed")
    event = events[0]
    require(event["side"] == "BID", "reference depletion side changed")
    require(event["depleted_price"] == "50024.8", "reference depletion price changed")
    require(event["previous_quantity"] == "1.25", "reference previous quantity changed")
    require(event["post_depletion_quantity"] == "0", "reference post quantity changed")
    require(event["depleted_quantity"] == "1.25", "reference depleted quantity changed")
    require(event["depletion_ratio"] == "1", "reference depletion ratio changed")
    require(event["depletion_sequence_id"] == 1003, "reference depletion sequence changed")
    require(event["replenishment_kind"] == "NONE", "unexpected replenishment classification")
    require(event["replenishment_sequence_id"] is None, "unexpected replenishment sequence")
    require(event["replenishment_time_us"] is None, "missing replenishment must not use zero time")
    require(event["replenished_quantity"] == "0", "unexpected replenished quantity")
    require(event["recovered_fraction"] == "0", "unexpected recovered fraction")
    require(event["directional_mid_shift_bps"] == "0", "unexpected mid shift")
    require(event["max_window_status"] == "EXPIRED_NO_REPLENISHMENT", "max window changed")
    require(event["participant_intent"] == "NOT_INFERRED", "participant intent changed")
    _verify_reference_slices(resilience["resilience_slices"])


def _verify_reference_slices(slices: list[dict[str, Any]]) -> None:
    require(len(slices) == 4, "reference resilience slice count changed")
    by_key = {(item["side"], item["horizon_us"]): item for item in slices}
    require(set(by_key) == {("BID", 10000), ("BID", 25000), ("ASK", 10000), ("ASK", 25000)}, "slice keys changed")
    for horizon in (10000, 25000):
        bid = by_key[("BID", horizon)]
        require(bid["depletion_events_total"] == 1, "BID depletion count changed")
        require(bid["expired_events_total"] == 1, "BID expired count changed")
        require(bid["recovered_events_total"] == 0, "unexpected BID recovery")
        require(bid["mid_shift_events_total"] == 0, "unexpected BID mid shift")
        require(bid["pending_events_total"] == 0, "unexpected BID pending event")
        require(bid["mean_recovered_fraction"] == "0", "BID mean recovery changed")
        require(bid["mean_replenishment_time_us"] is None, "BID mean time must be null")
        require(bid["resilience_status"] == "FRAGILE", "BID resilience status changed")
        ask = by_key[("ASK", horizon)]
        require(ask["depletion_events_total"] == 0, "unexpected ASK depletion")
        require(ask["mean_recovered_fraction"] is None, "ASK mean recovery must be null")
        require(ask["mean_replenishment_time_us"] is None, "ASK mean time must be null")
        require(ask["resilience_status"] == "NO_EVENTS", "ASK resilience status changed")


def _verify_links(
    state: dict[str, Any],
    audit: dict[str, Any],
    resilience: dict[str, Any],
    expected_code_commit: str,
) -> None:
    require(state["run_context"]["code_commit"] == expected_code_commit, "code commit mismatch")
    require(audit["run_context"]["code_commit"] == expected_code_commit, "audit commit mismatch")
    require(audit["state_output_checksum"] == state["output_checksum"], "audit/state link mismatch")
    require(audit["resilience_checksum"] == resilience["resilience_checksum"], "audit/resilience link mismatch")
    require(state["book_resilience"] == resilience, "state/resilience link mismatch")
    require(state["lineage"] == audit["lineage"], "state/audit lineage mismatch")


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


def _verify_persisted(expected: tuple[dict[str, Any], ...]) -> None:
    paths = (ROOT / STATE_PATH, ROOT / AUDIT_PATH, ROOT / RESILIENCE_PATH)
    for path, payload in zip(paths, expected, strict=True):
        require(path.exists(), f"persisted Lot 43 artifact missing: {path}")
        require(load_json_object(path) == payload, f"persisted Lot 43 artifact differs: {path}")


def _verify_schema_contracts() -> None:
    for path in SCHEMAS:
        require(path.exists(), f"Lot 43 schema missing: {path}")
        schema = load_json_object(path)
        require(schema.get("type") == "object", f"Lot 43 schema type changed: {path}")
        require(schema.get("additionalProperties") is False, f"Lot 43 schema must be closed: {path}")


def _verify_lot44_lock() -> None:
    for path in LOT44_FORBIDDEN:
        require(not path.exists(), f"Lot 44 must remain locked: {path}")


def validate(expected_code_commit: str, *, require_persisted: bool = False) -> dict[str, object]:
    first = build_lot43_artifacts(ROOT, expected_code_commit)
    second = build_lot43_artifacts(ROOT, expected_code_commit)
    require(first == second, "Lot 43 build is non-deterministic")
    state, audit, resilience = (item.to_dict() for item in first)
    _verify_checksum(state, "output_checksum", "Lot 43 state")
    _verify_checksum(audit, "audit_checksum", "Lot 43 audit")
    _verify_checksum(resilience, "resilience_checksum", "BookResilienceStateV1")
    for event in resilience["depletion_events"]:
        _verify_checksum(event, "event_checksum", "BookDepletionEventV1")
    for resilience_slice in resilience["resilience_slices"]:
        _verify_checksum(resilience_slice, "slice_checksum", "BookResilienceSliceV1")
    _verify_links(state, audit, resilience, expected_code_commit)
    _verify_reference(resilience)
    _verify_safety(state)
    _verify_schema_contracts()
    _verify_lot44_lock()
    payloads = state, audit, resilience
    if require_persisted:
        _verify_persisted(payloads)
    metrics = state["metrics"]
    result = {
        "schema_version": "lot43-validation-result-v1",
        "status": "PASS",
        "validation_state": state["validation_state"],
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "resilience_checksum": resilience["resilience_checksum"],
        "observations_total": metrics["lot_43_observations_total"],
        "depletion_events_total": metrics["lot_43_depletion_events_total"],
        "expired_max_window_events_total": metrics["lot_43_expired_max_window_events_total"],
        "volatility_regime": resilience["volatility_regime"],
        "lot44_status": "PLANNED_LOCKED",
        "participant_intent_inferred": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate deterministic Lot 43 implementation")
    parser.add_argument("--expected-code-commit", required=True)
    parser.add_argument("--require-persisted", action="store_true")
    arguments = parser.parse_args()
    try:
        result = validate(
            arguments.expected_code_commit,
            require_persisted=arguments.require_persisted,
        )
    except (Lot43ValidationError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT43 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
