from __future__ import annotations

import copy
import json
from pathlib import Path

from crypto_quant_bot.data_governance.candle_trade_book_reconciliation import (
    _build_veto,
    build_lot35_artifacts,
    build_reconciliation_reports,
    persist_lot35_artifacts,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/data_governance/candle_trade_book_reconciliation_v1.json"
CODE_COMMIT = "a4501bb0d400c6c1b5cf970fc5aa6456ad8c6ea8"


def load_config() -> dict[str, object]:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_reference_artifacts_are_deterministic_and_fail_closed() -> None:
    state1, audit1 = build_lot35_artifacts(ROOT, CODE_COMMIT)
    state2, audit2 = build_lot35_artifacts(ROOT, CODE_COMMIT)
    assert state1 == state2
    assert audit1 == audit2
    assert state1.output_checksum == "8fc7243beffdf985fd6947557b87ab7bd27f9191520eb2d5d9af25d1e7a886b4"
    assert audit1.audit_checksum == "98a88396f5b2e5ffc1cde02435399540ad213f5ec361b33e8a19c08b0fedf1de"
    assert canonical_checksum(state1.payload_without_checksum()) == state1.output_checksum
    assert canonical_checksum(audit1.payload_without_checksum()) == audit1.audit_checksum
    assert state1.veto.action == "ALLOW_ANALYSIS"
    assert state1.validation_state == "VALIDATED_RECONCILIATION_ONLY"
    assert state1.safety["trade_allowed"] is False
    assert state1.safety["execution_allowed"] is False
    assert state1.safety["approved_size"] == 0


def test_reference_reports_cover_all_three_entity_types() -> None:
    state, audit = build_lot35_artifacts(ROOT, CODE_COMMIT)
    assert [report.entity_type for report in state.reports] == ["BOOK", "CANDLE", "TRADE"]
    assert [report.classification for report in state.reports] == [
        "MATCH",
        "MATCH",
        "TOLERATED_DIFF",
    ]
    trade = state.reports[2]
    assert trade.delta is not None
    assert trade.delta.fee_abs == "0.005"
    assert trade.delta.timestamp_us == 50_000
    assert audit.report_count == 3
    assert audit.match_count == 2
    assert audit.tolerated_diff_count == 1
    assert audit.minor_divergence_count == 0
    assert audit.critical_divergence_count == 0


def test_persistence_writes_four_atomic_artifacts(tmp_path: Path) -> None:
    state, audit = build_lot35_artifacts(ROOT, CODE_COMMIT)
    persist_lot35_artifacts(tmp_path, state, audit)
    state_payload = json.loads(
        (tmp_path / "data/audit/candle_trade_book_reconciliation_lot35.json").read_text()
    )
    audit_payload = json.loads(
        (tmp_path / "data/audit/candle_trade_book_reconciliation_audit_lot35.json").read_text()
    )
    reports_payload = json.loads(
        (tmp_path / "data/audit/reconciliation_reports_lot35.json").read_text()
    )
    veto_payload = json.loads(
        (tmp_path / "data/audit/reconciliation_veto_lot35.json").read_text()
    )
    assert state_payload == state.to_dict()
    assert audit_payload == audit.to_dict()
    assert reports_payload["records"] == state_payload["reports"]
    assert veto_payload == state_payload["veto"]


def test_exact_tolerance_boundary_is_tolerated() -> None:
    config = load_config()
    record = copy.deepcopy(config["records"][0])
    record["secondary"]["price"] = "50010.01"
    config["records"] = [record]
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "TOLERATED_DIFF"
    assert report.delta is not None
    assert report.delta.price_abs == "0.01"
    assert report.corrective_action == "NONE"


def test_minor_divergence_pauses() -> None:
    config = load_config()
    record = copy.deepcopy(config["records"][0])
    record["secondary"]["price"] = "50010.02"
    config["records"] = [record]
    report = build_reconciliation_reports(config)[0]
    veto = _build_veto((report,))
    assert report.classification == "MINOR_DIVERGENCE"
    assert report.corrective_action == "REVIEW_AND_PAUSE"
    assert veto.action == "PAUSE"
    assert veto.minor_divergence_count == 1


def test_critical_divergence_uses_kill_switch_semantics() -> None:
    config = load_config()
    record = copy.deepcopy(config["records"][0])
    record["secondary"]["price"] = "50010.11"
    config["records"] = [record]
    report = build_reconciliation_reports(config)[0]
    veto = _build_veto((report,))
    assert report.classification == "CRITICAL_DIVERGENCE"
    assert report.corrective_action == "MANUAL_RECONCILIATION_REQUIRED"
    assert veto.action == "KILL_SWITCH"
    assert veto.critical_divergence_count == 1


def test_identifier_mismatch_is_critical_even_when_numeric_values_match() -> None:
    config = load_config()
    record = copy.deepcopy(config["records"][0])
    record["secondary"]["identifier"] = "btc-eur-spot:wrong"
    config["records"] = [record]
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "CRITICAL_DIVERGENCE"
    assert report.reason_codes == ("RECONCILIATION_IDENTIFIER_MISMATCH",)


def test_orphan_is_critical_without_fabricated_delta() -> None:
    config = load_config()
    record = copy.deepcopy(config["records"][0])
    record["secondary"] = None
    config["records"] = [record]
    report = build_reconciliation_reports(config)[0]
    assert report.orphan is True
    assert report.delta is None
    assert report.classification == "CRITICAL_DIVERGENCE"
    assert report.reason_codes == ("RECONCILIATION_ORPHAN",)


def test_unknown_source_of_truth_is_critical() -> None:
    config = load_config()
    record = copy.deepcopy(config["records"][0])
    record["source_of_truth"] = "UNKNOWN"
    config["records"] = [record]
    report = build_reconciliation_reports(config)[0]
    assert report.classification == "CRITICAL_DIVERGENCE"
    assert report.reason_codes == ("RECONCILIATION_SOURCE_OF_TRUTH_UNKNOWN",)


def test_duplicate_reconciliation_pauses_both_reports() -> None:
    config = load_config()
    first = copy.deepcopy(config["records"][0])
    second = copy.deepcopy(first)
    second["primary"]["record_id"] = "candle-primary-duplicate"
    second["secondary"]["record_id"] = "candle-secondary-duplicate"
    config["records"] = [first, second]
    reports = build_reconciliation_reports(config)
    assert len(reports) == 2
    assert all(report.duplicate for report in reports)
    assert all(report.classification == "MINOR_DIVERGENCE" for report in reports)
    assert _build_veto(reports).action == "PAUSE"
