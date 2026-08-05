from __future__ import annotations

from copy import deepcopy

import pytest
from hypothesis import given
from hypothesis import strategies as st
from lot26_fixtures import load_clock, load_config, load_registry

from crypto_quant_bot.market_analysis.alignment_common import Lot26ValidationError
from crypto_quant_bot.market_analysis.alignment_config import (
    config_checksum,
    validate_alignment_config,
    validate_decision_clock,
    validate_scale_registry,
)
from crypto_quant_bot.market_analysis.alignment_math import (
    classify_alignment,
    component_compatibility,
    compute_weighted_agreement,
    uncertainty_from_coverage,
)


def test_component_oracles_for_lot25_contexts() -> None:
    config = load_config()
    assert component_compatibility("trend", "TREND_CONTEXT_UPWARD", "TREND_CONTEXT_UPWARD", config) == 1.0
    assert component_compatibility("momentum", "MOMENTUM_CONTEXT_ACCELERATING", "MOMENTUM_CONTEXT_DECELERATING", config) == 0.0
    assert component_compatibility("volatility", "VOLATILITY_CONTEXT_LOW", "VOLATILITY_CONTEXT_HIGH", config) == 0.0
    assert component_compatibility("confluence", "CONFLUENCE_CONTEXT_PARTIAL", "CONFLUENCE_CONTEXT_ALIGNED", config) == 0.5
    assert component_compatibility("range", "RANGE_CONTEXT_BREAKING_STRUCTURE", "RANGE_CONTEXT_BREAKING_STRUCTURE", config) == 1.0
    assert component_compatibility("regime", "REGIME_CONTEXT_TRENDING", "REGIME_CONTEXT_COMPRESSED", config) == 0.25


def test_unknown_or_unencoded_states_propagate_null() -> None:
    config = load_config()
    assert component_compatibility("trend", "UNKNOWN", "TREND_CONTEXT_UPWARD", config) is None
    assert component_compatibility("momentum", "MOMENTUM_CONTEXT_DIVERGENT", "MOMENTUM_CONTEXT_NEUTRAL", config) is None
    with pytest.raises(Lot26ValidationError, match="unknown component"):
        component_compatibility("other", "A", "A", config)


def test_weighted_agreement_exact_oracle() -> None:
    scores = {"trend": 1.0, "range": 1.0, "momentum": 1.0, "volatility": 0.0, "regime": 0.25, "confluence": 0.5}
    count, coverage, score = compute_weighted_agreement(scores, load_config())
    assert count == 6
    assert coverage == 1.0
    assert score == 0.65


def test_weighted_agreement_requires_count_and_coverage() -> None:
    config = load_config()
    low_count = {"trend": 1.0, "range": 1.0, "momentum": 1.0, "volatility": None, "regime": None, "confluence": None}
    assert compute_weighted_agreement(low_count, config) == (3, 0.53, None)
    low_coverage = {"trend": None, "range": 1.0, "momentum": None, "volatility": 1.0, "regime": 1.0, "confluence": 1.0}
    assert compute_weighted_agreement(low_coverage, config) == (4, 0.6, None)


def test_weighted_agreement_rejects_bad_shape_and_scores() -> None:
    config = load_config()
    with pytest.raises(Lot26ValidationError, match="six components"):
        compute_weighted_agreement({"trend": 1.0}, config)
    scores = dict.fromkeys(config["component_weights"], 1.0)
    scores["trend"] = float("nan")
    with pytest.raises(Lot26ValidationError, match="invalid component score"):
        compute_weighted_agreement(scores, config)


def test_classification_priority_and_coherence() -> None:
    config = load_config()
    full = dict.fromkeys(config["component_weights"], 1.0)
    assert classify_alignment(0.9, full, config)[:4] == ("MTF_ALIGNED", "MTF_NO_HARD_DIVERGENCE", "MTF_COHERENT", "MTF_CONTEXT_ALIGNED")
    partial = {**full, "trend": 0.25}
    assert classify_alignment(0.7, partial, config)[:3] == ("MTF_PARTIAL", "MTF_DIRECTIONAL_MISMATCH", "MTF_MIXED")
    multi = {**full, "volatility": 0.0, "regime": 0.25}
    result = classify_alignment(0.65, multi, config)
    assert result[0] == "MTF_DIVERGENT"
    assert result[1] == "MTF_MULTI_COMPONENT_MISMATCH"
    assert result[2] == "MTF_INCOHERENT"
    assert result[4] == ("regime", "volatility")


