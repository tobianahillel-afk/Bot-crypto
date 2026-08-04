from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_quant_bot.closure import io as closure_io
from crypto_quant_bot.closure.models import ClosureCheck
from crypto_quant_bot.release import candidate


def test_closure_io_readers_cover_limits_and_invalid_inputs(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError):
        closure_io.read_text_limited(missing)

    text = tmp_path / "text.txt"
    text.write_text("abcdef", encoding="utf-8")
    assert closure_io.read_text_limited(text) == "abcdef"
    with pytest.raises(ValueError, match="text payload too large"):
        closure_io.read_text_limited(text, max_bytes=3)

    json_path = tmp_path / "payload.json"
    json_path.write_text(json.dumps({"value": 1}), encoding="utf-8")
    assert closure_io.load_json(json_path) == {"value": 1}

    jsonl_path = tmp_path / "rows.jsonl"
    jsonl_path.write_text('{"value":1}\n{"value":2}\n', encoding="utf-8")
    assert closure_io.load_jsonl(jsonl_path, max_lines=2) == [
        {"value": 1},
        {"value": 2},
    ]
    jsonl_path.write_text(
        '{"value":1}\n{"value":2}\n{"value":3}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="too many jsonl rows"):
        closure_io.load_jsonl(jsonl_path, max_lines=2)
    with pytest.raises(FileNotFoundError):
        closure_io.load_jsonl(missing, max_lines=2)


def test_closure_io_atomic_writers_and_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "nested" / "payload.json"
    closure_io.write_json(json_path, {"z": 2, "a": 1})
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"a": 1, "z": 2}

    jsonl_path = tmp_path / "rows.jsonl"
    closure_io.write_jsonl(
        jsonl_path,
        [
            ClosureCheck(check_name="first", observed_value=1),
            ClosureCheck(check_name="second", status="BLOCK", observed_value=2),
        ],
    )
    assert [json.loads(line) for line in jsonl_path.read_text().splitlines()] == [
        {
            "block_reason": "",
            "check_name": "first",
            "expected_value": "",
            "message": "",
            "observed_value": 1,
            "status": "PASS",
        },
        {
            "block_reason": "",
            "check_name": "second",
            "expected_value": "",
            "message": "",
            "observed_value": 2,
            "status": "BLOCK",
        },
    ]

    checksum_path = tmp_path / "archive.sha256"
    closure_io.write_sha256_file(
        checksum_path,
        checksum="a" * 64,
        archive_name="archive.tar.gz",
    )
    assert checksum_path.read_text(encoding="utf-8") == f"{'a' * 64}  archive.tar.gz\n"

    monkeypatch.setattr(
        closure_io.os,
        "fsync",
        lambda _fd: (_ for _ in ()).throw(OSError("unsupported")),
    )
    closure_io._atomic_replace_text(tmp_path / "fsync.txt", "ok")
    assert (tmp_path / "fsync.txt").read_text(encoding="utf-8") == "ok"

    monkeypatch.setattr(
        closure_io.os,
        "replace",
        lambda _source, _target: (_ for _ in ()).throw(RuntimeError("replace failed")),
    )
    with pytest.raises(RuntimeError, match="replace failed"):
        closure_io._atomic_replace_text(tmp_path / "failed.json", "{}\n")
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
    invalid = [*catalog, dict(catalog[0])]
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
    (tmp_path / "network.py").write_text(
        "import requests\nhttps://example.invalid",
        encoding="utf-8",
    )
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
        lambda path: 36 if Path(path).name.endswith("_5m.jsonl") else 12,
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
    assert by_name["archive_not_created"].status == "PASS"
    assert by_name["forbidden_semantics_absent"].status == "PASS"
