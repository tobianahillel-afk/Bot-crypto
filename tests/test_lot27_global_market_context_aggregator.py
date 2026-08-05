from __future__ import annotations

import copy

import pytest

from crypto_quant_bot.market_analysis.global_market_context_aggregator import (
    GlobalContextValidationError,
    build_global_market_context,
    replay_matches,
    validate_config,
)
from tests.lot27_fixtures import cloned_sources, load_config, load_sources

COMMIT = "abcdef1234567890"


def test_real_lot22_to_lot26_aggregation_oracle() -> None:
    state = build_global_market_context(load_sources(), load_config(), COMMIT)
    assert state.dominant_state == "GLOBAL_CONTEXT_MIXED"
    assert state.aggregate_evidence_score == 0.5646
    assert state.weighted_coverage_ratio == 1.0
    assert state.available_source_count == 5
    assert state.missing_source_weight == 0.0
    assert state.conflict_states == ("MTF_DIVERGENT",)
    assert state.category_support == {
        "TRENDING": 0.166955,
        "RANGE": 0.151198,
        "MIXED": 0.116448,
        "CONFLICT": 0.13,
    }
    assert "GMC_EXPLICIT_CONFLICT" in state.reason_codes
    assert state.confidence_interval is None
    assert state.trade_allowed is False
    assert state.execution_allowed is False


def test_replay_is_deterministic() -> None:
    first = build_global_market_context(load_sources(), load_config(), COMMIT)
    second = build_global_market_context(load_sources(), load_config(), COMMIT)
    assert replay_matches(first, second)
    assert first.output_checksum == second.output_checksum


@pytest.mark.parametrize(
    "removed_source",
    [
        "lot22_market_analysis",
        "lot23_technical_indicators",
        "lot24_trend_range_momentum",
        "lot25_volatility_regime_confluence",
        "lot26_multi_timeframe_alignment",
    ],
)
def test_source_ablation_never_renormalizes_weights(removed_source: str) -> None:
    sources = load_sources()
    sources.pop(removed_source)
    config = load_config()
    state = build_global_market_context(sources, config, COMMIT)
    expected = round(1.0 - float(config["source_weights"][removed_source]), 6)
    assert state.weighted_coverage_ratio == expected
    assert state.missing_source_weight == round(1.0 - expected, 6)
    contribution = next(item for item in state.contributions if item.source_id == removed_source)
    assert contribution.included is False
    assert contribution.effective_contribution == 0.0
    assert contribution.quality_state == "MISSING"


def test_missing_two_heavy_sources_is_unknown_without_renormalization() -> None:
    sources = load_sources()
    sources.pop("lot24_trend_range_momentum")
    sources.pop("lot25_volatility_regime_confluence")
    state = build_global_market_context(sources, load_config(), COMMIT)
    assert state.weighted_coverage_ratio == 0.5
    assert state.aggregate_evidence_score is None
    assert state.dominant_state == "GLOBAL_CONTEXT_UNKNOWN"
    assert state.validation_state == "UNKNOWN"
    assert "GMC_CONTEXT_UNKNOWN" in state.reason_codes


def test_invalid_source_is_excluded_fail_closed() -> None:
    sources = cloned_sources()
    sources["lot24_trend_range_momentum"]["execution_allowed"] = True
    state = build_global_market_context(sources, load_config(), COMMIT)
    contribution = next(
        item for item in state.contributions if item.source_id == "lot24_trend_range_momentum"
    )
    assert contribution.quality_state == "INVALID"
    assert contribution.included is False
    assert state.weighted_coverage_ratio == 0.75
    assert "GMC_SOURCE_INVALID" in state.reason_codes


def test_stale_source_is_excluded_and_age_is_preserved() -> None:
    sources = cloned_sources()
    for item in sources["lot22_market_analysis"]["timeframe_summaries"]:
        item["last_timestamp"] = "2026-05-25T00:00:00Z"
    state = build_global_market_context(sources, load_config(), COMMIT)
    contribution = next(item for item in state.contributions if item.source_id == "lot22_market_analysis")
    assert contribution.quality_state == "STALE"
    assert contribution.age_seconds is not None
    assert contribution.age_seconds > 900
    assert contribution.included is False


def test_no_explicit_conflict_and_clear_margin_can_be_trending() -> None:
    sources = cloned_sources()
    sources["lot26_multi_timeframe_alignment"]["alignment_state"] = "MTF_ALIGNED"
    sources["lot26_multi_timeframe_alignment"]["overall_agreement_score"] = 1.0
    state = build_global_market_context(sources, load_config(), COMMIT)
    assert state.dominant_state == "GLOBAL_CONTEXT_TRENDING"
    assert state.conflict_states == ()
    assert "GMC_CONTEXT_TRENDING" in state.reason_codes


def test_close_support_without_explicit_conflict_is_mixed() -> None:
    sources = cloned_sources()
    sources.pop("lot26_multi_timeframe_alignment")
    config = copy.deepcopy(load_config())
    config["thresholds"]["minimum_weighted_coverage_ratio"] = 0.75
    state = build_global_market_context(sources, config, COMMIT)
    assert state.dominant_state == "GLOBAL_CONTEXT_MIXED"
    assert "GMC_DOMINANCE_MARGIN_INSUFFICIENT" in state.reason_codes


def test_invalid_configs_are_rejected() -> None:
    config = load_config()
    config["source_weights"]["lot22_market_analysis"] = 0.2
    with pytest.raises(GlobalContextValidationError, match="sum"):
        validate_config(config)

    config = load_config()
    config["promotion_restrictions"]["signal_generation_allowed"] = True
    with pytest.raises(GlobalContextValidationError, match="permissions"):
        validate_config(config)

    config = load_config()
    config["source_specs"].pop("lot22_market_analysis")
    with pytest.raises(GlobalContextValidationError, match="source_specs"):
        validate_config(config)


def test_no_source_with_legal_time_is_rejected() -> None:
    with pytest.raises(GlobalContextValidationError, match="decision time"):
        build_global_market_context({}, load_config(), COMMIT)
