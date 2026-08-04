from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from statistics import mean
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.market_analysis.io import load_json, load_jsonl, read_text_limited
from crypto_quant_bot.market_analysis.models import (
    ALLOWED_CONTEXT_LABELS,
    MarketAnalysisCheck,
    MarketAnalysisInput,
    MarketAnalysisPolicy,
    MarketAnalysisResult,
    MarketContextSnapshot,
    MarketTimeframeSummary,
)
from crypto_quant_bot.market_analysis.numeric import require_finite_float

DATASET_CATALOG_PATH = "data/audit/dataset_catalog.json"
LOT20_OUTPUT_PATH = "data/audit/v1_closure_lot20.json"
LOT21_OUTPUT_PATH = "data/audit/product_scope_lot21.json"
LOT21_FREEZE_REPORT_PATH = "reports/lot_21_v1_archive_freeze_report.md"
LOT22_OUTPUT_PATH = "data/audit/market_analysis_lot22.json"
LOT22_TIMEFRAMES_OUTPUT_PATH = "data/audit/market_analysis_timeframes_lot22.jsonl"
LOT22_REPORT_OUTPUT_PATH = "reports/lot_22_market_analysis_report.md"
LOT22_VALIDATION_REPORT_PATH = "reports/lot_22_validation_report.md"
LOT22_OVERVIEW_DOC_PATH = "docs/LOT_22_MARKET_ANALYSIS.md"
LOT22_ACCEPTANCE_DOC_PATH = "docs/ACCEPTANCE_CRITERIA_LOT_22.md"
ARCHIVE_OUTPUT_PATH = "dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
ARCHIVE_SHA256_OUTPUT_PATH = "dist/crypto_quant_bot_v1_defensive_audit_lot_20.sha256"

INPUT_SPECS = {
    "5m": {
        "candles": "data/silver/btc_eur_5m_ohlcvt_lot5.jsonl",
        "lot2_features": "data/gold/btc_eur_5m_features_lot2.jsonl",
        "pivots": "data/gold/btc_eur_5m_pivots_lot3.jsonl",
        "vwap": "data/gold/btc_eur_5m_vwap_lot4.jsonl",
        "volatility": "data/gold/btc_eur_5m_volatility_lot5.jsonl",
        "regime": "data/gold/btc_eur_5m_regime_lot6.jsonl",
        "market_state": "data/gold/btc_eur_5m_market_state_lot7.jsonl",
    },
    "15m": {
        "candles": "data/silver/btc_eur_15m_ohlcvt_lot5.jsonl",
        "lot2_features": "data/gold/btc_eur_15m_features_lot2.jsonl",
        "pivots": "data/gold/btc_eur_15m_pivots_lot3.jsonl",
        "vwap": "data/gold/btc_eur_15m_vwap_lot4.jsonl",
        "volatility": "data/gold/btc_eur_15m_volatility_lot5.jsonl",
        "regime": "data/gold/btc_eur_15m_regime_lot6.jsonl",
        "market_state": "data/gold/btc_eur_15m_market_state_lot7.jsonl",
    },
}

ANALYSIS_INVARIANTS = {
    "TradingDecision": "WAIT",
    "SystemDecision": "BLOCK_TRADING",
    "final_decision": "WAIT",
    "final_system_decision": "BLOCK_TRADING",
    "trade_allowed": False,
    "execution_allowed": False,
    "Risk Engine blocks by default": True,
    "live_execution": "DISABLED",
    "leverage": "FORBIDDEN",
    "exposure_allowed": False,
    "allocation_allowed": False,
    "rebalance_allowed": False,
    "portfolio_state": "FROZEN",
    "capital_at_risk": 0,
    "external_connectivity_allowed": False,
    "human_review_required": True,
    "immutability_mode": "APPEND_ONLY_SIMULATED",
    "project_mode": "EDUCATIONAL_AUDIT_ONLY",
    "compliance_state": "COMPLIANT",
    "no_trading_state": "ENFORCED",
    "closure_state": "V1_DEFENSIVE_AUDIT_CLOSED",
    "source_v1_archive_frozen": True,
    "v2_scope_state": "OPENED_AS_PLANNING_ONLY",
}


