from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.market_analysis.foundation import (
    ANALYSIS_INVARIANTS,
    ARCHIVE_OUTPUT_PATH,
    ARCHIVE_SHA256_OUTPUT_PATH,
    DATASET_CATALOG_PATH,
    INPUT_SPECS,
    LOT20_OUTPUT_PATH,
    LOT21_FREEZE_REPORT_PATH,
    LOT21_OUTPUT_PATH,
    LOT22_OUTPUT_PATH,
    LOT22_TIMEFRAMES_OUTPUT_PATH,
)
from crypto_quant_bot.market_analysis.indicator_models import (
    ALLOWED_INDICATOR_STATES,
    DEFAULT_INDICATOR_BLOCK_REASONS,
    REQUIRED_INDICATOR_SET,
    IndicatorCheck,
    IndicatorValue,
    TechnicalIndicatorPolicy,
    TechnicalIndicatorResult,
    TechnicalIndicatorTimeframeSummary,
)
from crypto_quant_bot.market_analysis.io import load_json, load_jsonl, read_text_limited

LOT23_OUTPUT_PATH = "data/audit/technical_indicators_lot23.json"
LOT23_TIMEFRAMES_OUTPUT_PATH = "data/audit/technical_indicators_timeframes_lot23.jsonl"
LOT23_REPORT_OUTPUT_PATH = "reports/lot_23_technical_indicators_report.md"
LOT23_VALIDATION_REPORT_PATH = "reports/lot_23_validation_report.md"
LOT23_OVERVIEW_DOC_PATH = "docs/LOT_23_TECHNICAL_INDICATORS.md"
LOT23_ACCEPTANCE_DOC_PATH = "docs/ACCEPTANCE_CRITERIA_LOT_23.md"

INDICATOR_INVARIANTS = dict(ANALYSIS_INVARIANTS)
INDICATOR_INVARIANTS["analysis_mode"] = "LOCAL_OFFLINE_ANALYSIS_ONLY"


def default_indicator_source_artifacts() -> list[str]:
    candle_paths = [spec["candles"] for spec in INPUT_SPECS.values()]
    return sorted(
        {
            LOT20_OUTPUT_PATH,
            LOT21_OUTPUT_PATH,
            LOT21_FREEZE_REPORT_PATH,
            LOT22_OUTPUT_PATH,
            LOT22_TIMEFRAMES_OUTPUT_PATH,
            ARCHIVE_OUTPUT_PATH,
            ARCHIVE_SHA256_OUTPUT_PATH,
            "scripts/validate_v1_archive_frozen.py",
            *candle_paths,
        }
    )


def build_indicator_checksum(payload: dict[str, object]) -> str:
    normalized = json.loads(json.dumps(payload))

    def strip_runtime_fields(obj: object) -> object:
        if isinstance(obj, dict):
            next_obj: dict[str, object] = {}
            for key, value in obj.items():
                if key in {"created_at", "indicator_checksum"}:
                    continue
                next_obj[key] = strip_runtime_fields(value)
            return next_obj
        if isinstance(obj, list):
            return [strip_runtime_fields(item) for item in obj]
        return obj

    cleaned = strip_runtime_fields(normalized)
    if not isinstance(cleaned, dict):
        raise ValueError("indicator checksum payload must remain a mapping")
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


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def _as_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


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


def _sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return mean(values[-period:])


def _ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    multiplier = 2.0 / (period + 1.0)
    ema_value = values[0]
    series = [ema_value]
    for value in values[1:]:
        ema_value = (value - ema_value) * multiplier + ema_value
        series.append(ema_value)
    return series


