from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/explanations/explanation_core_why_not_trade_v1.json"
GLOBAL_CONTEXT_PATH = ROOT / "data/audit/global_market_context_aggregator_lot27.json"
ALIGNMENT_PATH = ROOT / "data/audit/multi_timeframe_alignment_engine_lot26.json"
SCHEMA_PATH = ROOT / "contracts/schemas/explanation_core_why_not_trade_layer_state_v1.schema.json"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def load_config() -> dict[str, Any]:
    return load_json(CONFIG_PATH)


def load_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    return load_json(GLOBAL_CONTEXT_PATH), load_json(ALIGNMENT_PATH)


def cloned_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    global_context, alignment = load_inputs()
    return copy.deepcopy(global_context), copy.deepcopy(alignment)
