#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine import (
    AUDIT_PATH,
    HEALTH_PATH,
    SNAPSHOT_PATH,
    STATE_PATH,
    build_lot38_artifacts,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_validation import (
    lot38_safety,
)


class Lot38ValidationError(RuntimeError):
    """Raised when committed Lot 38 evidence cannot be certified."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot38ValidationError(message)


def validate_checksum(payload: dict[str, Any], field: str, label: str) -> str:
    body = dict(payload)
    checksum = body.pop(field, None)
    require(isinstance(checksum, str), f"{label} checksum missing")
    require(canonical_checksum(body) == checksum, f"{label} checksum mismatch")
    return checksum


def load_artifacts(root: Path) -> tuple[dict[str, Any], ...]:
    return (
        load_json_object(root / STATE_PATH),
        load_json_object(root / AUDIT_PATH),
        load_json_object(root / SNAPSHOT_PATH),
        load_json_object(root / HEALTH_PATH),
    )


def validate_reference_state(
    state: dict[str, Any], snapshot: dict[str, Any], health: dict[str, Any]
) -> None:
    require(
        state.get("validation_state") == "VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY",
        "Lot 38 validation state changed",
    )
    require(state.get("safety") == lot38_safety(), "Lot 38 safety boundary changed")
    metrics = state.get("metrics")
    require(isinstance(metrics, dict), "Lot 38 metrics missing")
    expected_metrics = {
        "lot_38_records_processed_total": 1,
        "lot_38_source_levels_total": 6,
        "lot_38_normalized_levels_total": 6,
        "lot_38_duplicate_levels_aggregated_total": 0,
        "lot_38_published_levels_total": 4,
        "lot_38_validation_failures_total": 0,
        "lot_38_processing_latency_us": None,
        "latency_measurement_status": "NOT_MEASURED_OFFLINE_DETERMINISTIC_REPLAY",
    }
    for field, value in expected_metrics.items():
        require(metrics.get(field) == value, f"Lot 38 metric changed: {field}")
    require(snapshot.get("venue_state") == "OPEN", "Lot 38 reference venue state changed")
    require(health.get("health_status") == "HEALTHY", "Lot 38 health state changed")
    require(health.get("crossed") is False, "Lot 38 reference book became crossed")


def validate_links(
    state: dict[str, Any],
    audit: dict[str, Any],
    snapshot: dict[str, Any],
    health: dict[str, Any],
) -> tuple[str, str, str, str]:
    state_checksum = validate_checksum(state, "output_checksum", "Lot 38 state")
    audit_checksum = validate_checksum(audit, "audit_checksum", "Lot 38 audit")
    snapshot_checksum = validate_checksum(snapshot, "snapshot_checksum", "Lot 38 snapshot")
    health_checksum = validate_checksum(health, "health_checksum", "Lot 38 health")
    require(state.get("snapshot") == snapshot, "Lot 38 snapshot artifact mismatch")
    require(state.get("book_health") == health, "Lot 38 health artifact mismatch")
    require(audit.get("state_output_checksum") == state_checksum, "Lot 38 audit/state link mismatch")
    require(audit.get("snapshot_checksum") == snapshot_checksum, "Lot 38 audit/snapshot link mismatch")
    require(audit.get("health_checksum") == health_checksum, "Lot 38 audit/health link mismatch")
    require(audit.get("safety") == lot38_safety(), "Lot 38 audit safety changed")
    return state_checksum, audit_checksum, snapshot_checksum, health_checksum


def validate_code_commit(
    state: dict[str, Any], audit: dict[str, Any], expected_code_commit: str | None
) -> str:
    run_context = state.get("run_context")
    require(isinstance(run_context, dict), "Lot 38 run context missing")
    state_commit = run_context.get("code_commit")
    audit_commit = audit.get("code_commit")
    require(isinstance(state_commit, str), "Lot 38 state code commit missing")
    require(state_commit == audit_commit, "Lot 38 state/audit code commit mismatch")
    if expected_code_commit is not None:
        require(state_commit == expected_code_commit, "Lot 38 code commit differs from expected")
    return state_commit


def validate_replay(
    root: Path,
    code_commit: str,
    state: dict[str, Any],
    audit: dict[str, Any],
) -> None:
    replay_state, replay_audit = build_lot38_artifacts(root, code_commit)
    require(replay_state.to_dict() == state, "Lot 38 deterministic state replay mismatch")
    require(replay_audit.to_dict() == audit, "Lot 38 deterministic audit replay mismatch")


def validate(root: Path, expected_code_commit: str | None = None) -> dict[str, object]:
    state, audit, snapshot, health = load_artifacts(root)
    checksums = validate_links(state, audit, snapshot, health)
    validate_reference_state(state, snapshot, health)
    code_commit = validate_code_commit(state, audit, expected_code_commit)
    validate_replay(root, code_commit, state, audit)
    state_checksum, audit_checksum, snapshot_checksum, health_checksum = checksums
    return {
        "schema_version": "lot38-validation-v1",
        "status": "PASS",
        "validation_state": "VALIDATED_OFFLINE_L2_SNAPSHOT_ONLY",
        "code_commit": code_commit,
        "state_output_checksum": state_checksum,
        "audit_checksum": audit_checksum,
        "snapshot_checksum": snapshot_checksum,
        "health_checksum": health_checksum,
        "published_bid_depth": snapshot["published_bid_depth"],
        "published_ask_depth": snapshot["published_ask_depth"],
        "next_lot": 39,
        "next_lot_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Validate Lot 38 offline L2 snapshot evidence")
    value.add_argument("--root", type=Path, default=Path("."))
    value.add_argument("--expected-code-commit")
    return value


def main() -> int:
    args = parser().parse_args()
    try:
        print(
            json.dumps(
                validate(args.root.resolve(), args.expected_code_commit),
                sort_keys=True,
            )
        )
    except (Lot38ValidationError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT38 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
