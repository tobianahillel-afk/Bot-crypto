from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)

from .order_flow_delta_and_cvd_engine_models import (
    CVDPointV1,
    CVDSeriesV1,
    Lot45LineageEnvelopeV1,
    Lot45RunContextV1,
    OrderFlowDeltaCVDEngineAuditV1,
    OrderFlowDeltaCVDEngineStateV1,
    OrderFlowStateV1,
)
from .order_flow_delta_and_cvd_engine_validation import (
    EXPECTED_SAFETY,
    POLICY_VERSION,
    RUNTIME_MODE,
    VALIDATION_STATE,
    OrderFlowDeltaCVDValidationError,
    require,
    require_git_sha,
    require_sha256,
    validate_config,
)

CONFIG_PATH = Path("config/microstructure/order_flow_delta_cvd_engine_v1.json")
LOT44_STATE_PATH = Path("data/audit/trades_and_aggressor_classification_schema_lot44.json")
LOT44_AUDIT_PATH = Path("data/audit/trades_and_aggressor_classification_schema_audit_lot44.json")
LOT44_CONFIDENCE_PATH = Path("data/audit/aggressor_confidence_state_lot44.json")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrderFlowDeltaCVDValidationError(f"unable to load Lot45 JSON: {path}") from exc
    require(isinstance(payload, dict), f"Lot45 JSON root must be object: {path}")
    return payload


def _verify_canonical(payload: dict[str, Any], field: str) -> str:
    expected = require_sha256(payload.get(field), field)
    body = dict(payload)
    body.pop(field)
    require(canonical_checksum(body) == expected, f"Lot45 upstream canonical checksum mismatch: {field}")
    return expected


def _validate_lot44_inputs(
    state: dict[str, Any],
    audit: dict[str, Any],
    confidence: dict[str, Any],
) -> tuple[str, str, str, str]:
    state_checksum = _verify_canonical(state, "output_checksum")
    audit_checksum = _verify_canonical(audit, "audit_checksum")
    confidence_checksum = _verify_canonical(confidence, "confidence_checksum")
    require(
        state.get("schema_version") == "trades-aggressor-classification-schema-state-v1",
        "Lot45 requires Lot44 state v1",
    )
    require(
        audit.get("schema_version") == "trades-aggressor-classification-schema-audit-v1",
        "Lot45 requires Lot44 audit v1",
    )
    require(
        confidence.get("schema_version") == "aggressor-confidence-state-v1",
        "Lot45 requires Lot44 confidence state v1",
    )
    require(
        state.get("validation_state") == "VALIDATED_OFFLINE_AGGRESSOR_CLASSIFICATION_ONLY",
        "Lot45 requires validated Lot44 state",
    )
    require(audit.get("state_output_checksum") == state_checksum, "Lot44 audit/state link mismatch")
    require(state.get("confidence_state") == confidence, "Lot44 state/confidence link mismatch")
    run_context = state.get("run_context")
    require(isinstance(run_context, dict), "Lot44 run context missing")
    code_commit = require_git_sha(run_context.get("code_commit"), "lot44_code_commit")
    require(audit.get("code_commit") == code_commit, "Lot44 source identity mismatch")
    require(audit.get("safety") == EXPECTED_SAFETY, "Lot44 audit safety changed")
    require(state.get("safety") == EXPECTED_SAFETY, "Lot44 state safety changed")
    return state_checksum, audit_checksum, confidence_checksum, code_commit


def _build_order_flow(classified: list[dict[str, Any]]) -> OrderFlowStateV1:
    counts = {"BUY_AGGRESSOR": 0, "SELL_AGGRESSOR": 0, "UNKNOWN": 0}
    volumes = {
        "BUY_AGGRESSOR": Decimal("0"),
        "SELL_AGGRESSOR": Decimal("0"),
        "UNKNOWN": Decimal("0"),
    }
    for item in classified:
        classification = item.get("aggressor_classification")
        require(classification in counts, "Lot45 received unknown Lot44 classification")
        trade = item.get("trade")
        require(isinstance(trade, dict), "Lot45 classified trade payload missing")
        quantity = Decimal(str(trade.get("quantity")))
        require(quantity.is_finite() and quantity > 0, "Lot45 trade quantity invalid")
        counts[classification] += 1
        volumes[classification] += quantity
    total = sum(volumes.values(), Decimal("0"))
    payload = {
        "schema_version": "order-flow-state-v1",
        "trades_total": len(classified),
        "buy_trades_total": counts["BUY_AGGRESSOR"],
        "sell_trades_total": counts["SELL_AGGRESSOR"],
        "unknown_trades_total": counts["UNKNOWN"],
        "total_volume": str(total),
        "buy_volume": str(volumes["BUY_AGGRESSOR"]),
        "sell_volume": str(volumes["SELL_AGGRESSOR"]),
        "unknown_volume": str(volumes["UNKNOWN"]),
        "signed_delta": str(volumes["BUY_AGGRESSOR"] - volumes["SELL_AGGRESSOR"]),
        "unknown_volume_ratio": str(volumes["UNKNOWN"] / total),
    }
    checksum = canonical_checksum(payload)
    return OrderFlowStateV1(
        trades_total=len(classified),
        buy_trades_total=counts["BUY_AGGRESSOR"],
        sell_trades_total=counts["SELL_AGGRESSOR"],
        unknown_trades_total=counts["UNKNOWN"],
        total_volume=total,
        buy_volume=volumes["BUY_AGGRESSOR"],
        sell_volume=volumes["SELL_AGGRESSOR"],
        unknown_volume=volumes["UNKNOWN"],
        signed_delta=volumes["BUY_AGGRESSOR"] - volumes["SELL_AGGRESSOR"],
        unknown_volume_ratio=volumes["UNKNOWN"] / total,
        order_flow_checksum=checksum,
    )


