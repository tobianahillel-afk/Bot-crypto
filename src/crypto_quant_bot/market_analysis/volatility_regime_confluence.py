from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from statistics import mean
from typing import Any

from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.market_analysis.confluence_models import (
    DEFAULT_VRC_BLOCK_REASONS,
    VolatilityRegimeConfluenceCheck,
    VolatilityRegimeConfluencePolicy,
    VolatilityRegimeConfluenceResult,
    VolatilityRegimeConfluenceTimeframeSummary,
)
from crypto_quant_bot.market_analysis.foundation import (
    ARCHIVE_OUTPUT_PATH,
    ARCHIVE_SHA256_OUTPUT_PATH,
    INPUT_SPECS,
    LOT20_OUTPUT_PATH,
    LOT21_FREEZE_REPORT_PATH,
    LOT21_OUTPUT_PATH,
    LOT22_OUTPUT_PATH,
    LOT22_TIMEFRAMES_OUTPUT_PATH,
)
from crypto_quant_bot.market_analysis.io import load_json, load_jsonl, read_text_limited
from crypto_quant_bot.market_analysis.math_parameters import VRC_PARAMETERS
from crypto_quant_bot.market_analysis.numeric import require_finite_float
from crypto_quant_bot.market_analysis.technical_indicators import (
    LOT23_OUTPUT_PATH,
    LOT23_TIMEFRAMES_OUTPUT_PATH,
)
from crypto_quant_bot.market_analysis.trend_range_momentum import (
    LOT24_OUTPUT_PATH,
    LOT24_TIMEFRAMES_OUTPUT_PATH,
    TREND_INVARIANTS,
)

LOT25_OUTPUT_PATH = "data/audit/volatility_regime_confluence_lot25.json"
LOT25_TIMEFRAMES_OUTPUT_PATH = "data/audit/volatility_regime_confluence_timeframes_lot25.jsonl"
LOT25_REPORT_OUTPUT_PATH = "reports/lot_25_volatility_regime_confluence_report.md"
LOT25_VALIDATION_REPORT_PATH = "reports/lot_25_validation_report.md"
LOT25_OVERVIEW_DOC_PATH = "docs/LOT_25_VOLATILITY_REGIME_CONFLUENCE.md"
LOT25_ACCEPTANCE_DOC_PATH = "docs/ACCEPTANCE_CRITERIA_LOT_25.md"

VRC_INVARIANTS = dict(TREND_INVARIANTS)
VRC_INVARIANTS["trend_engine_mode"] = "LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY"
VRC_INVARIANTS["vrc_engine_mode"] = "LOCAL_OFFLINE_VOLATILITY_REGIME_CONFLUENCE_ONLY"


def default_vrc_source_artifacts() -> list[str]:
    return sorted(
        {
            LOT20_OUTPUT_PATH,
            LOT21_OUTPUT_PATH,
            LOT21_FREEZE_REPORT_PATH,
            LOT22_OUTPUT_PATH,
            LOT22_TIMEFRAMES_OUTPUT_PATH,
            LOT23_OUTPUT_PATH,
            LOT23_TIMEFRAMES_OUTPUT_PATH,
            LOT24_OUTPUT_PATH,
            LOT24_TIMEFRAMES_OUTPUT_PATH,
            ARCHIVE_OUTPUT_PATH,
            ARCHIVE_SHA256_OUTPUT_PATH,
            "scripts/validate_v1_archive_frozen.py",
            *[path for spec in INPUT_SPECS.values() for path in spec.values()],
        }
    )


