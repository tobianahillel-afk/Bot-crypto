from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from uuid import NAMESPACE_URL, uuid5

import pytest

import crypto_quant_bot.market_analysis.global_market_context_aggregator as aggregator
from crypto_quant_bot.market_analysis.global_market_context_aggregator_models import (
    SourceContributionV1,
)
from tests.lot27_fixtures import cloned_sources, load_config, load_sources

COMMIT = "abcdef1234567890"


def contribution(
    *,
    source_id: str = "lot22_market_analysis",
    category: str | None = "MIXED",
    score: float | None = 0.5,
    weight: float = 0.15,
    included: bool = True,
    quality: str = "VALID",
    event_time: str | None = "2026-05-25T03:00:00Z",
    age_seconds: float | None = 0.0,
    reason_codes: tuple[str, ...] = (),
) -> SourceContributionV1:
    effective = weight * score if included and score is not None else 0.0
    return SourceContributionV1(
        source_id=source_id,
        source_schema_version="source-v1" if included else None,
        source_artifact=f"data/audit/{source_id}.json",
        source_checksum="a" * 64 if included else None,
        source_state="STATE" if included else None,
        semantic_category=category if included else None,
        source_score=score if included else None,
        configured_weight=weight,
        effective_contribution=effective,
        quality_state=quality,
        event_time=event_time if included else None,
        age_seconds=age_seconds if included else None,
        included=included,
        reason_codes=reason_codes,
    )


def test_canonical_json_checksum_and_stable_id_have_exact_oracles() -> None:
    payload = {"b": 1, "a": "é"}
    expected_json = '{"a":"é","b":1}'
    assert aggregator.canonical_json(payload) == expected_json
    expected_checksum = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
    assert aggregator.checksum(payload) == expected_checksum
    expected_id = str(uuid5(NAMESPACE_URL, f"lot27:context:{expected_checksum}"))
    assert aggregator.stable_id("context", payload) == expected_id
    assert aggregator.stable_id("lineage", payload) != expected_id
    assert aggregator.stable_id("context", {"a": "é", "b": 2}) != expected_id


def test_require_mapping_returns_mapping_and_rejects_non_mapping() -> None:
    payload = {"a": 1}
    assert aggregator._require_mapping(payload, "payload") is payload
    with pytest.raises(aggregator.GlobalContextValidationError, match="payload must be an object"):
        aggregator._require_mapping([("a", 1)], "payload")


def test_weight_validator_rejects_missing_zero_and_non_normalized_weights() -> None:
    aggregator._validate_weights(load_config())

    missing = load_config()
    missing["source_weights"].pop("lot22_market_analysis")
    with pytest.raises(aggregator.GlobalContextValidationError, match="exactly five"):
        aggregator._validate_weights(missing)

    zero = load_config()
    zero["source_weights"]["lot22_market_analysis"] = 0.0
    zero["source_weights"]["lot23_technical_indicators"] = 0.3
    with pytest.raises(aggregator.GlobalContextValidationError, match="positive"):
        aggregator._validate_weights(zero)

    non_normalized = load_config()
    non_normalized["source_weights"]["lot22_market_analysis"] = 0.16
    with pytest.raises(aggregator.GlobalContextValidationError, match="sum to one"):
        aggregator._validate_weights(non_normalized)


def test_spec_validator_rejects_container_and_semantic_mapping_errors() -> None:
    aggregator._validate_specs(load_config())

    missing = load_config()
    missing["source_specs"].pop("lot22_market_analysis")
    with pytest.raises(aggregator.GlobalContextValidationError, match="exactly five"):
        aggregator._validate_specs(missing)

    malformed = load_config()
    malformed["source_specs"]["lot22_market_analysis"] = []
    with pytest.raises(aggregator.GlobalContextValidationError, match="must be an object"):
        aggregator._validate_specs(malformed)

    empty_mapping = load_config()
    empty_mapping["source_specs"]["lot22_market_analysis"]["semantic_mapping"] = {}
    with pytest.raises(aggregator.GlobalContextValidationError, match="invalid semantic mapping"):
        aggregator._validate_specs(empty_mapping)

    forbidden_category = load_config()
    forbidden_category["source_specs"]["lot22_market_analysis"]["semantic_mapping"] = {
        "CONTEXT_MIXED": "BUY"
    }
    with pytest.raises(aggregator.GlobalContextValidationError, match="invalid semantic mapping"):
        aggregator._validate_specs(forbidden_category)


