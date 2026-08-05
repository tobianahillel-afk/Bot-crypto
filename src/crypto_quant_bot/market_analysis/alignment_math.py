from __future__ import annotations

import math
from typing import Any, Mapping

from crypto_quant_bot.contracts.timeframe_alignment import COMPONENTS
from crypto_quant_bot.market_analysis.alignment_common import Lot26ValidationError
from crypto_quant_bot.market_analysis.alignment_config import validate_alignment_config

ORDINAL_RANGES = {"trend": 2.0, "momentum": 2.0, "volatility": 1.0, "confluence": 1.0}


def _known_state(value: str, config: Mapping[str, Any]) -> bool:
    tokens = config.get("unknown_state_tokens", [])
    if not isinstance(tokens, list):
        raise Lot26ValidationError("unknown_state_tokens must be a list")
    upper_value = value.upper()
    return bool(value) and not any(str(token) in upper_value for token in tokens)


def _ordinal_score(
    component: str,
    local_state: str,
    higher_state: str,
    config: Mapping[str, Any],
) -> float | None:
    encodings = config.get("ordinal_encodings")
    component_encoding = encodings.get(component) if isinstance(encodings, Mapping) else None
    if not isinstance(component_encoding, Mapping):
        raise Lot26ValidationError(f"ordinal encoding is missing for {component}")
    if local_state not in component_encoding or higher_state not in component_encoding:
        return None
    local_value = float(component_encoding[local_state])
    higher_value = float(component_encoding[higher_state])
    return 1.0 - abs(local_value - higher_value) / ORDINAL_RANGES[component]


def _categorical_score(
    component: str,
    local_state: str,
    higher_state: str,
    config: Mapping[str, Any],
) -> float | None:
    matrices = config.get("categorical_compatibility")
    matrix = matrices.get(component) if isinstance(matrices, Mapping) else None
    row = matrix.get(local_state) if isinstance(matrix, Mapping) else None
    if not isinstance(row, Mapping) or higher_state not in row:
        return None
    return float(row[higher_state])


def component_compatibility(
    component: str,
    local_state: str,
    higher_state: str,
    config: Mapping[str, Any],
) -> float | None:
    if component not in COMPONENTS:
        raise Lot26ValidationError(f"unknown component: {component}")
    if not _known_state(local_state, config) or not _known_state(higher_state, config):
        return None
    if component in ORDINAL_RANGES:
        score = _ordinal_score(component, local_state, higher_state, config)
    else:
        score = _categorical_score(component, local_state, higher_state, config)
    if score is None:
        return None
    if not math.isfinite(score):
        raise Lot26ValidationError(f"non-finite compatibility for {component}")
    return max(0.0, min(1.0, score))


def compute_weighted_agreement(
    scores: Mapping[str, float | None],
    config: Mapping[str, Any],
) -> tuple[int, float, float | None]:
    validate_alignment_config(config)
    if set(scores) != set(COMPONENTS):
        raise Lot26ValidationError("scores must contain exactly six components")
    weights = {key: float(value) for key, value in config["component_weights"].items()}
    available = {key: value for key, value in scores.items() if value is not None}
    for key, value in available.items():
        numeric = float(value)
        if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
            raise Lot26ValidationError(f"invalid component score: {key}")
    count = len(available)
    coverage = sum(weights[key] for key in available)
    minimum_count = int(config["minimum_available_component_count"])
    minimum_coverage = float(config["minimum_weighted_coverage_ratio"])
    rounded_coverage = round(coverage, 6)
    if count < minimum_count or coverage < minimum_coverage or coverage == 0.0:
        return count, rounded_coverage, None
    numerator = sum(weights[key] * float(value) for key, value in available.items())
    decimals = int(config["numeric_policy"]["round_decimal_places"])
    return count, rounded_coverage, round(numerator / coverage, decimals)


def _alignment_class(score: float, hard_count: int, config: Mapping[str, Any]) -> str:
    thresholds = config["classification_thresholds"]
    multi_count = int(thresholds["multi_mismatch_count"])
    if score >= float(thresholds["aligned_minimum"]) and hard_count < multi_count:
        return "MTF_ALIGNED"
    if score >= float(thresholds["partial_minimum"]) and hard_count < multi_count:
        return "MTF_PARTIAL"
    return "MTF_DIVERGENT"


def _divergence_class(hard: tuple[str, ...], config: Mapping[str, Any]) -> str:
    multi_count = int(config["classification_thresholds"]["multi_mismatch_count"])
    if len(hard) >= multi_count:
        return "MTF_MULTI_COMPONENT_MISMATCH"
    if any(component in hard for component in ("trend", "momentum")):
        return "MTF_DIRECTIONAL_MISMATCH"
    if "regime" in hard:
        return "MTF_REGIME_MISMATCH"
    if "volatility" in hard:
        return "MTF_VOLATILITY_MISMATCH"
    return "MTF_NO_HARD_DIVERGENCE"


def _classification_reasons(alignment: str, divergence: str) -> tuple[str, ...]:
    primary = {
        "MTF_ALIGNED": "MTF_ALIGNED",
        "MTF_PARTIAL": "MTF_PARTIAL_ALIGNMENT",
        "MTF_DIVERGENT": "MTF_DIVERGENT",
    }[alignment]
    if divergence == "MTF_NO_HARD_DIVERGENCE":
        return (primary,)
    return (primary, divergence)


def classify_alignment(
    score: float | None,
    scores: Mapping[str, float | None],
    config: Mapping[str, Any],
) -> tuple[str, str, str, str, tuple[str, ...], tuple[str, ...]]:
    hard_maximum = float(config["classification_thresholds"]["hard_mismatch_maximum"])
    hard = tuple(sorted(key for key, value in scores.items() if value is not None and value <= hard_maximum))
    if score is None:
        reasons = ("MTF_UNKNOWN", "MTF_INSUFFICIENT_COMPONENT_COVERAGE")
        return "MTF_UNKNOWN", "MTF_UNKNOWN", "MTF_UNKNOWN", "MTF_CONTEXT_UNKNOWN", hard, reasons
    alignment = _alignment_class(score, len(hard), config)
    divergence = _divergence_class(hard, config)
    directional = any(component in hard for component in ("trend", "momentum"))
    coherence = "MTF_INCOHERENT" if alignment == "MTF_DIVERGENT" else "MTF_COHERENT"
    if alignment == "MTF_PARTIAL" or (directional and alignment != "MTF_DIVERGENT"):
        coherence = "MTF_MIXED"
    context = alignment.replace("MTF_", "MTF_CONTEXT_")
    reasons = _classification_reasons(alignment, divergence)
    return alignment, divergence, coherence, context, hard, reasons


def uncertainty_from_coverage(coverage: float, available_count: int) -> str:
    if coverage >= 1.0 and available_count == len(COMPONENTS):
        return "LOW"
    if coverage >= 0.85:
        return "MODERATE"
    if coverage >= 0.70:
        return "HIGH"
    return "UNKNOWN"
