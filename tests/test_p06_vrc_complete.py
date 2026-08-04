from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.market_analysis import volatility_regime_confluence as vrc


def vrc_summary(
    *,
    state: str = "VOLATILITY_CONTEXT_NEUTRAL",
    score: float = 0.5,
) -> SimpleNamespace:
    return SimpleNamespace(
        volatility_state=state,
        volatility_context_score=score,
        regime_state=state.replace("VOLATILITY", "REGIME"),
        regime_context_score=score,
        confluence_state=state.replace("VOLATILITY", "CONFLUENCE"),
        confluence_context_score=score,
        combined_context_state=state.replace("VOLATILITY", "VRC"),
        combined_context_score=score,
    )


def test_vrc_checksum_source_artifacts_and_object_helpers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    first = {
        "created_at": "one",
        "vrc_checksum": "old",
        "nested": [{"created_at": "nested", "value": 1}],
    }
    second = {
        "created_at": "two",
        "vrc_checksum": "new",
        "nested": [{"created_at": "other", "value": 1}],
    }
    assert vrc.build_vrc_checksum(first) == vrc.build_vrc_checksum(second)
    artifacts = vrc.default_vrc_source_artifacts()
    assert artifacts == sorted(set(artifacts))
    assert vrc.LOT24_OUTPUT_PATH in artifacts

    monkeypatch.setattr(vrc, "load_json", lambda _path: {"status": "PASS"})
    assert vrc._require_object(tmp_path, "x.json") == {"status": "PASS"}
    monkeypatch.setattr(vrc, "load_json", lambda _path: [1])
    with pytest.raises(ValueError, match="must contain a JSON object"):
        vrc._require_object(tmp_path, "x.json")
    vrc._require_expected_pairs({"status": "PASS"}, {"status": "PASS"}, name="x")
    with pytest.raises(ValueError, match="x invalid status"):
        vrc._require_expected_pairs({"status": "FAIL"}, {"status": "PASS"}, name="x")


