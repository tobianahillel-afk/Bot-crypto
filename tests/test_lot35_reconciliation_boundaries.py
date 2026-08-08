from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.candle_trade_book_reconciliation import (
    _build_veto,
    _corrective_action,
    _snapshot,
    build_reconciliation_reports,
)
from crypto_quant_bot.data_governance.candle_trade_book_reconciliation_models import (
    CandleTradeBookReconciliationAuditV1,
    CandleTradeBookReconciliationStateV1,
    Lot35LineageEnvelopeV1,
    Lot35MetricsV1,
    Lot35RunContextV1,
    ReconciliationDeltaV1,
    ReconciliationReportV1,
    ReconciliationSnapshotV1,
    ReconciliationVetoV1,
)
from crypto_quant_bot.data_governance.candle_trade_book_reconciliation_validation import (
    ReconciliationError,
    canonical_decimal,
    duration_us,
    lot35_safety,
    validate_lot35_safety,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/data_governance/candle_trade_book_reconciliation_v1.json"


def load_config() -> dict[str, object]:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def single_record_config() -> dict[str, object]:
    config = load_config()
    config["records"] = [copy.deepcopy(config["records"][0])]
    return config


def test_critical_multiplier_boundary_is_minor_then_critical() -> None:
    config = single_record_config()
    config["records"][0]["secondary"]["price"] = "50010.10"
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "MINOR_DIVERGENCE"
    config["records"][0]["secondary"]["price"] = "50010.1001"
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "CRITICAL_DIVERGENCE"


def test_timestamp_boundary_is_tolerated_then_minor_then_critical() -> None:
    config = single_record_config()
    secondary = config["records"][0]["secondary"]
    secondary["event_time"] = "2026-08-06T19:18:00.100000Z"
    assert build_reconciliation_reports(config)[0].classification == "TOLERATED_DIFF"
    secondary["event_time"] = "2026-08-06T19:18:00.100001Z"
    assert build_reconciliation_reports(config)[0].classification == "MINOR_DIVERGENCE"
    secondary["event_time"] = "2026-08-06T19:18:01.000001Z"
    assert build_reconciliation_reports(config)[0].classification == "CRITICAL_DIVERGENCE"


def test_unexplained_fee_difference_adds_pause_reason() -> None:
    config = single_record_config()
    config["records"][0]["secondary"]["fee"] = "0.02"
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "MINOR_DIVERGENCE"
    assert "RECONCILIATION_FEE_DIFF_REQUIRES_PAUSE" in report.reason_codes


def test_quantity_balance_and_position_deltas_are_exact_decimal_strings() -> None:
    config = single_record_config()
    secondary = config["records"][0]["secondary"]
    secondary["quantity"] = "1.25000001"
    secondary["balance"] = "100000.01"
    secondary["position"] = "1.25000001"
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "TOLERATED_DIFF"
    assert report.delta is not None
    assert report.delta.quantity_abs == "0.00000001"
    assert report.delta.balance_abs == "0.01"
    assert report.delta.position_abs == "0.00000001"


def test_empty_records_fail_closed() -> None:
    config = load_config()
    config["records"] = []
    with pytest.raises(ReconciliationError, match="requires reconciliation records"):
        build_reconciliation_reports(config)


def test_unknown_config_field_fails_closed() -> None:
    config = load_config()
    config["unexpected"] = True
    with pytest.raises(ReconciliationError, match="configuration fields"):
        build_reconciliation_reports(config)


def test_invalid_config_schema_and_version_fail_closed() -> None:
    config = load_config()
    config["schema_version"] = "wrong"
    with pytest.raises(ReconciliationError, match="configuration schema"):
        build_reconciliation_reports(config)
    config = load_config()
    config["config_version"] = "wrong"
    with pytest.raises(ReconciliationError, match="configuration version"):
        build_reconciliation_reports(config)


def test_invalid_causal_times_fail_closed() -> None:
    config = load_config()
    config["available_at"] = "2026-08-06T19:18:59.000000Z"
    with pytest.raises(ReconciliationError, match="causal availability"):
        build_reconciliation_reports(config)


def test_invalid_tolerance_shapes_and_values_fail_closed() -> None:
    config = load_config()
    del config["tolerances"]["fee_abs"]
    with pytest.raises(ReconciliationError, match="tolerances differ"):
        build_reconciliation_reports(config)
    config = load_config()
    config["tolerances"]["fee_abs"] = "-0.01"
    with pytest.raises(ReconciliationError, match="non-negative"):
        build_reconciliation_reports(config)
    config = load_config()
    config["critical_multiplier"] = 0
    with pytest.raises(ReconciliationError, match=">= 1"):
        build_reconciliation_reports(config)


def test_invalid_record_and_snapshot_shapes_fail_closed() -> None:
    config = single_record_config()
    config["records"][0]["extra"] = "x"
    with pytest.raises(ReconciliationError, match="record fields"):
        build_reconciliation_reports(config)
    config = single_record_config()
    del config["records"][0]["primary"]["fee"]
    with pytest.raises(ReconciliationError, match="snapshot fields"):
        build_reconciliation_reports(config)


def test_invalid_entity_source_and_double_orphan_fail_closed() -> None:
    config = single_record_config()
    config["records"][0]["entity_type"] = "ORDER"
    with pytest.raises(ReconciliationError, match="entity type"):
        build_reconciliation_reports(config)
    config = single_record_config()
    config["records"][0]["source_of_truth"] = "MAGIC"
    with pytest.raises(ReconciliationError, match="source-of-truth"):
        build_reconciliation_reports(config)
    config = single_record_config()
    config["records"][0]["primary"] = None
    config["records"][0]["secondary"] = None
    with pytest.raises(ReconciliationError, match="two absent sources"):
        build_reconciliation_reports(config)


def test_snapshot_rejects_negative_values_and_bad_time() -> None:
    with pytest.raises(ReconciliationError, match="non-negative"):
        ReconciliationSnapshotV1("r", "i", "-1", "1", "0", "1", "0", "2026-08-06T00:00:00Z")
    with pytest.raises(ReconciliationError, match="must be UTC"):
        ReconciliationSnapshotV1("r", "i", "1", "1", "0", "1", "0", "2026-08-06T00:00:00+01:00")
    snapshot = ReconciliationSnapshotV1(
        "r", "i", "1", "2", "0", "3", "4", "2026-08-06T00:00:00Z"
    )
    assert snapshot.to_dict()["schema_version"] == "reconciliation-snapshot-v1"


def test_delta_and_report_contracts_reject_invalid_combinations() -> None:
    with pytest.raises(ReconciliationError, match="non-negative"):
        ReconciliationDeltaV1("-1", "0", "0", "0", "0", 0)
    delta = ReconciliationDeltaV1("0", "0", "0", "0", "0", 0)
    with pytest.raises(ReconciliationError, match="orphan reconciliation"):
        ReconciliationReportV1(
            "r", "TRADE", "PRIMARY", "p", None, "CRITICAL_DIVERGENCE",
            delta, "tol-v1", False, True, "MANUAL_RECONCILIATION_REQUIRED", ("ORPHAN",),
        )


def test_report_contract_rejects_all_invalid_enums_and_empty_reasons() -> None:
    delta = ReconciliationDeltaV1("0", "0", "0", "0", "0", 0)
    base = dict(
        reconciliation_id="r",
        entity_type="TRADE",
        source_of_truth="PRIMARY",
        primary_record_id="p",
        secondary_record_id="s",
        classification="MATCH",
        delta=delta,
        tolerance_version="tol",
        duplicate=False,
        orphan=False,
        corrective_action="NONE",
        reason_codes=("MATCH",),
    )
    for field, value, message in (
        ("entity_type", "ORDER", "entity type"),
        ("source_of_truth", "MAGIC", "source-of-truth"),
        ("classification", "UNKNOWN", "classification"),
        ("corrective_action", "WAIT", "corrective action"),
    ):
        payload = dict(base)
        payload[field] = value
        with pytest.raises(ReconciliationError, match=message):
            ReconciliationReportV1(**payload)
    payload = dict(base)
    payload["reason_codes"] = ()
    with pytest.raises(ReconciliationError, match="requires reason codes"):
        ReconciliationReportV1(**payload)
    orphan_primary_missing = ReconciliationReportV1(
        "orphan-primary", "TRADE", "PRIMARY", None, "s", "CRITICAL_DIVERGENCE",
        None, "tol", False, True, "MANUAL_RECONCILIATION_REQUIRED", ("ORPHAN",),
    )
    assert orphan_primary_missing.primary_record_id is None


def test_veto_contract_and_priority() -> None:
    match_report = ReconciliationReportV1(
        "m", "TRADE", "PRIMARY", "p", "s", "MATCH",
        ReconciliationDeltaV1("0", "0", "0", "0", "0", 0),
        "tol-v1", False, False, "NONE", ("MATCH",),
    )
    minor_report = ReconciliationReportV1(
        "n", "TRADE", "PRIMARY", "p2", "s2", "MINOR_DIVERGENCE",
        ReconciliationDeltaV1("0", "0.02", "0", "0", "0", 0),
        "tol-v1", False, False, "REVIEW_AND_PAUSE", ("MINOR",),
    )
    critical_report = ReconciliationReportV1(
        "c", "TRADE", "PRIMARY", "p3", "s3", "CRITICAL_DIVERGENCE",
        ReconciliationDeltaV1("0", "1", "0", "0", "0", 0),
        "tol-v1", False, False, "MANUAL_RECONCILIATION_REQUIRED", ("CRITICAL",),
    )
    assert _build_veto((match_report,)).action == "ALLOW_ANALYSIS"
    assert _build_veto((minor_report,)).action == "PAUSE"
    assert _build_veto((minor_report, critical_report)).action == "KILL_SWITCH"
    with pytest.raises(ReconciliationError, match="veto action"):
        ReconciliationVetoV1("WAIT", True, 0, 0, ("X",))
    with pytest.raises(ReconciliationError, match="requires reason codes"):
        ReconciliationVetoV1("PAUSE", True, 1, 0, ())


def test_validation_helpers_are_exact_and_fail_closed() -> None:
    from datetime import UTC, datetime
    from decimal import Decimal

    assert duration_us(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 1, 0, 0, 0, 1, tzinfo=UTC),
    ) == 1
    assert canonical_decimal(Decimal("1.230000")) == "1.23"
    assert canonical_decimal(Decimal("100")) == "100"
    assert canonical_decimal(Decimal("0.000")) == "0"
    with pytest.raises(ReconciliationError, match="finite"):
        canonical_decimal(Decimal("Infinity"))
    assert validate_lot35_safety(lot35_safety()) == lot35_safety()
    with pytest.raises(ReconciliationError, match="safety boundary"):
        validate_lot35_safety({})