def test_restriction_validator_requires_non_empty_all_false_mapping() -> None:
    aggregator._validate_restrictions(load_config())

    empty = load_config()
    empty["promotion_restrictions"] = {}
    with pytest.raises(aggregator.GlobalContextValidationError, match="permissions"):
        aggregator._validate_restrictions(empty)

    enabled = load_config()
    enabled["promotion_restrictions"]["signal_generation_allowed"] = True
    with pytest.raises(aggregator.GlobalContextValidationError, match="permissions"):
        aggregator._validate_restrictions(enabled)


def test_threshold_validator_checks_count_and_each_bounded_threshold() -> None:
    aggregator._validate_thresholds(load_config())
    for count in (0, 6):
        config = load_config()
        config["thresholds"]["minimum_available_source_count"] = count
        with pytest.raises(aggregator.GlobalContextValidationError, match="minimum source count"):
            aggregator._validate_thresholds(config)
    for key in (
        "minimum_weighted_coverage_ratio",
        "dominance_margin_minimum",
        "explicit_conflict_mixed_minimum",
    ):
        config = load_config()
        config["thresholds"][key] = 1.1
        with pytest.raises(ValueError, match=key):
            aggregator._validate_thresholds(config)


def test_validate_config_invokes_all_sections() -> None:
    aggregator.validate_config(load_config())
    wrong_schema = load_config()
    wrong_schema["schema_version"] = "other"
    with pytest.raises(aggregator.GlobalContextValidationError, match="unsupported"):
        aggregator.validate_config(wrong_schema)


def test_source_event_time_exact_oracles_and_failures() -> None:
    sources = load_sources()
    assert (
        aggregator._source_event_time(
            sources["lot26_multi_timeframe_alignment"],
            "lot26_multi_timeframe_alignment",
        )
        == "2026-05-25T03:00:00Z"
    )
    assert (
        aggregator._source_event_time(sources["lot22_market_analysis"], "lot22_market_analysis")
        == "2026-05-25T03:00:00Z"
    )

    missing_time = copy.deepcopy(sources["lot26_multi_timeframe_alignment"])
    missing_time.pop("decision_time")
    with pytest.raises(aggregator.GlobalContextValidationError, match="decision_time missing"):
        aggregator._source_event_time(missing_time, "lot26_multi_timeframe_alignment")

    no_summaries = copy.deepcopy(sources["lot22_market_analysis"])
    no_summaries["timeframe_summaries"] = []
    with pytest.raises(aggregator.GlobalContextValidationError, match="summaries missing"):
        aggregator._source_event_time(no_summaries, "lot22_market_analysis")

    malformed_summary = copy.deepcopy(sources["lot22_market_analysis"])
    malformed_summary["timeframe_summaries"] = ["invalid"]
    with pytest.raises(aggregator.GlobalContextValidationError, match="must be an object"):
        aggregator._source_event_time(malformed_summary, "lot22_market_analysis")

    unsupported = copy.deepcopy(sources["lot22_market_analysis"])
    unsupported["timeframe_summaries"][0]["timeframe"] = "1h"
    with pytest.raises(aggregator.GlobalContextValidationError, match="unsupported timeframe"):
        aggregator._source_event_time(unsupported, "lot22_market_analysis")


