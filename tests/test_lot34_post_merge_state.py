from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_lot34_post_merge.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("lot34_post_merge_validator", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_post_merge_validation_is_pass() -> None:
    module = load_validator()
    result = module.validate()
    assert result["status"] == "PASS"
    assert result["verdict"] == "GO_LOT34_POST_MERGE"
    assert result["project_version"] == "0.34.0"
    assert result["merged_commit"] == "27880f7e14f3d1c97cce9a73f9fe4b5498947068"
    assert result["latest_implemented_lot"] == 34
    assert result["next_lot"] == 35
    assert result["next_lot_status"] == "PLANNED_LOCKED"
    assert result["trade_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["approved_size"] == 0
    assert len(result["validation_checksum"]) == 64


def test_lifecycle_preserves_lots_26_to_33_exactly() -> None:
    previous = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot33.json").read_text(encoding="utf-8")
    )
    current = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot34.json").read_text(encoding="utf-8")
    )
    assert {str(lot): current["lots"][str(lot)] for lot in range(26, 34)} == {
        str(lot): previous["lots"][str(lot)] for lot in range(26, 34)
    }


def test_lot35_remains_locked_and_not_started() -> None:
    overlay = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot34.json").read_text(encoding="utf-8")
    )
    assert overlay["lots"]["35"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }
    assert "ContinuousMarketStateV1" in overlay["future_capabilities_locked"]


def test_quality_proofs_remain_above_gates() -> None:
    coverage = json.loads(
        (ROOT / "reports/lot34/coverage_summary.json").read_text(encoding="utf-8")
    )
    mutation = json.loads(
        (ROOT / "reports/lot34/mutation_summary.json").read_text(encoding="utf-8")
    )
    assert coverage["line_coverage_percent"] >= 95.0
    assert coverage["branch_coverage_percent"] >= 90.0
    assert coverage["anti_flake_repetitions"] >= 3
    assert mutation["mutation_score_percent"] >= 80.0
    assert mutation["killed_mutants"] == 1370
    assert mutation["evaluated_mutants"] == 1631


def test_validator_fails_if_lot35_is_unlocked(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_validator()
    original = module.load_json_object

    def altered(path: Path):
        payload = original(path)
        if path.name == "roadmap_lifecycle_overlay_lot34.json":
            payload["lots"]["35"] = {"implementation_started": True, "status": "ACTIVE"}
        return payload

    monkeypatch.setattr(module, "load_json_object", altered)
    with pytest.raises(ValueError, match="Lot 35 must remain locked"):
        module.validate_lifecycle()
