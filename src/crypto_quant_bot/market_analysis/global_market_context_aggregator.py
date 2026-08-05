from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import timedelta
from hashlib import sha256
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from crypto_quant_bot.contracts.timeframe_alignment import validate_score
from crypto_quant_bot.market_analysis.global_market_context_aggregator_models import (
    SEMANTIC_CATEGORIES,
    SOURCE_IDS,
    GlobalMarketContextAggregatorStateV1,
    SourceContributionV1,
    parse_utc,
)


class GlobalContextValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AggregationSummary:
    decision_time: str
    dominant_state: str
    alternatives: tuple[str, ...]
    category_support: dict[str, float]
    aggregate_score: float | None
    coverage: float
    contributions: tuple[SourceContributionV1, ...]
    reason_codes: tuple[str, ...]


def canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def checksum(payload: object) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def stable_id(prefix: str, payload: object) -> str:
    return str(uuid5(NAMESPACE_URL, f"lot27:{prefix}:{checksum(payload)}"))


def _require_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise GlobalContextValidationError(f"{field_name} must be an object")
    return value


def _validate_weights(config: Mapping[str, Any]) -> None:
    weights = _require_mapping(config.get("source_weights"), "source_weights")
    if set(weights) != set(SOURCE_IDS):
        raise GlobalContextValidationError("source_weights must contain exactly five sources")
    numeric_weights = [float(weights[source_id]) for source_id in SOURCE_IDS]
    positive = all(weight > 0 for weight in numeric_weights)
    normalized = abs(sum(numeric_weights) - 1.0) <= 1e-9
    if not positive or not normalized:
        raise GlobalContextValidationError("source weights must be positive and sum to one")


def _validate_specs(config: Mapping[str, Any]) -> None:
    specs = _require_mapping(config.get("source_specs"), "source_specs")
    if set(specs) != set(SOURCE_IDS):
        raise GlobalContextValidationError("source_specs must contain exactly five sources")
    for source_id in SOURCE_IDS:
        spec = _require_mapping(specs[source_id], f"source_specs.{source_id}")
        mapping = _require_mapping(spec.get("semantic_mapping"), "semantic_mapping")
        valid_categories = mapping and all(value in SEMANTIC_CATEGORIES for value in mapping.values())
        if not valid_categories:
            raise GlobalContextValidationError(f"invalid semantic mapping for {source_id}")


def _validate_restrictions(config: Mapping[str, Any]) -> None:
    restrictions = _require_mapping(config.get("promotion_restrictions"), "promotion_restrictions")
    if not restrictions or any(value is not False for value in restrictions.values()):
        raise GlobalContextValidationError("all Lot 27 promotion permissions must be false")


def _validate_thresholds(config: Mapping[str, Any]) -> None:
    thresholds = _require_mapping(config.get("thresholds"), "thresholds")
    minimum_count = int(thresholds.get("minimum_available_source_count", 0))
    if not 1 <= minimum_count <= len(SOURCE_IDS):
        raise GlobalContextValidationError("invalid minimum source count")
    for key in (
        "minimum_weighted_coverage_ratio",
        "dominance_margin_minimum",
        "explicit_conflict_mixed_minimum",
    ):
        validate_score(float(thresholds.get(key, -1)), f"thresholds.{key}")


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != "global-market-context-aggregator-config-v1":
        raise GlobalContextValidationError("unsupported Lot 27 config schema")
    _validate_weights(config)
    _validate_specs(config)
    _validate_restrictions(config)
    _validate_thresholds(config)


def _source_event_time(payload: Mapping[str, Any], source_id: str) -> str:
    if source_id == "lot26_multi_timeframe_alignment":
        value = payload.get("decision_time")
        if not isinstance(value, str):
            raise GlobalContextValidationError("Lot 26 decision_time missing")
        parse_utc(value, "decision_time")
        return value
    summaries = payload.get("timeframe_summaries")
    if not isinstance(summaries, list) or not summaries:
        raise GlobalContextValidationError(f"{source_id} timeframe summaries missing")
    closes = []
    for item in summaries:
        summary = _require_mapping(item, "timeframe_summary")
        timeframe = str(summary.get("timeframe", ""))
        seconds = {"5m": 300, "15m": 900}.get(timeframe)
        if seconds is None:
            raise GlobalContextValidationError("unsupported timeframe in source summary")
        opened = parse_utc(str(summary.get("last_timestamp", "")), "last_timestamp")
        closes.append(opened + timedelta(seconds=seconds))
    return max(closes).isoformat().replace("+00:00", "Z")


