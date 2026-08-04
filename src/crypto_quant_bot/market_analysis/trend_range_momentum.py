from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from statistics import mean
from typing import Any

from crypto_quant_bot.data.checksum import sha256_file
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
from crypto_quant_bot.market_analysis.indicator_models import REQUIRED_INDICATOR_SET
from crypto_quant_bot.market_analysis.io import load_json, load_jsonl, read_text_limited
from crypto_quant_bot.market_analysis.math_parameters import TREND_PARAMETERS
from crypto_quant_bot.market_analysis.numeric import require_finite_float
from crypto_quant_bot.market_analysis.technical_indicators import (
    INDICATOR_INVARIANTS,
    LOT23_OUTPUT_PATH,
    LOT23_TIMEFRAMES_OUTPUT_PATH,
)
from crypto_quant_bot.market_analysis.trend_models import (
    DEFAULT_TREND_BLOCK_REASONS,
    TrendRangeMomentumCheck,
    TrendRangeMomentumPolicy,
    TrendRangeMomentumResult,
    TrendRangeMomentumTimeframeSummary,
)

LOT24_OUTPUT_PATH = "data/audit/trend_range_momentum_lot24.json"
LOT24_TIMEFRAMES_OUTPUT_PATH = "data/audit/trend_range_momentum_timeframes_lot24.jsonl"
LOT24_REPORT_OUTPUT_PATH = "reports/lot_24_trend_range_momentum_report.md"
LOT24_VALIDATION_REPORT_PATH = "reports/lot_24_validation_report.md"
LOT24_OVERVIEW_DOC_PATH = "docs/LOT_24_TREND_RANGE_MOMENTUM.md"
LOT24_ACCEPTANCE_DOC_PATH = "docs/ACCEPTANCE_CRITERIA_LOT_24.md"

TREND_INVARIANTS = dict(INDICATOR_INVARIANTS)
TREND_INVARIANTS["indicator_mode"] = "LOCAL_OFFLINE_INDICATORS_ONLY"
TREND_INVARIANTS["trend_engine_mode"] = "LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY"


def default_trend_source_artifacts() -> list[str]:
    candle_paths = [spec["candles"] for spec in INPUT_SPECS.values()]
    return sorted(
        {
            LOT20_OUTPUT_PATH,
            LOT21_OUTPUT_PATH,
            LOT21_FREEZE_REPORT_PATH,
            LOT22_OUTPUT_PATH,
            LOT22_TIMEFRAMES_OUTPUT_PATH,
            LOT23_OUTPUT_PATH,
            LOT23_TIMEFRAMES_OUTPUT_PATH,
            ARCHIVE_OUTPUT_PATH,
            ARCHIVE_SHA256_OUTPUT_PATH,
            "scripts/validate_v1_archive_frozen.py",
            *candle_paths,
        }
    )


