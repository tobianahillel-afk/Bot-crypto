from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from crypto_quant_bot.closure import archive


def test_closure_checksum_and_path_helpers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first = {
        "created_at": "one",
        "closure_checksum": "old",
        "nested": [{"created_at": "nested", "value": 1}],
    }
    second = {
        "created_at": "two",
        "closure_checksum": "new",
        "nested": [{"created_at": "other", "value": 1}],
    }
    assert archive.build_closure_checksum(first) == archive.build_closure_checksum(second)

    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "b.txt").write_text("b", encoding="utf-8")
    assert archive._all_exist(tmp_path, ["a.txt", "nested/b.txt"])
    assert not archive._all_exist(tmp_path, ["a.txt", "missing.txt"])
    assert archive._expand_patterns(tmp_path, ["*.txt", "nested/*.txt"]) == [
        "a.txt",
        "nested/b.txt",
    ]
    assert archive._present_candidate_paths(tmp_path, ["a.txt", "missing.txt"]) == ["a.txt"]

    monkeypatch.setattr(archive, "ARCHIVE_EXCLUDED_PATHS", ["secret/", ".env", "cache"])
    assert archive._path_is_excluded("secret/key.txt")
    assert archive._path_is_excluded("project/.env")
    assert archive._path_is_excluded("cache/file")
    assert not archive._path_is_excluded("safe/file.txt")


def complete_catalog() -> list[dict[str, str]]:
    ids = sorted(
        archive.EXPECTED_LOT16_IDS
        | archive.EXPECTED_LOT17_IDS
        | archive.EXPECTED_LOT18_IDS
        | archive.EXPECTED_LOT19_IDS
    )
    return [{"dataset_id": dataset_id} for dataset_id in ids]


def test_validate_catalog_success_duplicates_and_missing_groups() -> None:
    valid, errors = archive._validate_catalog(complete_catalog())
    assert valid and errors == []

    rows = complete_catalog()
    rows.append(dict(rows[0]))
    valid, errors = archive._validate_catalog(rows)
    assert not valid
    assert "dataset_catalog duplicate dataset_id" in errors

    valid, errors = archive._validate_catalog([{"not_dataset_id": "x"}, "ignored"])
    assert not valid
    assert "dataset_catalog missing Lot 16 ids" in errors
    assert "dataset_catalog missing Lot 17 ids" in errors
    assert "dataset_catalog missing Lot 18 ids" in errors
    assert "dataset_catalog missing Lot 19 ids" in errors


def test_validate_manifest_all_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    catalog = complete_catalog()
    monkeypatch.setattr(archive, "load_json", lambda _path: [])
    valid, errors, payload, rows = archive._validate_manifest(tmp_path, catalog_rows=catalog)
    assert not valid and errors == ["Lot 16 manifest must be a JSON object"]
    assert payload == {} and rows == []

    artifact_rows = [{"artifact_id": "a"}, {"artifact_id": "b"}]
    expected = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "lineage_state": "RECORDED",
        "external_connectivity_allowed": False,
        "execution_allowed": False,
        "trade_allowed": False,
        "artifact_count": len(artifact_rows),
        "manifest_checksum": "manifest-ok",
        "source_catalog_checksum": "catalog-ok",
        "critical_counts": archive.EXPECTED_CRITICAL_COUNTS,
    }
    monkeypatch.setattr(archive, "load_json", lambda _path: expected)
    monkeypatch.setattr(archive, "load_jsonl", lambda _path, max_lines: artifact_rows)
    monkeypatch.setattr(archive, "build_manifest_checksum", lambda _payload: "manifest-ok")
    monkeypatch.setattr(archive, "build_source_catalog_checksum", lambda _rows: "catalog-ok")
    valid, errors, payload, rows = archive._validate_manifest(tmp_path, catalog_rows=catalog)
    assert valid and errors == [] and payload is expected and rows == artifact_rows

    broken = dict(expected)
    broken.update(
        {
            "project_name": "wrong",
            "artifact_count": 99,
            "manifest_checksum": "wrong",
            "source_catalog_checksum": "wrong",
            "critical_counts": {},
        }
    )
    monkeypatch.setattr(archive, "load_json", lambda _path: broken)
    valid, errors, _payload, _rows = archive._validate_manifest(tmp_path, catalog_rows=catalog)
    assert not valid
    assert "invalid manifest project_name" in errors
    assert "manifest artifact_count mismatch" in errors
    assert "manifest checksum mismatch" in errors
    assert "source catalog checksum mismatch" in errors
    assert "critical counts mismatch" in errors