def default_source_artifacts() -> list[str]:
    return sorted(
        {
            LOT20_OUTPUT_PATH,
            LOT21_OUTPUT_PATH,
            LOT21_FREEZE_REPORT_PATH,
            ARCHIVE_OUTPUT_PATH,
            ARCHIVE_SHA256_OUTPUT_PATH,
            "scripts/validate_v1_archive_frozen.py",
            *[path for spec in INPUT_SPECS.values() for path in spec.values()],
        }
    )


def build_analysis_checksum(payload: dict[str, object]) -> str:
    normalized = json.loads(json.dumps(payload))

    def strip_runtime_fields(obj: object) -> object:
        if isinstance(obj, dict):
            next_obj: dict[str, object] = {}
            for key, value in obj.items():
                if key in {"created_at", "analysis_checksum"}:
                    continue
                next_obj[key] = strip_runtime_fields(value)
            return next_obj
        if isinstance(obj, list):
            return [strip_runtime_fields(item) for item in obj]
        return obj

    cleaned = strip_runtime_fields(normalized)
    if not isinstance(cleaned, dict):
        raise ValueError("analysis checksum payload must remain a mapping")
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
    return max(minimum, min(maximum, value))



def _as_float(value: Any, *, field_name: str = "numeric_value") -> float:
    return require_finite_float(value, field_name=field_name)


def _round6(value: float) -> float:
    return round(float(value), 6)


def _volume_context(volume_ratio: float) -> str:
    if volume_ratio >= 1.15:
        return "ACTIVE_VOLUME"
    if volume_ratio <= 0.85:
        return "SOFT_VOLUME"
    return "BALANCED_VOLUME"


def _trend_context(close_change_percent: float) -> str:
    if close_change_percent >= 1.5:
        return "POSITIVE_DRIFT"
    if close_change_percent <= -1.5:
        return "NEGATIVE_DRIFT"
    if abs(close_change_percent) <= 0.5:
        return "BALANCED_DRIFT"
    return "TRANSITIONAL_DRIFT"


def _volatility_level(true_range_percent: float, realized_volatility: float) -> str:
    if true_range_percent >= 1.2 or realized_volatility >= 0.01:
        return "HIGH"
    if true_range_percent >= 0.6 or realized_volatility >= 0.004:
        return "MODERATE"
    return "LOW"


def _range_context(range_percent: float, close_change_percent: float, market_state_row: dict[str, Any]) -> str:
    range_state = (
        market_state_row.get("range_state", {}).get("range_state")
        if isinstance(market_state_row.get("range_state"), dict)
        else None
    )
    if isinstance(range_state, str) and range_state and range_state != "unknown":
        return range_state.upper()
    if range_percent <= 2.0 and abs(close_change_percent) <= 0.6:
        return "NARROW_BALANCE"
    if range_percent >= 5.0:
        return "WIDE_SWING"
    return "TRANSITIONAL_RANGE"


def _vwap_relation(close_last: float, vwap_value: float) -> str:
    if vwap_value <= 0:
        return "VWAP_UNAVAILABLE"
    diff_percent = ((close_last - vwap_value) / vwap_value) * 100.0
    if diff_percent >= 0.25:
        return "ABOVE_VWAP"
    if diff_percent <= -0.25:
        return "BELOW_VWAP"
    return "NEAR_VWAP"