def test_run_context_and_private_helpers_fail_closed() -> None:
    with pytest.raises(ReconciliationError, match="DATA_GOVERNANCE_ONLY"):
        Lot35RunContextV1("r", "PAPER", "c", "0" * 40, "x")
    with pytest.raises(ReconciliationError, match="snapshot must be an object"):
        _snapshot("not-an-object")
    with pytest.raises(ReconciliationError, match="unexpected reconciliation classification"):
        _corrective_action("UNKNOWN")


def _valid_state_parts() -> tuple[
    Lot35RunContextV1,
    Lot35LineageEnvelopeV1,
    ReconciliationReportV1,
    ReconciliationVetoV1,
    Lot35MetricsV1,
]:
    context = Lot35RunContextV1("r", "DATA_GOVERNANCE_ONLY", "c", "0" * 40, "x")
    lineage = Lot35LineageEnvelopeV1(
        "l", "0" * 64, "1" * 64, "2" * 64, "3" * 64, "4" * 64,
        "2026-08-06T00:00:00Z",
    )
    report = ReconciliationReportV1(
        "m", "BOOK", "PRIMARY", "p", "s", "MATCH",
        ReconciliationDeltaV1("0", "0", "0", "0", "0", 0),
        "tol", False, False, "NONE", ("MATCH",),
    )
    veto = ReconciliationVetoV1("ALLOW_ANALYSIS", True, 0, 0, ("PASS",))
    metrics = Lot35MetricsV1(1, 0, 1, 0, 0, 0, 0)
    return context, lineage, report, veto, metrics


