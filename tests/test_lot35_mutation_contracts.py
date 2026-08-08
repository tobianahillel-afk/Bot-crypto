from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.candle_trade_book_reconciliation import (
    _build_veto,
    build_reconciliation_reports,
)
from crypto_quant_bot.data_governance.candle_trade_book_reconciliation_models import (
    ReconciliationDeltaV1,
    ReconciliationReportV1,
)
from crypto_quant_bot.data_governance.candle_trade_book_reconciliation_validation import (
    ReconciliationError,
    canonical_decimal,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/data_governance/candle_trade_book_reconciliation_v1.json"


def load_config() -> dict[str, object]:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def one_record() -> dict[str, object]:
    config = load_config()
    config["records"] = [copy.deepcopy(config["records"][0])]
    return config


def classify_with(field: str, value: object) -> ReconciliationReportV1:
    config = one_record()
    secondary = config["records"][0]["secondary"]
    secondary[field] = value
    return build_reconciliation_reports(config)[0]


def test_zero_delta_serialization_is_exact() -> None:
    report = build_reconciliation_reports(one_record())[0]
    assert report.to_dict() == {
        "schema_version": "reconciliation-report-v1",
        "reconciliation_id": "lot35-candle-btc-eur-001",
        "entity_type": "CANDLE",
        "source_of_truth": "PRIMARY",
        "primary_record_id": "candle-primary-001",
        "secondary_record_id": "candle-secondary-001",
        "classification": "MATCH",
        "delta": {
            "schema_version": "reconciliation-delta-v1",
            "quantity_abs": "0",
            "price_abs": "0",
            "fee_abs": "0",
            "balance_abs": "0",
            "position_abs": "0",
            "timestamp_us": 0,
        },
        "tolerance_version": "lot35-reconciliation-tolerance-v1",
        "duplicate": False,
        "orphan": False,
        "corrective_action": "NONE",
        "reason_codes": ["RECONCILIATION_MATCH"],
    }


@pytest.mark.parametrize(
    ("field", "boundary", "inside", "outside"),
    [
        ("quantity", "1.25000001", "1.250000005", "1.250000011"),
        ("price", "50010.01", "50010.005", "50010.011"),
        ("fee", "0.01", "0.005", "0.011"),
        ("balance", "100000.01", "100000.005", "100000.011"),
        ("position", "1.25000001", "1.250000005", "1.250000011"),
    ],
)
def test_each_decimal_tolerance_is_inclusive_and_discriminating(
    field: str, boundary: str, inside: str, outside: str
) -> None:
    assert classify_with(field, inside).classification == "TOLERATED_DIFF"
    assert classify_with(field, boundary).classification == "TOLERATED_DIFF"
    assert classify_with(field, outside).classification == "MINOR_DIVERGENCE"


def test_each_decimal_critical_boundary_is_inclusive() -> None:
    cases = {
        "quantity": ("1.25000010", "1.250000101"),
        "price": ("50010.10", "50010.1001"),
        "fee": ("0.10", "0.1001"),
        "balance": ("100000.10", "100000.1001"),
        "position": ("1.25000010", "1.250000101"),
    }
    for field, (boundary, outside) in cases.items():
        assert classify_with(field, boundary).classification == "MINOR_DIVERGENCE"
        assert classify_with(field, outside).classification == "CRITICAL_DIVERGENCE"


def test_timestamp_boundaries_are_inclusive_by_one_microsecond() -> None:
    config = one_record()
    secondary = config["records"][0]["secondary"]
    secondary["event_time"] = "2026-08-06T19:18:00.100000Z"
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "TOLERATED_DIFF"
    assert report.delta is not None and report.delta.timestamp_us == 100_000

    secondary["event_time"] = "2026-08-06T19:18:00.100001Z"
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "MINOR_DIVERGENCE"
    assert report.delta is not None and report.delta.timestamp_us == 100_001

    secondary["event_time"] = "2026-08-06T19:18:01.000000Z"
    assert build_reconciliation_reports(config)[0].classification == "MINOR_DIVERGENCE"
    secondary["event_time"] = "2026-08-06T19:18:01.000001Z"
    assert build_reconciliation_reports(config)[0].classification == "CRITICAL_DIVERGENCE"


def test_source_truth_primary_and_secondary_are_allowed_but_unknown_blocks() -> None:
    config = one_record()
    config["records"][0]["source_of_truth"] = "PRIMARY"
    assert build_reconciliation_reports(config)[0].classification == "MATCH"
    config["records"][0]["source_of_truth"] = "SECONDARY"
    assert build_reconciliation_reports(config)[0].classification == "MATCH"
    config["records"][0]["source_of_truth"] = "UNKNOWN"
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "CRITICAL_DIVERGENCE"
    assert report.corrective_action == "MANUAL_RECONCILIATION_REQUIRED"


def test_duplicate_flag_changes_classification_and_veto_exactly() -> None:
    config = one_record()
    duplicate = copy.deepcopy(config["records"][0])
    duplicate["primary"]["record_id"] = "primary-copy"
    duplicate["secondary"]["record_id"] = "secondary-copy"
    config["records"].append(duplicate)
    reports = build_reconciliation_reports(config)
    assert [(item.duplicate, item.classification) for item in reports] == [
        (True, "MINOR_DIVERGENCE"),
        (True, "MINOR_DIVERGENCE"),
    ]
    veto = _build_veto(reports)
    assert veto.to_dict() == {
        "schema_version": "reconciliation-veto-v1",
        "action": "PAUSE",
        "reconciliation_known": True,
        "minor_divergence_count": 2,
        "critical_divergence_count": 0,
        "reason_codes": ["RECONCILIATION_MINOR_DIVERGENCE_PRESENT"],
    }


def test_critical_veto_has_priority_over_minor_veto() -> None:
    minor = ReconciliationReportV1(
        "minor", "TRADE", "PRIMARY", "p1", "s1", "MINOR_DIVERGENCE",
        ReconciliationDeltaV1("0", "0.02", "0", "0", "0", 0),
        "tol", False, False, "REVIEW_AND_PAUSE", ("MINOR",),
    )
    critical = ReconciliationReportV1(
        "critical", "BOOK", "PRIMARY", "p2", "s2", "CRITICAL_DIVERGENCE",
        ReconciliationDeltaV1("0", "1", "0", "0", "0", 0),
        "tol", False, False, "MANUAL_RECONCILIATION_REQUIRED", ("CRITICAL",),
    )
    veto = _build_veto((minor, critical))
    assert veto.action == "KILL_SWITCH"
    assert veto.minor_divergence_count == 1
    assert veto.critical_divergence_count == 1
    assert veto.reason_codes == ("RECONCILIATION_CRITICAL_DIVERGENCE_PRESENT",)


def test_identifier_comparison_is_exact_not_case_folded() -> None:
    config = one_record()
    config["records"][0]["secondary"]["identifier"] = "BTC-EUR-SPOT:1m:20260806T191800Z"
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "CRITICAL_DIVERGENCE"
    assert report.reason_codes == ("RECONCILIATION_IDENTIFIER_MISMATCH",)


def test_fee_reason_only_appears_above_normal_fee_tolerance() -> None:
    tolerated = classify_with("fee", "0.01")
    assert tolerated.classification == "TOLERATED_DIFF"
    assert "RECONCILIATION_FEE_DIFF_REQUIRES_PAUSE" not in tolerated.reason_codes
    minor = classify_with("fee", "0.011")
    assert minor.classification == "MINOR_DIVERGENCE"
    assert minor.reason_codes == (
        "RECONCILIATION_MINOR_DIVERGENCE",
        "RECONCILIATION_FEE_DIFF_REQUIRES_PAUSE",
    )


def test_canonical_decimal_never_uses_exponent_or_trailing_zeroes() -> None:
    assert canonical_decimal(Decimal("100.0000")) == "100"
    assert canonical_decimal(Decimal("0.0000000100")) == "0.00000001"
    assert canonical_decimal(Decimal("123.450000")) == "123.45"


def test_boolean_is_not_accepted_as_critical_multiplier() -> None:
    config = one_record()
    config["critical_multiplier"] = True
    with pytest.raises(ReconciliationError, match="integer"):
        build_reconciliation_reports(config)


def test_tolerance_timestamp_must_be_integer_not_boolean() -> None:
    config = one_record()
    config["tolerances"]["timestamp_us"] = False
    with pytest.raises(ReconciliationError, match="integer"):
        build_reconciliation_reports(config)


def test_record_order_does_not_change_deterministic_report_order() -> None:
    config = load_config()
    first = build_reconciliation_reports(config)
    config["records"] = list(reversed(config["records"]))
    second = build_reconciliation_reports(config)
    assert [item.to_dict() for item in first] == [item.to_dict() for item in second]
