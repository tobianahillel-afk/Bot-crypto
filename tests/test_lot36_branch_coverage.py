from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure as closure
from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure_validation import (
    V3ClosureError,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.data_governance.market_data_quality_engine import build_lot34_artifacts

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "5" * 40
GATE_PATH = ROOT / "data/audit/lot36_v3_entry_gate.json"
QUALITY_CONFIG_PATH = ROOT / "config/data_governance/market_data_quality_engine_v1.json"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _gate_with_checksum(**updates: object) -> dict[str, Any]:
    gate = load_json_object(GATE_PATH)
    gate.update(updates)
    gate.pop("output_checksum", None)
    gate["output_checksum"] = canonical_checksum(gate)
    return gate


def test_gate_rejects_authorization_and_safety_changes(tmp_path: Path) -> None:
    gate_path = tmp_path / "data/audit/lot36_v3_entry_gate.json"
    _write_json(gate_path, _gate_with_checksum(gate_status="BLOCKED"))
    with pytest.raises(V3ClosureError, match="does not authorize"):
        closure._verify_gate(tmp_path)

    unsafe = dict(closure.lot36_safety())
    unsafe["trade_allowed"] = True
    _write_json(gate_path, _gate_with_checksum(safety=unsafe))
    with pytest.raises(V3ClosureError, match="safety boundary"):
        closure._verify_gate(tmp_path)


def test_canonical_roadmap_rejects_blob_short_identity_and_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roadmap = tmp_path / closure.ROADMAP_PATH
    roadmap.parent.mkdir(parents=True, exist_ok=True)
    roadmap.write_text("{}\n", encoding="utf-8")
    with pytest.raises(V3ClosureError, match="blob changed"):
        closure._verify_canonical_roadmap(tmp_path, {})

    raw = roadmap.read_bytes()
    monkeypatch.setattr(closure, "EXPECTED_ROADMAP_BLOB", closure._git_blob_sha(raw))
    with pytest.raises(V3ClosureError, match="record missing"):
        closure._verify_canonical_roadmap(tmp_path, {})

    wrong_record = {
        "lot_id": "Lot 36",
        "lot_number": 36,
        "title": "Wrong title",
        "version_id": "V3_MARKET_DATA_GOVERNANCE",
        "responsible_component": "MarketDataGovernanceDomain",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "status": "PLANNED_LOCKED",
    }
    lines = [json.dumps({"line": index}) for index in range(36)] + [json.dumps(wrong_record)]
    roadmap.write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        closure,
        "EXPECTED_ROADMAP_BLOB",
        closure._git_blob_sha(roadmap.read_bytes()),
    )
    with pytest.raises(V3ClosureError, match="identity changed"):
        closure._verify_canonical_roadmap(tmp_path, {})

    monkeypatch.setattr(
        closure,
        "EXPECTED_ROADMAP_BLOB",
        "84de51bda788a8d124fb7d344419c4a4b12030b5",
    )
    with pytest.raises(V3ClosureError, match="binding missing"):
        closure._verify_canonical_roadmap(ROOT, {"canonical_roadmap": "bad"})
    with pytest.raises(V3ClosureError, match="lost canonical"):
        closure._verify_canonical_roadmap(
            ROOT,
            {"canonical_roadmap": {"source_blob_sha": "0" * 40}},
        )


@pytest.mark.parametrize(
    ("overlay", "message"),
    [
        ({"latest_implemented_lot": 34, "lots": {}}, "audited predecessor"),
        ({"latest_implemented_lot": 35, "lots": []}, "lots missing"),
        ({"latest_implemented_lot": 35, "lots": {"35": "bad"}}, "Lot 35 lifecycle"),
        (
            {
                "latest_implemented_lot": 35,
                "lots": {"35": {"status": "WRONG"}},
            },
            "status changed",
        ),
        (
            {
                "latest_implemented_lot": 35,
                "lots": {
                    "35": {"status": "IMPLEMENTED_VALIDATED_RECONCILIATION_ONLY"},
                    "36": {"implementation_started": True, "status": "PLANNED_LOCKED"},
                },
            },
            "historical lock changed",
        ),
    ],
)
def test_historical_lifecycle_rejects_each_invalid_precondition(
    tmp_path: Path, overlay: object, message: str
) -> None:
    path = tmp_path / "data/audit/roadmap_lifecycle_overlay_lot35.json"
    _write_json(path, overlay)
    with pytest.raises(V3ClosureError, match=message):
        closure._verify_historical_lifecycle(tmp_path)