def build_vrc_checksum(payload: dict[str, object]) -> str:
    normalized = json.loads(json.dumps(payload))

    def strip_runtime_fields(obj: object) -> object:
        if isinstance(obj, dict):
            next_obj: dict[str, object] = {}
            for key, value in obj.items():
                if key in {"created_at", "vrc_checksum"}:
                    continue
                next_obj[key] = strip_runtime_fields(value)
            return next_obj
        if isinstance(obj, list):
            return [strip_runtime_fields(item) for item in obj]
        return obj

    cleaned = strip_runtime_fields(normalized)
    if not isinstance(cleaned, dict):
        raise ValueError("vrc checksum payload must remain a mapping")
    encoded = json.dumps(cleaned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_object(root: Path, relative_path: str) -> dict[str, Any]:
    payload = load_json(root / relative_path)
    if not isinstance(payload, dict):
        raise ValueError(f"{relative_path} must contain a JSON object")
    return payload


def _require_expected_pairs(payload: dict[str, Any], expected_pairs: dict[str, Any], *, name: str) -> None:
    for key, value in expected_pairs.items():
        if payload.get(key) != value:
            raise ValueError(f"{name} invalid {key}: {payload.get(key)}")


def _validate_frozen_archive(root: Path, *, product_scope: dict[str, Any], closure_snapshot: dict[str, Any]) -> tuple[str, int]:
    archive_path = root / ARCHIVE_OUTPUT_PATH
    archive_sha_path = root / ARCHIVE_SHA256_OUTPUT_PATH
    freeze_report_path = root / LOT21_FREEZE_REPORT_PATH
    if not archive_path.exists():
        raise ValueError(f"missing archive: {ARCHIVE_OUTPUT_PATH}")
    if not archive_sha_path.exists():
        raise ValueError(f"missing archive sha256 sidecar: {ARCHIVE_SHA256_OUTPUT_PATH}")
    if not freeze_report_path.exists():
        raise ValueError(f"missing archive freeze report: {LOT21_FREEZE_REPORT_PATH}")
    archive_checksum = sha256_file(archive_path)
    archive_size_bytes = archive_path.stat().st_size
    expected_sha_line = f"{archive_checksum}  {archive_path.name}"
    if read_text_limited(archive_sha_path).strip() != expected_sha_line:
        raise ValueError("archive sha256 sidecar mismatch")
    if product_scope.get("source_v1_archive_frozen") is not True:
        raise ValueError("Lot 21 source_v1_archive_frozen must remain true")
    if product_scope.get("source_v1_archive_path") != ARCHIVE_OUTPUT_PATH:
        raise ValueError("Lot 21 source_v1_archive_path mismatch")
    if product_scope.get("source_v1_archive_sha256") != archive_checksum:
        raise ValueError("Lot 21 source_v1_archive_sha256 mismatch")
    if product_scope.get("source_v1_archive_size_bytes") != archive_size_bytes:
        raise ValueError("Lot 21 source_v1_archive_size_bytes mismatch")
    if closure_snapshot.get("archive_sha256") != archive_checksum:
        raise ValueError("Lot 20 archive checksum mismatch")
    if closure_snapshot.get("archive_size_bytes") != archive_size_bytes:
        raise ValueError("Lot 20 archive size mismatch")
    return archive_checksum, archive_size_bytes



def _as_float(value: Any, *, field_name: str = "numeric_value") -> float:
    return require_finite_float(value, field_name=field_name)


def _round6(value: float) -> float:
    return round(float(value), 6)


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _safe_percent(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return (numerator / denominator) * 100.0


def _latest_jsonl_row(root: Path, relative_path: str) -> dict[str, Any]:
    rows = load_jsonl(root / relative_path)
    return rows[-1] if rows else {}


def _component_dict(row: dict[str, Any], key: str) -> dict[str, Any]:
    value = row.get(key)
    return value if isinstance(value, dict) else {}


def _indicator_value_map(indicator_row: dict[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    raw_values = indicator_row.get("indicator_values")
    if isinstance(raw_values, list):
        for item in raw_values:
            if isinstance(item, dict) and isinstance(item.get("indicator_id"), str):
                values[str(item["indicator_id"])] = _as_float(item.get("value"))
    return values


def _volatility_expansion_score(
    *,
    atr_percent: float,
    true_range_percent: float,
    bollinger_width_5: float,
    range_width_percent: float,
    volatility_percentile: float,
    realized_volatility_6: float,
    expansion_score_source: float,
) -> float:
    return _round6(
        mean(
            [
                _clamp(atr_percent / float(VRC_PARAMETERS["atr_expansion_normalizer"])),
                _clamp(true_range_percent / float(VRC_PARAMETERS["true_range_normalizer"])),
                _clamp(bollinger_width_5 / float(VRC_PARAMETERS["bollinger_expansion_normalizer"])),
                _clamp(range_width_percent / float(VRC_PARAMETERS["range_expansion_normalizer"])),
                _clamp(volatility_percentile * float(VRC_PARAMETERS["volatility_percentile_multiplier"])),
                _clamp(realized_volatility_6 / float(VRC_PARAMETERS["realized_volatility_normalizer"])),
                _clamp(expansion_score_source),
            ]
        )
    )


def _volatility_compression_score(
    *,
    atr_percent: float,
    bollinger_width_5: float,
    range_width_percent: float,
    volatility_percentile: float,
    compression_score_source: float,
) -> float:
    return _round6(
        mean(
            [
                _clamp((float(VRC_PARAMETERS["atr_expansion_normalizer"]) - atr_percent) / float(VRC_PARAMETERS["atr_expansion_normalizer"])),
                _clamp((float(VRC_PARAMETERS["compression_bollinger_reference"]) - bollinger_width_5) / float(VRC_PARAMETERS["compression_bollinger_reference"])),
                _clamp((float(VRC_PARAMETERS["compression_range_reference"]) - range_width_percent) / float(VRC_PARAMETERS["compression_range_reference"])),
                _clamp(1.0 - volatility_percentile),
                _clamp(compression_score_source),
            ]
        )
    )


def _volatility_state(*, row_count: int, expansion_score: float, compression_score: float, volatility_level: str) -> str:
    if row_count < int(VRC_PARAMETERS["minimum_rows"]):
        return "VOLATILITY_CONTEXT_INSUFFICIENT_DATA"
    if compression_score >= float(VRC_PARAMETERS["compression_threshold"]) and expansion_score < 0.5:
        return "VOLATILITY_CONTEXT_COMPRESSING"
    if expansion_score >= float(VRC_PARAMETERS["expansion_threshold"]) and compression_score < 0.5:
        return "VOLATILITY_CONTEXT_EXPANDING"
    if expansion_score >= float(VRC_PARAMETERS["high_or_low_threshold"]) or volatility_level == "HIGH":
        return "VOLATILITY_CONTEXT_HIGH"
    if compression_score >= float(VRC_PARAMETERS["high_or_low_threshold"]) or volatility_level == "LOW":
        return "VOLATILITY_CONTEXT_LOW"
    if expansion_score >= float(VRC_PARAMETERS["moderate_threshold"]) or compression_score >= float(VRC_PARAMETERS["moderate_threshold"]) or volatility_level == "MODERATE":
        return "VOLATILITY_CONTEXT_MODERATE"
    if abs(expansion_score - compression_score) <= float(VRC_PARAMETERS["mixed_delta"]) and max(expansion_score, compression_score) >= float(VRC_PARAMETERS["mixed_minimum"]):
        return "VOLATILITY_CONTEXT_MIXED"
    return "VOLATILITY_CONTEXT_NEUTRAL"


def _regime_state(
    *,
    row_count: int,
    market_regime_source_state: str,
    trm_combined_state: str,
    trend_state: str,
    range_state: str,
    volatility_state: str,
) -> str:
    if row_count < int(VRC_PARAMETERS["minimum_rows"]):
        return "REGIME_CONTEXT_INSUFFICIENT_DATA"
    source = market_regime_source_state.lower()
    if source == "compressed" or volatility_state == "VOLATILITY_CONTEXT_COMPRESSING":
        return "REGIME_CONTEXT_COMPRESSED"
    if volatility_state in {"VOLATILITY_CONTEXT_HIGH", "VOLATILITY_CONTEXT_EXPANDING"}:
        return "REGIME_CONTEXT_VOLATILE"
    if trm_combined_state == "TRM_CONTEXT_TRENDING" or trend_state in {"TREND_CONTEXT_UPWARD", "TREND_CONTEXT_DOWNWARD"}:
        return "REGIME_CONTEXT_TRENDING"
    if source in {"range", "ranging"} or trm_combined_state in {"TRM_CONTEXT_RANGING", "TRM_CONTEXT_COMPRESSED"}:
        return "REGIME_CONTEXT_RANGING"
    if range_state == "RANGE_CONTEXT_NEUTRAL":
        return "REGIME_CONTEXT_NEUTRAL"
    return "REGIME_CONTEXT_MIXED"


def _regime_context_score(
    *,
    market_regime_source_state: str,
    trm_combined_state: str,
    trend_state: str,
    range_state: str,
    volatility_state: str,
    market_context_score: float,
) -> float:
    score = 0.0
    source = market_regime_source_state.lower()
    if source in {"range", "ranging"} and range_state.startswith("RANGE_CONTEXT"):
        score += float(VRC_PARAMETERS["regime_source_range_weight"])
    if source == "compressed" and volatility_state == "VOLATILITY_CONTEXT_COMPRESSING":
        score += float(VRC_PARAMETERS["regime_source_compressed_weight"])
    if trm_combined_state == "TRM_CONTEXT_TRENDING" and trend_state in {"TREND_CONTEXT_UPWARD", "TREND_CONTEXT_DOWNWARD"}:
        score += float(VRC_PARAMETERS["regime_trend_weight"])
    if trm_combined_state in {"TRM_CONTEXT_RANGING", "TRM_CONTEXT_COMPRESSED"} and range_state in {
        "RANGE_CONTEXT_NEUTRAL",
        "RANGE_CONTEXT_COMPRESSED",
    }:
        score += float(VRC_PARAMETERS["regime_range_weight"])
    if volatility_state in {"VOLATILITY_CONTEXT_HIGH", "VOLATILITY_CONTEXT_EXPANDING"} and source != "compressed":
        score += float(VRC_PARAMETERS["regime_volatility_weight"])
    score += _clamp(market_context_score) * float(VRC_PARAMETERS["market_context_weight"])
    return _round6(_clamp(score))


def _confluence_components(
    *,
    market_context_state: str,
    technical_indicator_state: str,
    trend_state: str,
    range_state: str,
    momentum_state: str,
    volatility_state: str,
    regime_state: str,
    trm_combined_state: str,
) -> dict[str, Any]:
    trend_alignment = trend_state in {"TREND_CONTEXT_UPWARD", "TREND_CONTEXT_DOWNWARD"} and momentum_state in {
        "MOMENTUM_CONTEXT_ACCELERATING",
        "MOMENTUM_CONTEXT_DECELERATING",
    }
    range_alignment = range_state in {
        "RANGE_CONTEXT_NEUTRAL",
        "RANGE_CONTEXT_COMPRESSED",
        "RANGE_CONTEXT_BREAKING_STRUCTURE",
    } and regime_state in {"REGIME_CONTEXT_RANGING", "REGIME_CONTEXT_COMPRESSED"}
    volatility_alignment = (
        volatility_state in {"VOLATILITY_CONTEXT_HIGH", "VOLATILITY_CONTEXT_EXPANDING"} and regime_state == "REGIME_CONTEXT_VOLATILE"
    ) or (
        volatility_state in {"VOLATILITY_CONTEXT_LOW", "VOLATILITY_CONTEXT_COMPRESSING"} and regime_state == "REGIME_CONTEXT_COMPRESSED"
    )
    indicator_alignment = technical_indicator_state == "INDICATOR_MIXED" and trm_combined_state in {
        "TRM_CONTEXT_TRENDING",
        "TRM_CONTEXT_MIXED",
        "TRM_CONTEXT_VOLATILE",
    }
    market_alignment = market_context_state == "CONTEXT_MIXED" or trm_combined_state in {
        "TRM_CONTEXT_TRENDING",
        "TRM_CONTEXT_RANGING",
        "TRM_CONTEXT_COMPRESSED",
    }
    return {
        "market_context_state": market_context_state,
        "technical_indicator_state": technical_indicator_state,
        "trend_state": trend_state,
        "range_state": range_state,
        "momentum_state": momentum_state,
        "volatility_state": volatility_state,
        "regime_state": regime_state,
        "trm_combined_state": trm_combined_state,
        "trend_alignment": trend_alignment,
        "range_alignment": range_alignment,
        "volatility_alignment": volatility_alignment,
        "indicator_alignment": indicator_alignment,
        "market_alignment": market_alignment,
    }


def _confluence_scores(components: dict[str, Any]) -> tuple[float, float]:
    agreement_flags = [
        bool(components.get("trend_alignment")),
        bool(components.get("range_alignment")),
        bool(components.get("volatility_alignment")),
        bool(components.get("indicator_alignment")),
        bool(components.get("market_alignment")),
    ]
    agreement_score = _round6(sum(1.0 for item in agreement_flags if item) / len(agreement_flags))
    divergence_flags = [
        components.get("trend_state") in {"TREND_CONTEXT_UPWARD", "TREND_CONTEXT_DOWNWARD"}
        and components.get("regime_state") == "REGIME_CONTEXT_COMPRESSED",
        components.get("volatility_state") in {"VOLATILITY_CONTEXT_HIGH", "VOLATILITY_CONTEXT_EXPANDING"}
        and components.get("range_state") == "RANGE_CONTEXT_COMPRESSED",
        components.get("trm_combined_state") == "TRM_CONTEXT_TRENDING"
        and components.get("technical_indicator_state") == "INDICATOR_NEUTRAL",
        components.get("market_context_state") == "CONTEXT_LOW_ACTIVITY"
        and components.get("volatility_state") in {"VOLATILITY_CONTEXT_HIGH", "VOLATILITY_CONTEXT_EXPANDING"},
        components.get("momentum_state") == "MOMENTUM_CONTEXT_DIVERGENT",
    ]
    divergence_score = _round6(sum(1.0 for item in divergence_flags if item) / len(divergence_flags))
    return agreement_score, divergence_score


def _confluence_state(*, row_count: int, agreement_score: float, divergence_score: float) -> str:
    if row_count < int(VRC_PARAMETERS["minimum_rows"]):
        return "CONFLUENCE_CONTEXT_INSUFFICIENT_DATA"
    if divergence_score >= 0.6:
        return "CONFLUENCE_CONTEXT_DIVERGENT"
    if agreement_score >= 0.75 and divergence_score <= 0.2:
        return "CONFLUENCE_CONTEXT_ALIGNED"
    if agreement_score >= 0.5 and divergence_score <= 0.4:
        return "CONFLUENCE_CONTEXT_PARTIAL"
    if agreement_score <= 0.25:
        return "CONFLUENCE_CONTEXT_WEAK"
    if agreement_score <= 0.2 and divergence_score <= 0.2:
        return "CONFLUENCE_CONTEXT_NEUTRAL"
    return "CONFLUENCE_CONTEXT_MIXED"


def _confluence_context_score(agreement_score: float, divergence_score: float) -> float:
    return _round6(_clamp(mean([agreement_score, 1.0 - divergence_score])))


def _combined_context_state(
    *,
    volatility_state: str,
    regime_state: str,
    confluence_state: str,
    trm_combined_state: str,
    combined_context_score: float,
) -> str:
    if "INSUFFICIENT_DATA" in {volatility_state, regime_state, confluence_state}:
        return "VRC_CONTEXT_INSUFFICIENT_DATA"
    if confluence_state == "CONFLUENCE_CONTEXT_DIVERGENT":
        return "VRC_CONTEXT_DIVERGENT"
    if regime_state == "REGIME_CONTEXT_COMPRESSED" and volatility_state in {
        "VOLATILITY_CONTEXT_LOW",
        "VOLATILITY_CONTEXT_COMPRESSING",
    }:
        return "VRC_CONTEXT_COMPRESSED"
    if regime_state == "REGIME_CONTEXT_VOLATILE" and confluence_state in {
        "CONFLUENCE_CONTEXT_MIXED",
        "CONFLUENCE_CONTEXT_PARTIAL",
    }:
        return "VRC_CONTEXT_VOLATILE_MIXED"
    if regime_state == "REGIME_CONTEXT_TRENDING" and trm_combined_state == "TRM_CONTEXT_TRENDING" and confluence_state in {
        "CONFLUENCE_CONTEXT_ALIGNED",
        "CONFLUENCE_CONTEXT_PARTIAL",
    }:
        return "VRC_CONTEXT_ALIGNED_TREND"
    if regime_state in {"REGIME_CONTEXT_RANGING", "REGIME_CONTEXT_COMPRESSED"} and confluence_state in {
        "CONFLUENCE_CONTEXT_ALIGNED",
        "CONFLUENCE_CONTEXT_PARTIAL",
    }:
        return "VRC_CONTEXT_ALIGNED_RANGE"
    if combined_context_score <= 0.2:
        return "VRC_CONTEXT_NEUTRAL"
    return "VRC_CONTEXT_MIXED"


def _aggregate_state(
    summaries: list[VolatilityRegimeConfluenceTimeframeSummary],
    *,
    field_name: str,
    default_state: str,
    preferred_states: list[str],
    score_field: str,
) -> tuple[str, float]:
    if not summaries:
        return default_state, 0.0
    average_score = _round6(mean(_as_float(getattr(summary, score_field)) for summary in summaries))
    states = [str(getattr(summary, field_name)) for summary in summaries]
    if len(set(states)) == 1:
        return states[0], average_score
    for state in preferred_states:
        if state in states:
            return state, average_score
    return default_state.replace("INSUFFICIENT_DATA", "MIXED"), average_score


def _non_executable_summary(*, timeframe: str, combined_context_state: str, combined_context_score: float) -> str:
    return (
        f"{timeframe} volatility/regime/confluence remains descriptive only with state {combined_context_state} "
        f"and score {combined_context_score}; execution, routing and allocation stay blocked."
    )


def _build_vrc_checks(
    *,
    product_scope: dict[str, Any],
    market_analysis: dict[str, Any],
    technical_indicators: dict[str, Any],
    trend_snapshot: dict[str, Any],
    archive_checksum: str,
    archive_size_bytes: int,
    timeframe_summaries: list[VolatilityRegimeConfluenceTimeframeSummary],
) -> list[VolatilityRegimeConfluenceCheck]:
    return [
        VolatilityRegimeConfluenceCheck(
            check_name="v1_archive_frozen",
            status="PASS",
            expected_value=True,
            observed_value=product_scope.get("source_v1_archive_frozen"),
            block_reason="NO_EXECUTION_ALLOWED",
            message=f"Frozen V1 archive remains validated with checksum {archive_checksum} and size {archive_size_bytes}.",
        ),
        VolatilityRegimeConfluenceCheck(
            check_name="product_scope_alignment",
            status="PASS",
            expected_value="OPENED_AS_PLANNING_ONLY",
            observed_value=product_scope.get("v2_scope_state"),
            block_reason="EDUCATIONAL_MODE_ONLY",
            message="Lot 21 product scope remains planning-only and blocks any executable layer.",
        ),
        VolatilityRegimeConfluenceCheck(
            check_name="market_analysis_alignment",
            status="PASS",
            expected_value="LOCAL_OFFLINE_ANALYSIS_ONLY",
            observed_value=market_analysis.get("analysis_mode"),
            block_reason="NO_STRATEGY_ENGINE",
            message="Lot 22 market analysis remains a local descriptive dependency only.",
        ),
        VolatilityRegimeConfluenceCheck(
            check_name="technical_indicator_alignment",
            status="PASS",
            expected_value="LOCAL_OFFLINE_INDICATORS_ONLY",
            observed_value=technical_indicators.get("indicator_mode"),
            block_reason="VOLATILITY_REGIME_CONFLUENCE_ONLY",
            message="Lot 23 technical indicators remain local and descriptive only.",
        ),
        VolatilityRegimeConfluenceCheck(
            check_name="trend_alignment",
            status="PASS",
            expected_value="LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY",
            observed_value=trend_snapshot.get("trend_engine_mode"),
            block_reason="VOLATILITY_REGIME_CONFLUENCE_ONLY",
            message="Lot 24 trend/range/momentum remains local and descriptive only.",
        ),
        VolatilityRegimeConfluenceCheck(
            check_name="vrc_timeframes",
            status="PASS",
            expected_value=["5m", "15m"],
            observed_value=[summary.timeframe for summary in timeframe_summaries],
            block_reason="VOLATILITY_REGIME_CONFLUENCE_ONLY",
            message="Volatility/Regime/Confluence summaries cover only the validated 5m and 15m local timeframes.",
        ),
    ]


def _build_timeframe_summary(
    *,
    timeframe: str,
    candles: list[dict[str, Any]],
    market_row: dict[str, Any],
    indicator_row: dict[str, Any],
    trend_row: dict[str, Any],
    volatility_row: dict[str, Any],
    regime_row: dict[str, Any],
    market_state_row: dict[str, Any],
) -> VolatilityRegimeConfluenceTimeframeSummary:
    row_count = len(candles)
    if not candles:
        return VolatilityRegimeConfluenceTimeframeSummary(
            timeframe=timeframe,
            row_count=0,
            first_timestamp="",
            last_timestamp="",
            atr_5=0.0,
            true_range_latest=0.0,
            bollinger_width_5=0.0,
            rolling_range_5=0.0,
            range_width_percent=0.0,
            volatility_expansion_score=0.0,
            volatility_compression_score=0.0,
            volatility_state="VOLATILITY_CONTEXT_INSUFFICIENT_DATA",
            volatility_context_score=0.0,
            market_regime_source_state="unknown",
            trend_state="TREND_CONTEXT_INSUFFICIENT_DATA",
            range_state="RANGE_CONTEXT_INSUFFICIENT_DATA",
            momentum_state="MOMENTUM_CONTEXT_INSUFFICIENT_DATA",
            technical_indicator_state="INDICATOR_INSUFFICIENT_DATA",
            regime_state="REGIME_CONTEXT_INSUFFICIENT_DATA",
            regime_context_score=0.0,
            confluence_components={"component_count": 0},
            confluence_agreement_score=0.0,
            confluence_divergence_score=0.0,
            confluence_state="CONFLUENCE_CONTEXT_INSUFFICIENT_DATA",
            confluence_context_score=0.0,
            combined_context_score=0.0,
            combined_context_state="VRC_CONTEXT_INSUFFICIENT_DATA",
            non_executable_summary="Insufficient local data; execution remains blocked and no decision layer is active.",
        )

    indicator_values = _indicator_value_map(indicator_row)
    latest_close = _as_float(candles[-1].get("close"))
    atr_5 = _as_float(indicator_values.get("atr_5"))
    true_range_latest = _as_float(indicator_values.get("true_range")) or _as_float(volatility_row.get("true_range"))
    bollinger_width_5 = _as_float(indicator_values.get("bollinger_width_5"))
    rolling_range_5 = _as_float(indicator_values.get("rolling_range_5"))
    range_width_percent = _as_float(trend_row.get("range_width_percent"))
    atr_percent = _safe_percent(atr_5, latest_close)
    true_range_percent = _safe_percent(true_range_latest, latest_close)
    volatility_percentile = _as_float(volatility_row.get("volatility_percentile_lookback"))
    realized_volatility_6 = _as_float(volatility_row.get("realized_volatility_6"))
    expansion_score_source = _as_float(regime_row.get("expansion_score"))
    compression_score_source = _as_float(regime_row.get("compression_score"))
    expansion_score = _volatility_expansion_score(
        atr_percent=atr_percent,
        true_range_percent=true_range_percent,
        bollinger_width_5=bollinger_width_5,
        range_width_percent=range_width_percent,
        volatility_percentile=volatility_percentile,
        realized_volatility_6=realized_volatility_6,
        expansion_score_source=expansion_score_source,
    )
    compression_score = _volatility_compression_score(
        atr_percent=atr_percent,
        bollinger_width_5=bollinger_width_5,
        range_width_percent=range_width_percent,
        volatility_percentile=volatility_percentile,
        compression_score_source=compression_score_source,
    )
    volatility_state = _volatility_state(
        row_count=row_count,
        expansion_score=expansion_score,
        compression_score=compression_score,
        volatility_level=str(market_row.get("volatility_level") or "LOW"),
    )
    volatility_context_score = _round6(max(expansion_score, compression_score))

    market_regime_source_state = str(
        _component_dict(market_state_row, "regime_state").get("regime_state")
        or regime_row.get("regime_state")
        or market_row.get("regime_state")
        or "unknown"
    )
    trend_state = str(trend_row.get("trend_state") or "TREND_CONTEXT_INSUFFICIENT_DATA")
    range_state = str(trend_row.get("range_state") or "RANGE_CONTEXT_INSUFFICIENT_DATA")
    momentum_state = str(trend_row.get("momentum_state") or "MOMENTUM_CONTEXT_INSUFFICIENT_DATA")
    technical_indicator_state = str(indicator_row.get("indicator_state") or "INDICATOR_INSUFFICIENT_DATA")
    trm_combined_state = str(trend_row.get("combined_context_state") or "TRM_CONTEXT_INSUFFICIENT_DATA")
    market_context_state = str(market_row.get("context_label") or "CONTEXT_INSUFFICIENT_DATA")

    regime_state = _regime_state(
        row_count=row_count,
        market_regime_source_state=market_regime_source_state,
        trm_combined_state=trm_combined_state,
        trend_state=trend_state,
        range_state=range_state,
        volatility_state=volatility_state,
    )
    regime_context_score = _regime_context_score(
        market_regime_source_state=market_regime_source_state,
        trm_combined_state=trm_combined_state,
        trend_state=trend_state,
        range_state=range_state,
        volatility_state=volatility_state,
        market_context_score=_as_float(market_row.get("context_score")),
    )
    components = _confluence_components(
        market_context_state=market_context_state,
        technical_indicator_state=technical_indicator_state,
        trend_state=trend_state,
        range_state=range_state,
        momentum_state=momentum_state,
        volatility_state=volatility_state,
        regime_state=regime_state,
        trm_combined_state=trm_combined_state,
    )
    agreement_score, divergence_score = _confluence_scores(components)
    confluence_state = _confluence_state(
        row_count=row_count,
        agreement_score=agreement_score,
        divergence_score=divergence_score,
    )
    confluence_context_score = _confluence_context_score(agreement_score, divergence_score)
    combined_context_score = _round6(mean([volatility_context_score, regime_context_score, confluence_context_score]))
    combined_context_state = _combined_context_state(
        volatility_state=volatility_state,
        regime_state=regime_state,
        confluence_state=confluence_state,
        trm_combined_state=trm_combined_state,
        combined_context_score=combined_context_score,
    )
    components["component_count"] = 5
    components["agreement_count"] = int(round(agreement_score * 5))
    components["divergence_count"] = int(round(divergence_score * 5))

    return VolatilityRegimeConfluenceTimeframeSummary(
        timeframe=timeframe,
        row_count=row_count,
        first_timestamp=str(candles[0].get("timestamp") or ""),
        last_timestamp=str(candles[-1].get("timestamp") or ""),
        atr_5=_round6(atr_5),
        true_range_latest=_round6(true_range_latest),
        bollinger_width_5=_round6(bollinger_width_5),
        rolling_range_5=_round6(rolling_range_5),
        range_width_percent=_round6(range_width_percent),
        volatility_expansion_score=expansion_score,
        volatility_compression_score=compression_score,
        volatility_state=volatility_state,
        volatility_context_score=volatility_context_score,
        market_regime_source_state=market_regime_source_state,
        trend_state=trend_state,
        range_state=range_state,
        momentum_state=momentum_state,
        technical_indicator_state=technical_indicator_state,
        regime_state=regime_state,
        regime_context_score=regime_context_score,
        confluence_components=components,
        confluence_agreement_score=agreement_score,
        confluence_divergence_score=divergence_score,
        confluence_state=confluence_state,
        confluence_context_score=confluence_context_score,
        combined_context_score=combined_context_score,
        combined_context_state=combined_context_state,
        non_executable_summary=_non_executable_summary(
            timeframe=timeframe,
            combined_context_state=combined_context_state,
            combined_context_score=combined_context_score,
        ),
    )


def build_volatility_regime_confluence_result(root: Path) -> VolatilityRegimeConfluenceResult:
    policy = VolatilityRegimeConfluencePolicy()
    product_scope = _require_object(root, LOT21_OUTPUT_PATH)
    closure_snapshot = _require_object(root, LOT20_OUTPUT_PATH)
    market_analysis = _require_object(root, LOT22_OUTPUT_PATH)
    technical_indicators = _require_object(root, LOT23_OUTPUT_PATH)
    trend_snapshot = _require_object(root, LOT24_OUTPUT_PATH)
    market_timeframes = load_jsonl(root / LOT22_TIMEFRAMES_OUTPUT_PATH)
    indicator_timeframes = load_jsonl(root / LOT23_TIMEFRAMES_OUTPUT_PATH)
    trend_timeframes = load_jsonl(root / LOT24_TIMEFRAMES_OUTPUT_PATH)

    _require_expected_pairs(
        product_scope,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "v2_scope_state": policy.v2_scope_state,
            "source_v1_archive_frozen": True,
        },
        name="Lot 21 product scope",
    )
    _require_expected_pairs(
        market_analysis,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "analysis_mode": policy.analysis_mode,
            "v2_scope_state": policy.v2_scope_state,
            "source_v1_archive_frozen": True,
        },
        name="Lot 22 market analysis",
    )
    _require_expected_pairs(
        technical_indicators,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "analysis_mode": policy.analysis_mode,
            "indicator_mode": policy.indicator_mode,
            "v2_scope_state": policy.v2_scope_state,
            "source_v1_archive_frozen": True,
        },
        name="Lot 23 technical indicators",
    )
    _require_expected_pairs(
        trend_snapshot,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "analysis_mode": policy.analysis_mode,
            "indicator_mode": policy.indicator_mode,
            "trend_engine_mode": policy.trend_engine_mode,
            "v2_scope_state": policy.v2_scope_state,
            "source_v1_archive_frozen": True,
        },
        name="Lot 24 trend/range/momentum",
    )
    archive_checksum, archive_size_bytes = _validate_frozen_archive(
        root,
        product_scope=product_scope,
        closure_snapshot=closure_snapshot,
    )

    market_by_timeframe = {str(row.get("timeframe")): row for row in market_timeframes}
    indicator_by_timeframe = {str(row.get("timeframe")): row for row in indicator_timeframes}
    trend_by_timeframe = {str(row.get("timeframe")): row for row in trend_timeframes}
    timeframe_summaries: list[VolatilityRegimeConfluenceTimeframeSummary] = []
    input_rows_by_timeframe: dict[str, int] = {}

    for timeframe, spec in INPUT_SPECS.items():
        candles = load_jsonl(root / spec["candles"])
        input_rows_by_timeframe[timeframe] = len(candles)
        timeframe_summaries.append(
            _build_timeframe_summary(
                timeframe=timeframe,
                candles=candles,
                market_row=market_by_timeframe.get(timeframe, {}),
                indicator_row=indicator_by_timeframe.get(timeframe, {}),
                trend_row=trend_by_timeframe.get(timeframe, {}),
                volatility_row=_latest_jsonl_row(root, spec["volatility"]),
                regime_row=_latest_jsonl_row(root, spec["regime"]),
                market_state_row=_latest_jsonl_row(root, spec["market_state"]),
            )
        )

    volatility_state, volatility_context_score = _aggregate_state(
        timeframe_summaries,
        field_name="volatility_state",
        default_state="VOLATILITY_CONTEXT_INSUFFICIENT_DATA",
        preferred_states=[
            "VOLATILITY_CONTEXT_EXPANDING",
            "VOLATILITY_CONTEXT_COMPRESSING",
            "VOLATILITY_CONTEXT_HIGH",
            "VOLATILITY_CONTEXT_LOW",
            "VOLATILITY_CONTEXT_MODERATE",
            "VOLATILITY_CONTEXT_MIXED",
            "VOLATILITY_CONTEXT_NEUTRAL",
        ],
        score_field="volatility_context_score",
    )
    regime_state, regime_context_score = _aggregate_state(
        timeframe_summaries,
        field_name="regime_state",
        default_state="REGIME_CONTEXT_INSUFFICIENT_DATA",
        preferred_states=[
            "REGIME_CONTEXT_VOLATILE",
            "REGIME_CONTEXT_COMPRESSED",
            "REGIME_CONTEXT_TRENDING",
            "REGIME_CONTEXT_RANGING",
            "REGIME_CONTEXT_MIXED",
            "REGIME_CONTEXT_NEUTRAL",
        ],
        score_field="regime_context_score",
    )
    confluence_state, confluence_context_score = _aggregate_state(
        timeframe_summaries,
        field_name="confluence_state",
        default_state="CONFLUENCE_CONTEXT_INSUFFICIENT_DATA",
        preferred_states=[
            "CONFLUENCE_CONTEXT_DIVERGENT",
            "CONFLUENCE_CONTEXT_ALIGNED",
            "CONFLUENCE_CONTEXT_PARTIAL",
            "CONFLUENCE_CONTEXT_MIXED",
            "CONFLUENCE_CONTEXT_WEAK",
            "CONFLUENCE_CONTEXT_NEUTRAL",
        ],
        score_field="confluence_context_score",
    )
    combined_context_score = _round6(mean(summary.combined_context_score for summary in timeframe_summaries))
    combined_context_state = _combined_context_state(
        volatility_state=volatility_state,
        regime_state=regime_state,
        confluence_state=confluence_state,
        trm_combined_state=str(trend_snapshot.get("combined_context_state") or "TRM_CONTEXT_INSUFFICIENT_DATA"),
        combined_context_score=combined_context_score,
    )

    result = VolatilityRegimeConfluenceResult(
        vrc_engine_version=policy.vrc_engine_version,
        policy_version=policy.policy_version,
        project_name=policy.project_name,
        project_mode=policy.project_mode,
        vrc_engine_mode=policy.vrc_engine_mode,
        analysis_mode=policy.analysis_mode,
        indicator_mode=policy.indicator_mode,
        trend_engine_mode=policy.trend_engine_mode,
        execution_allowed=policy.execution_allowed,
        trade_allowed=policy.trade_allowed,
        external_connectivity_allowed=policy.external_connectivity_allowed,
        live_execution=policy.live_execution,
        leverage=policy.leverage,
        source_v1_archive_frozen=policy.source_v1_archive_frozen,
        v2_scope_state=policy.v2_scope_state,
        dataset_timeframes=["5m", "15m"],
        vrc_timeframes=["5m", "15m"],
        input_rows_by_timeframe=input_rows_by_timeframe,
        volatility_state=volatility_state,
        regime_state=regime_state,
        confluence_state=confluence_state,
        volatility_context_score=volatility_context_score,
        regime_context_score=regime_context_score,
        confluence_context_score=confluence_context_score,
        combined_context_score=combined_context_score,
        combined_context_state=combined_context_state,
        timeframe_summaries=timeframe_summaries,
        vrc_checks=_build_vrc_checks(
            product_scope=product_scope,
            market_analysis=market_analysis,
            technical_indicators=technical_indicators,
            trend_snapshot=trend_snapshot,
            archive_checksum=archive_checksum,
            archive_size_bytes=archive_size_bytes,
            timeframe_summaries=timeframe_summaries,
        ),
        vrc_block_reasons=list(DEFAULT_VRC_BLOCK_REASONS),
        source_artifacts=default_vrc_source_artifacts(),
    )
    result_payload = result.to_dict()
    return replace(result, vrc_checksum=build_vrc_checksum(result_payload))