def test_vrc_small_helpers_and_latest_rows(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    assert vrc._round6(1.23456789) == 1.234568
    assert vrc._clamp(-1.0) == 0.0
    assert vrc._clamp(2.0) == 1.0
    assert vrc._safe_percent(2.0, 0.0) == 0.0
    assert vrc._safe_percent(2.0, 4.0) == 50.0
    monkeypatch.setattr(vrc, "load_jsonl", lambda _path: [])
    assert vrc._latest_jsonl_row(tmp_path, "empty.jsonl") == {}
    monkeypatch.setattr(vrc, "load_jsonl", lambda _path: [{"id": 1}, {"id": 2}])
    assert vrc._latest_jsonl_row(tmp_path, "rows.jsonl") == {"id": 2}
    assert vrc._component_dict({"x": {"value": 1}}, "x") == {"value": 1}
    assert vrc._component_dict({"x": "bad"}, "x") == {}


def test_indicator_value_map_accepts_only_typed_entries() -> None:
    mapped = vrc._indicator_value_map(
        {
            "indicator_values": [
                {"indicator_id": "atr_5", "value": 1.2},
                {"indicator_id": 1, "value": 2.0},
                "ignored",
            ]
        }
    )
    assert mapped == {"atr_5": 1.2}
    assert vrc._indicator_value_map({"indicator_values": "bad"}) == {}


def test_volatility_expansion_and_compression_scores_are_bounded() -> None:
    expansion = vrc._volatility_expansion_score(
        atr_percent=2.0,
        true_range_percent=2.0,
        bollinger_width_5=5.0,
        range_width_percent=5.0,
        volatility_percentile=1.0,
        realized_volatility_6=0.1,
        expansion_score_source=2.0,
    )
    compression = vrc._volatility_compression_score(
        atr_percent=0.0,
        bollinger_width_5=0.0,
        range_width_percent=0.0,
        volatility_percentile=0.0,
        compression_score_source=1.0,
    )
    assert expansion == 1.0
    assert compression == 1.0


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"row_count": 1}, "VOLATILITY_CONTEXT_INSUFFICIENT_DATA"),
        (
            {"compression_score": 0.8, "expansion_score": 0.2},
            "VOLATILITY_CONTEXT_COMPRESSING",
        ),
        (
            {"expansion_score": 0.8, "compression_score": 0.2},
            "VOLATILITY_CONTEXT_EXPANDING",
        ),
        ({"expansion_score": 0.6}, "VOLATILITY_CONTEXT_HIGH"),
        ({"volatility_level": "HIGH"}, "VOLATILITY_CONTEXT_HIGH"),
        ({"compression_score": 0.6}, "VOLATILITY_CONTEXT_LOW"),
        ({"volatility_level": "LOW"}, "VOLATILITY_CONTEXT_LOW"),
        ({"expansion_score": 0.4}, "VOLATILITY_CONTEXT_MODERATE"),
        ({"compression_score": 0.4}, "VOLATILITY_CONTEXT_MODERATE"),
        ({"volatility_level": "MODERATE"}, "VOLATILITY_CONTEXT_MODERATE"),
        (
            {"expansion_score": 0.36, "compression_score": 0.36},
            "VOLATILITY_CONTEXT_MIXED",
        ),
        ({}, "VOLATILITY_CONTEXT_NEUTRAL"),
    ],
)
def test_volatility_state_all_outcomes(
    kwargs: dict[str, float | int | str], expected: str
) -> None:
    values: dict[str, float | int | str] = {
        "row_count": 6,
        "expansion_score": 0.1,
        "compression_score": 0.1,
        "volatility_level": "UNKNOWN",
    }
    values.update(kwargs)
    assert vrc._volatility_state(**values) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"row_count": 1}, "REGIME_CONTEXT_INSUFFICIENT_DATA"),
        ({"market_regime_source_state": "compressed"}, "REGIME_CONTEXT_COMPRESSED"),
        (
            {"volatility_state": "VOLATILITY_CONTEXT_COMPRESSING"},
            "REGIME_CONTEXT_COMPRESSED",
        ),
        ({"volatility_state": "VOLATILITY_CONTEXT_HIGH"}, "REGIME_CONTEXT_VOLATILE"),
        ({"trm_combined_state": "TRM_CONTEXT_TRENDING"}, "REGIME_CONTEXT_TRENDING"),
        ({"trend_state": "TREND_CONTEXT_UPWARD"}, "REGIME_CONTEXT_TRENDING"),
        ({"market_regime_source_state": "range"}, "REGIME_CONTEXT_RANGING"),
        ({"trm_combined_state": "TRM_CONTEXT_COMPRESSED"}, "REGIME_CONTEXT_RANGING"),
        ({"range_state": "RANGE_CONTEXT_NEUTRAL"}, "REGIME_CONTEXT_NEUTRAL"),
        ({}, "REGIME_CONTEXT_MIXED"),
    ],
)
def test_regime_state_all_outcomes(kwargs: dict[str, object], expected: str) -> None:
    values: dict[str, object] = {
        "row_count": 6,
        "market_regime_source_state": "unknown",
        "trm_combined_state": "TRM_CONTEXT_MIXED",
        "trend_state": "TREND_CONTEXT_MIXED",
        "range_state": "RANGE_CONTEXT_MIXED",
        "volatility_state": "VOLATILITY_CONTEXT_NEUTRAL",
    }
    values.update(kwargs)
    assert vrc._regime_state(**values) == expected  # type: ignore[arg-type]


def test_regime_context_score_exercises_every_weight() -> None:
    score = vrc._regime_context_score(
        market_regime_source_state="range",
        trm_combined_state="TRM_CONTEXT_RANGING",
        trend_state="TREND_CONTEXT_UPWARD",
        range_state="RANGE_CONTEXT_NEUTRAL",
        volatility_state="VOLATILITY_CONTEXT_HIGH",
        market_context_score=2.0,
    )
    assert 0.0 < score <= 1.0
    compressed = vrc._regime_context_score(
        market_regime_source_state="compressed",
        trm_combined_state="TRM_CONTEXT_TRENDING",
        trend_state="TREND_CONTEXT_DOWNWARD",
        range_state="RANGE_CONTEXT_MIXED",
        volatility_state="VOLATILITY_CONTEXT_COMPRESSING",
        market_context_score=-1.0,
    )
    assert compressed > 0.0


