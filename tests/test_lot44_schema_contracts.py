from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema import (
    build_lot44_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts/schemas"
CODE_COMMIT = "b" * 40
CLASSIFIED_TRADE_SCHEMA = SCHEMAS / "classified_trade_v1.schema.json"
CONFIDENCE_SCHEMA = SCHEMAS / "aggressor_confidence_state_v1.schema.json"
STATE_SCHEMA = SCHEMAS / "trades_aggressor_classification_schema_state_v1.schema.json"
AUDIT_SCHEMA = SCHEMAS / "trades_aggressor_classification_schema_audit_v1.schema.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _assert_required_keys(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    required = schema["required"]
    assert isinstance(required, list)
    assert set(payload) == set(required)


def test_lot44_all_output_schemas_are_closed() -> None:
    for path in (
        CLASSIFIED_TRADE_SCHEMA,
        CONFIDENCE_SCHEMA,
        STATE_SCHEMA,
        AUDIT_SCHEMA,
    ):
        schema = _load(path)
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert isinstance(schema["required"], list)
        assert schema["required"]


def test_lot44_classified_trade_contract_is_closed_and_versioned() -> None:
    schema = _load(CLASSIFIED_TRADE_SCHEMA)
    properties = schema["properties"]
    trade = properties["trade"]
    assert trade["additionalProperties"] is False
    assert trade["properties"]["schema_version"]["const"] == "timestamped-trade-v1"
    assert trade["properties"]["market_type"]["const"] == "SPOT"
    assert trade["properties"]["source_side"]["const"] == "UNKNOWN"
    assert set(properties["aggressor_classification"]["enum"]) == {
        "BUY_AGGRESSOR",
        "SELL_AGGRESSOR",
        "UNKNOWN",
    }
    assert set(properties["classification_method"]["enum"]) == {
        "QUOTE_TEST",
        "TICK_RULE",
        "NONE",
    }
    assert properties["confidence_version"]["const"] == "lot44-aggressor-confidence-v1"
    assert len(schema["allOf"]) == 4


def test_lot44_trade_numeric_patterns_match_positive_runtime_contract() -> None:
    trade = _load(CLASSIFIED_TRADE_SCHEMA)["properties"]["trade"]
    for field in ("price", "quantity"):
        pattern = trade["properties"][field]["pattern"]
        for value in ("0.0001", "0.05", "1", "50025.1"):
            assert re.fullmatch(pattern, value)
        for value in ("0", "0.0", "-1", "NaN", "Infinity", "invalid"):
            assert re.fullmatch(pattern, value) is None


def test_lot44_classification_method_implications_are_closed() -> None:
    schema = _load(CLASSIFIED_TRADE_SCHEMA)
    clauses = schema["allOf"]
    by_method = {
        clause["if"]["properties"].get("classification_method", {}).get("const"): clause
        for clause in clauses
        if "classification_method" in clause["if"]["properties"]
    }
    quote = by_method["QUOTE_TEST"]["then"]["properties"]
    tick = by_method["TICK_RULE"]["then"]["properties"]
    none = by_method["NONE"]["then"]["properties"]
    assert set(quote["aggressor_classification"]["enum"]) == {
        "BUY_AGGRESSOR",
        "SELL_AGGRESSOR",
    }
    assert quote["confidence"]["const"] == "1"
    assert set(tick["aggressor_classification"]["enum"]) == {
        "BUY_AGGRESSOR",
        "SELL_AGGRESSOR",
    }
    assert tick["confidence"]["const"] == "0.5"
    assert none["aggressor_classification"]["const"] == "UNKNOWN"
    assert none["confidence"]["const"] == "0"


def test_lot44_confidence_contract_is_descriptive_not_probability_engine() -> None:
    schema = _load(CONFIDENCE_SCHEMA)
    properties = schema["properties"]
    assert properties["schema_version"]["const"] == "aggressor-confidence-state-v1"
    assert properties["policy_version"]["const"] == "lot44-aggressor-confidence-v1"
    assert properties["semantics"]["const"] == "DESCRIPTIVE_METHOD_CONFIDENCE_NOT_PROBABILITY"
    assert properties["quote_test_confidence"]["const"] == "1"
    assert properties["tick_rule_confidence"]["const"] == "0.5"
    assert properties["unknown_confidence"]["const"] == "0"


def test_lot44_state_schema_keeps_runtime_lineage_metrics_and_safety_closed() -> None:
    schema = _load(STATE_SCHEMA)
    properties = schema["properties"]
    run_context = properties["run_context"]
    lineage = properties["lineage"]
    metrics = properties["metrics"]
    safety = schema["$defs"]["safety"]
    assert run_context["additionalProperties"] is False
    assert lineage["additionalProperties"] is False
    assert metrics["additionalProperties"] is False
    assert safety["additionalProperties"] is False
    assert run_context["properties"]["runtime_mode"]["const"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert properties["validation_state"]["const"] == "VALIDATED_OFFLINE_AGGRESSOR_CLASSIFICATION_ONLY"
    assert properties["classified_trades"]["items"]["$ref"] == "classified_trade_v1.schema.json"
    assert properties["confidence_state"]["$ref"] == "aggressor_confidence_state_v1.schema.json"
    assert properties["safety"]["$ref"] == "#/$defs/safety"
    assert safety["properties"]["trade_allowed"]["const"] is False
    assert safety["properties"]["execution_allowed"]["const"] is False
    assert safety["properties"]["approved_size"]["const"] == 0
    assert safety["properties"]["used_for_decision"]["const"] is False


def test_lot44_metric_numeric_patterns_match_runtime_bounds() -> None:
    metrics = _load(STATE_SCHEMA)["properties"]["metrics"]["properties"]
    positive = metrics["total_volume"]["pattern"]
    non_negative = metrics["unknown_volume"]["pattern"]
    ratio = metrics["unknown_volume_ratio"]["pattern"]
    assert re.fullmatch(positive, "0.16")
    assert re.fullmatch(positive, "0") is None
    assert re.fullmatch(non_negative, "0")
    assert re.fullmatch(non_negative, "0.05")
    assert re.fullmatch(non_negative, "-0.1") is None
    for value in ("0", "0.3125", "1", "1.0"):
        assert re.fullmatch(ratio, value)
    for value in ("-0.1", "1.01", "NaN", "Infinity"):
        assert re.fullmatch(ratio, value) is None


def test_lot44_audit_schema_binds_frozen_inputs_and_closed_safety() -> None:
    schema = _load(AUDIT_SCHEMA)
    properties = schema["properties"]
    assert properties["entry_gate_checksum"]["const"] == "100d21ea18cfd7d9fe275ac0bea162c76a0bb7e5f85e319b543b4053e3c4d5ef"
    assert properties["trade_fixture_checksum"]["const"] == "b07e3a6a784c801c9ae386a33a1cbe1f936901b1549d5001bc5e53e42de9e2f8"
    assert properties["order_book_snapshot_checksum"]["const"] == "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16"
    assert properties["validation_state"]["const"] == "VALIDATED_OFFLINE_AGGRESSOR_CLASSIFICATION_ONLY"
    assert properties["safety"]["$ref"] == (
        "trades_aggressor_classification_schema_state_v1.schema.json#/$defs/safety"
    )


def test_lot44_runtime_outputs_match_closed_schema_key_sets() -> None:
    state, audit = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    state_schema = _load(STATE_SCHEMA)
    audit_schema = _load(AUDIT_SCHEMA)
    trade_schema = _load(CLASSIFIED_TRADE_SCHEMA)
    confidence_schema = _load(CONFIDENCE_SCHEMA)
    _assert_required_keys(state.to_dict(), state_schema)
    _assert_required_keys(audit.to_dict(), audit_schema)
    _assert_required_keys(state.confidence_state.to_dict(), confidence_schema)
    _assert_required_keys(state.safety, state_schema["$defs"]["safety"])
    for item in state.classified_trades:
        payload = item.to_dict()
        _assert_required_keys(payload, trade_schema)
        _assert_required_keys(payload["trade"], trade_schema["properties"]["trade"])


def test_lot44_schemas_do_not_authorize_lot45_or_lot46_outputs() -> None:
    joined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            CLASSIFIED_TRADE_SCHEMA,
            CONFIDENCE_SCHEMA,
            STATE_SCHEMA,
            AUDIT_SCHEMA,
        )
    )
    assert "CVDSeriesV1" not in joined
    assert "OrderFlowDeltaCVDEngineStateV1" not in joined
    assert "TradeClassificationConfidenceEngineStateV1" not in joined
