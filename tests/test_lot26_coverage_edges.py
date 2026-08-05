from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from crypto_quant_bot.contracts.timeframe_alignment import require_unique_codes, validate_score
from crypto_quant_bot.market_analysis import alignment_io
from crypto_quant_bot.market_analysis.alignment_common import (
    Lot26ValidationError,
    load_json_object,
    require_mapping,
)
from crypto_quant_bot.market_analysis.alignment_config import (
    validate_alignment_config,
    validate_scale_registry,
)
from crypto_quant_bot.market_analysis.alignment_math import component_compatibility
from tests.lot26_fixtures import load_config, load_registry, make_alignment


def test_common_helpers_fail_closed(tmp_path: Path) -> None:
    array_path = tmp_path / "array.json"
    array_path.write_text("[]", encoding="utf-8")
    with pytest.raises(Lot26ValidationError, match="expected JSON object"):
        load_json_object(array_path)
    object_path = tmp_path / "object.json"
    object_path.write_text('{"a": 1}', encoding="utf-8")
    assert load_json_object(object_path) == {"a": 1}
    with pytest.raises(Lot26ValidationError, match="must be a mapping"):
        require_mapping({"a": 1}, "a")
    with pytest.raises(ValueError, match="non-empty strings"):
        require_unique_codes(("",), "codes")
    validate_score(None, "score")


def test_more_configuration_failure_branches() -> None:
    config = deepcopy(load_config())
    config["classification_thresholds"]["multi_mismatch_count"] = 0
    with pytest.raises(Lot26ValidationError, match="multi_mismatch_count"):
        validate_alignment_config(config)

    config = deepcopy(load_config())
    config["time_policy"]["eligibility_rule"] = "future"
    with pytest.raises(Lot26ValidationError, match="eligibility_rule"):
        validate_alignment_config(config)

    config = deepcopy(load_config())
    config["categorical_compatibility"]["range"] = {}
    with pytest.raises(Lot26ValidationError, match="matrix is missing"):
        validate_alignment_config(config)

    config = deepcopy(load_config())
    config["categorical_compatibility"]["range"]["RANGE_CONTEXT_BREAKING_STRUCTURE"]["EXTRA"] = 0.5
    with pytest.raises(Lot26ValidationError, match="matrix is incomplete"):
        validate_alignment_config(config)


def test_more_registry_failure_branches() -> None:
    registry = deepcopy(load_registry())
    registry["lot26_initial_profile"]["join_method"] = "INNER"
    with pytest.raises(Lot26ValidationError, match="MTF_SCALE_RELATION_NOT_ALLOWED"):
        validate_scale_registry(registry)

    registry = deepcopy(load_registry())
    registry["scales"] = {}
    with pytest.raises(Lot26ValidationError, match="scales must be a list"):
        validate_scale_registry(registry)

    registry = deepcopy(load_registry())
    next(item for item in registry["scales"] if item["scale_id"] == "timebar-5m")["lot26_role"] = "OTHER"
    with pytest.raises(Lot26ValidationError, match="MTF_SCALE_RELATION_NOT_ALLOWED"):
        validate_scale_registry(registry)

    registry = deepcopy(load_registry())
    next(item for item in registry["scales"] if item["scale_id"] == "timebar-15m")["lot26_role"] = "OTHER"
    with pytest.raises(Lot26ValidationError, match="MTF_SCALE_RELATION_NOT_ALLOWED"):
        validate_scale_registry(registry)


def test_more_math_failure_branches() -> None:
    config = deepcopy(load_config())
    config["unknown_state_tokens"] = "UNKNOWN"
    with pytest.raises(Lot26ValidationError, match="must be a list"):
        component_compatibility("trend", "A", "A", config)

    config = deepcopy(load_config())
    config["ordinal_encodings"].pop("trend")
    with pytest.raises(Lot26ValidationError, match="ordinal encoding"):
        component_compatibility("trend", "A", "A", config)

    config = deepcopy(load_config())
    config["categorical_compatibility"]["range"].pop("RANGE_CONTEXT_NEUTRAL")
    assert component_compatibility(
        "range", "RANGE_CONTEXT_NEUTRAL", "RANGE_CONTEXT_MIXED", config
    ) is None


def test_jsonl_missing_large_and_cleanup_absent_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(FileNotFoundError):
        alignment_io.load_jsonl(tmp_path / "missing.jsonl")
    path = tmp_path / "large.jsonl"
    path.write_text('{"a": 1}\n', encoding="utf-8")
    monkeypatch.setattr(alignment_io, "MAX_JSON_BYTES", 1)
    with pytest.raises(Lot26ValidationError, match="too large"):
        alignment_io.load_jsonl(path)

    monkeypatch.setattr(alignment_io, "MAX_JSON_BYTES", 5_000_000)
    target = tmp_path / "target.json"
    monkeypatch.setattr(
        alignment_io.os,
        "replace",
        lambda *_: (_ for _ in ()).throw(OSError("x")),
    )
    monkeypatch.setattr(Path, "exists", lambda self: False)
    with pytest.raises(OSError):
        alignment_io.write_json_atomic(target, {"a": 1})


def test_alignment_schema_and_analysis_only_failures() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        replace(make_alignment(), schema_version="v2")
    with pytest.raises(ValueError, match="analysis_only"):
        replace(make_alignment(), analysis_only=False)
