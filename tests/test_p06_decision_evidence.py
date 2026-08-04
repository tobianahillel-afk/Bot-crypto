from __future__ import annotations

import json
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest

from crypto_quant_bot import __version__
from crypto_quant_bot.contracts import (
    DecisionEvidenceEnvelopeV1,
    EvidenceReferenceV1,
    UncertaintyEnvelopeV1,
)

ROOT = Path(__file__).resolve().parents[1]
HEX_A = "a" * 64
HEX_B = "b" * 64


def make_envelope(**overrides: object) -> DecisionEvidenceEnvelopeV1:
    values: dict[str, object] = {
        "decision_id": "decision-1",
        "parent_decision_ids": ["parent-1"],
        "run_id": "run-1",
        "correlation_id": "correlation-1",
        "replay_id": "replay-1",
        "event_time": "2026-08-04T19:00:00Z",
        "decision_time": "2026-08-04T19:00:01Z",
        "generated_at": "2026-08-04T19:00:02Z",
        "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "instrument_id": "BTC-EUR",
        "venue_id": None,
        "data_snapshot_id": "snapshot-1",
        "data_quality_state_id": "quality-1",
        "feature_set_id": "features-1",
        "market_context_id": "context-1",
        "scenario_set_id": None,
        "strategy_id": None,
        "strategy_version": None,
        "model_versions": {},
        "calibration_version": None,
        "risk_state_id": None,
        "risk_decision_id": None,
        "config_version": "config-v1",
        "code_commit": "abcdef1",
        "input_checksums": {"snapshot": HEX_A},
        "output_checksum": HEX_B,
        "decision_state": "WAIT",
        "reason_codes": ["NO_SIGNAL_EXPECTED"],
        "veto_codes": [],
        "uncertainty": UncertaintyEnvelopeV1(0.1, None, None, None),
        "human_approval_id": None,
        "facts_observed": ["closed bars only"],
        "features_computed": ["trend"],
        "inferences": ["descriptive alignment only"],
        "assumptions": ["fixture is immutable"],
        "supporting_evidence": [
            EvidenceReferenceV1("artifact-1", "fixture", HEX_A, "2026-08-04T18:59:59Z")
        ],
        "contradicting_evidence": [],
        "rules_triggered": ["NO_LOOKAHEAD"],
        "final_consequence": "No OrderIntent created.",
    }
    values.update(overrides)
    return DecisionEvidenceEnvelopeV1(**values)  # type: ignore[arg-type]


def test_runtime_version_comes_from_pyproject() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        expected = tomllib.load(handle)["project"]["version"]
    assert __version__ == expected


def test_decision_evidence_is_canonical_and_stable() -> None:
    first = make_envelope()
    second = make_envelope(model_versions={})
    assert first.canonical_json() == second.canonical_json()
    assert first.envelope_checksum() == second.envelope_checksum()
    assert len(first.envelope_checksum()) == 64


def test_decision_evidence_serializes_all_schema_fields() -> None:
    schema = json.loads(
        (ROOT / "contracts/schemas/decision_evidence_envelope_v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    payload = make_envelope().to_dict()
    assert set(schema["required"]) == set(payload)
    assert payload["schema_version"] == "decision-evidence-envelope-v1"


def test_decision_evidence_defensively_freezes_collections() -> None:
    models = {"forecast": "v1"}
    inputs = {"snapshot": HEX_A}
    envelope = make_envelope(model_versions=models, input_checksums=inputs)
    models["forecast"] = "v2"
    inputs["snapshot"] = HEX_B
    assert envelope.model_versions["forecast"] == "v1"
    assert envelope.input_checksums["snapshot"] == HEX_A
    with pytest.raises(TypeError):
        envelope.model_versions["new"] = "v3"  # type: ignore[index]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("event_time", "2026-08-04T19:00:00", "timezone-aware UTC"),
        ("code_commit", "not-a-commit", "code_commit"),
        ("output_checksum", "abc", "64-character hexadecimal"),
        ("input_checksums", {}, "must not be empty"),
        ("decision_state", "BUY", "unknown decision_state"),
    ],
)
def test_decision_evidence_rejects_invalid_integrity(
    field: str, value: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        make_envelope(**{field: value})


def test_approve_requires_risk_decision_and_reason() -> None:
    with pytest.raises(ValueError, match="risk_decision_id"):
        make_envelope(decision_state="APPROVE")
    with pytest.raises(ValueError, match="reason code"):
        make_envelope(decision_state="APPROVE", risk_decision_id="risk-1", reason_codes=[])
    approved = make_envelope(
        decision_state="APPROVE",
        risk_decision_id="risk-1",
        reason_codes=["RISK_APPROVED"],
    )
    assert approved.decision_state == "APPROVE"


@pytest.mark.parametrize("state", ["BLOCK_TRADING", "PAUSE", "KILL_SWITCH"])
def test_blocking_states_require_veto(state: str) -> None:
    with pytest.raises(ValueError, match="veto code"):
        make_envelope(decision_state=state)
    assert make_envelope(decision_state=state, veto_codes=["HARD_VETO"]).veto_codes == (
        "HARD_VETO",
    )


def test_duplicate_codes_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        make_envelope(reason_codes=["SAME", "SAME"])


def test_uncertainty_bounds_are_enforced() -> None:
    with pytest.raises(ValueError, match=r"within \[0, 1\]"):
        UncertaintyEnvelopeV1(1.01, None, None, None)


def test_evidence_reference_requires_checksum_and_utc() -> None:
    with pytest.raises(ValueError, match="checksum"):
        EvidenceReferenceV1("id", "fixture", "bad")
    with pytest.raises(ValueError, match="UTC"):
        EvidenceReferenceV1("id", "fixture", HEX_A, "2026-08-04T19:00:00+02:00")


def test_replace_preserves_validation() -> None:
    envelope = make_envelope()
    updated = replace(envelope, final_consequence="Still no OrderIntent.")
    assert updated.final_consequence == "Still no OrderIntent."
