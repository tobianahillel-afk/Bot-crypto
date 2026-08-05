from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from lot26_fixtures import ROOT

from crypto_quant_bot.market_analysis import alignment_io
from crypto_quant_bot.market_analysis.alignment_common import Lot26ValidationError
from crypto_quant_bot.market_analysis.alignment_io import (
    load_json,
    load_jsonl,
    write_json_atomic,
    write_jsonl_atomic,
)
from scripts.run_lot26_multi_timeframe_alignment_engine import run
from scripts.validate_lot26 import validate


def test_json_and_jsonl_atomic_round_trip(tmp_path: Path) -> None:
    json_path = tmp_path / "nested/data.json"
    jsonl_path = tmp_path / "nested/data.jsonl"
    write_json_atomic(json_path, {"b": 2, "a": 1})
    write_jsonl_atomic(jsonl_path, [{"a": 1}, {"b": 2}])
    assert load_json(json_path) == {"a": 1, "b": 2}
    assert load_jsonl(jsonl_path) == [{"a": 1}, {"b": 2}]
    assert not list(json_path.parent.glob("*.tmp"))


def test_loaders_reject_missing_large_invalid_and_non_object_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(FileNotFoundError):
        load_json(tmp_path / "missing.json")
    large = tmp_path / "large.json"
    large.write_text("{}")
    monkeypatch.setattr(alignment_io, "MAX_JSON_BYTES", 1)
    with pytest.raises(Lot26ValidationError, match="too large"):
        load_json(large)
    monkeypatch.setattr(alignment_io, "MAX_JSON_BYTES", 5_000_000)
    invalid = tmp_path / "invalid.jsonl"
    invalid.write_text("[]\n")
    with pytest.raises(Lot26ValidationError, match="must be objects"):
        load_jsonl(invalid)
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{")
    with pytest.raises(json.JSONDecodeError):
        load_json(malformed)


def test_jsonl_row_limit_and_blank_lines(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "rows.jsonl"
    path.write_text("\n{\"a\":1}\n{\"b\":2}\n")
    assert load_jsonl(path) == [{"a": 1}, {"b": 2}]
    monkeypatch.setattr(alignment_io, "MAX_JSONL_ROWS", 1)
    with pytest.raises(Lot26ValidationError, match="row limit"):
        load_jsonl(path)


def test_atomic_writer_cleans_temporary_file_on_replace_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "output.json"

    def fail_replace(_source: object, _target: object) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(alignment_io.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        write_json_atomic(target, {"a": 1})
    assert not list(tmp_path.glob("*.tmp"))


def _copy_inputs(root: Path) -> None:
    paths = [
        "data/audit/volatility_regime_confluence_timeframes_lot25.jsonl",
        "config/math/multi_timeframe_alignment_v1.json",
        "config/temporal/temporal_scale_registry_v1.json",
        "config/temporal/decision_clock_policy_v1.json",
        "contracts/schemas/timeframe_market_context_state_v1.schema.json",
        "contracts/schemas/closed_bar_availability_v1.schema.json",
        "contracts/schemas/multi_timeframe_alignment_state_v1.schema.json",
    ]
    for relative in paths:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)


def test_runner_writes_replayable_closed_artifacts(tmp_path: Path) -> None:
    _copy_inputs(tmp_path)
    result = run(tmp_path, "abcdef1")
    assert result["alignment"]["overall_agreement_score"] == 0.65
    assert result["replay"]["status"] == "MATCH"
    validation = validate(tmp_path)
    assert validation["status"] == "PASS"
    assert validation["contexts"] == 2
    report = (tmp_path / "reports/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_FINAL_REPORT.md").read_text()
    assert "GO_LOT26_IMPLEMENTED_VALIDATED" in report
    assert "trade_allowed=false" in report


def test_validator_rejects_tampered_output(tmp_path: Path) -> None:
    _copy_inputs(tmp_path)
    run(tmp_path, "abcdef1")
    path = tmp_path / "data/audit/multi_timeframe_alignment_engine_lot26.json"
    payload = json.loads(path.read_text())
    payload["overall_agreement_score"] = 0.9
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="checksum mismatch"):
        validate(tmp_path)
