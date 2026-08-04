from __future__ import annotations

import pytest

from crypto_quant_bot.regime import classifier


def classify(**overrides: float | None) -> str:
    values: dict[str, float | None] = {
        "direction_score": 0.0,
        "trend_score": 0.0,
        "range_score": 0.0,
        "compression_score": 0.0,
        "expansion_score": 0.0,
        "volatility_score": 0.0,
        "trend_up_threshold": 0.35,
        "trend_down_threshold": -0.35,
        "range_score_threshold": 0.60,
        "compression_threshold": 0.70,
        "expansion_threshold": 0.70,
        "volatility_high_threshold": 0.70,
    }
    values.update(overrides)
    return classifier.classify_state(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        (-2.0, 0.0),
        (0.25, 0.25),
        (2.0, 1.0),
    ],
)
def test_clamp01_boundaries(value: float | None, expected: float | None) -> None:
    assert classifier.clamp01(value) == expected


def test_trend_range_and_volatility_component_helpers() -> None:
    assert classifier.trend_score_from_direction(None) is None
    assert classifier.trend_score_from_direction(-0.6) == 0.6
    assert classifier.trend_score_from_direction(3.0) == 1.0

    assert classifier.range_score_from_components(None, 0.2, 0.1) is None
    assert classifier.range_score_from_components(0.2, None, 0.1) is None
    assert classifier.range_score_from_components(0.2, 0.1, None) is None
    assert classifier.range_score_from_components(0.2, 0.1, 0.3) == pytest.approx(0.72)
    assert classifier.range_score_from_components(2.0, 0.1, 0.3) == 0.0
    assert classifier.range_score_from_components(0.0, -1.0, 0.3) == 1.0

    assert classifier.volatility_score_from_row({}) is None
    assert classifier.volatility_score_from_row({"volatility_percentile_lookback": -2}) == 0.0
    assert classifier.volatility_score_from_row({"volatility_percentile_lookback": 2}) == 1.0


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"direction_score": None}, "unknown"),
        ({"compression_score": None}, "unknown"),
        ({"expansion_score": None}, "unknown"),
        ({"expansion_score": 0.8, "volatility_score": 0.8}, "volatile"),
        ({"expansion_score": 0.8, "volatility_score": None}, "expanding"),
        ({"expansion_score": 0.8, "volatility_score": 0.2}, "expanding"),
        ({"compression_score": 0.8}, "compressed"),
        ({"direction_score": 0.1, "range_score": 0.8}, "range"),
        ({"direction_score": 0.5}, "trend_up"),
        ({"direction_score": -0.5}, "trend_down"),
        ({"direction_score": 0.1, "range_score": None}, "mixed"),
        ({"direction_score": 0.1, "range_score": 0.2}, "mixed"),
    ],
)
def test_classify_state_all_precedence_branches(
    overrides: dict[str, float | None], expected: str
) -> None:
    assert classify(**overrides) == expected


def test_classify_regime_points_integrates_components_and_vwap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candles = [
        {
            "pair": "BTC/EUR",
            "timestamp": "2026-01-01T00:00:00Z",
            "available_at": "2026-01-01T00:00:01Z",
            "close": 100.0,
        },
        {
            "timestamp": "2026-01-01T00:05:00Z",
            "available_at": "2026-01-01T00:05:01Z",
            "close": 110.0,
        },
    ]
    volatility = [
        {"volatility_percentile_lookback": 0.9},
        {"volatility_percentile_lookback": None},
    ]
    ranges = [
        {
            "compression_score": 0.1,
            "expansion_score": 0.9,
            "range_width_pct": 0.2,
            "range_state": "expanding",
        },
        {
            "compression_score": 0.8,
            "expansion_score": 0.1,
            "range_width_pct": 0.1,
            "range_state": "compressed",
        },
    ]
    vwap = [
        {"timestamp": "2026-01-01T00:00:00Z", "vwap": 95.0},
    ]
    monkeypatch.setattr(classifier, "compute_direction_scores", lambda _rows, _window: [0.5, None])

    points = classifier.classify_regime_points(
        candles,
        volatility,
        ranges,
        vwap,
        config={
            "trend_window": 4,
            "trend_up_threshold": 0.35,
            "trend_down_threshold": -0.35,
            "range_score_threshold": 0.6,
            "compression_threshold": 0.7,
            "expansion_threshold": 0.7,
            "volatility_high_threshold": 0.7,
        },
        timeframe="5m",
        source_dataset_ids=["dataset-a", "dataset-b"],
        lineage_id="lineage-v1",
    )
    assert [point.regime_state for point in points] == ["volatile", "unknown"]
    assert points[0].components["close_vs_vwap"] == pytest.approx(0.05)
    assert points[1].components["close_vs_vwap"] is None
    assert points[0].components["trend_window"] == 4
    assert points[0].pair == "BTC/EUR"
    assert points[1].pair == "BTC/EUR"
    assert points[1].regime_id.startswith("regime_btc_eur_5m_1")
    assert all(point.used_for_decision is False for point in points)
    assert all(point.source_dataset_ids == ["dataset-a", "dataset-b"] for point in points)
