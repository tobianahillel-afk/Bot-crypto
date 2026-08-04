from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from crypto_quant_bot.closure import io as closure_io
from crypto_quant_bot.release import candidate


@dataclass
class PlainRecord:
    value: int


class DictRecord:
    def to_dict(self) -> dict[str, int]:
        return {"value": 2}


def test_closure_io_readers_cover_missing_truncation_and_jsonl_limits(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    assert closure_io.read_text_limited(missing) == ""

    text = tmp_path / "text.txt"
    text.write_text("abcdef", encoding="utf-8")
    assert closure_io.read_text_limited(text, max_bytes=3) == "abc"
    assert closure_io.sha256_file(text) == closure_io.sha256_bytes(b"abcdef")
    assert len(closure_io.sha256_bytes(b"x")) == 64

    json_path = tmp_path / "payload.json"
    json_path.write_text(json.dumps({"value": 1}), encoding="utf-8")
    assert closure_io.load_json(json_path) == {"value": 1}

    jsonl_path = tmp_path / "rows.jsonl"
    jsonl_path.write_text('\n{"value":1}\n{"value":2}\n{"value":3}\n', encoding="utf-8")
    assert closure_io.load_jsonl(jsonl_path, max_lines=2) == [
        {"value": 1},
        {"value": 2},
    ]
    assert closure_io.load_jsonl(missing, max_lines=2) == []


def test_closure_io_atomic_writers_support_shapes_and_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    json_path = closure_io.atomic_write_json(
        tmp_path / "nested" / "payload.json",
        {"z": 2, "a": 1},
    )
    assert json_path.read_text(encoding="utf-8") == '{\n  "a": 1,\n  "z": 2\n}\n'

    jsonl_path = closure_io.atomic_write_jsonl(
        tmp_path / "rows.jsonl",
        [DictRecord(), PlainRecord(3), {"value": 4}],
    )
    assert [json.loads(line) for line in jsonl_path.read_text().splitlines()] == [
        {"value": 2},
        {"value": 3},
        {"value": 4},
    ]
    text_path = closure_io.atomic_write_text(tmp_path / "message.txt", "hello")
    assert text_path.read_text() == "hello"

    monkeypatch.setattr(
        closure_io.os,
        "fsync",
        lambda _fd: (_ for _ in ()).throw(OSError("unsupported")),
    )
    closure_io.atomic_write_text(tmp_path / "fsync.txt", "ok")
    assert (tmp_path / "fsync.txt").read_text() == "ok"

    monkeypatch.setattr(
        closure_io.os,
        "replace",
        lambda _source, _target: (_ for _ in ()).throw(RuntimeError("replace failed")),
    )
    with pytest.raises(RuntimeError, match="replace failed"):
        closure_io.atomic_write_json(tmp_path / "failed.json", {"ok": False})
    assert list(tmp_path.glob(".*.tmp")) == []


def test_release_checksum_paths_and_catalog_helpers(tmp_path: Path) -> None:
    first = {
        "created_at": "one",
        "release_checksum": "old",
        "nested": [{"created_at": "nested", "value": 1}],
    }
    second = {
        "created_at": "two",
        "release_checksum": "new",
        "nested": [{"created_at": "other", "value": 1}],
    }
    assert candidate.build_release_checksum(first) == candidate.build_release_checksum(second)
    assert len(candidate.build_release_checksum({"value": 1})) == 64

    (tmp_path / "a.py").write_text("x", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "b.py").write_text("y", encoding="utf-8")
    assert candidate._all_exist(tmp_path, ["a.py", "nested/b.py"])
    assert not candidate._all_exist(tmp_path, ["a.py", "missing.py"])
    assert candidate._expand_patterns(tmp_path, ["*.py", "nested/*.py"]) == [
        "a.py",
        "nested/b.py",
    ]
    assert candidate._present_candidate_paths(tmp_path, ["a.py", "missing.py"]) == ["a.py"]

    catalog = [
        {"dataset_id": dataset_id}
        for dataset_id in sorted(
            candidate.EXPECTED_LOT16_IDS
            | candidate.EXPECTED_LOT17_IDS
            | candidate.EXPECTED_LOT18_IDS
        )
    ]
    assert candidate._validate_catalog(catalog) == (True, [])
    invalid = catalog + [dict(catalog[0])]
    valid, errors = candidate._validate_catalog(invalid)
    assert not valid
    assert "dataset_catalog duplicate dataset_id" in errors
    valid, errors = candidate._validate_catalog([])
    assert not valid
    assert errors == [
        "dataset_catalog missing Lot 16 ids",
        "dataset_catalog missing Lot 17 ids",
        "dataset_catalog missing Lot 18 ids",
    ]


def test_release_jsonl_validation_network_and_archive_detection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = {
        "empty.jsonl": [],
        "bad.jsonl": [{"status": "FAIL", "reasons": "bad"}],
        "good.jsonl": [{"status": "PASS", "reasons": ["one", "two"]}],
    }
    monkeypatch.setattr(
        candidate,
        "load_jsonl",
        lambda path, max_lines: rows[Path(path).name],
    )
    valid, errors = candidate._validate_jsonl_rows(
        tmp_path,
        relative_paths=["empty.jsonl", "bad.jsonl", "good.jsonl"],
        expectations={"status": "PASS"},
        reason_field="reasons",
        required_reasons=["one", "two"],
    )
    assert not valid
    assert "empty.jsonl has no rows" in errors
    assert "bad.jsonl invalid status: FAIL" in errors
    assert "bad.jsonl invalid reasons" in errors

    (tmp_path / "safe.py").write_text("print('safe')", encoding="utf-8")
    (tmp_path / "network.py").write_text("import requests\nhttps://example.invalid", encoding="utf-8")
    monkeypatch.setattr(candidate, "CODE_SURFACE_PATTERNS", ["*.py"])
    monkeypatch.setattr(candidate, "NETWORK_SCAN_EXCLUDED_PATHS", {"safe.py"})
    monkeypatch.setattr(candidate, "NETWORK_FORBIDDEN_FRAGMENTS", ["import requests", "https://"])
    hits = candidate._network_surface_hits(tmp_path)
    assert hits == ["network.py:import requests", "network.py:https://"]

    monkeypatch.setattr(candidate, "ARCHIVE_CANDIDATE_PATHS", ["archive.zip", "missing.zip"])
    (tmp_path / "archive.zip").write_text("archive", encoding="utf-8")
    assert candidate._archive_candidate_hits(tmp_path) == ["archive.zip"]


def test_release_default_artifacts_and_critical_counts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    artifacts = candidate.default_source_artifacts()
    assert artifacts == sorted(set(artifacts))
    assert candidate.DATASET_CATALOG_PATH in artifacts
    assert candidate.LOT18_OUTPUT_PATH in artifacts

    release = candidate.DefensiveReleaseCandidate(tmp_path)
    monkeypatch.setattr(
        candidate,
        "count_lines",
        lambda path: 36 if str(path).endswith("5m.jsonl") else 12,
    )
    valid, observed = release._compute_critical_counts()
    assert valid
    assert observed == candidate.EXPECTED_CRITICAL_COUNTS

    monkeypatch.setattr(candidate, "count_lines", lambda _path: 1)
    valid, observed = release._compute_critical_counts()
    assert not valid
    assert all(counts == {"5m": 1, "15m": 1, "total": 2} for counts in observed.values())


def test_release_build_checks_maps_boolean_states() -> None:
    release = candidate.DefensiveReleaseCandidate(Path("."))
    kwargs = {
        "required_artifacts_present": True,
        "required_reports_present": False,
        "required_scripts_present": True,
        "critical_counts_valid": False,
        "critical_counts_observed": {},
        "reproducibility_manifest_valid": True,
        "health_monitor_valid": False,
        "no_trading_compliance_valid": True,
        "dataset_catalog_valid": False,
        "lot12_valid": True,
        "lot13_valid": False,
        "lot14_valid": True,
        "lot15_valid": False,
        "archive_created": False,
        "archive_hits": [],
        "exchange_connector_present": False,
        "order_router_present": False,
        "api_key_present": False,
        "websocket_present": False,
        "paper_trading_present": False,
        "strategy_present": False,
        "forbidden_semantics_present": False,
        "network_hits": [],
    }
    checks = release.build_checks(**kwargs)
    by_name = {check.check_name: check for check in checks}
    assert by_name["required_artifacts_present"].status == "PASS"
    assert by_name["required_reports_present"].status == "BLOCK"
    assert by_name["critical_counts_valid"].status == "BLOCK"
    assert by_name["health_monitor_valid"].status == "BLOCK"
    assert by_name["archive_created"].status == "PASS"
    assert by_name["network_surface_absent"].status == "PASS"
