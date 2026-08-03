from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.market_analysis.models import (
    MarketContextSnapshot,
    MarketTimeframeSummary,
)
from crypto_quant_bot.market_analysis.indicator_models import (
    IndicatorValue,
    TechnicalIndicatorResult,
    TechnicalIndicatorTimeframeSummary,
)
from crypto_quant_bot.market_analysis.trend_models import (
    TrendRangeMomentumResult,
    TrendRangeMomentumTimeframeSummary,
)
from crypto_quant_bot.market_analysis.confluence_models import (
    VolatilityRegimeConfluenceResult,
    VolatilityRegimeConfluenceTimeframeSummary,
)

MAX_JSON_BYTES = 2_000_000
MAX_JSONL_BYTES = 2_000_000
MAX_TEXT_BYTES = 1_000_000
MAX_JSONL_LINES = 2_048


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"json payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path, *, max_lines: int = MAX_JSONL_LINES) -> list[dict[str, Any]]:
    if path.stat().st_size > MAX_JSONL_BYTES:
        raise ValueError(f"jsonl payload too large: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number > max_lines:
                raise ValueError(f"too many jsonl rows in {path}")
            if line.strip():
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError(f"invalid jsonl row in {path}")
                rows.append(payload)
    return rows


def read_text_limited(path: Path, *, max_bytes: int = MAX_TEXT_BYTES) -> str:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"text payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _atomic_replace_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.stem}.{os.getpid()}.{uuid4().hex}{path.suffix}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_replace_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_timeframes_jsonl(path: Path, summaries: list[MarketTimeframeSummary]) -> None:
    lines = [json.dumps(summary.to_dict(), ensure_ascii=False, sort_keys=True) for summary in summaries]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def write_indicator_timeframes_jsonl(path: Path, summaries: list[TechnicalIndicatorTimeframeSummary]) -> None:
    lines = [json.dumps(summary.to_dict(), ensure_ascii=False, sort_keys=True) for summary in summaries]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def write_trend_timeframes_jsonl(path: Path, summaries: list[TrendRangeMomentumTimeframeSummary]) -> None:
    lines = [json.dumps(summary.to_dict(), ensure_ascii=False, sort_keys=True) for summary in summaries]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def write_vrc_timeframes_jsonl(path: Path, summaries: list[VolatilityRegimeConfluenceTimeframeSummary]) -> None:
    lines = [json.dumps(summary.to_dict(), ensure_ascii=False, sort_keys=True) for summary in summaries]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def _timeframe_section(summary: MarketTimeframeSummary) -> str:
    return (
        f"## {summary.timeframe}\n\n"
        f"row_count: {summary.row_count}\n\n"
        f"first_timestamp: {summary.first_timestamp}\n\n"
        f"last_timestamp: {summary.last_timestamp}\n\n"
        f"close_first: {summary.close_first}\n\n"
        f"close_last: {summary.close_last}\n\n"
        f"close_change_absolute: {summary.close_change_absolute}\n\n"
        f"close_change_percent: {summary.close_change_percent}\n\n"
        f"range_high: {summary.range_high}\n\n"
        f"range_low: {summary.range_low}\n\n"
        f"range_percent: {summary.range_percent}\n\n"
        f"volatility_level: {summary.volatility_level}\n\n"
        f"regime_state: {summary.regime_state}\n\n"
        f"market_state: {summary.market_state}\n\n"
        f"vwap_relation: {summary.vwap_relation}\n\n"
        f"pivot_context: {summary.pivot_context}\n\n"
        f"volume_context: {summary.volume_context}\n\n"
        f"trend_context: {summary.trend_context}\n\n"
        f"range_context: {summary.range_context}\n\n"
        f"context_score: {summary.context_score}\n\n"
        f"context_label: {summary.context_label}\n\n"
        f"non_executable_summary: {summary.non_executable_summary}\n\n"
    )


def write_market_analysis_report(path: Path, *, snapshot: MarketContextSnapshot) -> None:
    sections = "".join(_timeframe_section(summary) for summary in snapshot.timeframe_summaries)
    body = (
        "# Lot 22 Market Analysis Report\n\n"
        "Lot 22 starts the V2 Market Analysis Foundation as a local offline analysis layer only.\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"market_context_state: {snapshot.market_context_state}\n\n"
        f"market_context_score: {snapshot.market_context_score}\n\n"
        f"trend_context: {snapshot.trend_context}\n\n"
        f"volatility_context: {snapshot.volatility_context}\n\n"
        f"volume_context: {snapshot.volume_context}\n\n"
        f"range_context: {snapshot.range_context}\n\n"
        f"regime_context: {snapshot.regime_context}\n\n"
        f"confidence_context: {snapshot.confidence_context}\n\n"
        "The context score is descriptive only and never opens execution, allocation or routing.\n\n"
        + sections
    )
    _atomic_replace_text(path, body)


def write_overview_doc(path: Path, *, snapshot: MarketContextSnapshot) -> None:
    body = (
        "# Lot 22 Market Analysis\n\n"
        "Le Lot 22 demarre la V2 Market Analysis Foundation avec une couche strictement locale, offline, audit-only et non executable.\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"market_context_state: {snapshot.market_context_state}\n\n"
        f"market_context_score: {snapshot.market_context_score}\n\n"
        "Le score de contexte reste un resume descriptif et ne constitue jamais une decision ou un signal de trading.\n\n"
        "Les libelles de contexte restent non directionnels et l'archive V1 figee n'est jamais regeneree par les chaines V2.\n\n"
        "Le Lot 23 pourra enrichir cette base avec un premier pack d'indicateurs techniques locaux/offline, toujours sans execution, sans routeur d'ordre et sans connectivite externe.\n"
    )
    _atomic_replace_text(path, body)


def write_acceptance_doc(path: Path, *, snapshot: MarketContextSnapshot) -> None:
    body = (
        "# Acceptance Criteria - Lot 22\n\n"
        "Le Lot 22 est accepte si :\n\n"
        "```text\n"
        "src/crypto_quant_bot/market_analysis/__init__.py existe.\n"
        "src/crypto_quant_bot/market_analysis/models.py existe.\n"
        "src/crypto_quant_bot/market_analysis/foundation.py existe.\n"
        "src/crypto_quant_bot/market_analysis/io.py existe.\n"
        "scripts/run_lot22_market_analysis.py existe.\n"
        "scripts/validate_lot22.py existe.\n"
        "scripts/validate_all_until_lot22.py existe.\n"
        "scripts/run_required_chain_until_lot22.sh existe.\n"
        "scripts/diagnose_lot22_required_chain_timing.py existe.\n"
        "scripts/diagnose_exact_chain_until_lot22.py existe.\n"
        "data/audit/market_analysis_lot22.json existe.\n"
        "data/audit/market_analysis_timeframes_lot22.jsonl existe.\n"
        "reports/lot_22_market_analysis_report.md existe.\n"
        "reports/lot_22_validation_report.md existe.\n"
        "docs/LOT_22_MARKET_ANALYSIS.md existe.\n"
        "docs/ACCEPTANCE_CRITERIA_LOT_22.md existe.\n"
        "project_name = Crypto Quant Bot V3.1-Ops.\n"
        "project_mode = EDUCATIONAL_AUDIT_ONLY.\n"
        "analysis_mode = LOCAL_OFFLINE_ANALYSIS_ONLY.\n"
        "source_v1_archive_frozen = true.\n"
        "v2_scope_state = OPENED_AS_PLANNING_ONLY.\n"
        "execution_allowed = false.\n"
        "trade_allowed = false.\n"
        "external_connectivity_allowed = false.\n"
        "live_execution = DISABLED.\n"
        "leverage = FORBIDDEN.\n"
        "dataset_timeframes contient 5m et 15m.\n"
        "analysis_timeframes contient 5m et 15m.\n"
        "market_context_score reste borne entre 0.0 et 1.0.\n"
        "Les libelles de contexte restent non directionnels et non executables.\n"
        "LOT 22 MARKET ANALYSIS: PASS.\n"
        "LOT 22 VALIDATION: PASS.\n"
        "LOT 22 ORCHESTRATED VALIDATION: PASS.\n"
        "LOT 22 REQUIRED CHAIN: PASS.\n"
        "DIAGNOSE LOT22 REQUIRED CHAIN TIMING: PASS.\n"
        "DIAGNOSE EXACT CHAIN LOT22: PASS.\n"
        "EXACT_CHAIN_LOT22_DONE.\n"
        "rc=0.\n"
        "```\n\n"
        "Le Lot 22 reste un bloc d'analyse locale uniquement, sans ordre, sans execution, sans serveur et sans connectivite externe.\n\n"
        "Le lot suivant pourra uniquement enrichir les indicateurs techniques locaux/offline sans activer de couche executable.\n\n"
        f"market_context_state: {snapshot.market_context_state}\n\n"
        f"market_context_score: {snapshot.market_context_score}\n"
    )
    _atomic_replace_text(path, body)


def write_validation_report(path: Path, *, snapshot: MarketContextSnapshot) -> None:
    body = (
        "# Lot 22 Validation Report\n\n"
        "Status: PASS\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"market_context_state: {snapshot.market_context_state}\n\n"
        f"market_context_score: {snapshot.market_context_score}\n\n"
        f"analysis_checksum: {snapshot.analysis_checksum}\n\n"
        "Le contexte marche reste descriptif uniquement et ne declenche aucune action executable.\n"
    )
    _atomic_replace_text(path, body)


def _indicator_value_line(indicator: IndicatorValue) -> str:
    return f"- {indicator.indicator_id}: {indicator.value} ({indicator.unit}, window={indicator.window})\n"


def _indicator_section(summary: TechnicalIndicatorTimeframeSummary) -> str:
    return (
        f"## {summary.timeframe}\n\n"
        f"row_count: {summary.row_count}\n\n"
        f"first_timestamp: {summary.first_timestamp}\n\n"
        f"last_timestamp: {summary.last_timestamp}\n\n"
        f"close_last: {summary.close_last}\n\n"
        f"market_context_state: {summary.market_context_state}\n\n"
        f"market_context_score: {summary.market_context_score}\n\n"
        f"indicator_state: {summary.indicator_state}\n\n"
        f"indicator_context_score: {summary.indicator_context_score}\n\n"
        "indicator_values:\n"
        + "".join(_indicator_value_line(indicator) for indicator in summary.indicator_values)
        + f"\nnon_executable_summary: {summary.non_executable_summary}\n\n"
    )


def write_technical_indicators_report(path: Path, *, snapshot: TechnicalIndicatorResult) -> None:
    sections = "".join(_indicator_section(summary) for summary in snapshot.timeframe_summaries)
    body = (
        "# Lot 23 Technical Indicators Report\n\n"
        "Lot 23 enrichit la V2 Market Analysis avec un premier pack d'indicateurs techniques strictement local, offline et non executable.\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Indicator mode: {snapshot.indicator_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"indicator_state: {snapshot.indicator_state}\n\n"
        f"indicator_context_score: {snapshot.indicator_context_score}\n\n"
        "Les indicateurs restent descriptifs uniquement et ne declenchent jamais de routage, d'allocation ou d'execution.\n\n"
        + sections
    )
    _atomic_replace_text(path, body)


def write_indicator_overview_doc(path: Path, *, snapshot: TechnicalIndicatorResult) -> None:
    body = (
        "# Lot 23 Technical Indicators\n\n"
        "Le Lot 23 enrichit la V2 Market Analysis avec un premier pack d'indicateurs techniques strictement local, offline, audit-only et non executable.\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Indicator mode: {snapshot.indicator_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"indicator_state: {snapshot.indicator_state}\n\n"
        f"indicator_context_score: {snapshot.indicator_context_score}\n\n"
        "Les indicateurs restent descriptifs et ne produisent aucune instruction executable.\n\n"
        "Les etats techniques restent non directionnels du point de vue execution et l'archive V1 figee n'est jamais regeneree par les chaines V2.\n\n"
        "Les prochains lots pourront enrichir trend, range et momentum sans activer le trading.\n"
    )
    _atomic_replace_text(path, body)


def write_indicator_acceptance_doc(path: Path, *, snapshot: TechnicalIndicatorResult) -> None:
    indicator_lines = "".join(f"- {indicator_id}\n" for indicator_id in snapshot.indicator_set)
    body = (
        "# Acceptance Criteria - Lot 23\n\n"
        "Le Lot 23 est accepte si :\n\n"
        "```text\n"
        "src/crypto_quant_bot/market_analysis/technical_indicators.py existe.\n"
        "src/crypto_quant_bot/market_analysis/indicator_models.py existe.\n"
        "scripts/run_lot23_technical_indicators.py existe.\n"
        "scripts/validate_lot23.py existe.\n"
        "scripts/validate_all_until_lot23.py existe.\n"
        "scripts/run_required_chain_until_lot23.sh existe.\n"
        "scripts/diagnose_lot23_required_chain_timing.py existe.\n"
        "scripts/diagnose_exact_chain_until_lot23.py existe.\n"
        "data/audit/technical_indicators_lot23.json existe.\n"
        "data/audit/technical_indicators_timeframes_lot23.jsonl existe.\n"
        "reports/lot_23_technical_indicators_report.md existe.\n"
        "reports/lot_23_validation_report.md existe.\n"
        "docs/LOT_23_TECHNICAL_INDICATORS.md existe.\n"
        "docs/ACCEPTANCE_CRITERIA_LOT_23.md existe.\n"
        "project_name = Crypto Quant Bot V3.1-Ops.\n"
        "project_mode = EDUCATIONAL_AUDIT_ONLY.\n"
        "indicator_mode = LOCAL_OFFLINE_INDICATORS_ONLY.\n"
        "analysis_mode = LOCAL_OFFLINE_ANALYSIS_ONLY.\n"
        "source_v1_archive_frozen = true.\n"
        "v2_scope_state = OPENED_AS_PLANNING_ONLY.\n"
        "execution_allowed = false.\n"
        "trade_allowed = false.\n"
        "external_connectivity_allowed = false.\n"
        "live_execution = DISABLED.\n"
        "leverage = FORBIDDEN.\n"
        "dataset_timeframes contient 5m et 15m.\n"
        "indicator_timeframes contient 5m et 15m.\n"
        "indicator_context_score reste borne entre 0.0 et 1.0.\n"
        "Les etats techniques restent descriptifs et non executables.\n"
        "LOT 23 TECHNICAL INDICATORS: PASS.\n"
        "LOT 23 VALIDATION: PASS.\n"
        "LOT 23 ORCHESTRATED VALIDATION: PASS.\n"
        "LOT 23 REQUIRED CHAIN: PASS.\n"
        "DIAGNOSE LOT23 REQUIRED CHAIN TIMING: PASS.\n"
        "DIAGNOSE EXACT CHAIN LOT23: PASS.\n"
        "EXACT_CHAIN_LOT23_DONE.\n"
        "rc=0.\n"
        "```\n\n"
        "Indicator set:\n"
        f"{indicator_lines}\n"
        "Le Lot 23 reste un bloc d'indicateurs locaux uniquement, sans ordre, sans execution, sans serveur et sans connectivite externe.\n\n"
        f"indicator_state: {snapshot.indicator_state}\n\n"
        f"indicator_context_score: {snapshot.indicator_context_score}\n"
    )
    _atomic_replace_text(path, body)


def write_indicator_validation_report(path: Path, *, snapshot: TechnicalIndicatorResult) -> None:
    body = (
        "# Lot 23 Validation Report\n\n"
        "Status: PASS\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Indicator mode: {snapshot.indicator_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"indicator_state: {snapshot.indicator_state}\n\n"
        f"indicator_context_score: {snapshot.indicator_context_score}\n\n"
        f"indicator_checksum: {snapshot.indicator_checksum}\n\n"
        "Le pack d'indicateurs reste descriptif uniquement et ne declenche aucune action executable.\n"
    )
    _atomic_replace_text(path, body)


def _trend_summary_section(summary: TrendRangeMomentumTimeframeSummary) -> str:
    return (
        f"## {summary.timeframe}\n\n"
        f"row_count: {summary.row_count}\n\n"
        f"first_timestamp: {summary.first_timestamp}\n\n"
        f"last_timestamp: {summary.last_timestamp}\n\n"
        f"close_first: {summary.close_first}\n\n"
        f"close_last: {summary.close_last}\n\n"
        f"close_change_percent: {summary.close_change_percent}\n\n"
        f"trend_slope_5: {summary.trend_slope_5}\n\n"
        f"trend_direction_context: {summary.trend_direction_context}\n\n"
        f"range_high_5: {summary.range_high_5}\n\n"
        f"range_low_5: {summary.range_low_5}\n\n"
        f"range_width_5: {summary.range_width_5}\n\n"
        f"range_width_percent: {summary.range_width_percent}\n\n"
        f"range_position_percent: {summary.range_position_percent}\n\n"
        f"momentum_3: {summary.momentum_3}\n\n"
        f"rate_of_change_3: {summary.rate_of_change_3}\n\n"
        f"rsi_5: {summary.rsi_5}\n\n"
        f"macd_histogram: {summary.macd_histogram}\n\n"
        f"bollinger_width_5: {summary.bollinger_width_5}\n\n"
        f"atr_5: {summary.atr_5}\n\n"
        f"trend_state: {summary.trend_state}\n\n"
        f"range_state: {summary.range_state}\n\n"
        f"momentum_state: {summary.momentum_state}\n\n"
        f"trend_context_score: {summary.trend_context_score}\n\n"
        f"range_context_score: {summary.range_context_score}\n\n"
        f"momentum_context_score: {summary.momentum_context_score}\n\n"
        f"combined_context_score: {summary.combined_context_score}\n\n"
        f"combined_context_state: {summary.combined_context_state}\n\n"
        f"non_executable_summary: {summary.non_executable_summary}\n\n"
    )


def write_trend_range_momentum_report(path: Path, *, snapshot: TrendRangeMomentumResult) -> None:
    sections = "".join(_trend_summary_section(summary) for summary in snapshot.timeframe_summaries)
    body = (
        "# Lot 24 Trend Range Momentum Report\n\n"
        "Lot 24 enrichit la V2 Market Analysis avec un moteur Trend / Range / Momentum strictement local, offline, audit-only et non executable.\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Trend engine mode: {snapshot.trend_engine_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"Indicator mode: {snapshot.indicator_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"trend_state: {snapshot.trend_state}\n\n"
        f"range_state: {snapshot.range_state}\n\n"
        f"momentum_state: {snapshot.momentum_state}\n\n"
        f"combined_context_state: {snapshot.combined_context_state}\n\n"
        f"combined_context_score: {snapshot.combined_context_score}\n\n"
        "Les scores restent descriptifs uniquement et ne declenchent jamais de routage, d'allocation ou d'execution.\n\n"
        + sections
    )
    _atomic_replace_text(path, body)


def write_trend_overview_doc(path: Path, *, snapshot: TrendRangeMomentumResult) -> None:
    body = (
        "# Lot 24 Trend Range Momentum\n\n"
        "Le Lot 24 enrichit la V2 Market Analysis avec un moteur Trend / Range / Momentum strictement local, offline, audit-only et non executable.\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Trend engine mode: {snapshot.trend_engine_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"Indicator mode: {snapshot.indicator_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"combined_context_state: {snapshot.combined_context_state}\n\n"
        f"combined_context_score: {snapshot.combined_context_score}\n\n"
        "Les etats produits restent descriptifs et ne produisent aucune instruction executable.\n\n"
        "Les termes directionnels et les champs d'execution interdits restent exclus des sorties, et l'archive V1 figee n'est jamais regeneree par les chaines V2.\n\n"
        "Les prochains lots pourront enrichir volatility, regime et confluence sans activer le trading.\n"
    )
    _atomic_replace_text(path, body)


def write_trend_acceptance_doc(path: Path, *, snapshot: TrendRangeMomentumResult) -> None:
    body = (
        "# Acceptance Criteria - Lot 24\n\n"
        "Le Lot 24 est accepte si :\n\n"
        "```text\n"
        "src/crypto_quant_bot/market_analysis/trend_range_momentum.py existe.\n"
        "src/crypto_quant_bot/market_analysis/trend_models.py existe.\n"
        "scripts/run_lot24_trend_range_momentum.py existe.\n"
        "scripts/validate_lot24.py existe.\n"
        "scripts/validate_all_until_lot24.py existe.\n"
        "scripts/run_required_chain_until_lot24.sh existe.\n"
        "scripts/diagnose_lot24_required_chain_timing.py existe.\n"
        "scripts/diagnose_exact_chain_until_lot24.py existe.\n"
        "data/audit/trend_range_momentum_lot24.json existe.\n"
        "data/audit/trend_range_momentum_timeframes_lot24.jsonl existe.\n"
        "reports/lot_24_trend_range_momentum_report.md existe.\n"
        "reports/lot_24_validation_report.md existe.\n"
        "docs/LOT_24_TREND_RANGE_MOMENTUM.md existe.\n"
        "docs/ACCEPTANCE_CRITERIA_LOT_24.md existe.\n"
        "project_name = Crypto Quant Bot V3.1-Ops.\n"
        "project_mode = EDUCATIONAL_AUDIT_ONLY.\n"
        "trend_engine_mode = LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY.\n"
        "analysis_mode = LOCAL_OFFLINE_ANALYSIS_ONLY.\n"
        "indicator_mode = LOCAL_OFFLINE_INDICATORS_ONLY.\n"
        "source_v1_archive_frozen = true.\n"
        "v2_scope_state = OPENED_AS_PLANNING_ONLY.\n"
        "execution_allowed = false.\n"
        "trade_allowed = false.\n"
        "external_connectivity_allowed = false.\n"
        "live_execution = DISABLED.\n"
        "leverage = FORBIDDEN.\n"
        "dataset_timeframes contient 5m et 15m.\n"
        "trend_timeframes contient 5m et 15m.\n"
        "combined_context_score reste borne entre 0.0 et 1.0.\n"
        "Les etats de contexte restent descriptifs et non executables.\n"
        "LOT 24 TREND RANGE MOMENTUM: PASS.\n"
        "LOT 24 VALIDATION: PASS.\n"
        "LOT 24 ORCHESTRATED VALIDATION: PASS.\n"
        "LOT 24 REQUIRED CHAIN: PASS.\n"
        "DIAGNOSE LOT24 REQUIRED CHAIN TIMING: PASS.\n"
        "DIAGNOSE EXACT CHAIN LOT24: PASS.\n"
        "EXACT_CHAIN_LOT24_DONE.\n"
        "rc=0.\n"
        "```\n\n"
        "Le Lot 24 reste un bloc local uniquement, sans ordre, sans execution, sans serveur et sans connectivite externe.\n\n"
        f"combined_context_state: {snapshot.combined_context_state}\n\n"
        f"combined_context_score: {snapshot.combined_context_score}\n"
    )
    _atomic_replace_text(path, body)


def write_trend_validation_report(path: Path, *, snapshot: TrendRangeMomentumResult) -> None:
    body = (
        "# Lot 24 Validation Report\n\n"
        "Status: PASS\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Trend engine mode: {snapshot.trend_engine_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"Indicator mode: {snapshot.indicator_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"trend_state: {snapshot.trend_state}\n\n"
        f"range_state: {snapshot.range_state}\n\n"
        f"momentum_state: {snapshot.momentum_state}\n\n"
        f"combined_context_state: {snapshot.combined_context_state}\n\n"
        f"combined_context_score: {snapshot.combined_context_score}\n\n"
        f"trend_checksum: {snapshot.trend_checksum}\n\n"
        "Le moteur reste descriptif uniquement et ne declenche aucune action executable.\n"
    )
    _atomic_replace_text(path, body)


def _vrc_summary_section(summary: VolatilityRegimeConfluenceTimeframeSummary) -> str:
    return (
        f"## {summary.timeframe}\n\n"
        f"row_count: {summary.row_count}\n\n"
        f"first_timestamp: {summary.first_timestamp}\n\n"
        f"last_timestamp: {summary.last_timestamp}\n\n"
        f"atr_5: {summary.atr_5}\n\n"
        f"true_range_latest: {summary.true_range_latest}\n\n"
        f"bollinger_width_5: {summary.bollinger_width_5}\n\n"
        f"rolling_range_5: {summary.rolling_range_5}\n\n"
        f"range_width_percent: {summary.range_width_percent}\n\n"
        f"volatility_expansion_score: {summary.volatility_expansion_score}\n\n"
        f"volatility_compression_score: {summary.volatility_compression_score}\n\n"
        f"volatility_state: {summary.volatility_state}\n\n"
        f"volatility_context_score: {summary.volatility_context_score}\n\n"
        f"market_regime_source_state: {summary.market_regime_source_state}\n\n"
        f"trend_state: {summary.trend_state}\n\n"
        f"range_state: {summary.range_state}\n\n"
        f"momentum_state: {summary.momentum_state}\n\n"
        f"technical_indicator_state: {summary.technical_indicator_state}\n\n"
        f"regime_state: {summary.regime_state}\n\n"
        f"regime_context_score: {summary.regime_context_score}\n\n"
        f"confluence_agreement_score: {summary.confluence_agreement_score}\n\n"
        f"confluence_divergence_score: {summary.confluence_divergence_score}\n\n"
        f"confluence_state: {summary.confluence_state}\n\n"
        f"confluence_context_score: {summary.confluence_context_score}\n\n"
        f"combined_context_score: {summary.combined_context_score}\n\n"
        f"combined_context_state: {summary.combined_context_state}\n\n"
        f"confluence_components: {json.dumps(summary.confluence_components, ensure_ascii=False, sort_keys=True)}\n\n"
        f"non_executable_summary: {summary.non_executable_summary}\n\n"
    )


def write_vrc_report(path: Path, *, snapshot: VolatilityRegimeConfluenceResult) -> None:
    sections = "".join(_vrc_summary_section(summary) for summary in snapshot.timeframe_summaries)
    body = (
        "# Lot 25 Volatility Regime Confluence Report\n\n"
        "Lot 25 enrichit la V2 Market Analysis avec un moteur Volatility / Regime / Confluence strictement local, offline, audit-only et non executable.\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"VRC engine mode: {snapshot.vrc_engine_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"Indicator mode: {snapshot.indicator_mode}\n\n"
        f"Trend engine mode: {snapshot.trend_engine_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"volatility_state: {snapshot.volatility_state}\n\n"
        f"regime_state: {snapshot.regime_state}\n\n"
        f"confluence_state: {snapshot.confluence_state}\n\n"
        f"combined_context_state: {snapshot.combined_context_state}\n\n"
        f"combined_context_score: {snapshot.combined_context_score}\n\n"
        "Les scores restent descriptifs uniquement et ne declenchent jamais de routage, d'allocation ou d'execution.\n\n"
        + sections
    )
    _atomic_replace_text(path, body)


def write_vrc_overview_doc(path: Path, *, snapshot: VolatilityRegimeConfluenceResult) -> None:
    body = (
        "# Lot 25 Volatility Regime Confluence\n\n"
        "Le Lot 25 enrichit la V2 Market Analysis avec un moteur Volatility / Regime / Confluence strictement local, offline, audit-only et non executable.\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"VRC engine mode: {snapshot.vrc_engine_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"Indicator mode: {snapshot.indicator_mode}\n\n"
        f"Trend engine mode: {snapshot.trend_engine_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"combined_context_state: {snapshot.combined_context_state}\n\n"
        f"combined_context_score: {snapshot.combined_context_score}\n\n"
        "Les etats produits restent descriptifs et ne produisent aucune instruction executable.\n\n"
        "Les champs d'execution interdits restent exclus des sorties, et l'archive V1 figee n'est jamais regeneree par les chaines V2.\n\n"
        "Les prochains lots pourront enrichir l'agregation multi-timeframe et le contexte global sans activer le trading.\n"
    )
    _atomic_replace_text(path, body)


def write_vrc_acceptance_doc(path: Path, *, snapshot: VolatilityRegimeConfluenceResult) -> None:
    body = (
        "# Acceptance Criteria - Lot 25\n\n"
        "Le Lot 25 est accepte si :\n\n"
        "```text\n"
        "src/crypto_quant_bot/market_analysis/volatility_regime_confluence.py existe.\n"
        "src/crypto_quant_bot/market_analysis/confluence_models.py existe.\n"
        "scripts/run_lot25_volatility_regime_confluence.py existe.\n"
        "scripts/validate_lot25.py existe.\n"
        "scripts/validate_all_until_lot25.py existe.\n"
        "scripts/run_required_chain_until_lot25.sh existe.\n"
        "scripts/diagnose_lot25_required_chain_timing.py existe.\n"
        "scripts/diagnose_exact_chain_until_lot25.py existe.\n"
        "data/audit/volatility_regime_confluence_lot25.json existe.\n"
        "data/audit/volatility_regime_confluence_timeframes_lot25.jsonl existe.\n"
        "reports/lot_25_volatility_regime_confluence_report.md existe.\n"
        "reports/lot_25_validation_report.md existe.\n"
        "docs/LOT_25_VOLATILITY_REGIME_CONFLUENCE.md existe.\n"
        "docs/ACCEPTANCE_CRITERIA_LOT_25.md existe.\n"
        "project_name = Crypto Quant Bot V3.1-Ops.\n"
        "project_mode = EDUCATIONAL_AUDIT_ONLY.\n"
        "vrc_engine_mode = LOCAL_OFFLINE_VOLATILITY_REGIME_CONFLUENCE_ONLY.\n"
        "analysis_mode = LOCAL_OFFLINE_ANALYSIS_ONLY.\n"
        "indicator_mode = LOCAL_OFFLINE_INDICATORS_ONLY.\n"
        "trend_engine_mode = LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY.\n"
        "source_v1_archive_frozen = true.\n"
        "v2_scope_state = OPENED_AS_PLANNING_ONLY.\n"
        "execution_allowed = false.\n"
        "trade_allowed = false.\n"
        "external_connectivity_allowed = false.\n"
        "live_execution = DISABLED.\n"
        "leverage = FORBIDDEN.\n"
        "dataset_timeframes contient 5m et 15m.\n"
        "vrc_timeframes contient 5m et 15m.\n"
        "combined_context_score reste borne entre 0.0 et 1.0.\n"
        "Les etats de contexte restent descriptifs et non executables.\n"
        "LOT 25 VOLATILITY REGIME CONFLUENCE: PASS.\n"
        "LOT 25 VALIDATION: PASS.\n"
        "LOT 25 ORCHESTRATED VALIDATION: PASS.\n"
        "LOT 25 REQUIRED CHAIN: PASS.\n"
        "DIAGNOSE LOT25 REQUIRED CHAIN TIMING: PASS.\n"
        "DIAGNOSE EXACT CHAIN LOT25: PASS.\n"
        "EXACT_CHAIN_LOT25_DONE.\n"
        "rc=0.\n"
        "```\n\n"
        "Le Lot 25 reste un bloc local uniquement, sans ordre, sans execution, sans serveur et sans connectivite externe.\n\n"
        f"combined_context_state: {snapshot.combined_context_state}\n\n"
        f"combined_context_score: {snapshot.combined_context_score}\n"
    )
    _atomic_replace_text(path, body)


def write_vrc_validation_report(path: Path, *, snapshot: VolatilityRegimeConfluenceResult) -> None:
    body = (
        "# Lot 25 Validation Report\n\n"
        "Status: PASS\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"VRC engine mode: {snapshot.vrc_engine_mode}\n\n"
        f"Analysis mode: {snapshot.analysis_mode}\n\n"
        f"Indicator mode: {snapshot.indicator_mode}\n\n"
        f"Trend engine mode: {snapshot.trend_engine_mode}\n\n"
        f"source_v1_archive_frozen: {str(snapshot.source_v1_archive_frozen).lower()}\n\n"
        f"v2_scope_state: {snapshot.v2_scope_state}\n\n"
        f"volatility_state: {snapshot.volatility_state}\n\n"
        f"regime_state: {snapshot.regime_state}\n\n"
        f"confluence_state: {snapshot.confluence_state}\n\n"
        f"combined_context_state: {snapshot.combined_context_state}\n\n"
        f"combined_context_score: {snapshot.combined_context_score}\n\n"
        f"vrc_checksum: {snapshot.vrc_checksum}\n\n"
        "Le moteur reste descriptif uniquement et ne declenche aucune action executable.\n"
    )
    _atomic_replace_text(path, body)