def _pivot_context(close_last: float, pivots: list[dict[str, Any]]) -> str:
    if not pivots:
        return "NO_CONFIRMED_PIVOT_CONTEXT"
    nearest_pivot = min(pivots, key=lambda row: abs(_as_float(row.get("price")) - close_last))
    pivot_price = _as_float(nearest_pivot.get("price"))
    if close_last <= 0 or pivot_price <= 0:
        return "PIVOT_CONTEXT_UNAVAILABLE"
    distance_percent = abs(close_last - pivot_price) / close_last * 100.0
    if distance_percent <= 1.0:
        if nearest_pivot.get("side") == "high":
            return "NEAR_CONFIRMED_RESISTANCE"
        if nearest_pivot.get("side") == "low":
            return "NEAR_CONFIRMED_SUPPORT"
    return "AWAY_FROM_CONFIRMED_PIVOTS"


def _context_label(
    *,
    row_count: int,
    context_score: float,
    close_change_percent: float,
    range_percent: float,
    volatility_intensity: float,
    volume_activity: float,
    confidence_score: float,
) -> str:
    if row_count < 3:
        return "CONTEXT_INSUFFICIENT_DATA"
    if volatility_intensity >= 0.75 and context_score >= 0.55:
        return "CONTEXT_VOLATILE"
    if abs(close_change_percent) >= 1.5 and confidence_score >= 0.2:
        return "CONTEXT_TRENDING"
    if volume_activity <= 0.35 and volatility_intensity <= 0.35:
        return "CONTEXT_LOW_ACTIVITY"
    if abs(close_change_percent) <= 0.75 and range_percent <= 3.0:
        return "CONTEXT_RANGING"
    if context_score < 0.35:
        return "CONTEXT_NEUTRAL"
    return "CONTEXT_MIXED"


def _aggregate_market_context(summaries: list[MarketTimeframeSummary]) -> tuple[str, float]:
    if not summaries:
        return "CONTEXT_INSUFFICIENT_DATA", 0.0
    labels = [summary.context_label for summary in summaries]
    average_score = _round6(mean(summary.context_score for summary in summaries))
    if len(set(labels)) == 1:
        return labels[0], average_score
    if "CONTEXT_VOLATILE" in labels and average_score >= 0.55:
        return "CONTEXT_VOLATILE", average_score
    if "CONTEXT_TRENDING" in labels and average_score >= 0.45:
        return "CONTEXT_TRENDING", average_score
    if set(labels).issubset({"CONTEXT_RANGING", "CONTEXT_NEUTRAL"}):
        if "CONTEXT_RANGING" in labels:
            return "CONTEXT_RANGING", average_score
        return "CONTEXT_NEUTRAL", average_score
    return "CONTEXT_MIXED", average_score


def _format_context_by_timeframe(summaries: list[MarketTimeframeSummary], attribute: str) -> str:
    return "; ".join(f"{summary.timeframe}={getattr(summary, attribute)}" for summary in summaries)


def _confidence_context(market_state_rows: dict[str, dict[str, Any]]) -> str:
    parts: list[str] = []
    for timeframe, row in market_state_rows.items():
        regime_state = row.get("regime_state")
        if isinstance(regime_state, dict):
            score = _as_float(regime_state.get("confidence_score"))
        else:
            score = 0.0
        parts.append(f"{timeframe}={_round6(score)}")
    return "; ".join(parts)


def _make_inputs(root: Path) -> dict[str, MarketAnalysisInput]:
    inputs: dict[str, MarketAnalysisInput] = {}
    for timeframe, spec in INPUT_SPECS.items():
        candles_path = root / spec["candles"]
        row_count = len(load_jsonl(candles_path))
        inputs[timeframe] = MarketAnalysisInput(
            timeframe=timeframe,
            candles_path=spec["candles"],
            lot2_features_path=spec["lot2_features"],
            pivots_path=spec["pivots"],
            vwap_path=spec["vwap"],
            volatility_path=spec["volatility"],
            regime_path=spec["regime"],
            market_state_path=spec["market_state"],
            row_count=row_count,
        )
    return inputs


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


