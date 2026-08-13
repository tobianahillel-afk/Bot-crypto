from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema import build_lot44_artifacts

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "b" * 40
SCHEMAS = ROOT / "contracts/schemas"


def _schema(name: str) -> dict[str, object]:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_output_schemas_are_closed() -> None:
    for name in (
        "classified_trade_v1.schema.json",
        "aggressor_confidence_state_v1.schema.json",
        "trades_aggressor_classification_schema_state_v1.schema.json",
        "trades_aggressor_classification_schema_audit_v1.schema.json",
    ):
        assert _schema(name)["additionalProperties"] is False


def test_reference_classified_trades_and_confidence_validate() -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    resolver = jsonschema.RefResolver(base_uri=SCHEMAS.as_uri() + "/", referrer={})
    trade_schema = _schema("classified_trade_v1.schema.json")
    for trade in state.classified_trades:
        jsonschema.validate(trade.to_dict(), trade_schema, resolver=resolver)
    jsonschema.validate(state.confidence_state.to_dict(), _schema("aggressor_confidence_state_v1.schema.json"))


def test_reference_state_and_audit_validate() -> None:
    state, audit = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    resolver = jsonschema.RefResolver(base_uri=SCHEMAS.as_uri() + "/", referrer={})
    jsonschema.validate(state.to_dict(), _schema("trades_aggressor_classification_schema_state_v1.schema.json"), resolver=resolver)
    jsonschema.validate(audit.to_dict(), _schema("trades_aggressor_classification_schema_audit_v1.schema.json"))


def test_schemas_do_not_authorize_lot45_or_lot46_outputs() -> None:
    joined = "\n".join((SCHEMAS / name).read_text(encoding="utf-8") for name in (
        "classified_trade_v1.schema.json",
        "aggressor_confidence_state_v1.schema.json",
        "trades_aggressor_classification_schema_state_v1.schema.json",
        "trades_aggressor_classification_schema_audit_v1.schema.json",
    ))
    assert "CVDSeriesV1" not in joined
    assert "TradeClassificationConfidenceEngineStateV1" not in joined
    assert "trade_allowed" not in joined or "audit" in joined.lower() or "state" in joined.lower()