def _build_cvd(classified: list[dict[str, Any]]) -> CVDSeriesV1:
    running = Decimal("0")
    points: list[CVDPointV1] = []
    for sequence, item in enumerate(classified):
        trade = item["trade"]
        classification = str(item["aggressor_classification"])
        quantity = Decimal(str(trade["quantity"]))
        signed = {
            "BUY_AGGRESSOR": quantity,
            "SELL_AGGRESSOR": -quantity,
            "UNKNOWN": Decimal("0"),
        }[classification]
        running += signed
        points.append(
            CVDPointV1(
                sequence=sequence,
                trade_id=str(trade["trade_id"]),
                event_time=str(trade["event_time"]),
                receive_time=str(trade["receive_time"]),
                aggressor_classification=classification,
                quantity=quantity,
                signed_trade_delta=signed,
                cumulative_delta=running,
            )
        )
    provisional = CVDSeriesV1(
        policy_version=POLICY_VERSION,
        starting_cvd=Decimal("0"),
        points=tuple(points),
        final_cvd=running,
        cvd_checksum="0" * 64,
    )
    checksum = canonical_checksum(provisional.payload_without_checksum())
    return CVDSeriesV1(
        policy_version=POLICY_VERSION,
        starting_cvd=Decimal("0"),
        points=tuple(points),
        final_cvd=running,
        cvd_checksum=checksum,
    )


def build_lot45_artifacts(
    root: Path,
    *,
    code_commit: str,
) -> tuple[OrderFlowDeltaCVDEngineStateV1, OrderFlowDeltaCVDEngineAuditV1]:
    code_commit = require_git_sha(code_commit, "code_commit")
    config = _load_json(root / CONFIG_PATH)
    validate_config(config)
    lot44_state = _load_json(root / LOT44_STATE_PATH)
    lot44_audit = _load_json(root / LOT44_AUDIT_PATH)
    lot44_confidence = _load_json(root / LOT44_CONFIDENCE_PATH)
    state_checksum, audit_checksum, confidence_checksum, lot44_code_commit = _validate_lot44_inputs(
        lot44_state,
        lot44_audit,
        lot44_confidence,
    )
    classified_raw = lot44_state.get("classified_trades")
    require(isinstance(classified_raw, list) and bool(classified_raw), "Lot45 requires non-empty Lot44 classified trades")
    classified = [dict(item) for item in classified_raw]
    order_flow = _build_order_flow(classified)
    cvd = _build_cvd(classified)
    event_time = max(str(item["trade"]["event_time"]) for item in classified)
    receive_time = max(str(item["trade"]["receive_time"]) for item in classified)
    generated_at = str(config["generated_at"])
    run_context = Lot45RunContextV1(
        run_id="lot45-reference-run",
        runtime_mode=RUNTIME_MODE,
        config_version=str(config["config_version"]),
        code_commit=code_commit,
        correlation_id="lot45-reference-correlation",
    )
    lineage = Lot45LineageEnvelopeV1(
        lot44_state_checksum=state_checksum,
        lot44_audit_checksum=audit_checksum,
        lot44_confidence_checksum=confidence_checksum,
        lot44_code_commit=lot44_code_commit,
        available_at=str(lot44_state["generated_at"]),
    )
    provisional = OrderFlowDeltaCVDEngineStateV1(
        run_context=run_context,
        lineage=lineage,
        event_time=event_time,
        receive_time=receive_time,
        generated_at=generated_at,
        validation_state=VALIDATION_STATE,
        order_flow=order_flow,
        cvd=cvd,
        reason_codes=(
            "LOT45_ORDER_FLOW_DELTA_CVD_VALIDATED",
            "UNKNOWN_VOLUME_PRESERVED_UNSIGNED",
            "CVD_SOURCE_ORDER_DETERMINISTIC",
            "LOT44_CLASSIFICATION_LINEAGE_BOUND",
            "LOT46_REMAINS_LOCKED",
        ),
        safety=EXPECTED_SAFETY,
        output_checksum="0" * 64,
    )
    output_checksum = canonical_checksum(provisional.payload_without_checksum())
    state = OrderFlowDeltaCVDEngineStateV1(
        run_context=run_context,
        lineage=lineage,
        event_time=event_time,
        receive_time=receive_time,
        generated_at=generated_at,
        validation_state=VALIDATION_STATE,
        order_flow=order_flow,
        cvd=cvd,
        reason_codes=provisional.reason_codes,
        safety=EXPECTED_SAFETY,
        output_checksum=output_checksum,
    )
    config_checksum = canonical_checksum(config)
    audit_provisional = OrderFlowDeltaCVDEngineAuditV1(
        code_commit=code_commit,
        state_output_checksum=output_checksum,
        config_checksum=config_checksum,
        lot44_state_checksum=state_checksum,
        lot44_audit_checksum=audit_checksum,
        lot44_confidence_checksum=confidence_checksum,
        validation_state=VALIDATION_STATE,
        safety=EXPECTED_SAFETY,
        audit_checksum="0" * 64,
    )
    final_audit_checksum = canonical_checksum(audit_provisional.payload_without_checksum())
    audit = OrderFlowDeltaCVDEngineAuditV1(
        code_commit=code_commit,
        state_output_checksum=output_checksum,
        config_checksum=config_checksum,
        lot44_state_checksum=state_checksum,
        lot44_audit_checksum=audit_checksum,
        lot44_confidence_checksum=confidence_checksum,
        validation_state=VALIDATION_STATE,
        safety=EXPECTED_SAFETY,
        audit_checksum=final_audit_checksum,
    )
    return state, audit
