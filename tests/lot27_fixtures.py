from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/math/global_market_context_aggregator_v1.json"
SOURCE_PATHS = {
    "lot22_market_analysis": ROOT / "data/audit/market_analysis_lot22.json",
    "lot23_technical_indicators": ROOT / "data/audit/technical_indicators_lot23.json",
    "lot24_trend_range_momentum": ROOT / "data/audit/trend_range_momentum_lot24.json",
    "lot25_volatility_regime_confluence": ROOT / "data/audit/volatility_regime_confluence_lot25.json",
    "lot26_multi_timeframe_alignment": ROOT / "data/audit/multi_timeframe_alignment_engine_lot26.json",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def load_config() -> dict[str, Any]:
    return load_json(CONFIG_PATH)


def load_sources() -> dict[str, dict[str, Any]]:
    return {source_id: load_json(path) for source_id, path in SOURCE_PATHS.items()}


def cloned_sources() -> dict[str, dict[str, Any]]:
    return copy.deepcopy(load_sources())