def build_trend_checksum(payload: dict[str, object]) -> str:
    normalized = json.loads(json.dumps(payload))

    def strip_runtime_fields(obj: object) -> object:
        if isinstance(obj, dict):
            next_obj: dict[str, object] = {}
            for key, value in obj.items():
                if key in {"created_at", "trend_checksum"}:
                    continue
                next_obj[key] = strip_runtime_fields(value)
            return next_obj
        if isinstance(obj, list):
            return [strip_runtime_fields(item) for item in obj]
        return obj

    cleaned = strip_runtime_fields(normalized)
    if not isinstance(cleaned, dict):
        raise ValueError("trend checksum payload must remain a mapping")
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


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _indicator_value_map(indicator_row: dict[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    raw_values = indicator_row.get("indicator_values")
    if isinstance(raw_values, list):
        for item in raw_values:
            if isinstance(item, dict) and isinstance(item.get("indicator_id"), str):
                values[str(item["indicator_id"])] = _as_float(item.get("value"))
    missing = set(REQUIRED_INDICATOR_SET) - set(values)
    if missing:
        raise ValueError(f"missing Lot 23 indicators: {', '.join(sorted(missing))}")
    return values


def _safe_percent(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return (numerator / denominator) * 100.0


def _trend_slope_5(closes: list[float]) -> float:
    if len(closes) < 5:
        return 0.0
    return (closes[-1] - closes[-5]) / 4.0


def _trend_direction_context(slope_percent: float, close_vs_ema_percent: float) -> str:
    if slope_percent >= float(TREND_PARAMETERS["direction_threshold_percent"]) and close_vs_ema_percent >= float(TREND_PARAMETERS["direction_threshold_percent"]):
        return "UPWARD_SLOPE"
    if slope_percent <= -float(TREND_PARAMETERS["direction_threshold_percent"]) and close_vs_ema_percent <= -float(TREND_PARAMETERS["direction_threshold_percent"]):
        return "DOWNWARD_SLOPE"
    if abs(slope_percent) <= float(TREND_PARAMETERS["flat_slope_threshold_percent"]) and abs(close_vs_ema_percent) <= float(TREND_PARAMETERS["direction_threshold_percent"]):
        return "FLAT_SLOPE"
    return "TRANSITIONAL_SLOPE"


def _trend_context_score(
    *,
    slope_percent: float,
    close_vs_ema_percent: float,
    close_change_percent: float,
    market_context_score: float,
) -> float:
    slope_strength = _clamp(abs(slope_percent) / float(TREND_PARAMETERS["trend_slope_normalizer"]))
    extension_strength = _clamp(abs(close_vs_ema_percent) / float(TREND_PARAMETERS["trend_extension_normalizer"]))
    drift_strength = _clamp(abs(close_change_percent) / float(TREND_PARAMETERS["trend_drift_normalizer"]))
    alignment_strength = 1.0 if _sign(slope_percent) == _sign(close_vs_ema_percent) and _sign(slope_percent) != 0 else 0.35
    return _round6(mean([slope_strength, extension_strength, drift_strength, alignment_strength, _clamp(market_context_score)]))


def _range_context_score(
    *,
    range_width_percent: float,
    range_position_percent: float,
    bollinger_width_5: float,
    atr_percent: float,
) -> float:
    width_strength = max(_clamp((float(TREND_PARAMETERS["range_width_reference"]) - range_width_percent) / float(TREND_PARAMETERS["range_width_reference"])), _clamp((range_width_percent - float(TREND_PARAMETERS["range_width_reference"])) / float(TREND_PARAMETERS["range_width_expansion_span"])))
    edge_strength = _clamp(abs(range_position_percent - 50.0) / float(TREND_PARAMETERS["range_edge_normalizer"]))
    volatility_strength = max(_clamp(bollinger_width_5 / float(TREND_PARAMETERS["range_bollinger_normalizer"])), _clamp(atr_percent / float(TREND_PARAMETERS["range_atr_normalizer"])))
    return _round6(mean([width_strength, edge_strength, volatility_strength]))


def _momentum_context_score(
    *,
    momentum_percent: float,
    rate_of_change_3: float,
    rsi_5: float,
    macd_histogram: float,
) -> float:
    momentum_strength = max(_clamp(abs(momentum_percent) / float(TREND_PARAMETERS["momentum_normalizer"])), _clamp(abs(rate_of_change_3) / float(TREND_PARAMETERS["momentum_normalizer"])))
    oscillator_strength = _clamp(abs(rsi_5 - 50.0) / float(TREND_PARAMETERS["rsi_normalizer"]))
    macd_strength = _clamp(abs(macd_histogram) / float(TREND_PARAMETERS["macd_normalizer"]))
    return _round6(mean([momentum_strength, oscillator_strength, macd_strength]))


def _trend_state(
    *,
    row_count: int,
    close_vs_ema_percent: float,
    slope_percent: float,
    close_change_percent: float,
    trend_context_score: float,
) -> str:
    if row_count < int(TREND_PARAMETERS["minimum_rows"]):
        return "TREND_CONTEXT_INSUFFICIENT_DATA"
    if close_vs_ema_percent >= float(TREND_PARAMETERS["direction_threshold_percent"]) and slope_percent >= float(TREND_PARAMETERS["direction_threshold_percent"]) and close_change_percent >= float(TREND_PARAMETERS["close_change_threshold_percent"]) and trend_context_score >= float(TREND_PARAMETERS["minimum_context_score"]):
        return "TREND_CONTEXT_UPWARD"
    if close_vs_ema_percent <= -float(TREND_PARAMETERS["direction_threshold_percent"]) and slope_percent <= -float(TREND_PARAMETERS["direction_threshold_percent"]) and close_change_percent <= -float(TREND_PARAMETERS["close_change_threshold_percent"]) and trend_context_score >= float(TREND_PARAMETERS["minimum_context_score"]):
        return "TREND_CONTEXT_DOWNWARD"
    if abs(close_vs_ema_percent) <= float(TREND_PARAMETERS["direction_threshold_percent"]) and abs(slope_percent) <= float(TREND_PARAMETERS["flat_slope_threshold_percent"]):
        return "TREND_CONTEXT_FLAT"
    if trend_context_score <= float(TREND_PARAMETERS["neutral_context_score"]):
        return "TREND_CONTEXT_NEUTRAL"
    return "TREND_CONTEXT_MIXED"


def _range_state(
    *,
    row_count: int,
    range_width_percent: float,
    range_position_percent: float,
    bollinger_width_5: float,
    atr_percent: float,
    trend_context_score: float,
) -> str:
    if row_count < int(TREND_PARAMETERS["minimum_rows"]):
        return "RANGE_CONTEXT_INSUFFICIENT_DATA"
    if range_width_percent <= float(TREND_PARAMETERS["range_compressed_width_percent"]) and bollinger_width_5 <= float(TREND_PARAMETERS["range_compressed_bollinger_percent"]):
        return "RANGE_CONTEXT_COMPRESSED"
    if (range_position_percent >= float(TREND_PARAMETERS["range_break_edge_high_percent"]) or range_position_percent <= float(TREND_PARAMETERS["range_break_edge_low_percent"])) and range_width_percent >= float(TREND_PARAMETERS["range_break_width_percent"]) and trend_context_score >= float(TREND_PARAMETERS["minimum_context_score"]):
        return "RANGE_CONTEXT_BREAKING_STRUCTURE"
    if range_width_percent >= float(TREND_PARAMETERS["range_expanded_width_percent"]) or bollinger_width_5 >= float(TREND_PARAMETERS["range_expanded_bollinger_percent"]) or atr_percent >= float(TREND_PARAMETERS["range_expanded_atr_percent"]):
        return "RANGE_CONTEXT_EXPANDED"
    if float(TREND_PARAMETERS["range_neutral_low_percent"]) <= range_position_percent <= float(TREND_PARAMETERS["range_neutral_high_percent"]) and range_width_percent <= float(TREND_PARAMETERS["range_neutral_width_percent"]):
        return "RANGE_CONTEXT_NEUTRAL"
    return "RANGE_CONTEXT_MIXED"


def _momentum_state(
    *,
    row_count: int,
    momentum_3: float,
    rate_of_change_3: float,
    rsi_5: float,
    macd_histogram: float,
    momentum_context_score: float,
) -> str:
    if row_count < int(TREND_PARAMETERS["minimum_rows"]):
        return "MOMENTUM_CONTEXT_INSUFFICIENT_DATA"
    if momentum_context_score <= 0.2:
        return "MOMENTUM_CONTEXT_NEUTRAL"
    if (_sign(macd_histogram) != _sign(rate_of_change_3) and _sign(rate_of_change_3) != 0) or (rsi_5 >= float(TREND_PARAMETERS["momentum_rsi_divergence_level"]) and rate_of_change_3 <= float(TREND_PARAMETERS["direction_threshold_percent"])):
        return "MOMENTUM_CONTEXT_DIVERGENT"
    if momentum_3 > 0 and rate_of_change_3 >= float(TREND_PARAMETERS["momentum_rate_threshold_percent"]) and macd_histogram > 0:
        return "MOMENTUM_CONTEXT_ACCELERATING"
    if momentum_3 < 0 and rate_of_change_3 <= -float(TREND_PARAMETERS["momentum_rate_threshold_percent"]) and macd_histogram < 0:
        return "MOMENTUM_CONTEXT_DECELERATING"
    return "MOMENTUM_CONTEXT_MIXED"


def _combined_context_state(
    *,
    trend_state: str,
    range_state: str,
    momentum_state: str,
    combined_context_score: float,
) -> str:
    if "INSUFFICIENT_DATA" in {trend_state, range_state, momentum_state}:
        return "TRM_CONTEXT_INSUFFICIENT_DATA"
    if range_state == "RANGE_CONTEXT_COMPRESSED" and trend_state in {"TREND_CONTEXT_FLAT", "TREND_CONTEXT_NEUTRAL"}:
        return "TRM_CONTEXT_COMPRESSED"
    if range_state == "RANGE_CONTEXT_EXPANDED" and momentum_state in {"MOMENTUM_CONTEXT_ACCELERATING", "MOMENTUM_CONTEXT_DECELERATING"} and combined_context_score >= float(TREND_PARAMETERS["volatile_combined_score"]):
        return "TRM_CONTEXT_VOLATILE"
    if trend_state in {"TREND_CONTEXT_UPWARD", "TREND_CONTEXT_DOWNWARD"} and combined_context_score >= float(TREND_PARAMETERS["trend_combined_score"]):
        return "TRM_CONTEXT_TRENDING"
    if range_state in {"RANGE_CONTEXT_NEUTRAL", "RANGE_CONTEXT_COMPRESSED"} and trend_state in {"TREND_CONTEXT_FLAT", "TREND_CONTEXT_NEUTRAL"}:
        return "TRM_CONTEXT_RANGING"
    if combined_context_score <= float(TREND_PARAMETERS["neutral_context_score"]):
        return "TRM_CONTEXT_NEUTRAL"
    return "TRM_CONTEXT_MIXED"


def _aggregate_trend_state(summaries: list[TrendRangeMomentumTimeframeSummary]) -> tuple[str, float]:
    if not summaries:
        return "TREND_CONTEXT_INSUFFICIENT_DATA", 0.0
    average_score = _round6(mean(summary.trend_context_score for summary in summaries))
    states = [summary.trend_state for summary in summaries]
    if len(set(states)) == 1:
        return states[0], average_score
    if "TREND_CONTEXT_UPWARD" in states and "TREND_CONTEXT_DOWNWARD" not in states and average_score >= float(TREND_PARAMETERS["trend_combined_score"]):
        return "TREND_CONTEXT_UPWARD", average_score
    if "TREND_CONTEXT_DOWNWARD" in states and "TREND_CONTEXT_UPWARD" not in states and average_score >= float(TREND_PARAMETERS["trend_combined_score"]):
        return "TREND_CONTEXT_DOWNWARD", average_score
    if all(state in {"TREND_CONTEXT_FLAT", "TREND_CONTEXT_NEUTRAL"} for state in states):
        return "TREND_CONTEXT_FLAT", average_score
    return "TREND_CONTEXT_MIXED", average_score


def _aggregate_range_state(summaries: list[TrendRangeMomentumTimeframeSummary]) -> tuple[str, float]:
    if not summaries:
        return "RANGE_CONTEXT_INSUFFICIENT_DATA", 0.0
    average_score = _round6(mean(summary.range_context_score for summary in summaries))
    states = [summary.range_state for summary in summaries]
    if len(set(states)) == 1:
        return states[0], average_score
    if "RANGE_CONTEXT_BREAKING_STRUCTURE" in states and average_score >= 0.45:
        return "RANGE_CONTEXT_BREAKING_STRUCTURE", average_score
    if "RANGE_CONTEXT_EXPANDED" in states and average_score >= 0.45:
        return "RANGE_CONTEXT_EXPANDED", average_score
    if "RANGE_CONTEXT_COMPRESSED" in states and all(state not in {"RANGE_CONTEXT_EXPANDED", "RANGE_CONTEXT_BREAKING_STRUCTURE"} for state in states):
        return "RANGE_CONTEXT_COMPRESSED", average_score
    if all(state in {"RANGE_CONTEXT_NEUTRAL", "RANGE_CONTEXT_COMPRESSED"} for state in states):
        return "RANGE_CONTEXT_NEUTRAL", average_score
    return "RANGE_CONTEXT_MIXED", average_score


def _aggregate_momentum_state(summaries: list[TrendRangeMomentumTimeframeSummary]) -> tuple[str, float]:
    if not summaries:
        return "MOMENTUM_CONTEXT_INSUFFICIENT_DATA", 0.0
    average_score = _round6(mean(summary.momentum_context_score for summary in summaries))
    states = [summary.momentum_state for summary in summaries]
    if len(set(states)) == 1:
        return states[0], average_score
    if "MOMENTUM_CONTEXT_DIVERGENT" in states:
        return "MOMENTUM_CONTEXT_DIVERGENT", average_score
    if "MOMENTUM_CONTEXT_ACCELERATING" in states and "MOMENTUM_CONTEXT_DECELERATING" not in states and average_score >= float(TREND_PARAMETERS["trend_combined_score"]):
        return "MOMENTUM_CONTEXT_ACCELERATING", average_score
    if "MOMENTUM_CONTEXT_DECELERATING" in states and "MOMENTUM_CONTEXT_ACCELERATING" not in states and average_score >= float(TREND_PARAMETERS["trend_combined_score"]):
        return "MOMENTUM_CONTEXT_DECELERATING", average_score
    if all(state in {"MOMENTUM_CONTEXT_NEUTRAL", "MOMENTUM_CONTEXT_MIXED"} for state in states):
        return "MOMENTUM_CONTEXT_NEUTRAL", average_score
    return "MOMENTUM_CONTEXT_MIXED", average_score


def _aggregate_combined_state(summaries: list[TrendRangeMomentumTimeframeSummary]) -> tuple[str, float]:
    if not summaries:
        return "TRM_CONTEXT_INSUFFICIENT_DATA", 0.0
    average_score = _round6(mean(summary.combined_context_score for summary in summaries))
    states = [summary.combined_context_state for summary in summaries]
    if len(set(states)) == 1:
        return states[0], average_score
    if "TRM_CONTEXT_VOLATILE" in states and average_score >= 0.5:
        return "TRM_CONTEXT_VOLATILE", average_score
    if "TRM_CONTEXT_TRENDING" in states and average_score >= float(TREND_PARAMETERS["trend_combined_score"]):
        return "TRM_CONTEXT_TRENDING", average_score
    if "TRM_CONTEXT_COMPRESSED" in states and all(state not in {"TRM_CONTEXT_VOLATILE", "TRM_CONTEXT_TRENDING"} for state in states):
        return "TRM_CONTEXT_COMPRESSED", average_score
    if all(state in {"TRM_CONTEXT_RANGING", "TRM_CONTEXT_NEUTRAL", "TRM_CONTEXT_COMPRESSED"} for state in states):
        return "TRM_CONTEXT_RANGING", average_score
    return "TRM_CONTEXT_MIXED", average_score


def _non_executable_summary(*, timeframe: str, combined_context_state: str, combined_context_score: float) -> str:
    return (
        f"{timeframe} trend/range/momentum remains descriptive only with state {combined_context_state} "
        f"and score {combined_context_score}; execution, routing and allocation stay blocked."
    )


def _build_trend_checks(
    *,
    product_scope: dict[str, Any],
    market_analysis: dict[str, Any],
    technical_indicators: dict[str, Any],
    archive_checksum: str,
    archive_size_bytes: int,
    timeframe_summaries: list[TrendRangeMomentumTimeframeSummary],
) -> list[TrendRangeMomentumCheck]:
    return [
        TrendRangeMomentumCheck(
            check_name="v1_archive_frozen",
            status="PASS",
            expected_value=True,
            observed_value=product_scope.get("source_v1_archive_frozen"),
            block_reason="NO_EXECUTION_ALLOWED",
            message=f"Frozen V1 archive remains validated with checksum {archive_checksum} and size {archive_size_bytes}.",
        ),
        TrendRangeMomentumCheck(
            check_name="product_scope_alignment",
            status="PASS",
            expected_value="OPENED_AS_PLANNING_ONLY",
            observed_value=product_scope.get("v2_scope_state"),
            block_reason="EDUCATIONAL_MODE_ONLY",
            message="Lot 21 product scope remains planning-only and blocks any executable layer.",
        ),
        TrendRangeMomentumCheck(
            check_name="market_analysis_alignment",
            status="PASS",
            expected_value="LOCAL_OFFLINE_ANALYSIS_ONLY",
            observed_value=market_analysis.get("analysis_mode"),
            block_reason="NO_STRATEGY_ENGINE",
            message="Lot 22 market analysis remains a local descriptive dependency only.",
        ),
        TrendRangeMomentumCheck(
            check_name="technical_indicator_alignment",
            status="PASS",
            expected_value="LOCAL_OFFLINE_INDICATORS_ONLY",
            observed_value=technical_indicators.get("indicator_mode"),
            block_reason="TREND_RANGE_MOMENTUM_ONLY",
            message="Lot 23 technical indicators remain local and descriptive only.",
        ),
        TrendRangeMomentumCheck(
            check_name="trend_timeframes",
            status="PASS",
            expected_value=["5m", "15m"],
            observed_value=[summary.timeframe for summary in timeframe_summaries],
            block_reason="TREND_RANGE_MOMENTUM_ONLY",
            message="Trend/Range/Momentum summaries cover only the validated 5m and 15m local timeframes.",
        ),
    ]


def _build_timeframe_summary(
    *,
    timeframe: str,
    candles: list[dict[str, Any]],
    market_row: dict[str, Any],
    indicator_row: dict[str, Any],
) -> TrendRangeMomentumTimeframeSummary:
    row_count = len(candles)
    if not candles:
        return TrendRangeMomentumTimeframeSummary(
            timeframe=timeframe,
            row_count=0,
            first_timestamp="",
            last_timestamp="",
            close_first=0.0,
            close_last=0.0,
            close_change_percent=0.0,
            trend_slope_5=0.0,
            trend_direction_context="NO_DATA",
            range_high_5=0.0,
            range_low_5=0.0,
            range_width_5=0.0,
            range_width_percent=0.0,
            range_position_percent=0.0,
            momentum_3=0.0,
            rate_of_change_3=0.0,
            rsi_5=0.0,
            macd_histogram=0.0,
            bollinger_width_5=0.0,
            atr_5=0.0,
            trend_state="TREND_CONTEXT_INSUFFICIENT_DATA",
            range_state="RANGE_CONTEXT_INSUFFICIENT_DATA",
            momentum_state="MOMENTUM_CONTEXT_INSUFFICIENT_DATA",
            trend_context_score=0.0,
            range_context_score=0.0,
            momentum_context_score=0.0,
            combined_context_score=0.0,
            combined_context_state="TRM_CONTEXT_INSUFFICIENT_DATA",
            non_executable_summary="Insufficient local data; execution remains blocked and no decision layer is active.",
        )

    indicator_values = _indicator_value_map(indicator_row)
    closes = [_as_float(row.get("close")) for row in candles]
    highs = [_as_float(row.get("high")) for row in candles]
    lows = [_as_float(row.get("low")) for row in candles]
    close_first = closes[0]
    close_last = closes[-1]
    close_change_percent = _safe_percent(close_last - close_first, close_first)
    trend_slope_5 = _trend_slope_5(closes)
    reference_close = closes[-5] if len(closes) >= 5 else close_last
    slope_percent = _safe_percent(close_last - reference_close, reference_close)
    range_high_5 = max(highs[-5:]) if len(highs) >= 5 else max(highs)
    range_low_5 = min(lows[-5:]) if len(lows) >= 5 else min(lows)
    range_width_5 = range_high_5 - range_low_5
    range_width_percent = _safe_percent(range_width_5, close_last)
    if range_width_5 <= 0:
        range_position_percent = 50.0
    else:
        range_position_percent = _clamp(((close_last - range_low_5) / range_width_5), 0.0, 1.0) * 100.0

    market_context_score = _as_float(market_row.get("context_score"))
    close_vs_ema_percent = _as_float(indicator_values.get("close_vs_ema_5_percent"))
    momentum_3 = _as_float(indicator_values.get("momentum_3"))
    rate_of_change_3 = _as_float(indicator_values.get("rate_of_change_3"))
    rsi_5 = _as_float(indicator_values.get("rsi_5"))
    macd_histogram = _as_float(indicator_values.get("macd_histogram"))
    bollinger_width_5 = _as_float(indicator_values.get("bollinger_width_5"))
    atr_5 = _as_float(indicator_values.get("atr_5"))
    atr_percent = _safe_percent(atr_5, close_last)
    momentum_percent = _safe_percent(momentum_3, close_last)

    trend_context_score = _trend_context_score(
        slope_percent=slope_percent,
        close_vs_ema_percent=close_vs_ema_percent,
        close_change_percent=close_change_percent,
        market_context_score=market_context_score,
    )
    range_context_score = _range_context_score(
        range_width_percent=range_width_percent,
        range_position_percent=range_position_percent,
        bollinger_width_5=bollinger_width_5,
        atr_percent=atr_percent,
    )
    momentum_context_score = _momentum_context_score(
        momentum_percent=momentum_percent,
        rate_of_change_3=rate_of_change_3,
        rsi_5=rsi_5,
        macd_histogram=macd_histogram,
    )
    trend_state = _trend_state(
        row_count=row_count,
        close_vs_ema_percent=close_vs_ema_percent,
        slope_percent=slope_percent,
        close_change_percent=close_change_percent,
        trend_context_score=trend_context_score,
    )
    range_state = _range_state(
        row_count=row_count,
        range_width_percent=range_width_percent,
        range_position_percent=range_position_percent,
        bollinger_width_5=bollinger_width_5,
        atr_percent=atr_percent,
        trend_context_score=trend_context_score,
    )
    momentum_state = _momentum_state(
        row_count=row_count,
        momentum_3=momentum_3,
        rate_of_change_3=rate_of_change_3,
        rsi_5=rsi_5,
        macd_histogram=macd_histogram,
        momentum_context_score=momentum_context_score,
    )
    combined_context_score = _round6(mean([trend_context_score, range_context_score, momentum_context_score]))
    combined_context_state = _combined_context_state(
        trend_state=trend_state,
        range_state=range_state,
        momentum_state=momentum_state,
        combined_context_score=combined_context_score,
    )
    return TrendRangeMomentumTimeframeSummary(
        timeframe=timeframe,
        row_count=row_count,
        first_timestamp=str(candles[0].get("timestamp") or ""),
        last_timestamp=str(candles[-1].get("timestamp") or ""),
        close_first=_round6(close_first),
        close_last=_round6(close_last),
        close_change_percent=_round6(close_change_percent),
        trend_slope_5=_round6(trend_slope_5),
        trend_direction_context=_trend_direction_context(slope_percent, close_vs_ema_percent),
        range_high_5=_round6(range_high_5),
        range_low_5=_round6(range_low_5),
        range_width_5=_round6(range_width_5),
        range_width_percent=_round6(range_width_percent),
        range_position_percent=_round6(range_position_percent),
        momentum_3=_round6(momentum_3),
        rate_of_change_3=_round6(rate_of_change_3),
        rsi_5=_round6(rsi_5),
        macd_histogram=_round6(macd_histogram),
        bollinger_width_5=_round6(bollinger_width_5),
        atr_5=_round6(atr_5),
        trend_state=trend_state,
        range_state=range_state,
        momentum_state=momentum_state,
        trend_context_score=trend_context_score,
        range_context_score=range_context_score,
        momentum_context_score=momentum_context_score,
        combined_context_score=combined_context_score,
        combined_context_state=combined_context_state,
        non_executable_summary=_non_executable_summary(
            timeframe=timeframe,
            combined_context_state=combined_context_state,
            combined_context_score=combined_context_score,
        ),
    )


def build_trend_range_momentum_result(root: Path) -> TrendRangeMomentumResult:
    policy = TrendRangeMomentumPolicy()
    product_scope = _require_object(root, LOT21_OUTPUT_PATH)
    closure_snapshot = _require_object(root, LOT20_OUTPUT_PATH)
    market_analysis = _require_object(root, LOT22_OUTPUT_PATH)
    technical_indicators = _require_object(root, LOT23_OUTPUT_PATH)
    market_timeframes = load_jsonl(root / LOT22_TIMEFRAMES_OUTPUT_PATH)
    indicator_timeframes = load_jsonl(root / LOT23_TIMEFRAMES_OUTPUT_PATH)

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
    archive_checksum, archive_size_bytes = _validate_frozen_archive(
        root,
        product_scope=product_scope,
        closure_snapshot=closure_snapshot,
    )

    market_by_timeframe = {str(row.get("timeframe")): row for row in market_timeframes}
    indicator_by_timeframe = {str(row.get("timeframe")): row for row in indicator_timeframes}
    timeframe_summaries: list[TrendRangeMomentumTimeframeSummary] = []
    input_rows_by_timeframe: dict[str, int] = {}
    for timeframe in ["5m", "15m"]:
        candles = load_jsonl(root / INPUT_SPECS[timeframe]["candles"])
        input_rows_by_timeframe[timeframe] = len(candles)
        timeframe_summaries.append(
            _build_timeframe_summary(
                timeframe=timeframe,
                candles=candles,
                market_row=market_by_timeframe.get(timeframe, {}),
                indicator_row=indicator_by_timeframe.get(timeframe, {}),
            )
        )

    trend_state, trend_context_score = _aggregate_trend_state(timeframe_summaries)
    range_state, range_context_score = _aggregate_range_state(timeframe_summaries)
    momentum_state, momentum_context_score = _aggregate_momentum_state(timeframe_summaries)
    combined_context_state, combined_context_score = _aggregate_combined_state(timeframe_summaries)

    result = TrendRangeMomentumResult(
        trend_engine_version=policy.trend_engine_version,
        policy_version=policy.policy_version,
        project_name=policy.project_name,
        project_mode=policy.project_mode,
        trend_engine_mode=policy.trend_engine_mode,
        analysis_mode=policy.analysis_mode,
        indicator_mode=policy.indicator_mode,
        execution_allowed=policy.execution_allowed,
        trade_allowed=policy.trade_allowed,
        external_connectivity_allowed=policy.external_connectivity_allowed,
        live_execution=policy.live_execution,
        leverage=policy.leverage,
        source_v1_archive_frozen=policy.source_v1_archive_frozen,
        v2_scope_state=policy.v2_scope_state,
        dataset_timeframes=["5m", "15m"],
        trend_timeframes=["5m", "15m"],
        input_rows_by_timeframe=input_rows_by_timeframe,
        trend_state=trend_state,
        range_state=range_state,
        momentum_state=momentum_state,
        trend_context_score=trend_context_score,
        range_context_score=range_context_score,
        momentum_context_score=momentum_context_score,
        combined_context_score=combined_context_score,
        combined_context_state=combined_context_state,
        timeframe_summaries=timeframe_summaries,
        trend_checks=_build_trend_checks(
            product_scope=product_scope,
            market_analysis=market_analysis,
            technical_indicators=technical_indicators,
            archive_checksum=archive_checksum,
            archive_size_bytes=archive_size_bytes,
            timeframe_summaries=timeframe_summaries,
        ),
        trend_block_reasons=list(DEFAULT_TREND_BLOCK_REASONS),
        source_artifacts=default_trend_source_artifacts(),
    )
    result_payload = result.to_dict()
    return replace(result, trend_checksum=build_trend_checksum(result_payload))
