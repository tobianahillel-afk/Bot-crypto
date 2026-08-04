from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.market_analysis import trend_range_momentum as trm


def summary(
    *,
    trend_state: str = "TREND_CONTEXT_NEUTRAL",
    trend_score: float = 0.5,
    range_state: str = "RANGE_CONTEXT_NEUTRAL",
    range_score: float = 0.5,
    momentum_state: str = "MOMENTUM_CONTEXT_NEUTRAL",
    momentum_score: float = 0.5,
    combined_state: str = "TRM_CONTEXT_NEUTRAL",
    combined_score: float = 0.5,
) -> SimpleNamespace:
    return SimpleNamespace(
        trend_state=trend_state,
        trend_context_score=trend_score,
        range_state=range_state,
        range_context_score=range_score,
        momentum_state=momentum_state,
        momentum_context_score=momentum_score,
        combined_context_state=combined_state,
        combined_context_score=combined_score,
    )


def test_trend_checksum_and_small_helpers() -> None:
    first = {
        "created_at": "one",
        "trend_checksum": "old",
        "nested": [{"created_at": "nested", "value": 1}],
    }
    second = {
        "created_at": "two",
        "trend_checksum": "new",
        "nested": [{"created_at": "other", "value": 1}],
    }
    assert trm.build_trend_checksum(first) == trm.build_trend_checksum(second)
    assert trm._sign(2.0) == 1
    assert trm._sign(-2.0) == -1
    assert trm._sign(0.0) == 0
    assert trm._safe_percent(5.0, 0.0) == 0.0
    assert trm._safe_percent(5.0, 10.0) == 50.0
    assert trm._trend_slope_5([1.0, 2.0]) == 0.0
    assert trm._trend_slope_5([1.0, 2.0, 3.0, 4.0, 5.0]) == 1.0
    assert trm._clamp(-1.0) == 0.0
    assert trm._clamp(2.0) == 1.0
    assert trm._round6(1.23456789) == 1.234568


def test_indicator_value_map_validation() -> None:
    values = [
        {"indicator_id": indicator_id, "value": index + 1.0}
        for index, indicator_id in enumerate(sorted(trm.REQUIRED_INDICATOR_SET))
    ]
    values.extend(["ignored", {"indicator_id": 3, "value": 1}])
    mapped = trm._indicator_value_map({"indicator_values": values})
    assert set(mapped) == set(trm.REQUIRED_INDICATOR_SET)
    with pytest.raises(ValueError, match="missing Lot 23 indicators"):
        trm._indicator_value_map({"indicator_values": "not-list"})
    with pytest.raises(ValueError, match="missing Lot 23 indicators"):
        trm._indicator_value_map({"indicator_values": values[:-3]})


@pytest.mark.parametrize(
    ("slope", "extension", "expected"),
    [
        (0.2, 0.2, "UPWARD_SLOPE"),
        (-0.2, -0.2, "DOWNWARD_SLOPE"),
        (0.01, 0.01, "FLAT_SLOPE"),
        (0.2, -0.2, "TRANSITIONAL_SLOPE"),
    ],
)
def test_trend_direction_context_all_states(
    slope: float, extension: float, expected: str
) -> None:
    assert trm._trend_direction_context(slope, extension) == expected