def test_validate_health_snapshot_success_and_failure_matrix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    catalog = complete_catalog()
    monkeypatch.setattr(archive, "load_json", lambda _path: "not-object")
    valid, errors, payload, rows = archive._validate_health_snapshot(tmp_path, catalog_rows=catalog)
    assert not valid and errors == ["Lot 17 health monitor must be a JSON object"]
    assert payload == {} and rows == []

    check_rows = [{"check": "one"}]
    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "health_state": "HEALTHY_FOR_LOCAL_AUDIT",
        "integrity_state": "VERIFIED",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "monitoring_mode": "LOCAL_STATIC_ONLY",
        "external_connectivity_allowed": False,
        "execution_allowed": False,
        "trade_allowed": False,
        "dataset_catalog_readable": True,
        "lot16_manifest_readable": True,
        "lot16_artifacts_readable": True,
        "required_artifacts_present": True,
        "required_reports_present": True,
        "required_scripts_present": True,
        "required_diagnostics_present": True,
        "critical_counts_valid": True,
        "checksum_references_valid": True,
        "artifact_count": 1,
        "health_checksum": "health-ok",
        "dataset_catalog_checksum": "catalog-ok",
        "health_checks": [{"check": "one"}],
    }
    monkeypatch.setattr(archive, "load_json", lambda _path: expected_pairs)
    monkeypatch.setattr(archive, "load_jsonl", lambda _path, max_lines: check_rows)
    monkeypatch.setattr(archive, "build_health_checksum", lambda _payload: "health-ok")
    monkeypatch.setattr(archive, "build_dataset_catalog_checksum", lambda _rows: "catalog-ok")
    valid, errors, _payload, _rows = archive._validate_health_snapshot(
        tmp_path, catalog_rows=catalog
    )
    assert valid and errors == []

    broken = dict(expected_pairs)
    broken.update(
        {
            "health_state": "BAD",
            "artifact_count": 0,
            "health_checksum": "bad",
            "dataset_catalog_checksum": "bad",
            "health_checks": "bad",
        }
    )
    monkeypatch.setattr(archive, "load_json", lambda _path: broken)
    monkeypatch.setattr(archive, "load_jsonl", lambda _path, max_lines: [])
    valid, errors, _payload, _rows = archive._validate_health_snapshot(
        tmp_path, catalog_rows=catalog
    )
    assert not valid
    assert "invalid health health_state" in errors
    assert "health artifact_count must be positive" in errors
    assert "health checksum mismatch" in errors
    assert "health dataset catalog checksum mismatch" in errors
    assert "health check count mismatch" in errors


def snapshot_expected(kind: str) -> dict[str, object]:
    common: dict[str, object] = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "compliance_state": "COMPLIANT",
        "no_trading_state": "ENFORCED",
        "health_state": "HEALTHY_FOR_LOCAL_AUDIT",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
        "trading_decision": "WAIT",
        "system_decision": "BLOCK_TRADING",
        "final_decision": "WAIT",
        "final_system_decision": "BLOCK_TRADING",
        "trade_allowed": False,
        "execution_allowed": False,
        "external_connectivity_allowed": False,
        "exchange_connector_present": False,
        "order_router_present": False,
        "api_key_present": False,
        "websocket_present": False,
        "paper_trading_present": False,
        "strategy_present": False,
        "forbidden_semantics_present": False,
        "critical_counts_valid": True,
        "health_monitor_valid": True,
        "reproducibility_manifest_valid": True,
        "dataset_catalog_valid": True,
        "required_artifacts_present": True,
        "required_reports_present": True,
        "required_scripts_present": True,
    }
    if kind == "compliance":
        common.update(
            {
                "execution_state": "DISABLED",
                "connectivity_state": "DISABLED",
                "artifact_integrity_state": "VERIFIED",
                "compliance_checksum": "checksum-ok",
                "compliance_checks": [{"check": "one"}],
            }
        )
    else:
        common.update(
            {
                "release_candidate_state": "READY_FOR_LOCAL_AUDIT_REVIEW",
                "acceptance_state": "ACCEPTANCE_BUNDLE_GENERATED",
                "packaging_state": "NO_ARCHIVE_CREATED",
                "archive_created": False,
                "integrity_state": "VERIFIED",
                "pytest_state": "EXPECTED_GREEN",
                "exact_chain_state": "EXPECTED_GREEN",
                "no_trading_compliance_valid": True,
                "release_checksum": "checksum-ok",
                "release_checks": [{"check": "one"}],
            }
        )
    return common