def test_checks_valid_exact_truth_table() -> None:
    assert aggregator._checks_valid({}, None) is True
    assert aggregator._checks_valid({"checks": []}, "checks") is False
    assert aggregator._checks_valid({"checks": {}}, "checks") is False
    assert aggregator._checks_valid({"checks": ["PASS"]}, "checks") is False
    assert aggregator._checks_valid({"checks": [{"status": "FAIL"}]}, "checks") is False
    assert aggregator._checks_valid({"checks": [{"status": "PASS"}]}, "checks") is True
    assert (
        aggregator._checks_valid(
            {"checks": [{"status": "PASS"}, {"status": "PASS"}]},
            "checks",
        )
        is True
    )


def test_safety_valid_rejects_every_executable_permission() -> None:
    baseline = {
        "execution_allowed": False,
        "trade_allowed": False,
        "analysis_only": True,
        "used_for_decision": False,
        "forecast_generation_allowed": False,
        "probability_claims_allowed": False,
        "signal_generation_allowed": False,
        "order_routing_allowed": False,
    }
    assert aggregator._safety_valid(baseline) is True
    for field in (
        "execution_allowed",
        "trade_allowed",
        "used_for_decision",
        "forecast_generation_allowed",
        "probability_claims_allowed",
        "signal_generation_allowed",
        "order_routing_allowed",
    ):
        payload = dict(baseline)
        payload[field] = True
        assert aggregator._safety_valid(payload) is False
    not_analysis = dict(baseline)
    not_analysis["analysis_only"] = False
    assert aggregator._safety_valid(not_analysis) is False


def test_missing_and_invalid_contributions_preserve_exact_metadata() -> None:
    config = load_config()
    spec = config["source_specs"]["lot22_market_analysis"]
    missing = aggregator._missing_contribution("lot22_market_analysis", spec, 0.15)
    assert missing.to_dict() == {
        "source_id": "lot22_market_analysis",
        "source_schema_version": None,
        "source_artifact": "data/audit/market_analysis_lot22.json",
        "source_checksum": None,
        "source_state": None,
        "semantic_category": None,
        "source_score": None,
        "configured_weight": 0.15,
        "effective_contribution": 0.0,
        "quality_state": "MISSING",
        "event_time": None,
        "age_seconds": None,
        "included": False,
        "reason_codes": ["GMC_SOURCE_MISSING"],
        "schema_version": "global-context-source-contribution-v1",
    }

    payload = load_sources()["lot22_market_analysis"]
    invalid = aggregator._invalid_contribution(
        "lot22_market_analysis",
        spec,
        0.15,
        payload,
        "GMC_SOURCE_INVALID",
    )
    assert invalid.source_schema_version == payload["analysis_version"]
    assert invalid.source_checksum == aggregator.checksum(payload)
    assert invalid.reason_codes == ("GMC_SOURCE_INVALID",)
    assert invalid.included is False


def test_raw_contribution_exact_values_and_invalid_paths() -> None:
    config = load_config()
    spec = config["source_specs"]["lot22_market_analysis"]
    payload = load_sources()["lot22_market_analysis"]
    item = aggregator._raw_contribution("lot22_market_analysis", spec, 0.15, payload)
    assert item.source_state == "CONTEXT_MIXED"
    assert item.semantic_category == "MIXED"
    assert item.source_score == 0.438757
    assert item.effective_contribution == pytest.approx(0.06581355)
    assert item.event_time == "2026-05-25T03:00:00Z"
    assert item.quality_state == "VALID"
    assert item.included is True

    bad_checks = copy.deepcopy(payload)
    bad_checks["analysis_checks"][0]["status"] = "FAIL"
    assert (
        aggregator._raw_contribution("lot22_market_analysis", spec, 0.15, bad_checks).quality_state
        == "INVALID"
    )

    bad_state = copy.deepcopy(payload)
    bad_state["market_context_state"] = "BUY"
    assert (
        aggregator._raw_contribution("lot22_market_analysis", spec, 0.15, bad_state).quality_state
        == "INVALID"
    )

    no_score = copy.deepcopy(payload)
    no_score["market_context_score"] = None
    assert (
        aggregator._raw_contribution("lot22_market_analysis", spec, 0.15, no_score).quality_state
        == "INVALID"
    )

    bad_score = copy.deepcopy(payload)
    bad_score["market_context_score"] = True
    with pytest.raises(aggregator.GlobalContextValidationError, match="numeric"):
        aggregator._raw_contribution("lot22_market_analysis", spec, 0.15, bad_score)


