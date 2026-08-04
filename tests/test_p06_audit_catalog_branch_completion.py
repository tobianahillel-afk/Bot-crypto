from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from crypto_quant_bot.audit import lookahead
from crypto_quant_bot.data import catalog
from crypto_quant_bot.data.catalog import DatasetCatalog


@dataclass(frozen=True)
class _Metadata:
    dataset_id: str
    value: int

    def to_dict(self) -> dict[str, object]:
        return {"dataset_id": self.dataset_id, "value": self.value}


def test_default_audited_paths_are_rooted(tmp_path: Path) -> None:
    paths = lookahead.default_audited_dataset_paths(tmp_path)
    assert len(paths) == len(lookahead.AUDITED_DATASET_RELATIVE_PATHS)
    assert all(path.is_relative_to(tmp_path) for path in paths)


def test_read_jsonl_enforces_presence_size_rows_and_skips_blanks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.jsonl"
    with pytest.raises(FileNotFoundError):
        lookahead.read_jsonl(missing)

    path = tmp_path / "rows.jsonl"
    path.write_text('{}\n', encoding="utf-8")
    monkeypatch.setattr(lookahead, "MAX_AUDITED_DATASET_BYTES", 1)
    with pytest.raises(ValueError, match="too large"):
        lookahead.read_jsonl(path)

    monkeypatch.setattr(lookahead, "MAX_AUDITED_DATASET_BYTES", 1_000)
    monkeypatch.setattr(lookahead, "MAX_AUDITED_ROWS_PER_DATASET", 1)
    path.write_text('{}\n{}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="row limit exceeded"):
        lookahead.read_jsonl(path)

    monkeypatch.setattr(lookahead, "MAX_AUDITED_ROWS_PER_DATASET", 10)
    path.write_text('\n{"value": 1}\n', encoding="utf-8")
    assert lookahead.read_jsonl(path) == [{"value": 1}]


def test_dataset_audit_covers_errors_empty_rows_and_component_metadata(
    tmp_path: Path,
) -> None:
    missing_result = lookahead.audit_dataset_no_lookahead(tmp_path / "missing.jsonl")
    assert missing_result.validation_status == "failed_lot8"
    assert missing_result.quality_flag == "invalid"
    assert missing_result.errors

    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    empty_result = lookahead.audit_dataset_no_lookahead(empty)
    assert empty_result.validation_status == "validated_lot8"
    assert empty_result.quality_flag == "valid"
    assert empty_result.warnings == ["dataset is empty"]
    assert not empty_result.component_available_at_checked

    populated = tmp_path / "populated.jsonl"
    populated.write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00Z",
                "available_at": "2026-01-01T00:00:00Z",
                "component_available_at": {},
                "used_for_decision": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    populated_result = lookahead.audit_dataset_no_lookahead(populated)
    assert populated_result.validation_status == "validated_lot8"
    assert populated_result.component_available_at_checked


def test_aggregate_lookahead_audit_classifies_every_violation_type(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "audited.jsonl"
    path.write_text(
        '{"timestamp":"2026-01-01T00:00:00Z","available_at":"2026-01-01T00:00:00Z"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        lookahead,
        "audit_forbidden_names",
        lambda _rows, _path: [
            {"rule": "forbidden_name", "key": "future_return"},
            {"rule": "generic_lookahead_rule"},
        ],
    )
    monkeypatch.setattr(
        lookahead,
        "audit_available_at",
        lambda _rows, _path: [{"rule": "available_at_after_timestamp"}],
    )
    monkeypatch.setattr(
        lookahead,
        "audit_used_for_decision",
        lambda _rows, _path: [{"rule": "used_for_decision_true"}],
    )

    payload = lookahead.audit_no_lookahead([path])

    assert payload["validation_status"] == "failed_lot8"
    assert payload["quality_flag"] == "invalid"
    assert len(payload["forbidden_feature_names"]) == 1
    assert len(payload["available_at_violations"]) == 1
    assert len(payload["used_for_decision_violations"]) == 1
    assert len(payload["lookahead_violations"]) == 1
    assert len(payload["violations"]) == 4


def test_catalog_load_handles_absent_oversized_non_list_and_filters_rows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "catalog.json"
    store = DatasetCatalog(path)
    assert store.load() == []

    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(catalog, "MAX_CATALOG_BYTES", 1)
    with pytest.raises(ValueError, match="catalog too large"):
        store.load()

    monkeypatch.setattr(catalog, "MAX_CATALOG_BYTES", 1_000)
    assert store.load() == []
    path.write_text('[{"dataset_id":"a"}, 1, null]', encoding="utf-8")
    assert store.load() == [{"dataset_id": "a"}]


def test_catalog_save_deduplicates_ids_and_preserves_idless_records(
    tmp_path: Path,
) -> None:
    store = DatasetCatalog(tmp_path / "nested" / "catalog.json")
    store.save(
        [
            {"dataset_id": "b", "value": 1},
            {"value": "idless"},
            {"dataset_id": "a", "value": 2},
            {"dataset_id": "b", "value": 3},
            {"dataset_id": "", "value": "empty-id"},
        ]
    )
    assert store.load() == [
        {"value": "idless"},
        {"dataset_id": "", "value": "empty-id"},
        {"dataset_id": "a", "value": 2},
        {"dataset_id": "b", "value": 3},
    ]


def test_catalog_atomic_failure_removes_temporary_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = DatasetCatalog(tmp_path / "catalog.json")

    def fail_replace(_source: object, _target: object) -> None:
        raise RuntimeError("replace failed")

    monkeypatch.setattr(catalog.os, "replace", fail_replace)
    with pytest.raises(RuntimeError, match="replace failed"):
        store.save([{"dataset_id": "a"}])
    assert not list(tmp_path.glob("*.tmp"))


def test_catalog_upsert_replaces_once_appends_new_and_gets_records(
    tmp_path: Path,
) -> None:
    path = tmp_path / "catalog.json"
    path.write_text(
        '[{"dataset_id":"same","value":1},'
        '{"dataset_id":"same","value":2},'
        '{"dataset_id":"other","value":3}]',
        encoding="utf-8",
    )
    store = DatasetCatalog(path)

    store.upsert(_Metadata("same", 10))  # type: ignore[arg-type]
    assert store.get("same") == {"dataset_id": "same", "value": 10}
    assert store.get("other") == {"dataset_id": "other", "value": 3}

    store.upsert(_Metadata("new", 20))  # type: ignore[arg-type]
    assert store.get("new") == {"dataset_id": "new", "value": 20}
    assert store.get("absent") is None