def test_confluence_components_alignment_and_divergence() -> None:
    components = vrc._confluence_components(
        market_context_state="CONTEXT_MIXED",
        technical_indicator_state="INDICATOR_MIXED",
        trend_state="TREND_CONTEXT_UPWARD",
        range_state="RANGE_CONTEXT_COMPRESSED",
        momentum_state="MOMENTUM_CONTEXT_DIVERGENT",
        volatility_state="VOLATILITY_CONTEXT_HIGH",
        regime_state="REGIME_CONTEXT_COMPRESSED",
        trm_combined_state="TRM_CONTEXT_TRENDING",
    )
    assert components["trend_alignment"] is False
    assert components["range_alignment"] is True
    assert components["indicator_alignment"] is True
    assert components["market_alignment"] is True
    agreement, divergence = vrc._confluence_scores(components)
    assert agreement == 0.6
    assert divergence == 0.8

    low_alignment = vrc._confluence_components(
        market_context_state="CONTEXT_LOW_ACTIVITY",
        technical_indicator_state="INDICATOR_NEUTRAL",
        trend_state="TREND_CONTEXT_MIXED",
        range_state="RANGE_CONTEXT_MIXED",
        momentum_state="MOMENTUM_CONTEXT_NEUTRAL",
        volatility_state="VOLATILITY_CONTEXT_EXPANDING",
        regime_state="REGIME_CONTEXT_VOLATILE",
        trm_combined_state="TRM_CONTEXT_TRENDING",
    )
    agreement, divergence = vrc._confluence_scores(low_alignment)
    assert agreement >= 0.2
    assert divergence >= 0.4


@pytest.mark.parametrize(
    ("row_count", "agreement", "divergence", "expected"),
    [
        (1, 1.0, 0.0, "CONFLUENCE_CONTEXT_INSUFFICIENT_DATA"),
        (6, 0.8, 0.6, "CONFLUENCE_CONTEXT_DIVERGENT"),
        (6, 0.8, 0.1, "CONFLUENCE_CONTEXT_ALIGNED"),
        (6, 0.6, 0.3, "CONFLUENCE_CONTEXT_PARTIAL"),
        (6, 0.1, 0.1, "CONFLUENCE_CONTEXT_NEUTRAL"),
        (6, 0.23, 0.3, "CONFLUENCE_CONTEXT_WEAK"),
        (6, 0.4, 0.5, "CONFLUENCE_CONTEXT_MIXED"),
    ],
)
def test_confluence_state_all_outcomes(
    row_count: int,
    agreement: float,
    divergence: float,
    expected: str,
) -> None:
    assert vrc._confluence_state(
        row_count=row_count,
        agreement_score=agreement,
        divergence_score=divergence,
    ) == expected


def test_confluence_context_score_is_bounded() -> None:
    assert vrc._confluence_context_score(1.0, 0.0) == 1.0
    assert vrc._confluence_context_score(0.0, 1.0) == 0.0


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {"volatility_state": "VOLATILITY_CONTEXT_INSUFFICIENT_DATA"},
            "VRC_CONTEXT_INSUFFICIENT_DATA",
        ),
        (
            {"confluence_state": "CONFLUENCE_CONTEXT_DIVERGENT"},
            "VRC_CONTEXT_DIVERGENT",
        ),
        (
            {
                "regime_state": "REGIME_CONTEXT_COMPRESSED",
                "volatility_state": "VOLATILITY_CONTEXT_LOW",
            },
            "VRC_CONTEXT_COMPRESSED",
        ),
        (
            {
                "regime_state": "REGIME_CONTEXT_VOLATILE",
                "confluence_state": "CONFLUENCE_CONTEXT_PARTIAL",
            },
            "VRC_CONTEXT_VOLATILE_MIXED",
        ),
        (
            {
                "regime_state": "REGIME_CONTEXT_TRENDING",
                "trm_combined_state": "TRM_CONTEXT_TRENDING",
                "confluence_state": "CONFLUENCE_CONTEXT_ALIGNED",
            },
            "VRC_CONTEXT_ALIGNED_TREND",
        ),
        (
            {
                "regime_state": "REGIME_CONTEXT_RANGING",
                "confluence_state": "CONFLUENCE_CONTEXT_PARTIAL",
            },
            "VRC_CONTEXT_ALIGNED_RANGE",
        ),
        ({"combined_context_score": 0.1}, "VRC_CONTEXT_NEUTRAL"),
        ({"combined_context_score": 0.5}, "VRC_CONTEXT_MIXED"),
    ],
)
def test_combined_vrc_state_all_outcomes(kwargs: dict[str, object], expected: str) -> None:
    values: dict[str, object] = {
        "volatility_state": "VOLATILITY_CONTEXT_NEUTRAL",
        "regime_state": "REGIME_CONTEXT_MIXED",
        "confluence_state": "CONFLUENCE_CONTEXT_MIXED",
        "trm_combined_state": "TRM_CONTEXT_MIXED",
        "combined_context_score": 0.5,
    }
    values.update(kwargs)
    assert vrc._combined_context_state(**values) == expected  # type: ignore[arg-type]


