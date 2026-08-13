#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema import (
    AUDIT_PATH,
    CONFIDENCE_PATH,
    STATE_PATH,
    build_lot44_artifacts,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_validation import (
    TradesAggressorClassificationValidationError,
    require,
)

EXPECTED_CLASSIFICATIONS = (
    "UNKNOWN",
    "BUY_AGGRESSOR",
    "SELL_AGGRESSOR",
)
EXPECTED_METHODS = ("NONE", "QUOTE_TEST", "QUOTE_TEST")
EXPECTED_TOTAL_VOLUME = "0.16"
EXPECTED_BUY_VOLUME = "0.08"
EXPECTED_SELL_VOLUME = "0.03"
EXPECTED_UNKNOWN_VOLUME = "0.05"
EXPECTED_UNKNOWN_RATIO = "0.3125"


def _validate_reference(state: dict[str, object]) -> None:
    trades = state.get("classified_trades")
    require(isinstance(trades, list) and len(trades) == 3, "reference must contain three classified trades")
    classifications = tuple(item["aggressor_classification"] for item in trades)
    methods = tuple(item["classification_method"] for item in trades)
    require(classifications == EXPECTED_CLASSIFICATIONS, "reference aggressor classifications changed")
    require(methods == EXPECTED_METHODS, "reference classification methods changed")
    metrics = state.get("metrics")
    require(isinstance(metrics, dict), "reference metrics missing")
    expected = {
        "lot_44_trades_total": 3,
        "lot_44_buy_trades_total": 1,
        "lot_44_sell_trades_total": 1,
        "lot_44_unknown_trades_total": 1,
        "total_volume": EXPECTED_TOTAL_VOLUME,
        "buy_volume": EXPECTED_BUY_VOLUME,
        "sell_volume": EXPECTED_SELL_VOLUME,
        "unknown_volume": EXPECTED_UNKNOWN_VOLUME,
        "unknown_volume_ratio": EXPECTED_UNKNOWN_RATIO,
    }
    require(all(metrics.get(field) == value for field, value in expected.items()), "reference metrics changed")
    require(state.get("safety", {}).get("trade_allowed") is False, "Lot 44 enabled trading")
    require(state.get("safety", {}).get("execution_allowed") is False, "Lot 44 enabled execution")
    require(state.get("safety", {}).get("approved_size") == 0, "Lot 44 approved size changed")


def _verify_checksum(payload: dict[str, object], field: str) -> None:
    body = dict(payload)
    value = body.pop(field, None)
    require(isinstance(value, str) and canonical_checksum(body) == value, f"{field} mismatch")


def validate(root: Path, *, expected_code_commit: str, require_persisted: bool) -> dict[str, object]:
    state, audit = build_lot44_artifacts(root, code_commit=expected_code_commit)
    state_dict, audit_dict = state.to_dict(), audit.to_dict()
    _validate_reference(state_dict)
    _verify_checksum(state_dict, "output_checksum")
    _verify_checksum(audit_dict, "audit_checksum")
    _verify_checksum(state.confidence_state.to_dict(), "confidence_checksum")
    if require_persisted:
        require(load_json_object(root / STATE_PATH) == state_dict, "persisted Lot 44 state differs from replay")
        require(load_json_object(root / AUDIT_PATH) == audit_dict, "persisted Lot 44 audit differs from replay")
        require(load_json_object(root / CONFIDENCE_PATH) == state.confidence_state.to_dict(), "persisted confidence state differs from replay")
    result: dict[str, object] = {
        "schema_version": "lot44-validation-v1",
        "status": "PASS",
        "code_commit": expected_code_commit,
        "state_output_checksum": state.output_checksum,
        "audit_checksum": audit.audit_checksum,
        "confidence_checksum": state.confidence_state.confidence_checksum,
        "reference_classifications": list(EXPECTED_CLASSIFICATIONS),
        "unknown_volume_ratio": EXPECTED_UNKNOWN_RATIO,
        "lot45_status": "PLANNED_LOCKED",
        "lot46_status": "PLANNED_LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = canonical_checksum(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Lot 44")
    parser.add_argument("--expected-code-commit", required=True)
    parser.add_argument("--require-persisted", action="store_true")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    try:
        result = validate(Path(args.root).resolve(), expected_code_commit=args.expected_code_commit, require_persisted=args.require_persisted)
        print(json.dumps(result, sort_keys=True))
    except (TradesAggressorClassificationValidationError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"LOT44 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