def test_state_rejects_bad_causality_validation_state_empty_reports_and_safety() -> None:
    context, lineage, report, veto, metrics = _valid_state_parts()
    with pytest.raises(ReconciliationError, match="causal availability"):
        CandleTradeBookReconciliationStateV1(
            context, lineage, "2026-08-06T00:00:02Z", "2026-08-06T00:00:01Z",
            "2026-08-06T00:00:03Z", "VALIDATED_RECONCILIATION_ONLY", (report,), veto,
            metrics, ("PASS",), lot35_safety(), "5" * 64,
        )
    with pytest.raises(ReconciliationError, match="validation state"):
        CandleTradeBookReconciliationStateV1(
            context, lineage, "2026-08-06T00:00:00Z", "2026-08-06T00:00:01Z",
            "2026-08-06T00:00:02Z", "UNKNOWN", (report,), veto,
            metrics, ("PASS",), lot35_safety(), "5" * 64,
        )
    with pytest.raises(ReconciliationError, match="requires reconciliation reports"):
        CandleTradeBookReconciliationStateV1(
            context, lineage, "2026-08-06T00:00:00Z", "2026-08-06T00:00:01Z",
            "2026-08-06T00:00:02Z", "VALIDATED_RECONCILIATION_ONLY", (), veto,
            metrics, ("PASS",), lot35_safety(), "5" * 64,
        )
    bad_safety = lot35_safety()
    bad_safety["trade_allowed"] = True
    with pytest.raises(ReconciliationError, match="safety boundary"):
        CandleTradeBookReconciliationStateV1(
            context, lineage, "2026-08-06T00:00:00Z", "2026-08-06T00:00:01Z",
            "2026-08-06T00:00:02Z", "VALIDATED_RECONCILIATION_ONLY", (report,), veto,
            metrics, ("PASS",), bad_safety, "5" * 64,
        )


def test_audit_contract_rejects_invalid_veto() -> None:
    with pytest.raises(ReconciliationError, match="audit veto action"):
        CandleTradeBookReconciliationAuditV1(
            "0" * 40, "1" * 64, "2" * 64, "3" * 64, "4" * 64,
            1, 1, 0, 0, 0, "WAIT", "VALIDATED_RECONCILIATION_ONLY",
            lot35_safety(), "5" * 64,
        )
