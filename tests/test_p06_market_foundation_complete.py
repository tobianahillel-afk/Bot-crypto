from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.market_analysis import foundation


def market_summary(label: str, score: float, timeframe: str = "5m") -> SimpleNamespace:
    return SimpleNamespace(
        timeframe=timeframe,
        context_label=label,
        context_score=score,
        trend_context="TREND",
        volatility_level="MODERATE",
        volume_context="BALANCED_VOLUME",
        range_context="TRANSITIONAL_RANGE",
        regime_state="mixed",
    )


def test_analysis_checksum_and_source_artifacts_are_stable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = {
        "created_at": "one",
        "analysis_checksum": "old",
        "nested": [{"created_at": "nested", "value": 1}],
    }
    second = {
        "created_at": "two",
        "analysis_checksum": "new",
        "nested": [{"created_at": "other", "value": 1}],
    }
    assert foundation.build_analysis_checksum(first) == foundation.build_analysis_checksum(second)
    monkeypatch.setattr(
        foundation,
        "INPUT_SPECS",
        {
            "5m": {
                "candles": "a",
                "lot2_features": "b",
                "pivots": "c",
                "vwap": "d",
                "volatility": "e",
                "regime": "f",
                "market_state": "g",
            },
            "15m": {
                "candles": "a",
                "lot2_features": "h",
                "pivots": "i",
                "vwap": "j",
                "volatility": "k",
                "regime": "l",
                "market_state": "m",
            },
        },
    )
    artifacts = foundation.default_source_artifacts()
    assert artifacts == sorted(set(artifacts))
    assert {"a", "b", "m"}.issubset(artifacts)


def test_require_object_expected_pairs_and_numeric_helpers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(foundation, "load_json", lambda _path: {"status": "PASS"})
    assert foundation._require_object(tmp_path, "x.json") == {"status": "PASS"}
    monkeypatch.setattr(foundation, "load_json", lambda _path: [1])
    with pytest.raises(ValueError, match="must contain a JSON object"):
        foundation._require_object(tmp_path, "x.json")
    foundation._require_expected_pairs({"status": "PASS"}, {"status": "PASS"}, name="x")
    with pytest.raises(ValueError, match="x invalid status"):
        foundation._require_expected_pairs({"status": "FAIL"}, {"status": "PASS"}, name="x")
    assert foundation._clamp(-1.0) == 0.0
    assert foundation._clamp(2.0) == 1.0
    assert foundation._round6(1.23456789) == 1.234568


@pytest.mark.parametrize(
    ("ratio", "expected"),
    [(1.2, "ACTIVE_VOLUME"), (0.8, "SOFT_VOLUME"), (1.0, "BALANCED_VOLUME")],
)
def test_volume_context_states(ratio: float, expected: str) -> None:
    assert foundation._volume_context(ratio) == expected


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (2.0, "POSITIVE_DRIFT"),
        (-2.0, "NEGATIVE_DRIFT"),
        (0.2, "BALANCED_DRIFT"),
        (1.0, "TRANSITIONAL_DRIFT"),
    ],
)
def test_trend_context_states(change: float, expected: str) -> None:
    assert foundation._trend_context(change) == expected


@pytest.mark.parametrize(
    ("true_range", "realized", "expected"),
    [(1.3, 0.0, "HIGH"), (0.0, 0.02, "HIGH"), (0.7, 0.0, "MODERATE"), (0.0, 0.005, "MODERATE"), (0.1, 0.001, "LOW")],
)
def test_volatility_level_states(true_range: float, realized: float, expected: str) -> None:
    assert foundation._volatility_level(true_range, realized) == expected


def test_range_context_prefers_valid_market_state_and_fallbacks() -> None:
    assert foundation._range_context(9.0, 9.0, {"range_state": {"range_state": "compressed"}}) == "COMPRESSED"
    assert foundation._range_context(1.0, 0.1, {"range_state": {"range_state": "unknown"}}) == "NARROW_BALANCE"
    assert foundation._range_context(6.0, 2.0, {"range_state": "invalid"}) == "WIDE_SWING"
    assert foundation._range_context(3.0, 1.0, {}) == "TRANSITIONAL_RANGE"


