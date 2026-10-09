from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    OrderFlowPolicy,
    _build_engine_state,
    build_order_flow,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_models import (
    Lot45MarketIdentityV1,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    WINDOW_POLICY_VERSION,
    Lot45ValidationError,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (
    ClassifiedTradeV1,
    TimestampedTradeV1,
)

ROOT = Path(__file__).resolve().parents[1]


def _policy() -> OrderFlowPolicy:
    return OrderFlowPolicy(
        50,
        1_000_000,
        2_000_000,
        Decimal("0.5"),
        WINDOW_POLICY_VERSION,
        SESSION_POLICY_VERSION,
        POLICY_VERSION,
    )


def _trade(instrument_id: str) -> ClassifiedTradeV1:
    trade = TimestampedTradeV1(
        "kraken-reference-offline-fixture",
        "KRAKEN",
        instrument_id,
        "SPOT",
        "identity-binding-trade",
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06T19:18:40.110000Z",
        Decimal("50000"),
        Decimal("1"),
        "UNKNOWN",
    )
    return ClassifiedTradeV1(
        trade,
        "BUY_AGGRESSOR",
        "QUOTE_TEST",
        Decimal("1"),
        "lot44-aggressor-confidence-v1",
        "1" * 64,
        ("QUOTE_REFERENCE",),
    )


def _build(instrument_id: str):
    return build_order_flow((_trade(instrument_id),), _policy())


def _identity(instrument_id: str) -> Lot45MarketIdentityV1:
    return Lot45MarketIdentityV1(
        "kraken-reference-offline-fixture",
        "KRAKEN",
        instrument_id,
        "SPOT",
    )


def test_standalone_checksums_bind_market_identity() -> None:
    btc_flow, btc_cvd = _build("BTC-EUR-SPOT")
    eth_flow, eth_cvd = _build("ETH-EUR-SPOT")

    assert btc_flow.market_identity == _identity("BTC-EUR-SPOT")
    assert eth_flow.market_identity == _identity("ETH-EUR-SPOT")
    assert btc_cvd.market_identity == btc_flow.market_identity
    assert eth_cvd.market_identity == eth_flow.market_identity
    assert btc_flow.order_flow_checksum != eth_flow.order_flow_checksum
    assert btc_cvd.cvd_checksum != eth_cvd.cvd_checksum

    btc_flow_payload = btc_flow.to_dict()
    eth_flow_payload = eth_flow.to_dict()
    btc_flow_payload.pop("market_identity")
    eth_flow_payload.pop("market_identity")
    btc_flow_payload.pop("order_flow_checksum")
    eth_flow_payload.pop("order_flow_checksum")
    assert btc_flow_payload == eth_flow_payload

    btc_cvd_payload = btc_cvd.to_dict()
    eth_cvd_payload = eth_cvd.to_dict()
    btc_cvd_payload.pop("market_identity")
    eth_cvd_payload.pop("market_identity")
    btc_cvd_payload.pop("cvd_checksum")
    eth_cvd_payload.pop("cvd_checksum")
    assert btc_cvd_payload == eth_cvd_payload


def test_public_reconstruction_rejects_missing_market_identity() -> None:
    flow, cvd = _build("BTC-EUR-SPOT")
    with pytest.raises(Lot45ValidationError):
        replace(flow, market_identity=None)
    with pytest.raises(Lot45ValidationError):
        replace(cvd, market_identity=None)


def test_engine_state_rejects_cross_market_order_flow_and_cvd() -> None:
    btc_trade = _trade("BTC-EUR-SPOT")
    btc_flow, _ = build_order_flow((btc_trade,), _policy())
    _, eth_cvd = _build("ETH-EUR-SPOT")
    config = {
        "run_id": "lot45-market-identity-binding",
        "correlation_id": "lot45-market-identity-binding",
        "lineage_id": "lot45-from-certified-lot44-order-flow-inputs-v1",
        "generated_at": "2026-08-06T19:18:41.100000Z",
    }
    state44 = {
        "receive_time": "2026-08-06T19:18:40.110000Z",
        "generated_at": "2026-08-06T19:18:41.000000Z",
    }
    with pytest.raises(Lot45ValidationError, match="market identities differ"):
        _build_engine_state(
            config,
            "a" * 40,
            state44,
            (btc_trade,),
            btc_flow,
            eth_cvd,
        )


@pytest.mark.parametrize(
    ("schema_path", "payload_index"),
    (
        ("contracts/schemas/order_flow_state_v1.schema.json", 0),
        ("contracts/schemas/cvd_series_v1.schema.json", 1),
    ),
)
def test_published_schemas_require_market_identity(
    schema_path: str,
    payload_index: int,
) -> None:
    flow, cvd = _build("BTC-EUR-SPOT")
    payloads = (flow.to_dict(), cvd.to_dict())
    schema = json.loads((ROOT / schema_path).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    assert list(validator.iter_errors(payloads[payload_index])) == []

    without_identity = dict(payloads[payload_index])
    without_identity.pop("market_identity")
    errors = list(validator.iter_errors(without_identity))
    assert any(error.validator == "required" for error in errors)
