from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from crypto_quant_bot.contracts.timeframe_alignment import COMPONENTS
from crypto_quant_bot.market_analysis.alignment_common import (
    Lot26ValidationError,
    checksum,
    require_mapping,
)


def _validate_weights(config: Mapping[str, Any]) -> None:
    weights = config.get("component_weights")
    if not isinstance(weights, Mapping) or set(weights) != set(COMPONENTS):
        raise Lot26ValidationError("component_weights must contain exactly six components")
    values = [float(value) for value in weights.values()]
    if any(not math.isfinite(value) or value <= 0.0 for value in values):
        raise Lot26ValidationError("component weights must be finite and positive")
    if not math.isclose(sum(values), 1.0, abs_tol=1e-9, rel_tol=1e-9):
        raise Lot26ValidationError("component weights must sum to one")


def _validate_thresholds(config: Mapping[str, Any]) -> None:
    thresholds = require_mapping(config, "classification_thresholds")
    partial = float(thresholds.get("partial_minimum", -1.0))
    aligned = float(thresholds.get("aligned_minimum", -1.0))
    mismatch = float(thresholds.get("hard_mismatch_maximum", -1.0))
    mismatch_count = thresholds.get("multi_mismatch_count")
    if not 0.0 <= mismatch < partial < aligned <= 1.0:
        raise Lot26ValidationError("classification thresholds are invalid")
    if not isinstance(mismatch_count, int) or mismatch_count < 1:
        raise Lot26ValidationError("multi_mismatch_count is invalid")


def _validate_coverage(config: Mapping[str, Any]) -> None:
    minimum_count = config.get("minimum_available_component_count")
    if not isinstance(minimum_count, int) or not 1 <= minimum_count <= len(COMPONENTS):
        raise Lot26ValidationError("minimum_available_component_count is invalid")
    minimum_coverage = float(config.get("minimum_weighted_coverage_ratio", -1.0))
    if not 0.0 <= minimum_coverage <= 1.0:
        raise Lot26ValidationError("minimum_weighted_coverage_ratio is invalid")


def _validate_time_policy(config: Mapping[str, Any]) -> None:
    policy = require_mapping(config, "time_policy")
    if policy.get("join_method") != "ASOF_BACKWARD":
        raise Lot26ValidationError("join_method must be ASOF_BACKWARD")
    if policy.get("eligibility_rule") != "available_at <= decision_time":
        raise Lot26ValidationError("eligibility_rule is invalid")
    for key in ("local_max_staleness_seconds", "higher_max_staleness_seconds"):
        value = policy.get(key)
        if not isinstance(value, int) or value < 0:
            raise Lot26ValidationError(f"{key} is invalid")


def _validate_matrix(name: str, matrix: Mapping[str, Any]) -> None:
    if not matrix:
        raise Lot26ValidationError(f"{name} compatibility matrix is missing")
    states = set(matrix)
    for source, raw_row in matrix.items():
        if not isinstance(raw_row, Mapping) or set(raw_row) != states:
            raise Lot26ValidationError(f"{name} matrix is incomplete at {source}")
        for target, raw_score in raw_row.items():
            reverse_row = matrix.get(target)
            reverse = reverse_row.get(source) if isinstance(reverse_row, Mapping) else None
            score = float(raw_score)
            if reverse is None or not 0.0 <= score <= 1.0:
                raise Lot26ValidationError(f"{name} matrix has an invalid score")
            if not math.isclose(score, float(reverse), abs_tol=1e-9, rel_tol=1e-9):
                raise Lot26ValidationError(f"{name} matrix must be symmetric")


def validate_alignment_config(config: Mapping[str, Any]) -> None:
    _validate_weights(config)
    _validate_thresholds(config)
    _validate_coverage(config)
    _validate_time_policy(config)
    restrictions = require_mapping(config, "promotion_restrictions")
    if any(value is not False for value in restrictions.values()):
        raise Lot26ValidationError("all promotion restrictions must remain false")
    matrices = require_mapping(config, "categorical_compatibility")
    for name in ("range", "regime"):
        matrix = matrices.get(name)
        if not isinstance(matrix, Mapping):
            raise Lot26ValidationError(f"{name} compatibility matrix is missing")
        _validate_matrix(name, matrix)


def validate_scale_registry(registry: Mapping[str, Any]) -> tuple[str, str]:
    profile = require_mapping(registry, "lot26_initial_profile")
    local = str(profile.get("local_scale_id", ""))
    higher = str(profile.get("higher_scale_id", ""))
    if (local, higher) != ("timebar-5m", "timebar-15m"):
        raise Lot26ValidationError("MTF_SCALE_RELATION_NOT_ALLOWED")
    if profile.get("join_method") != "ASOF_BACKWARD":
        raise Lot26ValidationError("MTF_SCALE_RELATION_NOT_ALLOWED")
    scales = registry.get("scales")
    if not isinstance(scales, list):
        raise Lot26ValidationError("temporal registry scales must be a list")
    enabled = {
        item.get("scale_id"): item
        for item in scales
        if isinstance(item, Mapping) and item.get("enabled_in_lot26") is True
    }
    if set(enabled) != {local, higher}:
        raise Lot26ValidationError("MTF_SCALE_RELATION_NOT_ALLOWED")
    if enabled[local].get("lot26_role") != "LOCAL_CONTEXT":
        raise Lot26ValidationError("MTF_SCALE_RELATION_NOT_ALLOWED")
    if enabled[higher].get("lot26_role") != "HIGHER_CONTEXT":
        raise Lot26ValidationError("MTF_SCALE_RELATION_NOT_ALLOWED")
    return local, higher


def validate_decision_clock(policy: Mapping[str, Any]) -> str:
    lot26_policy = require_mapping(policy, "lot26_policy")
    if lot26_policy.get("enabled_triggers") != ["CLOSED_LOCAL_BAR"]:
        raise Lot26ValidationError("Lot 26 must enable only CLOSED_LOCAL_BAR")
    if lot26_policy.get("trade_decision_allowed") is not False:
        raise Lot26ValidationError("trade decision must remain disabled")
    return "CLOSED_LOCAL_BAR"


def config_checksum(config: Mapping[str, Any]) -> str:
    validate_alignment_config(config)
    return checksum(config)