def _build_timeframe_summary(
    *,
    timeframe: str,
    candles: list[dict[str, Any]],
    lot2_features: list[dict[str, Any]],
    pivots: list[dict[str, Any]],
    vwap_rows: list[dict[str, Any]],
    volatility_rows: list[dict[str, Any]],
    regime_rows: list[dict[str, Any]],
    market_state_rows: list[dict[str, Any]],
) -> MarketTimeframeSummary:
    row_count = len(candles)
    if not candles:
        return MarketTimeframeSummary(
            timeframe=timeframe,
            row_count=0,
            first_timestamp="",
            last_timestamp="",
            close_first=0.0,
            close_last=0.0,
            close_change_absolute=0.0,
            close_change_percent=0.0,
            range_high=0.0,
            range_low=0.0,
            range_percent=0.0,
            volatility_level="UNAVAILABLE",
            regime_state="unknown",
            market_state="UNKNOWN",
            vwap_relation="VWAP_UNAVAILABLE",
            pivot_context="NO_CONFIRMED_PIVOT_CONTEXT",
            volume_context="SOFT_VOLUME",
            trend_context="BALANCED_DRIFT",
            range_context="TRANSITIONAL_RANGE",
            context_score=0.0,
            context_label="CONTEXT_INSUFFICIENT_DATA",
            non_executable_summary="Insufficient local data; execution remains blocked and no decision layer is active.",
        )

    first_candle = candles[0]
    last_candle = candles[-1]
    close_first = _as_float(first_candle.get("close"))
    close_last = _as_float(last_candle.get("close"))
    close_change_absolute = close_last - close_first
    close_change_percent = ((close_change_absolute / close_first) * 100.0) if close_first else 0.0
    range_high = max(_as_float(row.get("high")) for row in candles)
    range_low = min(_as_float(row.get("low")) for row in candles)
    range_percent = (((range_high - range_low) / close_first) * 100.0) if close_first else 0.0

    latest_vwap = vwap_rows[-1] if vwap_rows else {}
    latest_volatility = volatility_rows[-1] if volatility_rows else {}
    latest_regime = regime_rows[-1] if regime_rows else {}
    latest_market_state = market_state_rows[-1] if market_state_rows else {}

    latest_vwap_value = _as_float(latest_vwap.get("vwap"))
    last_volume = _as_float(last_candle.get("volume"))
    mean_volume = mean(_as_float(row.get("volume")) for row in candles) if candles else 0.0
    volume_ratio = (last_volume / mean_volume) if mean_volume else 0.0
    true_range = _as_float(latest_volatility.get("true_range"))
    true_range_percent = ((true_range / close_last) * 100.0) if close_last else 0.0
    realized_volatility = _as_float(latest_volatility.get("realized_volatility_3")) or _as_float(
        latest_volatility.get("realized_volatility_6")
    )
    regime_state = str(latest_regime.get("regime_state", "unknown"))
    market_state = str(latest_market_state.get("data_quality", {}).get("status", "unknown")).upper()
    confidence_score = _clamp(
        _as_float(latest_regime.get("confidence_score"))
        or _as_float(latest_market_state.get("regime_state", {}).get("confidence_score"))
    )

    trend_intensity = _clamp(abs(close_change_percent) / 4.0)
    range_intensity = _clamp(range_percent / 8.0)
    volatility_intensity = _clamp(max(true_range_percent / 2.0, realized_volatility * 80.0))
    volume_activity = _clamp(last_volume / (mean_volume * 1.25)) if mean_volume else 0.0
    context_score = _round6(
        (0.25 * trend_intensity)
        + (0.2 * range_intensity)
        + (0.2 * volatility_intensity)
        + (0.2 * volume_activity)
        + (0.15 * confidence_score)
    )

    trend_context = _trend_context(close_change_percent)
    volatility_level = _volatility_level(true_range_percent, realized_volatility)
    volume_context = _volume_context(volume_ratio)
    range_context = _range_context(range_percent, close_change_percent, latest_market_state)
    vwap_relation = _vwap_relation(close_last, latest_vwap_value)
    pivot_context = _pivot_context(close_last, pivots)
    context_label = _context_label(
        row_count=row_count,
        context_score=context_score,
        close_change_percent=close_change_percent,
        range_percent=range_percent,
        volatility_intensity=volatility_intensity,
        volume_activity=volume_activity,
        confidence_score=confidence_score,
    )
    if context_label not in ALLOWED_CONTEXT_LABELS:
        raise ValueError(f"invalid context_label: {context_label}")

    features_present = len(lot2_features) > 0
    non_executable_summary = (
        f"{timeframe} context remains offline and descriptive only; "
        f"lot2_reference_present={str(features_present).lower()}, "
        f"execution stays blocked and human review remains mandatory."
    )

    return MarketTimeframeSummary(
        timeframe=timeframe,
        row_count=row_count,
        first_timestamp=str(first_candle.get("timestamp", "")),
        last_timestamp=str(last_candle.get("timestamp", "")),
        close_first=_round6(close_first),
        close_last=_round6(close_last),
        close_change_absolute=_round6(close_change_absolute),
        close_change_percent=_round6(close_change_percent),
        range_high=_round6(range_high),
        range_low=_round6(range_low),
        range_percent=_round6(range_percent),
        volatility_level=volatility_level,
        regime_state=regime_state,
        market_state=market_state,
        vwap_relation=vwap_relation,
        pivot_context=pivot_context,
        volume_context=volume_context,
        trend_context=trend_context,
        range_context=range_context,
        context_score=context_score,
        context_label=context_label,
        non_executable_summary=non_executable_summary,
    )