def test_context_scores_cover_alignment_and_extremes() -> None:
    aligned = trm._trend_context_score(
        slope_percent=0.4,
        close_vs_ema_percent=0.4,
        close_change_percent=0.5,
        market_context_score=0.8,
    )
    conflicting = trm._trend_context_score(
        slope_percent=0.4,
        close_vs_ema_percent=-0.4,
        close_change_percent=0.5,
        market_context_score=2.0,
    )
    assert aligned > 0.0
    assert conflicting > 0.0
    assert aligned != conflicting
    assert 0.0 <= trm._range_context_score(
        range_width_percent=0.5,
        range_position_percent=100.0,
        bollinger_width_5=3.0,
        atr_percent=1.0,
    ) <= 1.0
    assert 0.0 <= trm._range_context_score(
        range_width_percent=4.0,
        range_position_percent=50.0,
        bollinger_width_5=0.0,
        atr_percent=0.0,
    ) <= 1.0
    assert 0.0 <= trm._momentum_context_score(
        momentum_percent=1.0,
        rate_of_change_3=-1.0,
        rsi_5=100.0,
        macd_histogram=100.0,
    ) <= 1.0


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"row_count": 1}, "TREND_CONTEXT_INSUFFICIENT_DATA"),
        (
            {
                "close_vs_ema_percent": 0.3,
                "slope_percent": 0.3,
                "close_change_percent": 0.4,
                "trend_context_score": 0.8,
            },
            "TREND_CONTEXT_UPWARD",
        ),
        (
            {
                "close_vs_ema_percent": -0.3,
                "slope_percent": -0.3,
                "close_change_percent": -0.4,
                "trend_context_score": 0.8,
            },
            "TREND_CONTEXT_DOWNWARD",
        ),
        (
            {"close_vs_ema_percent": 0.01, "slope_percent": 0.01},
            "TREND_CONTEXT_FLAT",
        ),
        ({"trend_context_score": 0.1, "slope_percent": 0.2}, "TREND_CONTEXT_NEUTRAL"),
        ({"trend_context_score": 0.8, "slope_percent": 0.2}, "TREND_CONTEXT_MIXED"),
    ],
)
def test_trend_state_all_outcomes(kwargs: dict[str, float | int], expected: str) -> None:
    values: dict[str, float | int] = {
        "row_count": 6,
        "close_vs_ema_percent": 0.1,
        "slope_percent": 0.1,
        "close_change_percent": 0.1,
        "trend_context_score": 0.5,
    }
    values.update(kwargs)
    assert trm._trend_state(**values) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"row_count": 1}, "RANGE_CONTEXT_INSUFFICIENT_DATA"),
        (
            {"range_width_percent": 1.0, "bollinger_width_5": 1.0},
            "RANGE_CONTEXT_COMPRESSED",
        ),
        (
            {
                "range_width_percent": 1.5,
                "range_position_percent": 90.0,
                "trend_context_score": 0.8,
            },
            "RANGE_CONTEXT_BREAKING_STRUCTURE",
        ),
        ({"range_width_percent": 2.0}, "RANGE_CONTEXT_EXPANDED"),
        ({"bollinger_width_5": 3.0}, "RANGE_CONTEXT_EXPANDED"),
        ({"atr_percent": 1.0}, "RANGE_CONTEXT_EXPANDED"),
        (
            {"range_width_percent": 1.5, "range_position_percent": 50.0},
            "RANGE_CONTEXT_NEUTRAL",
        ),
        (
            {"range_width_percent": 1.5, "range_position_percent": 75.0},
            "RANGE_CONTEXT_MIXED",
        ),
    ],
)
def test_range_state_all_outcomes(kwargs: dict[str, float | int], expected: str) -> None:
    values: dict[str, float | int] = {
        "row_count": 6,
        "range_width_percent": 1.5,
        "range_position_percent": 50.0,
        "bollinger_width_5": 2.0,
        "atr_percent": 0.5,
        "trend_context_score": 0.5,
    }
    values.update(kwargs)
    assert trm._range_state(**values) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"row_count": 1}, "MOMENTUM_CONTEXT_INSUFFICIENT_DATA"),
        ({"momentum_context_score": 0.1}, "MOMENTUM_CONTEXT_NEUTRAL"),
        (
            {"rate_of_change_3": 0.3, "macd_histogram": -0.1},
            "MOMENTUM_CONTEXT_DIVERGENT",
        ),
        (
            {"rsi_5": 80.0, "rate_of_change_3": 0.1, "macd_histogram": 0.1},
            "MOMENTUM_CONTEXT_DIVERGENT",
        ),
        (
            {"momentum_3": 1.0, "rate_of_change_3": 0.3, "macd_histogram": 0.1},
            "MOMENTUM_CONTEXT_ACCELERATING",
        ),
        (
            {"momentum_3": -1.0, "rate_of_change_3": -0.3, "macd_histogram": -0.1},
            "MOMENTUM_CONTEXT_DECELERATING",
        ),
        ({"momentum_3": 0.0}, "MOMENTUM_CONTEXT_MIXED"),
    ],
)
def test_momentum_state_all_outcomes(kwargs: dict[str, float | int], expected: str) -> None:
    values: dict[str, float | int] = {
        "row_count": 6,
        "momentum_3": 0.0,
        "rate_of_change_3": 0.0,
        "rsi_5": 50.0,
        "macd_histogram": 0.0,
        "momentum_context_score": 0.5,
    }
    values.update(kwargs)
    assert trm._momentum_state(**values) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("trend", "range_", "momentum", "score", "expected"),
    [
        (
            "TREND_CONTEXT_INSUFFICIENT_DATA",
            "RANGE_CONTEXT_NEUTRAL",
            "MOMENTUM_CONTEXT_NEUTRAL",
            0.5,
            "TRM_CONTEXT_INSUFFICIENT_DATA",
        ),
        (
            "TREND_CONTEXT_FLAT",
            "RANGE_CONTEXT_COMPRESSED",
            "MOMENTUM_CONTEXT_NEUTRAL",
            0.5,
            "TRM_CONTEXT_COMPRESSED",
        ),
        (
            "TREND_CONTEXT_MIXED",
            "RANGE_CONTEXT_EXPANDED",
            "MOMENTUM_CONTEXT_ACCELERATING",
            0.6,
            "TRM_CONTEXT_VOLATILE",
        ),
        (
            "TREND_CONTEXT_UPWARD",
            "RANGE_CONTEXT_MIXED",
            "MOMENTUM_CONTEXT_MIXED",
            0.6,
            "TRM_CONTEXT_TRENDING",
        ),
        (
            "TREND_CONTEXT_NEUTRAL",
            "RANGE_CONTEXT_NEUTRAL",
            "MOMENTUM_CONTEXT_NEUTRAL",
            0.4,
            "TRM_CONTEXT_RANGING",
        ),
        (
            "TREND_CONTEXT_MIXED",
            "RANGE_CONTEXT_MIXED",
            "MOMENTUM_CONTEXT_MIXED",
            0.1,
            "TRM_CONTEXT_NEUTRAL",
        ),
        (
            "TREND_CONTEXT_MIXED",
            "RANGE_CONTEXT_MIXED",
            "MOMENTUM_CONTEXT_MIXED",
            0.5,
            "TRM_CONTEXT_MIXED",
        ),
    ],
)
def test_combined_context_state_all_outcomes(
    trend: str, range_: str, momentum: str, score: float, expected: str
) -> None:
    assert trm._combined_context_state(
        trend_state=trend,
        range_state=range_,
        momentum_state=momentum,
        combined_context_score=score,
    ) == expected


