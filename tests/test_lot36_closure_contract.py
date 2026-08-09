from __future__ import annotations

import json
from pathlib import Path

from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_ROADMAP_BLOB,
    build_lot36_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "2" * 40
GATE_PATH = ROOT / "data/audit/lot36_v3_entry_gate.json"


def test_lot36_canonical_required_outputs_are_implemented_by_contract() -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    assert gate["output_checksum"] == EXPECTED_GATE_CHECKSUM
    assert gate["canonical_roadmap"]["source_blob_sha"] == EXPECTED_ROADMAP_BLOB
    assert set(gate["required_outputs"]) == {
        "FreshnessGapOutageAuditV3ClosureStateV1",
        "FreshnessGapOutageAuditV3ClosureAuditV1",
        "ReplayEvidenceV1",
        "LotValidationReportV1",
        "ClosureManifestV1",
        "DataQualityStateV1",
        "DataAnomalyV1",
        "DataQualityVetoV1",
    }


def test_lot36_validation_report_covers_complete_v3_chain() -> None:
    state, _ = build_lot36_artifacts(ROOT, CODE_COMMIT)
    assert state.validation_report.validated_lots == (31, 32, 33, 34, 35, 36)
    assert state.validation_report.required_validator_count == 6
    assert state.validation_report.closure_candidate_ready is True


def test_lot36_manifest_cannot_claim_final_v3_closure_before_audit() -> None:
    state, _ = build_lot36_artifacts(ROOT, CODE_COMMIT)
    manifest = state.closure_manifest
    assert manifest.version_id == "V3_MARKET_DATA_GOVERNANCE"
    assert manifest.lots_included == (31, 32, 33, 34, 35, 36)
    assert manifest.v3_closed is False
    assert manifest.post_merge_audit_required is True
    assert manifest.human_review_required is True
    assert manifest.next_lot == 37
    assert manifest.next_lot_status == "PLANNED_LOCKED"


def test_lot36_never_opens_trading_or_execution() -> None:
    state, audit = build_lot36_artifacts(ROOT, CODE_COMMIT)
    for payload in (state.safety, audit.safety):
        assert payload["analysis_only"] is True
        assert payload["used_for_decision"] is False
        assert payload["external_connectivity_allowed"] is False
        assert payload["network_ingestion_allowed"] is False
        assert payload["raw_data_mutation_allowed"] is False
        assert payload["signal_generation_allowed"] is False
        assert payload["risk_approval_allowed"] is False
        assert payload["order_routing_allowed"] is False
        assert payload["trade_allowed"] is False
        assert payload["execution_allowed"] is False
        assert payload["approved_size"] == 0