def _build_analysis_checks(
    *,
    archive_checksum: str,
    archive_size_bytes: int,
    product_scope: dict[str, Any],
    closure_snapshot: dict[str, Any],
    inputs: dict[str, MarketAnalysisInput],
    summaries: list[MarketTimeframeSummary],
) -> list[MarketAnalysisCheck]:
    scores_bounded = all(0.0 <= summary.context_score <= 1.0 for summary in summaries)
    labels_valid = all(summary.context_label in ALLOWED_CONTEXT_LABELS for summary in summaries)
    checks = [
        MarketAnalysisCheck(
            check_name="source_v1_archive_frozen",
            status="PASS",
            expected_value=True,
            observed_value=product_scope.get("source_v1_archive_frozen"),
            block_reason="",
            message="La V2 reference uniquement l'archive V1 gelee validee au Lot 21-bis.",
        ),
        MarketAnalysisCheck(
            check_name="v1_archive_checksum_locked",
            status="PASS",
            expected_value=product_scope.get("source_v1_archive_sha256"),
            observed_value=archive_checksum,
            block_reason="",
            message="Le checksum archive observe reste identique a la preuve V1 gelee.",
        ),
        MarketAnalysisCheck(
            check_name="v1_archive_size_locked",
            status="PASS",
            expected_value=product_scope.get("source_v1_archive_size_bytes"),
            observed_value=archive_size_bytes,
            block_reason="",
            message="La taille archivee observee reste coherente avec la preuve V1 gelee.",
        ),
        MarketAnalysisCheck(
            check_name="v2_scope_state",
            status="PASS",
            expected_value="OPENED_AS_PLANNING_ONLY",
            observed_value=product_scope.get("v2_scope_state"),
            block_reason="",
            message="Le scope V2 reste planning-only pendant l'analyse marche Lot 22.",
        ),
        MarketAnalysisCheck(
            check_name="trade_execution_blocked",
            status="PASS",
            expected_value=False,
            observed_value=False,
            block_reason="",
            message="Le Lot 22 ne declenche aucune execution, allocation ou connectivite externe.",
        ),
        MarketAnalysisCheck(
            check_name="lot2_reference_rows_present",
            status="PASS",
            expected_value=True,
            observed_value=all(inputs[timeframe].row_count > 0 for timeframe in inputs),
            block_reason="",
            message="Les couches resamplees issues du lot2_resampler restent presentes via les datasets silver validates.",
        ),
        MarketAnalysisCheck(
            check_name="timeframe_rows_present",
            status="PASS",
            expected_value=True,
            observed_value=all(summary.row_count > 0 for summary in summaries),
            block_reason="",
            message="Chaque timeframe dispose de lignes locales pour l'analyse.",
        ),
        MarketAnalysisCheck(
            check_name="context_scores_bounded",
            status="PASS" if scores_bounded else "FAIL",
            expected_value="0.0<=score<=1.0",
            observed_value=scores_bounded,
            block_reason="" if scores_bounded else "INVALID_CONTEXT_SCORE",
            message="Les scores de contexte restent bornes et descriptifs.",
        ),
        MarketAnalysisCheck(
            check_name="context_labels_allowed",
            status="PASS" if labels_valid else "FAIL",
            expected_value="NON_DIRECTIONAL_ALLOWED_SET",
            observed_value=labels_valid,
            block_reason="" if labels_valid else "INVALID_CONTEXT_LABEL",
            message="Les libelles de contexte restent non directionnels et non executables.",
        ),
        MarketAnalysisCheck(
            check_name="closure_state",
            status="PASS",
            expected_value="V1_DEFENSIVE_AUDIT_CLOSED",
            observed_value=closure_snapshot.get("closure_state"),
            block_reason="",
            message="La cloture V1 defensive/audit reste la base verrouillee de l'analyse Lot 22.",
        ),
    ]
    return checks