def test_aggregate_state_branches() -> None:
    assert trm._aggregate_trend_state([]) == ("TREND_CONTEXT_INSUFFICIENT_DATA", 0.0)
    assert trm._aggregate_trend_state([summary(trend_state="TREND_CONTEXT_UPWARD")])[0] == "TREND_CONTEXT_UPWARD"
    assert trm._aggregate_trend_state([
        summary(trend_state="TREND_CONTEXT_UPWARD", trend_score=0.8),
        summary(trend_state="TREND_CONTEXT_NEUTRAL", trend_score=0.8),
    ])[0] == "TREND_CONTEXT_UPWARD"
    assert trm._aggregate_trend_state([
        summary(trend_state="TREND_CONTEXT_DOWNWARD", trend_score=0.8),
        summary(trend_state="TREND_CONTEXT_NEUTRAL", trend_score=0.8),
    ])[0] == "TREND_CONTEXT_DOWNWARD"
    assert trm._aggregate_trend_state([
        summary(trend_state="TREND_CONTEXT_FLAT"),
        summary(trend_state="TREND_CONTEXT_NEUTRAL"),
    ])[0] == "TREND_CONTEXT_FLAT"
    assert trm._aggregate_trend_state([
        summary(trend_state="TREND_CONTEXT_UPWARD"),
        summary(trend_state="TREND_CONTEXT_DOWNWARD"),
    ])[0] == "TREND_CONTEXT_MIXED"

    assert trm._aggregate_range_state([]) == ("RANGE_CONTEXT_INSUFFICIENT_DATA", 0.0)
    assert trm._aggregate_range_state([summary(range_state="RANGE_CONTEXT_EXPANDED")])[0] == "RANGE_CONTEXT_EXPANDED"
    assert trm._aggregate_range_state([
        summary(range_state="RANGE_CONTEXT_BREAKING_STRUCTURE", range_score=0.8),
        summary(range_state="RANGE_CONTEXT_MIXED", range_score=0.8),
    ])[0] == "RANGE_CONTEXT_BREAKING_STRUCTURE"
    assert trm._aggregate_range_state([
        summary(range_state="RANGE_CONTEXT_EXPANDED", range_score=0.8),
        summary(range_state="RANGE_CONTEXT_MIXED", range_score=0.8),
    ])[0] == "RANGE_CONTEXT_EXPANDED"
    assert trm._aggregate_range_state([
        summary(range_state="RANGE_CONTEXT_COMPRESSED"),
        summary(range_state="RANGE_CONTEXT_MIXED"),
    ])[0] == "RANGE_CONTEXT_COMPRESSED"
    assert trm._aggregate_range_state([
        summary(range_state="RANGE_CONTEXT_NEUTRAL"),
        summary(range_state="RANGE_CONTEXT_COMPRESSED"),
    ])[0] == "RANGE_CONTEXT_COMPRESSED"
    assert trm._aggregate_range_state([
        summary(range_state="RANGE_CONTEXT_NEUTRAL"),
        summary(range_state="RANGE_CONTEXT_MIXED"),
    ])[0] == "RANGE_CONTEXT_MIXED"

    assert trm._aggregate_momentum_state([]) == ("MOMENTUM_CONTEXT_INSUFFICIENT_DATA", 0.0)
    assert trm._aggregate_momentum_state([summary(momentum_state="MOMENTUM_CONTEXT_NEUTRAL")])[0] == "MOMENTUM_CONTEXT_NEUTRAL"
    assert trm._aggregate_momentum_state([
        summary(momentum_state="MOMENTUM_CONTEXT_DIVERGENT"),
        summary(momentum_state="MOMENTUM_CONTEXT_NEUTRAL"),
    ])[0] == "MOMENTUM_CONTEXT_DIVERGENT"
    assert trm._aggregate_momentum_state([
        summary(momentum_state="MOMENTUM_CONTEXT_ACCELERATING", momentum_score=0.8),
        summary(momentum_state="MOMENTUM_CONTEXT_NEUTRAL", momentum_score=0.8),
    ])[0] == "MOMENTUM_CONTEXT_ACCELERATING"
    assert trm._aggregate_momentum_state([
        summary(momentum_state="MOMENTUM_CONTEXT_DECELERATING", momentum_score=0.8),
        summary(momentum_state="MOMENTUM_CONTEXT_NEUTRAL", momentum_score=0.8),
    ])[0] == "MOMENTUM_CONTEXT_DECELERATING"
    assert trm._aggregate_momentum_state([
        summary(momentum_state="MOMENTUM_CONTEXT_NEUTRAL"),
        summary(momentum_state="MOMENTUM_CONTEXT_MIXED"),
    ])[0] == "MOMENTUM_CONTEXT_NEUTRAL"
    assert trm._aggregate_momentum_state([
        summary(momentum_state="MOMENTUM_CONTEXT_ACCELERATING"),
        summary(momentum_state="MOMENTUM_CONTEXT_DECELERATING"),
    ])[0] == "MOMENTUM_CONTEXT_MIXED"

    assert trm._aggregate_combined_state([]) == ("TRM_CONTEXT_INSUFFICIENT_DATA", 0.0)
    assert trm._aggregate_combined_state([summary(combined_state="TRM_CONTEXT_TRENDING")])[0] == "TRM_CONTEXT_TRENDING"
    assert trm._aggregate_combined_state([
        summary(combined_state="TRM_CONTEXT_VOLATILE", combined_score=0.8),
        summary(combined_state="TRM_CONTEXT_MIXED", combined_score=0.8),
    ])[0] == "TRM_CONTEXT_VOLATILE"
    assert trm._aggregate_combined_state([
        summary(combined_state="TRM_CONTEXT_TRENDING", combined_score=0.8),
        summary(combined_state="TRM_CONTEXT_MIXED", combined_score=0.8),
    ])[0] == "TRM_CONTEXT_TRENDING"
    assert trm._aggregate_combined_state([
        summary(combined_state="TRM_CONTEXT_COMPRESSED"),
        summary(combined_state="TRM_CONTEXT_RANGING"),
    ])[0] == "TRM_CONTEXT_COMPRESSED"
    assert trm._aggregate_combined_state([
        summary(combined_state="TRM_CONTEXT_RANGING"),
        summary(combined_state="TRM_CONTEXT_NEUTRAL"),
    ])[0] == "TRM_CONTEXT_RANGING"
    assert trm._aggregate_combined_state([
        summary(combined_state="TRM_CONTEXT_TRENDING"),
        summary(combined_state="TRM_CONTEXT_VOLATILE"),
    ])[0] == "TRM_CONTEXT_VOLATILE"