def _checks_valid(payload: Mapping[str, Any], checks_field: object) -> bool:
    if checks_field is None:
        return True
    checks = payload.get(str(checks_field))
    return isinstance(checks, list) and bool(checks) and all(
        isinstance(item, Mapping) and item.get("status") == "PASS" for item in checks
    )


def _safety_valid(payload: Mapping[str, Any]) -> bool:
    if payload.get("execution_allowed") is not False:
        return False
    if "trade_allowed" in payload and payload.get("trade_allowed") is not False:
        return False
    if "analysis_only" in payload and payload.get("analysis_only") is not True:
        return False
    forbidden_true = (
        "used_for_decision",
        "forecast_generation_allowed",
        "probability_claims_allowed",
        "signal_generation_allowed",
        "order_routing_allowed",
    )
    return all(payload.get(field) is not True for field in forbidden_true)


def _missing_contribution(source_id: str, spec: Mapping[str, Any], weight: float) -> SourceContributionV1:
    return SourceContributionV1(
        source_id=source_id,
        source_schema_version=None,
        source_artifact=str(spec["artifact"]),
        source_checksum=None,
        source_state=None,
        semantic_category=None,
        source_score=None,
        configured_weight=weight,
        effective_contribution=0.0,
        quality_state="MISSING",
        event_time=None,
        age_seconds=None,
        included=False,
        reason_codes=("GMC_SOURCE_MISSING",),
    )


def _invalid_contribution(
    source_id: str,
    spec: Mapping[str, Any],
    weight: float,
    payload: Mapping[str, Any],
    reason: str,
) -> SourceContributionV1:
    return SourceContributionV1(
        source_id=source_id,
        source_schema_version=str(payload.get(str(spec["version_field"]), "UNKNOWN")),
        source_artifact=str(spec["artifact"]),
        source_checksum=checksum(payload),
        source_state=None,
        semantic_category=None,
        source_score=None,
        configured_weight=weight,
        effective_contribution=0.0,
        quality_state="INVALID",
        event_time=None,
        age_seconds=None,
        included=False,
        reason_codes=(reason,),
    )


def _raw_contribution(
    source_id: str,
    spec: Mapping[str, Any],
    weight: float,
    payload: Mapping[str, Any],
) -> SourceContributionV1:
    if not _checks_valid(payload, spec.get("checks_field")) or not _safety_valid(payload):
        return _invalid_contribution(source_id, spec, weight, payload, "GMC_SOURCE_INVALID")
    state = payload.get(str(spec["state_field"]))
    score = payload.get(str(spec["score_field"]))
    mapping = _require_mapping(spec.get("semantic_mapping"), "semantic_mapping")
    if not isinstance(state, str) or state not in mapping:
        return _invalid_contribution(source_id, spec, weight, payload, "GMC_SOURCE_INVALID")
    try:
        validate_score(score, f"{source_id}.score")
        event_time = _source_event_time(payload, source_id)
    except (ValueError, TypeError) as exc:
        raise GlobalContextValidationError(str(exc)) from exc
    if score is None:
        return _invalid_contribution(source_id, spec, weight, payload, "GMC_SOURCE_INVALID")
    numeric_score = float(score)
    return SourceContributionV1(
        source_id=source_id,
        source_schema_version=str(payload.get(str(spec["version_field"]), "UNKNOWN")),
        source_artifact=str(spec["artifact"]),
        source_checksum=checksum(payload),
        source_state=state,
        semantic_category=str(mapping[state]),
        source_score=numeric_score,
        configured_weight=weight,
        effective_contribution=weight * numeric_score,
        quality_state="VALID",
        event_time=event_time,
        age_seconds=0.0,
        included=True,
        reason_codes=(),
    )