def test_freshness_exact_boundaries_and_excluded_identity() -> None:
    item = contribution()
    same = aggregator._apply_freshness(item, "2026-05-25T03:00:00Z", 900)
    assert same.included is True
    assert same.age_seconds == 0.0

    boundary = aggregator._apply_freshness(item, "2026-05-25T03:15:00Z", 900)
    assert boundary.included is True
    assert boundary.quality_state == "VALID"
    assert boundary.age_seconds == 900.0

    stale = aggregator._apply_freshness(item, "2026-05-25T03:15:01Z", 900)
    assert stale.included is False
    assert stale.quality_state == "STALE"
    assert stale.age_seconds == 901.0
    assert stale.reason_codes == ("GMC_SOURCE_STALE",)

    future = aggregator._apply_freshness(item, "2026-05-25T02:59:59Z", 900)
    assert future.included is False
    assert future.quality_state == "INVALID"
    assert future.age_seconds is None
    assert future.reason_codes == ("GMC_SOURCE_INVALID",)

    excluded = contribution(included=False, quality="MISSING", event_time=None, age_seconds=None)
    assert aggregator._apply_freshness(excluded, "2026-05-25T03:00:00Z", 900) is excluded


def test_classify_exact_states_reasons_and_ordering() -> None:
    config = load_config()
    unknown = aggregator._classify(
        {"TRENDING": 0.2, "RANGE": 0.1, "MIXED": 0.0, "CONFLICT": 0.0},
        0.5,
        3,
        config,
    )
    assert unknown == ("GLOBAL_CONTEXT_UNKNOWN", (), ("GMC_CONTEXT_UNKNOWN",))

    explicit_conflict = aggregator._classify(
        {"TRENDING": 0.3, "RANGE": 0.2, "MIXED": 0.1, "CONFLICT": 0.1},
        1.0,
        5,
        config,
    )
    assert explicit_conflict == (
        "GLOBAL_CONTEXT_MIXED",
        ("TRENDING", "RANGE", "CONFLICT", "MIXED"),
        ("GMC_EXPLICIT_CONFLICT", "GMC_CONTEXT_MIXED"),
    )

    close_margin = aggregator._classify(
        {"TRENDING": 0.3, "RANGE": 0.26, "MIXED": 0.1, "CONFLICT": 0.0},
        1.0,
        5,
        config,
    )
    assert close_margin[0] == "GLOBAL_CONTEXT_MIXED"
    assert close_margin[2] == (
        "GMC_DOMINANCE_MARGIN_INSUFFICIENT",
        "GMC_CONTEXT_MIXED",
    )

    trending = aggregator._classify(
        {"TRENDING": 0.4, "RANGE": 0.2, "MIXED": 0.1, "CONFLICT": 0.0},
        1.0,
        5,
        config,
    )
    assert trending[0] == "GLOBAL_CONTEXT_TRENDING"
    assert trending[2] == ("GMC_CONTEXT_TRENDING",)

    range_state = aggregator._classify(
        {"TRENDING": 0.1, "RANGE": 0.4, "MIXED": 0.2, "CONFLICT": 0.0},
        1.0,
        5,
        config,
    )
    assert range_state[0] == "GLOBAL_CONTEXT_RANGE"
    assert range_state[2] == ("GMC_CONTEXT_RANGE",)


def test_build_raw_contributions_preserves_order_and_missing_source() -> None:
    sources = load_sources()
    result = aggregator._build_raw_contributions(sources, load_config())
    assert tuple(item.source_id for item in result) == aggregator.SOURCE_IDS
    assert all(item.included for item in result)

    missing_sources = dict(sources)
    missing_sources.pop("lot23_technical_indicators")
    missing_result = aggregator._build_raw_contributions(missing_sources, load_config())
    missing = missing_result[1]
    assert missing.source_id == "lot23_technical_indicators"
    assert missing.quality_state == "MISSING"
    assert missing.configured_weight == 0.15