def setup_archive(monkeypatch: pytest.MonkeyPatch, root: Path) -> tuple[str, int]:
    monkeypatch.setattr(trm, "ARCHIVE_OUTPUT_PATH", "archive.tar.gz")
    monkeypatch.setattr(trm, "ARCHIVE_SHA256_OUTPUT_PATH", "archive.tar.gz.sha256")
    monkeypatch.setattr(trm, "LOT21_FREEZE_REPORT_PATH", "freeze.md")
    archive_path = root / "archive.tar.gz"
    archive_path.write_bytes(b"archive")
    checksum = sha256_file(archive_path)
    size = archive_path.stat().st_size
    (root / "archive.tar.gz.sha256").write_text(
        f"{checksum}  archive.tar.gz\n", encoding="utf-8"
    )
    (root / "freeze.md").write_text("frozen", encoding="utf-8")
    return checksum, size


def test_trend_archive_validation_success_and_failures(
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
    assert trm._validate_frozen_archive(
        tmp_path, product_scope=scope, closure_snapshot=closure
    ) == (checksum, size)

    failures = [
        ({**scope, "source_v1_archive_frozen": False}, closure, "source_v1_archive_frozen"),
        ({**scope, "source_v1_archive_path": "bad"}, closure, "source_v1_archive_path"),
        ({**scope, "source_v1_archive_sha256": "bad"}, closure, "source_v1_archive_sha256"),
        ({**scope, "source_v1_archive_size_bytes": size + 1}, closure, "source_v1_archive_size_bytes"),
        (scope, {**closure, "archive_sha256": "bad"}, "Lot 20 archive checksum"),
        (scope, {**closure, "archive_size_bytes": size + 1}, "Lot 20 archive size"),
    ]
    for bad_scope, bad_closure, message in failures:
        with pytest.raises(ValueError, match=message):
            trm._validate_frozen_archive(
                tmp_path,
                product_scope=bad_scope,
                closure_snapshot=bad_closure,
            )


def test_build_empty_timeframe_summary_and_summary_text() -> None:
    result = trm._build_timeframe_summary(
        timeframe="5m",
        candles=[],
        market_row={},
        indicator_row={},
    )
    assert result.row_count == 0
    assert result.combined_context_state == "TRM_CONTEXT_INSUFFICIENT_DATA"
    assert "execution remains blocked" in result.non_executable_summary
    text = trm._non_executable_summary(
        timeframe="15m",
        combined_context_state="TRM_CONTEXT_TRENDING",
        combined_context_score=0.75,
    )
    assert "15m" in text and "execution" in text and "0.75" in text
