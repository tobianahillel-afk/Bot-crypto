from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    build_lot45_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "c" * 40


def schema(name: str) -> dict[str, object]:
    return json.loads((ROOT / "contracts/schemas" / name).read_text(encoding="utf-8"))


def test_runtime_outputs_validate_against_published_schemas() -> None:
    state, audit = build_lot45_artifacts(ROOT, code_commit=CODE_COMMIT)

    Draft202012Validator(schema("order_flow_state_v1.schema.json")).validate(state.order_flow.to_dict())
    Draft202012Validator(schema("cvd_series_v1.schema.json")).validate(state.cvd.to_dict())
    Draft202012Validator(schema("order_flow_delta_cvd_engine_state_v1.schema.json")).validate(state.to_dict())
    Draft202012Validator(schema("order_flow_delta_cvd_engine_audit_v1.schema.json")).validate(audit.to_dict())


def test_state_schema_rejects_enabled_trade_safety() -> None:
    state, _ = build_lot45_artifacts(ROOT, code_commit=CODE_COMMIT)
    payload = deepcopy(state.to_dict())
    payload["safety"]["trade_allowed"] = True

    with pytest.raises(ValidationError):
        Draft202012Validator(schema("order_flow_delta_cvd_engine_state_v1.schema.json")).validate(payload)


def test_schemas_are_closed_against_extra_properties() -> None:
    state, audit = build_lot45_artifacts(ROOT, code_commit=CODE_COMMIT)
    state_payload = state.to_dict()
    audit_payload = audit.to_dict()
    state_payload["unexpected"] = True
    audit_payload["unexpected"] = True

    with pytest.raises(ValidationError):
        Draft202012Validator(schema("order_flow_delta_cvd_engine_state_v1.schema.json")).validate(state_payload)
    with pytest.raises(ValidationError):
        Draft202012Validator(schema("order_flow_delta_cvd_engine_audit_v1.schema.json")).validate(audit_payload)