@pytest.mark.parametrize("kind", ["compliance", "release"])
def test_validate_compliance_and_release_snapshots(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    kind: str,
) -> None:
    function = (
        archive._validate_compliance_snapshot
        if kind == "compliance"
        else archive._validate_release_snapshot
    )
    label = "Lot 18 compliance snapshot" if kind == "compliance" else "Lot 19 release candidate snapshot"
    monkeypatch.setattr(archive, "load_json", lambda _path: [])
    valid, errors, payload, rows = function(tmp_path)
    assert not valid and errors == [f"{label} must be a JSON object"]
    assert payload == {} and rows == []

    checks = [{"check": "one"}]
    payload = snapshot_expected(kind)
    monkeypatch.setattr(archive, "load_json", lambda _path: payload)
    monkeypatch.setattr(archive, "load_jsonl", lambda _path, max_lines: checks)
    checksum_name = "build_compliance_checksum" if kind == "compliance" else "build_release_checksum"
    monkeypatch.setattr(archive, checksum_name, lambda _payload: "checksum-ok")
    valid, errors, _payload, _rows = function(tmp_path)
    assert valid and errors == []

    broken = dict(payload)
    broken["project_name"] = "wrong"
    broken[f"{kind}_checksum"] = "wrong"
    broken[f"{kind}_checks"] = None
    monkeypatch.setattr(archive, "load_json", lambda _path: broken)
    monkeypatch.setattr(archive, "load_jsonl", lambda _path, max_lines: [])
    valid, errors, _payload, _rows = function(tmp_path)
    assert not valid
    assert f"invalid {'compliance' if kind == 'compliance' else 'release candidate'} project_name" in errors
    assert f"{kind} checksum mismatch" in errors
    assert f"{kind} check count mismatch" in errors


def test_validate_jsonl_rows_all_branches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    rows_by_name = {
        "empty.jsonl": [],
        "bad.jsonl": [
            {"status": "FAIL", "reasons": "not-list"},
            {"status": "PASS", "reasons": ["one"]},
        ],
        "good.jsonl": [{"status": "PASS", "reasons": ["one", "two"]}],
    }
    monkeypatch.setattr(
        archive,
        "load_jsonl",
        lambda path, max_lines: rows_by_name[Path(path).name],
    )
    valid, errors = archive._validate_jsonl_rows(
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
    assert "bad.jsonl missing reasons: two" in errors

    valid, errors = archive._validate_jsonl_rows(
        tmp_path,
        relative_paths=["good.jsonl"],
        expectations={"status": "PASS"},
        reason_field="reasons",
        required_reasons=["one", "two"],
    )
    assert valid and errors == []


def test_build_included_paths_filters_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "safe.txt").write_text("safe", encoding="utf-8")
    (tmp_path / "excluded.txt").write_text("excluded", encoding="utf-8")
    (tmp_path / "self.json").write_text("self", encoding="utf-8")
    monkeypatch.setattr(archive, "ARCHIVE_INCLUDE_PATTERNS", ["*.txt", "safe.txt", "self.json"])
    monkeypatch.setattr(archive, "ARCHIVE_EXCLUDED_PATHS", ["excluded.txt"])
    monkeypatch.setattr(archive, "LOT20_SELF_EXCLUDED_OUTPUTS", {"self.json"})
    included, excluded = archive.build_included_paths(tmp_path)
    assert included == ["safe.txt"]
    assert excluded == ["excluded.txt"]


def test_create_archive_is_deterministic_and_normalized(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.txt").write_text("beta", encoding="utf-8")

    checksum1, size1 = archive.create_archive(
        tmp_path,
        archive_relative_path="dist/one.tar.gz",
        included_paths=["a.txt", "nested/b.txt"],
    )
    checksum2, size2 = archive.create_archive(
        tmp_path,
        archive_relative_path="dist/two.tar.gz",
        included_paths=["a.txt", "nested/b.txt"],
    )
    assert checksum1 == checksum2
    assert size1 == size2
    with tarfile.open(tmp_path / "dist/one.tar.gz", "r:gz") as handle:
        members = handle.getmembers()
        assert [member.name for member in members] == ["a.txt", "nested/b.txt"]
        assert all(member.uid == member.gid == member.mtime == 0 for member in members)

    monkeypatch.setattr(
        archive.os,
        "fsync",
        lambda _fd: (_ for _ in ()).throw(OSError("unsupported")),
    )
    checksum3, _size3 = archive.create_archive(
        tmp_path,
        archive_relative_path="dist/fsync.tar.gz",
        included_paths=["a.txt"],
    )
    assert len(checksum3) == 64


def test_create_archive_cleans_temporary_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
    monkeypatch.setattr(
        archive.os,
        "replace",
        lambda _source, _target: (_ for _ in ()).throw(RuntimeError("replace failed")),
    )
    with pytest.raises(RuntimeError, match="replace failed"):
        archive.create_archive(
            tmp_path,
            archive_relative_path="dist/fail.tar.gz",
            included_paths=["a.txt"],
        )
    assert list((tmp_path / "dist").glob(".*.tmp")) == []