@pytest.mark.parametrize(
    ("close", "vwap", "expected"),
    [(100.0, 0.0, "VWAP_UNAVAILABLE"), (101.0, 100.0, "ABOVE_VWAP"), (99.0, 100.0, "BELOW_VWAP"), (100.1, 100.0, "NEAR_VWAP")],
)
def test_vwap_relation_states(close: float, vwap: float, expected: str) -> None:
    assert foundation._vwap_relation(close, vwap) == expected


def test_pivot_context_states() -> None:
    assert foundation._pivot_context(100.0, []) == "NO_CONFIRMED_PIVOT_CONTEXT"
    assert foundation._pivot_context(0.0, [{"price": 1.0, "side": "high"}]) == "PIVOT_CONTEXT_UNAVAILABLE"
    assert foundation._pivot_context(100.0, [{"price": 0.0, "side": "low"}]) == "PIVOT_CONTEXT_UNAVAILABLE"
    assert foundation._pivot_context(100.0, [{"price": 100.5, "side": "high"}]) == "NEAR_CONFIRMED_RESISTANCE"
    assert foundation._pivot_context(100.0, [{"price": 99.5, "side": "low"}]) == "NEAR_CONFIRMED_SUPPORT"
    assert foundation._pivot_context(100.0, [{"price": 90.0, "side": "low"}]) == "AWAY_FROM_CONFIRMED_PIVOTS"
    assert foundation._pivot_context(100.0, [{"price": 100.5, "side": "other"}]) == "AWAY_FROM_CONFIRMED_PIVOTS"


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"row_count": 2}, "CONTEXT_INSUFFICIENT_DATA"),
        ({"volatility_intensity": 0.8, "context_score": 0.8}, "CONTEXT_VOLATILE"),
        ({"close_change_percent": 2.0, "confidence_score": 0.3}, "CONTEXT_TRENDING"),
        ({"volume_activity": 0.2, "volatility_intensity": 0.2}, "CONTEXT_LOW_ACTIVITY"),
        ({"close_change_percent": 0.2, "range_percent": 2.0}, "CONTEXT_RANGING"),
        ({"context_score": 0.2, "range_percent": 4.0}, "CONTEXT_NEUTRAL"),
        ({"context_score": 0.5, "range_percent": 4.0}, "CONTEXT_MIXED"),
    ],
)
def test_context_label_all_outcomes(kwargs: dict[str, float | int], expected: str) -> None:
    values: dict[str, float | int] = {
        "row_count": 6,
        "context_score": 0.5,
        "close_change_percent": 1.0,
        "range_percent": 4.0,
        "volatility_intensity": 0.5,
        "volume_activity": 0.5,
        "confidence_score": 0.5,
    }
    values.update(kwargs)
    assert foundation._context_label(**values) == expected  # type: ignore[arg-type]