def test_aggregate_support_and_reasons_have_exact_outputs() -> None:
    items = (
        contribution(category="TRENDING", score=0.8, weight=0.25),
        contribution(
            source_id="lot23_technical_indicators",
            category="RANGE",
            score=0.5,
            weight=0.15,
        ),
        contribution(
            source_id="lot24_trend_range_momentum",
            included=False,
            quality="MISSING",
            weight=0.25,
            reason_codes=("GMC_SOURCE_MISSING",),
        ),
    )
    coverage, support, score = aggregator._aggregate_support(items)
    assert coverage == 0.4
    assert support == {"TRENDING": 0.2, "RANGE": 0.075, "MIXED": 0.0, "CONFLICT": 0.0}
    assert score == 0.275
    reasons = aggregator._build_reasons(items, ("GMC_CONTEXT_TRENDING",))
    assert reasons == (
        "GMC_SOURCE_MISSING",
        "GMC_CONTEXT_TRENDING",
        "GMC_CONFIDENCE_INTERVAL_UNAVAILABLE_UNCALIBRATED",
    )

    all_valid = tuple(contribution(source_id=source_id) for source_id in aggregator.SOURCE_IDS)
    all_valid_reasons = aggregator._build_reasons(all_valid, ("GMC_CONTEXT_MIXED",))
    assert all_valid_reasons[0] == "GMC_ALL_SOURCES_VALID"
    assert len(all_valid_reasons) == 3


def test_aggregate_support_rejects_included_source_without_category() -> None:
    invalid = object.__new__(SourceContributionV1)
    object.__setattr__(invalid, "included", True)
    object.__setattr__(invalid, "configured_weight", 0.1)
    object.__setattr__(invalid, "semantic_category", None)
    object.__setattr__(invalid, "effective_contribution", 0.1)
    with pytest.raises(aggregator.GlobalContextValidationError, match="semantic category"):
        aggregator._aggregate_support((invalid,))


def test_summarize_and_state_checksums_change_with_commit() -> None:
    config = load_config()
    raw = aggregator._build_raw_contributions(load_sources(), config)
    summary = aggregator._summarize(raw, config)
    assert summary.decision_time == "2026-05-25T03:00:00Z"
    assert summary.aggregate_score == 0.5646
    assert summary.coverage == 1.0
    assert summary.dominant_state == "GLOBAL_CONTEXT_MIXED"

    config_checksum = aggregator.checksum(config)
    first = aggregator._build_state(summary, config, config_checksum, COMMIT)
    second = aggregator._build_state(summary, config, config_checksum, "fedcba0987654321")
    assert first.config_checksum == config_checksum
    assert first.code_commit == COMMIT
    assert first.context_id != second.context_id
    assert first.lineage_id != second.lineage_id
    assert first.output_checksum != second.output_checksum
    first_payload = first.to_dict()
    stored = first_payload.pop("output_checksum")
    assert stored == aggregator.checksum(first_payload)


def test_public_builder_validates_config_and_replay_detects_changes() -> None:
    state = aggregator.build_global_market_context(load_sources(), load_config(), COMMIT)
    same = aggregator.build_global_market_context(load_sources(), load_config(), COMMIT)
    assert aggregator.replay_matches(state, same) is True
    changed = replace(same, output_checksum="b" * 64)
    assert aggregator.replay_matches(state, changed) is False

    invalid_config = load_config()
    invalid_config["schema_version"] = "invalid"
    with pytest.raises(aggregator.GlobalContextValidationError, match="unsupported"):
        aggregator.build_global_market_context(load_sources(), invalid_config, COMMIT)


def test_real_source_checksum_matches_independent_json_serialization() -> None:
    source = cloned_sources()["lot22_market_analysis"]
    expected = hashlib.sha256(
        json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert aggregator.checksum(source) == expected
