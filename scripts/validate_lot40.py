#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector import (
    AUDIT_PATH,
    INTEGRITY_PATH,
    STATE_PATH,
    VETO_PATH,
    build_lot40_artifacts,
)
from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector_validation import (
    BookIntegrityValidationError,
    lot40_safety,
)

LOT41_FORBIDDEN_PATHS = (
    "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine.py",
    "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine_models.py",
    "scripts/run_lot41_spread_depth_and_imbalance_engine.py",
    "scripts/validate_lot41.py",
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Validate Lot 40 deterministic book integrity")
    value.add_argument("--root", type=Path, default=Path("."))
    value.add_argument("--expected-code-commit", required=True)
    value.add_argument("--require-persisted", action="store_true")
    return value


def _verify_reference(
    root: Path,
    code_commit: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    state, audit = build_lot40_artifacts(root, code_commit)
    integrity = state.book_integrity
    veto = state.book_health_veto
    if state.validation_state != "VALIDATED_OFFLINE_BOOK_INTEGRITY_ONLY":
        raise BookIntegrityValidationError("canonical Lot 40 validation state changed")
    if integrity.health_status != "HEALTHY":
        raise BookIntegrityValidationError("canonical Lot 40 health is not HEALTHY")
    if integrity.book_health_score != Decimal("100"):
        raise BookIntegrityValidationError("canonical Lot 40 score changed")
    if veto.consequence != "NONE" or veto.veto_active or veto.critical_veto_active:
        raise BookIntegrityValidationError("canonical Lot 40 veto state changed")
    if integrity.stale_age_us != 30_000:
        raise BookIntegrityValidationError("canonical Lot 40 stale age changed")
    if (integrity.bid_depth_levels, integrity.ask_depth_levels) != (2, 3):
        raise BookIntegrityValidationError("canonical Lot 40 depth changed")
    if integrity.crossed or integrity.locked:
        raise BookIntegrityValidationError("canonical Lot 40 reference book is crossed/locked")
    if not integrity.checksum_valid or not integrity.level_monotonicity_valid:
        raise BookIntegrityValidationError("canonical Lot 40 integrity component changed")
    if any(not component.passed for component in integrity.components):
        raise BookIntegrityValidationError("canonical Lot 40 component failed")
    if state.metrics.health_components_failed_total != 0:
        raise BookIntegrityValidationError("canonical Lot 40 failure metric changed")
    if state.metrics.critical_components_failed_total != 0:
        raise BookIntegrityValidationError("canonical Lot 40 critical metric changed")
    if "LOT41_REMAINS_LOCKED" not in state.reason_codes:
        raise BookIntegrityValidationError("Lot 41 lock reason missing")
    if state.safety != lot40_safety() or audit.safety != lot40_safety():
        raise BookIntegrityValidationError("Lot 40 safety boundary changed")
    if audit.state_output_checksum != state.output_checksum:
        raise BookIntegrityValidationError("Lot 40 state/audit checksum link changed")
    if audit.integrity_checksum != integrity.integrity_checksum:
        raise BookIntegrityValidationError("Lot 40 integrity/audit checksum link changed")
    if audit.veto_checksum != veto.veto_checksum:
        raise BookIntegrityValidationError("Lot 40 veto/audit checksum link changed")
    return state.to_dict(), audit.to_dict()


def _verify_deterministic(
    root: Path,
    code_commit: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    state1, audit1 = _verify_reference(root, code_commit)
    state2, audit2 = _verify_reference(root, code_commit)
    if state1 != state2 or audit1 != audit2:
        raise BookIntegrityValidationError("Lot 40 replay is non-deterministic")
    return state1, audit1


def _verify_checksum(payload: dict[str, Any], field: str, label: str) -> None:
    body = dict(payload)
    checksum = body.pop(field, None)
    if not isinstance(checksum, str) or canonical_checksum(body) != checksum:
        raise BookIntegrityValidationError(f"persisted Lot 40 {label} checksum invalid")


def _verify_persisted(root: Path, state: dict[str, Any], audit: dict[str, Any]) -> None:
    paths = {
        "state": root / STATE_PATH,
        "audit": root / AUDIT_PATH,
        "integrity": root / INTEGRITY_PATH,
        "veto": root / VETO_PATH,
    }
    for label, path in paths.items():
        if not path.exists():
            raise BookIntegrityValidationError(f"persisted Lot 40 {label} missing")
    persisted = {label: load_json_object(path) for label, path in paths.items()}
    if persisted["state"] != state:
        raise BookIntegrityValidationError("persisted Lot 40 state differs from replay")
    if persisted["audit"] != audit:
        raise BookIntegrityValidationError("persisted Lot 40 audit differs from replay")
    if persisted["integrity"] != state["book_integrity"]:
        raise BookIntegrityValidationError("persisted Lot 40 integrity differs from state")
    if persisted["veto"] != state["book_health_veto"]:
        raise BookIntegrityValidationError("persisted Lot 40 veto differs from state")
    _verify_checksum(persisted["state"], "output_checksum", "state")
    _verify_checksum(persisted["audit"], "audit_checksum", "audit")
    _verify_checksum(persisted["integrity"], "integrity_checksum", "integrity")
    _verify_checksum(persisted["veto"], "veto_checksum", "veto")


def _verify_lot41_absent(root: Path) -> None:
    for relative in LOT41_FORBIDDEN_PATHS:
        if (root / relative).exists():
            raise BookIntegrityValidationError(f"Lot 41 implementation detected: {relative}")


def validate(root: Path, code_commit: str, require_persisted: bool) -> dict[str, Any]:
    state, audit = _verify_deterministic(root, code_commit)
    _verify_lot41_absent(root)
    if require_persisted:
        _verify_persisted(root, state, audit)
    integrity = state["book_integrity"]
    veto = state["book_health_veto"]
    if not isinstance(integrity, dict) or not isinstance(veto, dict):
        raise BookIntegrityValidationError("canonical Lot 40 surfaces missing")
    result: dict[str, Any] = {
        "schema_version": "lot40-validation-result-v1",
        "status": "PASS",
        "validation_state": state["validation_state"],
        "health_status": integrity["health_status"],
        "book_health_score": integrity["book_health_score"],
        "consequence": veto["consequence"],
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "integrity_checksum": integrity["integrity_checksum"],
        "veto_checksum": veto["veto_checksum"],
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
        "lot41_status": "PLANNED_LOCKED",
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = validate(
            args.root.resolve(),
            args.expected_code_commit,
            args.require_persisted,
        )
        print(json.dumps(result, sort_keys=True))
    except (
        BookIntegrityValidationError,
        OSError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"LOT40 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
