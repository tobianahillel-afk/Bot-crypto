from __future__ import annotations

import copy
from dataclasses import replace

import pytest

from crypto_quant_bot.market_analysis.global_market_context_aggregator import (
    GlobalContextValidationError,
    build_global_market_context,
    validate_config,
)
from tests.lot27_fixtures import cloned_sources, load_config, load_sources

COMMIT = "abcdef1234567890"


def test_state_contract_rejects_invalid_global_fields() -> None:
    state = build_global_market_context(load_sources(), load_config(), COMMIT)
    changes = (
        {"dominant_state": "BUY"},
        {"validation_state": "APPROVED"},
        {"category_support": {"TRENDING": 0.1}},
        {"available_source_count": 6},
        {"alternative_states": ("MIXED", "MIXED")},
        {"conflict_states": ("A", "A")},
        {"reason_codes": ("A", "A")},
        {"analysis_only": False},
        {"used_for_decision": True},
        {"forecast_generation_allowed": True},
        {"probability_claims_allowed": True},
        {"signal_generation_allowed": True},
        {"order_routing_allowed": True},
        {"execution_allowed": True},
        {"trade_allowed": True},
        {"approved_size": 1},
    )
    for change in changes:
        with pytest.raises(ValueError):
            replace(state, **change)


def test_state_contract_rejects_invalid_contribution_collection() -> None:
    state = build_global_market_context(load_sources(), load_config(), COMMIT)
    with pytest.raises(ValueError, match="all configured"):
        replace(state, contributions=state.contributions[:-1])
    duplicated = (*state.contributions[:-1], state.contributions[0])
    with pytest.raises(ValueError, match="invalid sources"):
        replace(state, contributions=duplicated)


def test_config_rejects_schema_weights_mappings_counts_and_thresholds() -> None:
    mutations = []
    config = load_config()
    config["schema_version"] = "v2"
    mutations.append(config)
    config = load_config()
    config["source_weights"].pop("lot22_market_analysis")
    mutations.append(config)
    config = load_config()
    config["source_weights"]["lot22_market_analysis"] = -0.1
    mutations.append(config)
    config = load_config()
    config["source_specs"]["lot22_market_analysis"]["semantic_mapping"] = {}
    mutations.append(config)
    config = load_config()
    config["source_specs"]["lot22_market_analysis"]["semantic_mapping"] = {
        "CONTEXT_MIXED": "BUY"
    }
    mutations.append(config)
    config = load_config()
    config["thresholds"]["minimum_available_source_count"] = 6
    mutations.append(config)
    config = load_config()
    config["thresholds"]["dominance_margin_minimum"] = 2.0
    mutations.append(config)
    for payload in mutations:
        with pytest.raises((GlobalContextValidationError, ValueError)):
            validate_config(payload)


def test_malformed_checks_state_score_and_time_are_fail_closed() -> None:
    sources = cloned_sources()
    sources["lot22_market_analysis"]["analysis_checks"] = []
    state = build_global_market_context(sources, load_config(), COMMIT)
    contribution = next(item for item in state.contributions if item.source_id == "lot22_market_analysis")
    assert contribution.quality_state == "INVALID"

    sources = cloned_sources()
    sources["lot23_technical_indicators"]["indicator_state"] = "BUY"
    state = build_global_market_context(sources, load_config(), COMMIT)
    contribution = next(item for item in state.contributions if item.source_id == "lot23_technical_indicators")
    assert contribution.quality_state == "INVALID"

    sources = cloned_sources()
    sources["lot24_trend_range_momentum"]["combined_context_score"] = True
    with pytest.raises(GlobalContextValidationError, match="numeric"):
        build_global_market_context(sources, load_config(), COMMIT)

    sources = cloned_sources()
    sources["lot25_volatility_regime_confluence"]["timeframe_summaries"] = []
    with pytest.raises(GlobalContextValidationError, match="summaries"):
        build_global_market_context(sources, load_config(), COMMIT)


def test_future_source_becomes_decision_clock_and_others_stale() -> None:
    sources = cloned_sources()
    sources["lot22_market_analysis"]["timeframe_summaries"][0]["last_timestamp"] = "2026-05-25T04:00:00Z"
    sources["lot22_market_analysis"]["timeframe_summaries"][1]["last_timestamp"] = "2026-05-25T04:00:00Z"
    state = build_global_market_context(sources, load_config(), COMMIT)
    contribution = next(item for item in state.contributions if item.source_id == "lot22_market_analysis")
    assert contribution.quality_state == "VALID"
    assert contribution.age_seconds == 0.0
    assert state.decision_time == "2026-05-25T04:15:00Z"
    stale = [item for item in state.contributions if item.source_id != "lot22_market_analysis"]
    assert all(item.quality_state == "STALE" for item in stale)


def test_range_can_dominate_when_conflict_and_trend_support_are_removed() -> None:
    sources = cloned_sources()
    sources.pop("lot24_trend_range_momentum")
    sources.pop("lot26_multi_timeframe_alignment")
    config = copy.deepcopy(load_config())
    config["thresholds"]["minimum_available_source_count"] = 3
    config["thresholds"]["minimum_weighted_coverage_ratio"] = 0.5
    state = build_global_market_context(sources, config, COMMIT)
    assert state.dominant_state == "GLOBAL_CONTEXT_RANGE"
    assert "GMC_CONTEXT_RANGE" in state.reason_codes


def test_zero_score_source_is_valid_and_contributes_zero() -> None:
    sources = cloned_sources()
    sources["lot23_technical_indicators"]["indicator_context_score"] = 0.0
    state = build_global_market_context(sources, load_config(), COMMIT)
    item = next(
        contribution
        for contribution in state.contributions
        if contribution.source_id == "lot23_technical_indicators"
    )
    assert item.included is True
    assert item.effective_contribution == 0.0
