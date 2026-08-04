from __future__ import annotations

from pathlib import Path

from crypto_quant_bot.market_analysis.math_parameters import (
    INDICATOR_PARAMETERS,
    PARAMETER_SET_VERSION,
    PARAMETER_STATUS,
    TREND_PARAMETERS,
    VRC_PARAMETERS,
    parameter_manifest_checksum,
    validate_parameter_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def test_parameter_manifest_is_versioned_and_matches_code() -> None:
    assert PARAMETER_SET_VERSION == "market-analysis-thresholds-v1"
    assert PARAMETER_STATUS == "PROVISIONAL_UNCALIBRATED_OFFLINE_ONLY"
    validate_parameter_manifest(ROOT / "config/math/market_analysis_thresholds_v1.json")
    assert len(parameter_manifest_checksum()) == 64


def test_parameter_domains_are_defensive() -> None:
    assert int(INDICATOR_PARAMETERS["short_period"]) > 0
    assert int(INDICATOR_PARAMETERS["medium_period"]) > int(INDICATOR_PARAMETERS["short_period"])
    assert int(INDICATOR_PARAMETERS["long_period"]) > int(INDICATOR_PARAMETERS["medium_period"])
    assert 0.0 < float(TREND_PARAMETERS["minimum_context_score"]) < 1.0
    assert 0.0 < float(VRC_PARAMETERS["compression_threshold"]) < 1.0
    assert 0.0 < float(VRC_PARAMETERS["expansion_threshold"]) < 1.0