def build_market_context_snapshot(root: Path) -> MarketContextSnapshot:
    policy = MarketAnalysisPolicy()
    product_scope = _require_object(root, LOT21_OUTPUT_PATH)
    closure_snapshot = _require_object(root, LOT20_OUTPUT_PATH)

    _require_expected_pairs(
        product_scope,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "scope_state": "FUNCTIONAL_SCOPE_LOCKED",
            "v2_scope_state": policy.v2_scope_state,
            "source_v1_archive_frozen": policy.source_v1_archive_frozen,
            "execution_allowed": policy.execution_allowed,
            "trade_allowed": policy.trade_allowed,
            "external_connectivity_allowed": policy.external_connectivity_allowed,
            "live_execution": policy.live_execution,
            "leverage": policy.leverage,
        },
        name="Lot 21 product scope snapshot",
    )
    _require_expected_pairs(
        closure_snapshot,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "closure_state": "V1_DEFENSIVE_AUDIT_CLOSED",
            "compliance_state": "COMPLIANT",
            "no_trading_state": "ENFORCED",
            "execution_allowed": policy.execution_allowed,
            "trade_allowed": policy.trade_allowed,
            "external_connectivity_allowed": policy.external_connectivity_allowed,
            "live_execution": policy.live_execution,
            "leverage": policy.leverage,
        },
        name="Lot 20 closure snapshot",
    )

    archive_checksum, archive_size_bytes = _validate_frozen_archive(
        root,
        product_scope=product_scope,
        closure_snapshot=closure_snapshot,
    )

    inputs = _make_inputs(root)
    summaries: list[MarketTimeframeSummary] = []
    market_state_index: dict[str, dict[str, Any]] = {}
    for timeframe, spec in INPUT_SPECS.items():
        candles = load_jsonl(root / spec["candles"])
        lot2_features = load_jsonl(root / spec["lot2_features"])
        pivots = load_jsonl(root / spec["pivots"])
        vwap_rows = load_jsonl(root / spec["vwap"])
        volatility_rows = load_jsonl(root / spec["volatility"])
        regime_rows = load_jsonl(root / spec["regime"])
        market_state_rows = load_jsonl(root / spec["market_state"])
        if not all(
            [
                candles,
                lot2_features,
                pivots,
                vwap_rows,
                volatility_rows,
                regime_rows,
                market_state_rows,
            ]
        ):
            raise ValueError(f"missing rows for timeframe {timeframe}")
        summary = _build_timeframe_summary(
            timeframe=timeframe,
            candles=candles,
            lot2_features=lot2_features,
            pivots=pivots,
            vwap_rows=vwap_rows,
            volatility_rows=volatility_rows,
            regime_rows=regime_rows,
            market_state_rows=market_state_rows,
        )
        summaries.append(summary)
        market_state_index[timeframe] = market_state_rows[-1]

    market_context_state, market_context_score = _aggregate_market_context(summaries)
    analysis_checks = _build_analysis_checks(
        archive_checksum=archive_checksum,
        archive_size_bytes=archive_size_bytes,
        product_scope=product_scope,
        closure_snapshot=closure_snapshot,
        inputs=inputs,
        summaries=summaries,
    )
    if any(check.status != "PASS" for check in analysis_checks):
        failing = [check.check_name for check in analysis_checks if check.status != "PASS"]
        raise ValueError(f"market analysis checks failing: {', '.join(failing)}")

    snapshot = MarketContextSnapshot(
        analysis_version=policy.analysis_version,
        policy_version=policy.policy_version,
        project_name=policy.project_name,
        project_mode=policy.project_mode,
        created_at=utc_now_iso(),
        analysis_mode=policy.analysis_mode,
        execution_allowed=policy.execution_allowed,
        trade_allowed=policy.trade_allowed,
        external_connectivity_allowed=policy.external_connectivity_allowed,
        live_execution=policy.live_execution,
        leverage=policy.leverage,
        source_v1_archive_frozen=policy.source_v1_archive_frozen,
        v2_scope_state=policy.v2_scope_state,
        dataset_timeframes=list(INPUT_SPECS.keys()),
        analysis_timeframes=list(INPUT_SPECS.keys()),
        input_rows_by_timeframe={timeframe: inputs[timeframe].row_count for timeframe in INPUT_SPECS},
        market_context_state=market_context_state,
        market_context_score=market_context_score,
        trend_context=_format_context_by_timeframe(summaries, "trend_context"),
        volatility_context=_format_context_by_timeframe(summaries, "volatility_level"),
        volume_context=_format_context_by_timeframe(summaries, "volume_context"),
        range_context=_format_context_by_timeframe(summaries, "range_context"),
        regime_context=_format_context_by_timeframe(summaries, "regime_state"),
        confidence_context=_confidence_context(market_state_index),
        analysis_block_reasons=list(policy.analysis_block_reasons),
        timeframe_summaries=summaries,
        analysis_checks=analysis_checks,
        source_artifacts=default_source_artifacts(),
        analysis_checksum="",
    )
    return replace(snapshot, analysis_checksum=build_analysis_checksum(snapshot.to_dict()))


def build_market_analysis_result(_root: Path, snapshot: MarketContextSnapshot) -> MarketAnalysisResult:
    return MarketAnalysisResult(
        analysis_version=snapshot.analysis_version,
        policy_version=snapshot.policy_version,
        project_name=snapshot.project_name,
        project_mode=snapshot.project_mode,
        analysis_mode=snapshot.analysis_mode,
        timeframe_count=len(snapshot.timeframe_summaries),
        output_paths=[
            LOT22_OUTPUT_PATH,
            LOT22_TIMEFRAMES_OUTPUT_PATH,
            LOT22_REPORT_OUTPUT_PATH,
            LOT22_VALIDATION_REPORT_PATH,
            LOT22_OVERVIEW_DOC_PATH,
            LOT22_ACCEPTANCE_DOC_PATH,
        ],
        source_artifacts=list(snapshot.source_artifacts),
        created_at=snapshot.created_at,
    )