def _apply_freshness(
    contribution: SourceContributionV1,
    decision_time: str,
    maximum_staleness_seconds: int,
) -> SourceContributionV1:
    if not contribution.included or contribution.event_time is None:
        return contribution
    age = (parse_utc(decision_time, "decision_time") - parse_utc(contribution.event_time, "event_time")).total_seconds()
    if age < 0:
        return replace(
            contribution,
            effective_contribution=0.0,
            quality_state="INVALID",
            age_seconds=None,
            included=False,
            reason_codes=("GMC_SOURCE_INVALID",),
        )
    if age > maximum_staleness_seconds:
        return replace(
            contribution,
            effective_contribution=0.0,
            quality_state="STALE",
            age_seconds=age,
            included=False,
            reason_codes=("GMC_SOURCE_STALE",),
        )
    return replace(contribution, age_seconds=age)


def _classify(
    category_support: Mapping[str, float],
    coverage: float,
    count: int,
    config: Mapping[str, Any],
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    thresholds = _require_mapping(config["thresholds"], "thresholds")
    minimum_count = int(thresholds["minimum_available_source_count"])
    minimum_coverage = float(thresholds["minimum_weighted_coverage_ratio"])
    if count < minimum_count or coverage < minimum_coverage:
        return "GLOBAL_CONTEXT_UNKNOWN", (), ("GMC_CONTEXT_UNKNOWN",)
    ranked = sorted(category_support, key=lambda item: (-category_support[item], item))
    alternatives = tuple(category for category in ranked if category_support[category] > 0)
    if category_support["CONFLICT"] >= float(thresholds["explicit_conflict_mixed_minimum"]):
        reasons = ("GMC_EXPLICIT_CONFLICT", "GMC_CONTEXT_MIXED")
        return "GLOBAL_CONTEXT_MIXED", alternatives, reasons
    margin = category_support[ranked[0]] - category_support[ranked[1]]
    if margin < float(thresholds["dominance_margin_minimum"]):
        reasons = ("GMC_DOMINANCE_MARGIN_INSUFFICIENT", "GMC_CONTEXT_MIXED")
        return "GLOBAL_CONTEXT_MIXED", alternatives, reasons
    state = {
        "TRENDING": "GLOBAL_CONTEXT_TRENDING",
        "RANGE": "GLOBAL_CONTEXT_RANGE",
        "MIXED": "GLOBAL_CONTEXT_MIXED",
        "CONFLICT": "GLOBAL_CONTEXT_MIXED",
    }[ranked[0]]
    reason = {
        "GLOBAL_CONTEXT_TRENDING": "GMC_CONTEXT_TRENDING",
        "GLOBAL_CONTEXT_RANGE": "GMC_CONTEXT_RANGE",
        "GLOBAL_CONTEXT_MIXED": "GMC_CONTEXT_MIXED",
    }[state]
    return state, alternatives, (reason,)


def _build_raw_contributions(
    sources: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
) -> tuple[SourceContributionV1, ...]:
    specs = _require_mapping(config["source_specs"], "source_specs")
    weights = _require_mapping(config["source_weights"], "source_weights")
    result = []
    for source_id in SOURCE_IDS:
        spec = _require_mapping(specs[source_id], f"source_specs.{source_id}")
        payload = sources.get(source_id)
        weight = float(weights[source_id])
        result.append(
            _missing_contribution(source_id, spec, weight)
            if payload is None
            else _raw_contribution(source_id, spec, weight, payload)
        )
    return tuple(result)


def _aggregate_support(
    contributions: tuple[SourceContributionV1, ...],
) -> tuple[float, dict[str, float], float]:
    included = tuple(item for item in contributions if item.included)
    coverage = round(sum(item.configured_weight for item in included), 6)
    support = dict.fromkeys(SEMANTIC_CATEGORIES, 0.0)
    for item in included:
        assert item.semantic_category is not None
        support[item.semantic_category] += item.effective_contribution
    rounded = {key: round(value, 6) for key, value in support.items()}
    score = round(sum(item.effective_contribution for item in included), 6)
    return coverage, rounded, score


def _build_reasons(
    contributions: tuple[SourceContributionV1, ...],
    classification_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    included = tuple(item for item in contributions if item.included)
    reasons = ["GMC_ALL_SOURCES_VALID"] if len(included) == len(SOURCE_IDS) else []
    if len(included) != len(SOURCE_IDS):
        reasons.extend(sorted({code for item in contributions for code in item.reason_codes}))
    reasons.extend(classification_reasons)
    reasons.append("GMC_CONFIDENCE_INTERVAL_UNAVAILABLE_UNCALIBRATED")
    return tuple(dict.fromkeys(reasons))


def _summarize(
    raw: tuple[SourceContributionV1, ...],
    config: Mapping[str, Any],
) -> AggregationSummary:
    event_times = [item.event_time for item in raw if item.event_time is not None]
    if not event_times:
        raise GlobalContextValidationError("no source provides a legal decision time")
    decision_time = max(event_times, key=lambda value: parse_utc(value, "event_time"))
    thresholds = _require_mapping(config["thresholds"], "thresholds")
    maximum_age = int(thresholds["maximum_staleness_seconds"])
    contributions = tuple(_apply_freshness(item, decision_time, maximum_age) for item in raw)
    coverage, support, score = _aggregate_support(contributions)
    included_count = sum(item.included for item in contributions)
    dominant, alternatives, classification_reasons = _classify(
        support,
        coverage,
        included_count,
        config,
    )
    minimum_coverage = float(thresholds["minimum_weighted_coverage_ratio"])
    aggregate_score = score if coverage >= minimum_coverage else None
    return AggregationSummary(
        decision_time=decision_time,
        dominant_state=dominant,
        alternatives=alternatives,
        category_support=support,
        aggregate_score=aggregate_score,
        coverage=coverage,
        contributions=contributions,
        reason_codes=_build_reasons(contributions, classification_reasons),
    )


def _build_state(
    summary: AggregationSummary,
    config: Mapping[str, Any],
    config_checksum: str,
    code_commit: str,
) -> GlobalMarketContextAggregatorStateV1:
    included = tuple(item for item in summary.contributions if item.included)
    conflicts = tuple(
        item.source_state
        for item in included
        if item.semantic_category == "CONFLICT" and item.source_state is not None
    )
    identity = {
        "decision_time": summary.decision_time,
        "contributions": [item.to_dict() for item in summary.contributions],
        "config_checksum": config_checksum,
        "code_commit": code_commit,
    }
    provisional = GlobalMarketContextAggregatorStateV1(
        context_id=stable_id("context", identity),
        instrument_id=str(config["instrument_id"]),
        decision_time=summary.decision_time,
        dominant_state=summary.dominant_state,
        alternative_states=summary.alternatives,
        category_support=summary.category_support,
        aggregate_evidence_score=summary.aggregate_score,
        weighted_coverage_ratio=summary.coverage,
        available_source_count=len(included),
        missing_source_weight=round(1.0 - summary.coverage, 6),
        conflict_states=conflicts,
        confidence_interval=None,
        contributions=summary.contributions,
        lineage_id=stable_id("lineage", identity),
        config_version=str(config["config_id"]),
        config_checksum=config_checksum,
        code_commit=code_commit,
        output_checksum="pending",
        reason_codes=summary.reason_codes,
        validation_state="UNKNOWN" if summary.dominant_state == "GLOBAL_CONTEXT_UNKNOWN" else "VALID",
    )
    payload = provisional.to_dict()
    payload.pop("output_checksum")
    return replace(provisional, output_checksum=checksum(payload))


def build_global_market_context(
    sources: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
    code_commit: str,
) -> GlobalMarketContextAggregatorStateV1:
    validate_config(config)
    raw = _build_raw_contributions(sources, config)
    summary = _summarize(raw, config)
    return _build_state(summary, config, checksum(config), code_commit)


def replay_matches(
    first: GlobalMarketContextAggregatorStateV1,
    second: GlobalMarketContextAggregatorStateV1,
) -> bool:
    return first.to_dict() == second.to_dict() and first.output_checksum == second.output_checksum