def _rolling_high(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return max(values[-period:])


def _rolling_low(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return min(values[-period:])


def _rolling_range(highs: list[float], lows: list[float], period: int) -> float | None:
    high_value = _rolling_high(highs, period)
    low_value = _rolling_low(lows, period)
    if high_value is None or low_value is None:
        return None
    return high_value - low_value


def _percent_distance(base_value: float | None, reference_value: float) -> float | None:
    if base_value is None or base_value == 0:
        return None
    return ((reference_value - base_value) / base_value) * 100.0


def _rsi(values: list[float], period: int) -> float | None:
    if len(values) < period + 1:
        return None
    deltas = [values[index] - values[index - 1] for index in range(1, len(values))]
    recent = deltas[-period:]
    average_gain = sum(max(delta, 0.0) for delta in recent) / period
    average_loss = sum(max(-delta, 0.0) for delta in recent) / period
    if average_loss == 0 and average_gain == 0:
        return 50.0
    if average_loss == 0:
        return 100.0
    rs = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _bollinger(values: list[float], period: int) -> tuple[float | None, float | None, float | None, float | None]:
    if len(values) < period:
        return None, None, None, None
    sample = values[-period:]
    mid = mean(sample)
    deviation = pstdev(sample)
    upper = mid + (2.0 * deviation)
    lower = mid - (2.0 * deviation)
    width = ((upper - lower) / mid) * 100.0 if mid else 0.0
    return mid, upper, lower, width


def _true_range_series(candles: list[dict[str, Any]]) -> list[float]:
    closes = [_as_float(row.get("close")) for row in candles]
    series: list[float] = []
    for index, candle in enumerate(candles):
        high_value = _as_float(candle.get("high"))
        low_value = _as_float(candle.get("low"))
        if index == 0:
            previous_close = _as_float(candle.get("open"))
        else:
            previous_close = closes[index - 1]
        series.append(
            max(
                high_value - low_value,
                abs(high_value - previous_close),
                abs(low_value - previous_close),
            )
        )
    return series


def _atr(candles: list[dict[str, Any]], period: int) -> float | None:
    true_ranges = _true_range_series(candles)
    if len(true_ranges) < period:
        return None
    return mean(true_ranges[-period:])


def _momentum(values: list[float], period: int) -> float | None:
    if len(values) <= period:
        return None
    return values[-1] - values[-(period + 1)]


def _rate_of_change(values: list[float], period: int) -> float | None:
    if len(values) <= period:
        return None
    base_value = values[-(period + 1)]
    if base_value == 0:
        return None
    return ((values[-1] - base_value) / base_value) * 100.0


def _macd(values: list[float]) -> tuple[float | None, float | None, float | None]:
    if len(values) < 6:
        return None, None, None
    fast_series = _ema_series(values, 3)
    slow_series = _ema_series(values, 6)
    macd_series = [fast_value - slow_value for fast_value, slow_value in zip(fast_series, slow_series)]
    signal_series = _ema_series(macd_series, 3)
    if not macd_series or not signal_series:
        return None, None, None
    macd_value = macd_series[-1]
    signal_value = signal_series[-1]
    histogram = macd_value - signal_value
    return macd_value, signal_value, histogram


def _indicator_value(indicator_id: str, value: float | None, unit: str, window: int) -> IndicatorValue:
    return IndicatorValue(
        indicator_id=indicator_id,
        value=_round6(value),
        unit=unit,
        window=window,
    )


def _indicator_map(candles: list[dict[str, Any]]) -> dict[str, float | None]:
    closes = [_as_float(row.get("close")) for row in candles]
    highs = [_as_float(row.get("high")) for row in candles]
    lows = [_as_float(row.get("low")) for row in candles]
    close_last = closes[-1] if closes else 0.0

    sma_3 = _sma(closes, 3)
    sma_5 = _sma(closes, 5)
    ema_3_series = _ema_series(closes, 3)
    ema_5_series = _ema_series(closes, 5)
    ema_3 = ema_3_series[-1] if len(ema_3_series) >= 3 else None
    ema_5 = ema_5_series[-1] if len(ema_5_series) >= 5 else None
    rolling_high_5 = _rolling_high(highs, 5)
    rolling_low_5 = _rolling_low(lows, 5)
    rolling_range_5 = _rolling_range(highs, lows, 5)
    close_vs_sma_5_percent = _percent_distance(sma_5, close_last)
    close_vs_ema_5_percent = _percent_distance(ema_5, close_last)
    rsi_5 = _rsi(closes, 5)
    macd_fast_3_slow_6, macd_signal_3, macd_histogram = _macd(closes)
    bollinger_mid_5, bollinger_upper_5, bollinger_lower_5, bollinger_width_5 = _bollinger(closes, 5)
    true_range_series = _true_range_series(candles)
    true_range = true_range_series[-1] if true_range_series else None
    atr_5 = _atr(candles, 5)
    momentum_3 = _momentum(closes, 3)
    rate_of_change_3 = _rate_of_change(closes, 3)

    return {
        "sma_3": sma_3,
        "sma_5": sma_5,
        "ema_3": ema_3,
        "ema_5": ema_5,
        "rolling_high_5": rolling_high_5,
        "rolling_low_5": rolling_low_5,
        "rolling_range_5": rolling_range_5,
        "close_vs_sma_5_percent": close_vs_sma_5_percent,
        "close_vs_ema_5_percent": close_vs_ema_5_percent,
        "rsi_5": rsi_5,
        "macd_fast_3_slow_6": macd_fast_3_slow_6,
        "macd_signal_3": macd_signal_3,
        "macd_histogram": macd_histogram,
        "bollinger_mid_5": bollinger_mid_5,
        "bollinger_upper_5": bollinger_upper_5,
        "bollinger_lower_5": bollinger_lower_5,
        "bollinger_width_5": bollinger_width_5,
        "true_range": true_range,
        "atr_5": atr_5,
        "momentum_3": momentum_3,
        "rate_of_change_3": rate_of_change_3,
    }


def _indicator_units() -> dict[str, tuple[str, int]]:
    return {
        "sma_3": ("price", 3),
        "sma_5": ("price", 5),
        "ema_3": ("price", 3),
        "ema_5": ("price", 5),
        "rolling_high_5": ("price", 5),
        "rolling_low_5": ("price", 5),
        "rolling_range_5": ("price", 5),
        "close_vs_sma_5_percent": ("percent", 5),
        "close_vs_ema_5_percent": ("percent", 5),
        "rsi_5": ("oscillator", 5),
        "macd_fast_3_slow_6": ("price_delta", 6),
        "macd_signal_3": ("price_delta", 3),
        "macd_histogram": ("price_delta", 3),
        "bollinger_mid_5": ("price", 5),
        "bollinger_upper_5": ("price", 5),
        "bollinger_lower_5": ("price", 5),
        "bollinger_width_5": ("percent", 5),
        "true_range": ("price_range", 1),
        "atr_5": ("price_range", 5),
        "momentum_3": ("price_delta", 3),
        "rate_of_change_3": ("percent", 3),
    }


def _indicator_values_from_map(values: dict[str, float | None]) -> list[IndicatorValue]:
    metadata = _indicator_units()
    return [
        _indicator_value(indicator_id, values[indicator_id], metadata[indicator_id][0], metadata[indicator_id][1])
        for indicator_id in REQUIRED_INDICATOR_SET
    ]


def _indicator_context_score(values: dict[str, float | None], *, close_last: float, market_context_score: float) -> float:
    atr_percent = ((_as_float(values.get("atr_5")) / close_last) * 100.0) if close_last > 0 else 0.0
    true_range_percent = ((_as_float(values.get("true_range")) / close_last) * 100.0) if close_last > 0 else 0.0
    momentum_percent = ((_as_float(values.get("momentum_3")) / close_last) * 100.0) if close_last > 0 else 0.0
    extension_strength = max(
        _clamp(abs(_as_float(values.get("close_vs_sma_5_percent"))) / 2.5),
        _clamp(abs(_as_float(values.get("close_vs_ema_5_percent"))) / 2.5),
    )
    oscillator_strength = _clamp(abs(_as_float(values.get("rsi_5")) - 50.0) / 25.0)
    momentum_strength = max(
        _clamp(abs(momentum_percent) / 2.5),
        _clamp(abs(_as_float(values.get("rate_of_change_3"))) / 2.5),
    )
    volatility_strength = max(
        _clamp(_as_float(values.get("bollinger_width_5")) / 6.0),
        _clamp(atr_percent / 1.6),
        _clamp(true_range_percent / 1.8),
    )
    score = mean(
        [
            extension_strength,
            oscillator_strength,
            momentum_strength,
            volatility_strength,
            _clamp(market_context_score),
        ]
    )
    return round(_clamp(score), 6)


def _indicator_state(
    values: dict[str, float | None],
    *,
    row_count: int,
    close_last: float,
    indicator_context_score: float,
) -> str:
    if row_count < 6:
        return "INDICATOR_INSUFFICIENT_DATA"

    close_vs_ema = _as_float(values.get("close_vs_ema_5_percent"))
    rsi_value = _as_float(values.get("rsi_5"))
    macd_histogram = _as_float(values.get("macd_histogram"))
    rate_of_change = _as_float(values.get("rate_of_change_3"))
    bollinger_width = _as_float(values.get("bollinger_width_5"))
    atr_percent = ((_as_float(values.get("atr_5")) / close_last) * 100.0) if close_last > 0 else 0.0

    if max(bollinger_width / 6.0, atr_percent / 1.6) >= 0.8 and indicator_context_score >= 0.5:
        return "INDICATOR_VOLATILE"
    if close_vs_ema >= 0.8 and rsi_value >= 60.0 and macd_histogram > 0 and rate_of_change >= 0.5:
        return "INDICATOR_EXTENDED_UP"
    if close_vs_ema <= -0.8 and rsi_value <= 40.0 and macd_histogram < 0 and rate_of_change <= -0.5:
        return "INDICATOR_EXTENDED_DOWN"
    if bollinger_width <= 1.2 and abs(close_vs_ema) <= 0.5 and abs(rate_of_change) <= 0.6:
        return "INDICATOR_COMPRESSED"
    if indicator_context_score <= 0.3:
        return "INDICATOR_NEUTRAL"
    return "INDICATOR_MIXED"


def _aggregate_indicator_state(summaries: list[TechnicalIndicatorTimeframeSummary]) -> tuple[str, float]:
    if not summaries:
        return "INDICATOR_INSUFFICIENT_DATA", 0.0
    average_score = round(mean(summary.indicator_context_score for summary in summaries), 6)
    states = [summary.indicator_state for summary in summaries]
    if len(set(states)) == 1:
        return states[0], average_score
    if "INDICATOR_VOLATILE" in states and average_score >= 0.5:
        return "INDICATOR_VOLATILE", average_score
    if states.count("INDICATOR_COMPRESSED") == len(states):
        return "INDICATOR_COMPRESSED", average_score
    if all(state in {"INDICATOR_NEUTRAL", "INDICATOR_COMPRESSED"} for state in states):
        return "INDICATOR_NEUTRAL", average_score
    return "INDICATOR_MIXED", average_score


def _non_executable_summary(
    *,
    timeframe: str,
    indicator_state: str,
    market_context_state: str,
    indicator_context_score: float,
) -> str:
    return (
        f"{timeframe} indicator pack stays descriptive only with state {indicator_state}, "
        f"market context reference {market_context_state} and score {indicator_context_score}; "
        "execution, routing and allocation remain blocked."
    )


def _build_indicator_checks(
    *,
    product_scope: dict[str, Any],
    market_analysis: dict[str, Any],
    archive_checksum: str,
    archive_size_bytes: int,
    timeframe_summaries: list[TechnicalIndicatorTimeframeSummary],
) -> list[IndicatorCheck]:
    return [
        IndicatorCheck(
            check_name="v1_archive_frozen",
            status="PASS",
            expected_value=True,
            observed_value=product_scope.get("source_v1_archive_frozen"),
            block_reason="NO_EXECUTION_ALLOWED",
            message=f"Frozen V1 archive remains validated with checksum {archive_checksum} and size {archive_size_bytes}.",
        ),
        IndicatorCheck(
            check_name="product_scope_alignment",
            status="PASS",
            expected_value="OPENED_AS_PLANNING_ONLY",
            observed_value=product_scope.get("v2_scope_state"),
            block_reason="EDUCATIONAL_MODE_ONLY",
            message="Product scope remains planning-only and blocks any active trading implementation.",
        ),
        IndicatorCheck(
            check_name="market_analysis_alignment",
            status="PASS",
            expected_value="LOCAL_OFFLINE_ANALYSIS_ONLY",
            observed_value=market_analysis.get("analysis_mode"),
            block_reason="NO_STRATEGY_ENGINE",
            message="Lot 22 market analysis remains a local offline dependency only.",
        ),
        IndicatorCheck(
            check_name="indicator_timeframes",
            status="PASS",
            expected_value=["5m", "15m"],
            observed_value=[summary.timeframe for summary in timeframe_summaries],
            block_reason="TECHNICAL_INDICATORS_ONLY",
            message="Technical indicators are produced only for the validated local 5m and 15m timeframes.",
        ),
    ]


def _build_timeframe_summary(
    *,
    timeframe: str,
    candles: list[dict[str, Any]],
    market_row: dict[str, Any],
) -> TechnicalIndicatorTimeframeSummary:
    row_count = len(candles)
    if not candles:
        return TechnicalIndicatorTimeframeSummary(
            timeframe=timeframe,
            row_count=0,
            first_timestamp="",
            last_timestamp="",
            close_last=0.0,
            market_context_state="CONTEXT_INSUFFICIENT_DATA",
            market_context_score=0.0,
            indicator_count=len(REQUIRED_INDICATOR_SET),
            indicator_values=_indicator_values_from_map({indicator_id: None for indicator_id in REQUIRED_INDICATOR_SET}),
            indicator_state="INDICATOR_INSUFFICIENT_DATA",
            indicator_context_score=0.0,
            non_executable_summary="Insufficient local data; execution remains blocked and no decision layer is active.",
        )

    first_timestamp = str(candles[0].get("timestamp") or "")
    last_timestamp = str(candles[-1].get("timestamp") or "")
    close_last = _as_float(candles[-1].get("close"))
    values = _indicator_map(candles)
    market_context_state = str(market_row.get("context_label") or "CONTEXT_INSUFFICIENT_DATA")
    market_context_score = float(market_row.get("context_score", 0.0))
    context_score = _indicator_context_score(values, close_last=close_last, market_context_score=market_context_score)
    indicator_state = _indicator_state(values, row_count=row_count, close_last=close_last, indicator_context_score=context_score)
    indicator_values = _indicator_values_from_map(values)
    return TechnicalIndicatorTimeframeSummary(
        timeframe=timeframe,
        row_count=row_count,
        first_timestamp=first_timestamp,
        last_timestamp=last_timestamp,
        close_last=round(close_last, 6),
        market_context_state=market_context_state,
        market_context_score=round(market_context_score, 6),
        indicator_count=len(indicator_values),
        indicator_values=indicator_values,
        indicator_state=indicator_state,
        indicator_context_score=context_score,
        non_executable_summary=_non_executable_summary(
            timeframe=timeframe,
            indicator_state=indicator_state,
            market_context_state=market_context_state,
            indicator_context_score=context_score,
        ),
    )


def build_technical_indicator_result(root: Path) -> TechnicalIndicatorResult:
    policy = TechnicalIndicatorPolicy()
    product_scope = _require_object(root, LOT21_OUTPUT_PATH)
    closure_snapshot = _require_object(root, LOT20_OUTPUT_PATH)
    market_analysis = _require_object(root, LOT22_OUTPUT_PATH)
    market_timeframes = load_jsonl(root / LOT22_TIMEFRAMES_OUTPUT_PATH)

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
    archive_checksum, archive_size_bytes = _validate_frozen_archive(
        root,
        product_scope=product_scope,
        closure_snapshot=closure_snapshot,
    )

    market_by_timeframe = {str(row.get("timeframe")): row for row in market_timeframes}
    timeframe_summaries: list[TechnicalIndicatorTimeframeSummary] = []
    input_rows_by_timeframe: dict[str, int] = {}
    for timeframe in ["5m", "15m"]:
        candles = load_jsonl(root / INPUT_SPECS[timeframe]["candles"])
        input_rows_by_timeframe[timeframe] = len(candles)
        timeframe_summaries.append(
            _build_timeframe_summary(
                timeframe=timeframe,
                candles=candles,
                market_row=market_by_timeframe.get(timeframe, {}),
            )
        )

    indicator_state, indicator_context_score = _aggregate_indicator_state(timeframe_summaries)
    result = TechnicalIndicatorResult(
        indicator_version=policy.indicator_version,
        policy_version=policy.policy_version,
        project_name=policy.project_name,
        project_mode=policy.project_mode,
        indicator_mode=policy.indicator_mode,
        execution_allowed=policy.execution_allowed,
        trade_allowed=policy.trade_allowed,
        external_connectivity_allowed=policy.external_connectivity_allowed,
        live_execution=policy.live_execution,
        leverage=policy.leverage,
        source_v1_archive_frozen=policy.source_v1_archive_frozen,
        v2_scope_state=policy.v2_scope_state,
        analysis_mode=policy.analysis_mode,
        dataset_timeframes=["5m", "15m"],
        indicator_timeframes=["5m", "15m"],
        input_rows_by_timeframe=input_rows_by_timeframe,
        indicator_set=list(REQUIRED_INDICATOR_SET),
        indicator_state=indicator_state,
        indicator_context_score=indicator_context_score,
        timeframe_summaries=timeframe_summaries,
        indicator_checks=_build_indicator_checks(
            product_scope=product_scope,
            market_analysis=market_analysis,
            archive_checksum=archive_checksum,
            archive_size_bytes=archive_size_bytes,
            timeframe_summaries=timeframe_summaries,
        ),
        indicator_block_reasons=list(DEFAULT_INDICATOR_BLOCK_REASONS),
        source_artifacts=default_indicator_source_artifacts(),
    )
    result_payload = result.to_dict()
    return replace(result, indicator_checksum=build_indicator_checksum(result_payload))
