from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final

PARAMETER_SET_VERSION: Final[str] = "market-analysis-thresholds-v1"
PARAMETER_STATUS: Final[str] = "PROVISIONAL_UNCALIBRATED_OFFLINE_ONLY"

INDICATOR_PARAMETERS: Final[Mapping[str, float | int]] = MappingProxyType(
    {
        "short_period": 3,
        "medium_period": 5,
        "long_period": 6,
        "signal_period": 3,
        "bollinger_stddev_multiplier": 2.0,
    }
)

TREND_PARAMETERS: Final[Mapping[str, float | int]] = MappingProxyType(
    {
        "minimum_rows": 6,
        "direction_threshold_percent": 0.15,
        "flat_slope_threshold_percent": 0.05,
        "close_change_threshold_percent": 0.25,
        "minimum_context_score": 0.35,
        "neutral_context_score": 0.20,
        "trend_combined_score": 0.40,
        "volatile_combined_score": 0.50,
        "range_compressed_width_percent": 1.40,
        "range_compressed_bollinger_percent": 1.50,
        "range_break_edge_high_percent": 85.0,
        "range_break_edge_low_percent": 15.0,
        "range_break_width_percent": 1.20,
        "range_expanded_width_percent": 1.80,
        "range_expanded_bollinger_percent": 2.40,
        "range_expanded_atr_percent": 0.80,
        "range_neutral_low_percent": 30.0,
        "range_neutral_high_percent": 70.0,
        "range_neutral_width_percent": 2.0,
        "momentum_rate_threshold_percent": 0.18,
        "momentum_rsi_divergence_level": 70.0,
        "trend_slope_normalizer": 0.60,
        "trend_extension_normalizer": 0.80,
        "trend_drift_normalizer": 1.20,
        "range_width_reference": 1.40,
        "range_width_expansion_span": 1.60,
        "range_edge_normalizer": 40.0,
        "range_bollinger_normalizer": 2.60,
        "range_atr_normalizer": 0.90,
        "momentum_normalizer": 0.40,
        "rsi_normalizer": 25.0,
        "macd_normalizer": 50.0,
    }
)

VRC_PARAMETERS: Final[Mapping[str, float | int]] = MappingProxyType(
    {
        "minimum_rows": 6,
        "compression_threshold": 0.68,
        "expansion_threshold": 0.70,
        "high_or_low_threshold": 0.58,
        "moderate_threshold": 0.38,
        "mixed_delta": 0.08,
        "mixed_minimum": 0.35,
        "atr_expansion_normalizer": 0.90,
        "true_range_normalizer": 0.55,
        "bollinger_expansion_normalizer": 2.50,
        "range_expansion_normalizer": 2.10,
        "volatility_percentile_multiplier": 1.35,
        "realized_volatility_normalizer": 0.01,
        "compression_bollinger_reference": 1.90,
        "compression_range_reference": 1.90,
        "regime_source_range_weight": 0.22,
        "regime_source_compressed_weight": 0.24,
        "regime_trend_weight": 0.26,
        "regime_range_weight": 0.20,
        "regime_volatility_weight": 0.14,
        "market_context_weight": 0.18,
    }
)


def parameter_manifest() -> dict[str, object]:
    return {
        "parameter_set_version": PARAMETER_SET_VERSION,
        "status": PARAMETER_STATUS,
        "runtime_scope": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "indicator_parameters": dict(INDICATOR_PARAMETERS),
        "trend_parameters": dict(TREND_PARAMETERS),
        "vrc_parameters": dict(VRC_PARAMETERS),
        "promotion_restrictions": {
            "probability_claims_allowed": False,
            "alpha_claims_allowed": False,
            "paper_promotion_allowed": False,
            "live_use_allowed": False,
        },
    }


def parameter_manifest_checksum() -> str:
    payload = json.dumps(
        parameter_manifest(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_parameter_manifest(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = parameter_manifest()
    if payload != expected:
        raise ValueError("versioned mathematical parameter manifest mismatch")
