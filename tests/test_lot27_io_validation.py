from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.run_lot27_global_market_context_aggregator import run
from scripts.validate_lot27 import validate
from tests.lot27_fixtures import CONFIG_PATH, ROOT, SOURCE_PATHS


def copy_inputs(root: Path) -> None:
    paths = [CONFIG_PATH, *SOURCE_PATHS.values()]
    paths.append(ROOT / "contracts/schemas/global_market_context_aggregator_state_v1.schema.json")
    for source in paths:
        relative = source.relative_to(ROOT)
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def test_runner_writes_replayable_closed_evidence(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    first = run(tmp_path, "abcdef1234567890")
    second = run(tmp_path, "abcdef1234567890")
    assert first == second
    assert first["state"]["dominant_state"] == "GLOBAL_CONTEXT_MIXED"
    assert first["state"]["aggregate_evidence_score"] == 0.5646
    assert first["audit"]["replay_status"] == "MATCH"
    result = validate(tmp_path)
    assert result["status"] == "PASS"
    report = (tmp_path / "reports/lot_27_global_market_context_aggregator_report.md").read_text(
        encoding="utf-8"
    )
    assert "GO_LOT27_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY" in report
    assert "trade_allowed=false" in report


def test_validator_rejects_tampered_state(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    run(tmp_path, "abcdef1234567890")
    path = tmp_path / "data/audit/global_market_context_aggregator_lot27.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["aggregate_evidence_score"] = 0.9
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        validate(tmp_path)


def test_validator_rejects_schema_drift(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    run(tmp_path, "abcdef1234567890")
    path = tmp_path / "data/audit/global_market_context_aggregator_lot27.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["unexpected"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="fields diverge"):
        validate(tmp_path)