def test_market_context_aggregation_and_formatting() -> None:
    assert foundation._aggregate_market_context([]) == ("CONTEXT_INSUFFICIENT_DATA", 0.0)
    assert foundation._aggregate_market_context([market_summary("CONTEXT_RANGING", 0.6)])[0] == "CONTEXT_RANGING"
    assert foundation._aggregate_market_context([
        market_summary("CONTEXT_VOLATILE", 0.8),
        market_summary("CONTEXT_MIXED", 0.8, "15m"),
    ])[0] == "CONTEXT_VOLATILE"
    assert foundation._aggregate_market_context([
        market_summary("CONTEXT_TRENDING", 0.6),
        market_summary("CONTEXT_MIXED", 0.6, "15m"),
    ])[0] == "CONTEXT_TRENDING"
    assert foundation._aggregate_market_context([
        market_summary("CONTEXT_RANGING", 0.4),
        market_summary("CONTEXT_NEUTRAL", 0.4, "15m"),
    ])[0] == "CONTEXT_RANGING"
    assert foundation._aggregate_market_context([
        market_summary("CONTEXT_NEUTRAL", 0.2),
        market_summary("CONTEXT_NEUTRAL", 0.2, "15m"),
    ])[0] == "CONTEXT_NEUTRAL"
    assert foundation._aggregate_market_context([
        market_summary("CONTEXT_LOW_ACTIVITY", 0.4),
        market_summary("CONTEXT_TRENDING", 0.4, "15m"),
    ])[0] == "CONTEXT_MIXED"
    formatted = foundation._format_context_by_timeframe(
        [market_summary("CONTEXT_RANGING", 0.4), market_summary("CONTEXT_NEUTRAL", 0.2, "15m")],
        "context_label",
    )
    assert formatted == "5m=CONTEXT_RANGING; 15m=CONTEXT_NEUTRAL"


def test_confidence_context_dict_and_missing_paths() -> None:
    result = foundation._confidence_context(
        {
            "5m": {"regime_state": {"confidence_score": 0.3333333}},
            "15m": {"regime_state": "unknown"},
        }
    )
    assert result == "5m=0.333333; 15m=0.0"


def test_make_inputs_uses_registered_specs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        foundation,
        "INPUT_SPECS",
        {
            "5m": {
                "candles": "candles.jsonl",
                "lot2_features": "features.jsonl",
                "pivots": "pivots.jsonl",
                "vwap": "vwap.jsonl",
                "volatility": "volatility.jsonl",
                "regime": "regime.jsonl",
                "market_state": "market.jsonl",
            }
        },
    )
    monkeypatch.setattr(foundation, "load_jsonl", lambda _path: [{}, {}, {}])
    inputs = foundation._make_inputs(tmp_path)
    assert inputs["5m"].row_count == 3
    assert inputs["5m"].candles_path == "candles.jsonl"


def setup_archive(monkeypatch: pytest.MonkeyPatch, root: Path) -> tuple[str, int]:
    monkeypatch.setattr(foundation, "ARCHIVE_OUTPUT_PATH", "archive.tar.gz")
    monkeypatch.setattr(foundation, "ARCHIVE_SHA256_OUTPUT_PATH", "archive.tar.gz.sha256")
    monkeypatch.setattr(foundation, "LOT21_FREEZE_REPORT_PATH", "freeze.md")
    path = root / "archive.tar.gz"
    path.write_bytes(b"archive")
    checksum = sha256_file(path)
    size = path.stat().st_size
    (root / "archive.tar.gz.sha256").write_text(f"{checksum}  archive.tar.gz\n", encoding="utf-8")
    (root / "freeze.md").write_text("frozen", encoding="utf-8")
    return checksum, size


def test_foundation_archive_validation_success_and_selected_failures(
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
    assert foundation._validate_frozen_archive(tmp_path, product_scope=scope, closure_snapshot=closure) == (checksum, size)
    with pytest.raises(ValueError, match="source_v1_archive_frozen"):
        foundation._validate_frozen_archive(
            tmp_path,
            product_scope={**scope, "source_v1_archive_frozen": False},
            closure_snapshot=closure,
        )
    with pytest.raises(ValueError, match="Lot 20 archive checksum"):
        foundation._validate_frozen_archive(
            tmp_path,
            product_scope=scope,
            closure_snapshot={**closure, "archive_sha256": "bad"},
        )


def test_build_empty_timeframe_summary() -> None:
    result = foundation._build_timeframe_summary(
        timeframe="5m",
        candles=[],
        lot2_features=[],
        pivots=[],
        vwap_rows=[],
        volatility_rows=[],
        regime_rows=[],
        market_state_rows=[],
    )
    assert result.row_count == 0
    assert result.context_label == "CONTEXT_INSUFFICIENT_DATA"
    assert result.volatility_level == "UNAVAILABLE"