def test_classification_single_regime_volatility_and_unknown() -> None:
    config = load_config()
    full = dict.fromkeys(config["component_weights"], 1.0)
    assert classify_alignment(0.8, {**full, "regime": 0.25}, config)[1] == "MTF_REGIME_MISMATCH"
    assert classify_alignment(0.8, {**full, "volatility": 0.25}, config)[1] == "MTF_VOLATILITY_MISMATCH"
    unknown = classify_alignment(None, dict.fromkeys(full), config)
    assert unknown[:4] == ("MTF_UNKNOWN", "MTF_UNKNOWN", "MTF_UNKNOWN", "MTF_CONTEXT_UNKNOWN")


@pytest.mark.parametrize(
    ("coverage", "count", "expected"),
    [(1.0, 6, "LOW"), (0.9, 5, "MODERATE"), (0.75, 4, "HIGH"), (0.69, 4, "UNKNOWN")],
)
def test_uncertainty_from_coverage(coverage: float, count: int, expected: str) -> None:
    assert uncertainty_from_coverage(coverage, count) == expected


def test_config_registry_clock_and_checksum_are_valid() -> None:
    config = load_config()
    validate_alignment_config(config)
    assert len(config_checksum(config)) == 64
    assert validate_scale_registry(load_registry()) == ("timebar-5m", "timebar-15m")
    assert validate_decision_clock(load_clock()) == "CLOSED_LOCAL_BAR"


@pytest.mark.parametrize(
    "mutator",
    [
        lambda c: c.update(component_weights={"trend": 1.0}),
        lambda c: c["component_weights"].update(trend=0.0),
        lambda c: c["component_weights"].update(trend=0.5),
        lambda c: c["classification_thresholds"].update(partial_minimum=0.9),
        lambda c: c.update(minimum_available_component_count=7),
        lambda c: c.update(minimum_weighted_coverage_ratio=2.0),
        lambda c: c["time_policy"].update(join_method="INNER"),
        lambda c: c["time_policy"].update(local_max_staleness_seconds=-1),
        lambda c: c["promotion_restrictions"].update(signal_generation_allowed=True),
        lambda c: c["categorical_compatibility"].pop("range"),
        lambda c: c["categorical_compatibility"]["range"]["RANGE_CONTEXT_NEUTRAL"].pop("RANGE_CONTEXT_MIXED"),
        lambda c: c["categorical_compatibility"]["regime"]["REGIME_CONTEXT_RANGE"].update(REGIME_CONTEXT_TRENDING=0.4),
    ],
)
def test_invalid_configurations_fail_closed(mutator: object) -> None:
    config = deepcopy(load_config())
    mutator(config)  # type: ignore[operator]
    with pytest.raises(Lot26ValidationError):
        validate_alignment_config(config)


def test_invalid_registry_and_clock_fail_closed() -> None:
    registry = deepcopy(load_registry())
    registry["lot26_initial_profile"]["local_scale_id"] = "timebar-1m"
    with pytest.raises(Lot26ValidationError, match="MTF_SCALE_RELATION_NOT_ALLOWED"):
        validate_scale_registry(registry)
    registry = deepcopy(load_registry())
    next(item for item in registry["scales"] if item["scale_id"] == "timebar-1m")["enabled_in_lot26"] = True
    with pytest.raises(Lot26ValidationError):
        validate_scale_registry(registry)
    clock = deepcopy(load_clock())
    clock["lot26_policy"]["enabled_triggers"] = ["FORECAST_UPDATE"]
    with pytest.raises(Lot26ValidationError):
        validate_decision_clock(clock)
    clock = deepcopy(load_clock())
    clock["lot26_policy"]["trade_decision_allowed"] = True
    with pytest.raises(Lot26ValidationError):
        validate_decision_clock(clock)


@given(st.sampled_from(["trend", "momentum", "volatility", "confluence"]))
def test_ordinal_compatibility_is_symmetric_and_bounded(component: str) -> None:
    config = load_config()
    states = list(config["ordinal_encodings"][component])
    for left in states:
        for right in states:
            forward = component_compatibility(component, left, right, config)
            reverse = component_compatibility(component, right, left, config)
            assert forward == reverse
            assert forward is not None and 0.0 <= forward <= 1.0


@given(st.dictionaries(st.sampled_from(["trend", "range", "momentum", "volatility", "regime", "confluence"]), st.one_of(st.none(), st.floats(min_value=0, max_value=1, allow_nan=False)), min_size=6, max_size=6))
def test_weighted_coverage_is_bounded(scores: dict[str, float | None]) -> None:
    count, coverage, score = compute_weighted_agreement(scores, load_config())
    assert 0 <= count <= 6
    assert 0.0 <= coverage <= 1.0
    assert score is None or 0.0 <= score <= 1.0
