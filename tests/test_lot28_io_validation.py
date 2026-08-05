from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.run_lot28_explanation_core_and_why_not_trade_layer import run
from scripts.validate_lot28 import validate
from tests.lot28_fixtures import ALIGNMENT_PATH, CONFIG_PATH, GLOBAL_CONTEXT_PATH, ROOT, SCHEMA_PATH


def copy_inputs(root: Path) -> None:
    for source in (CONFIG_PATH, GLOBAL_CONTEXT_PATH, ALIGNMENT_PATH, SCHEMA_PATH):
        destination = root / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def output_path(root: Path) -> Path:
    return root / "data/audit/explanation_core_and_why_not_trade_layer_lot28.json"


def test_runner_writes_replayable_evidence_and_validator_passes(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    first = run(tmp_path, "abcdef1234567890")
    second = run(tmp_path, "abcdef1234567890")
    assert first == second
    assert first["audit"]["replay_status"] == "MATCH"
    assert first["audit"]["statement_count"] == 14
    assert first["audit"]["why_not_reason_count"] == 3
    assert first["audit"]["dominant_reason_code"] == "WNT_PERMISSIONS_DISABLED"
    assert validate(tmp_path)["status"] == "PASS"
    report = (tmp_path / "reports/lot_28_explanation_core_and_why_not_trade_layer_report.md").read_text(
        encoding="utf-8"
    )
    assert "GO_LOT28_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY" in report
    assert "no_order_intent_created=true" in report


def test_validator_rejects_tampered_text(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    run(tmp_path, "abcdef1234567890")
    path = output_path(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["bundle"]["facts_observed"][0]["text"] = "Altered text."
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="text diverges"):
        validate(tmp_path)


def test_validator_rejects_tampered_evidence_value(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    run(tmp_path, "abcdef1234567890")
    path = output_path(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["bundle"]["facts_observed"][0]["evidence_refs"][0]["observed_value"] = "OTHER"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="observed value mismatch"):
        validate(tmp_path)


def test_validator_rejects_reason_without_evidence(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    run(tmp_path, "abcdef1234567890")
    path = output_path(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["bundle"]["why_not_trade"]["reasons"][0]["evidence_refs"] = []
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="evidence reference list"):
        validate(tmp_path)


def test_validator_rejects_closed_schema_drift_and_checksum_tamper(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    run(tmp_path, "abcdef1234567890")
    path = output_path(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["unexpected"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="state/schema fields diverge"):
        validate(tmp_path)

    run(tmp_path, "abcdef1234567890")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["output_checksum"] = "0" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        validate(tmp_path)


def test_validator_rejects_forbidden_output_token(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    run(tmp_path, "abcdef1234567890")
    path = output_path(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["bundle"]["final_consequence"][0]["text"] += " BUY"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="text diverges|forbidden"):
        validate(tmp_path)