def _good_lot34() -> tuple[SimpleNamespace, SimpleNamespace]:
    return (
        SimpleNamespace(output_checksum=closure.EXPECTED_LOT34_STATE_CHECKSUM),
        SimpleNamespace(audit_checksum=closure.EXPECTED_LOT34_AUDIT_CHECKSUM),
    )


def _good_lot35() -> tuple[SimpleNamespace, SimpleNamespace]:
    return (
        SimpleNamespace(output_checksum=closure.EXPECTED_LOT35_STATE_CHECKSUM),
        SimpleNamespace(audit_checksum=closure.EXPECTED_LOT35_AUDIT_CHECKSUM),
    )


@pytest.mark.parametrize(
    "failure",
    ["lot34_state", "lot34_audit", "lot35_state", "lot35_audit"],
)
def test_previous_lot_replay_rejects_every_checksum_divergence(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    lot34_state, lot34_audit = _good_lot34()
    lot35_state, lot35_audit = _good_lot35()
    if failure == "lot34_state":
        lot34_state.output_checksum = "0" * 64
    elif failure == "lot34_audit":
        lot34_audit.audit_checksum = "0" * 64
    elif failure == "lot35_state":
        lot35_state.output_checksum = "0" * 64
    else:
        lot35_audit.audit_checksum = "0" * 64
    monkeypatch.setattr(closure, "build_lot34_artifacts", lambda *_: (lot34_state, lot34_audit))
    monkeypatch.setattr(closure, "build_lot35_artifacts", lambda *_: (lot35_state, lot35_audit))
    with pytest.raises(V3ClosureError, match="deterministic replay"):
        closure._replay_previous_lots(ROOT)


def test_freshness_group_rejects_missing_timeframe_configuration() -> None:
    quality_config = load_json_object(QUALITY_CONFIG_PATH)
    records = copy.deepcopy(quality_config["records"])
    state, _ = build_lot34_artifacts(ROOT, closure.EXPECTED_LOT34_IMPLEMENTATION_COMMIT)
    key = (
        state.quality_states[0].source_id,
        state.quality_states[0].instrument_id,
        state.quality_states[0].timeframe,
    )
    reference = closure.parse_utc_timestamp(
        "2026-08-06T19:18:00.100000Z", "reference_time"
    )
    with pytest.raises(V3ClosureError, match="timeframe interval missing"):
        closure._freshness_evidence_for_group(
            key,
            records,
            state.quality_states[0],
            {},
            reference,
            121,
            3,
        )


def test_build_rejects_lot34_anomaly_replay_divergence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        closure,
        "detect_anomalies",
        lambda *_: (SimpleNamespace(anomaly_type="FORCED_DIVERGENCE"),),
    )
    with pytest.raises(V3ClosureError, match="anomaly replay diverged"):
        closure.build_lot36_artifacts(ROOT, CODE_COMMIT)


def test_write_lot36_artifacts_persists_every_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outputs = {
        "state": tmp_path / "state.json",
        "audit": tmp_path / "audit.json",
        "quality_states": tmp_path / "quality_states.json",
        "anomalies": tmp_path / "anomalies.json",
        "quality_veto": tmp_path / "quality_veto.json",
        "replay": tmp_path / "replay.json",
        "manifest": tmp_path / "manifest.json",
    }
    monkeypatch.setattr(closure, "_output_paths", lambda _root: outputs)
    observed = closure.write_lot36_artifacts(ROOT, CODE_COMMIT)
    assert set(observed) == set(outputs)
    for name, path in outputs.items():
        assert path.exists(), name
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