def test_aggregate_state_empty_same_preferred_and_mixed() -> None:
    assert vrc._aggregate_state(
        [],
        field_name="volatility_state",
        default_state="VOLATILITY_CONTEXT_INSUFFICIENT_DATA",
        preferred_states=["VOLATILITY_CONTEXT_HIGH"],
        score_field="volatility_context_score",
    ) == ("VOLATILITY_CONTEXT_INSUFFICIENT_DATA", 0.0)
    same = [vrc_summary(state="VOLATILITY_CONTEXT_HIGH", score=0.8)]
    assert vrc._aggregate_state(
        same,
        field_name="volatility_state",
        default_state="VOLATILITY_CONTEXT_INSUFFICIENT_DATA",
        preferred_states=["VOLATILITY_CONTEXT_HIGH"],
        score_field="volatility_context_score",
    ) == ("VOLATILITY_CONTEXT_HIGH", 0.8)
    preferred = [
        vrc_summary(state="VOLATILITY_CONTEXT_HIGH", score=0.8),
        vrc_summary(state="VOLATILITY_CONTEXT_LOW", score=0.2),
    ]
    assert vrc._aggregate_state(
        preferred,
        field_name="volatility_state",
        default_state="VOLATILITY_CONTEXT_INSUFFICIENT_DATA",
        preferred_states=["VOLATILITY_CONTEXT_HIGH"],
        score_field="volatility_context_score",
    ) == ("VOLATILITY_CONTEXT_HIGH", 0.5)
    mixed = [
        vrc_summary(state="VOLATILITY_CONTEXT_LOW", score=0.4),
        vrc_summary(state="VOLATILITY_CONTEXT_MODERATE", score=0.6),
    ]
    assert vrc._aggregate_state(
        mixed,
        field_name="volatility_state",
        default_state="VOLATILITY_CONTEXT_INSUFFICIENT_DATA",
        preferred_states=["VOLATILITY_CONTEXT_HIGH"],
        score_field="volatility_context_score",
    ) == ("VOLATILITY_CONTEXT_MIXED", 0.5)


def test_vrc_non_executable_summary_and_empty_timeframe() -> None:
    text = vrc._non_executable_summary(
        timeframe="5m",
        combined_context_state="VRC_CONTEXT_MIXED",
        combined_context_score=0.5,
    )
    assert "5m" in text and "execution" in text
    result = vrc._build_timeframe_summary(
        timeframe="5m",
        candles=[],
        market_row={},
        indicator_row={},
        trend_row={},
        volatility_row={},
        regime_row={},
        market_state_row={},
    )
    assert result.row_count == 0
    assert result.combined_context_state == "VRC_CONTEXT_INSUFFICIENT_DATA"


def setup_archive(monkeypatch: pytest.MonkeyPatch, root: Path) -> tuple[str, int]:
    monkeypatch.setattr(vrc, "ARCHIVE_OUTPUT_PATH", "archive.tar.gz")
    monkeypatch.setattr(vrc, "ARCHIVE_SHA256_OUTPUT_PATH", "archive.tar.gz.sha256")
    monkeypatch.setattr(vrc, "LOT21_FREEZE_REPORT_PATH", "freeze.md")
    path = root / "archive.tar.gz"
    path.write_bytes(b"archive")
    checksum = sha256_file(path)
    size = path.stat().st_size
    (root / "archive.tar.gz.sha256").write_text(
        f"{checksum}  archive.tar.gz\n",
        encoding="utf-8",
    )
    (root / "freeze.md").write_text("frozen", encoding="utf-8")
    return checksum, size


def test_vrc_archive_validation_success_and_selected_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    checksum, size = setup_archive(monkeypatch, tmp_path)
    scope = {
        "source_v1_archive_frozen": True,
        "source_v1_archive_path": "archive.tar.gz",
        "source_v1_archive_sha256": checksum,
        "source_v1_archive_size_bytes": size,
    }
    closure = {"archive_sha256": checksum, "archive_size_bytes": size}
    assert vrc._validate_frozen_archive(
        tmp_path,
        product_scope=scope,
        closure_snapshot=closure,
    ) == (checksum, size)
    with pytest.raises(ValueError, match="source_v1_archive_path"):
        vrc._validate_frozen_archive(
            tmp_path,
            product_scope={**scope, "source_v1_archive_path": "bad"},
            closure_snapshot=closure,
        )
    with pytest.raises(ValueError, match="Lot 20 archive size"):
        vrc._validate_frozen_archive(
            tmp_path,
            product_scope=scope,
            closure_snapshot={**closure, "archive_size_bytes": size + 1},
        )
