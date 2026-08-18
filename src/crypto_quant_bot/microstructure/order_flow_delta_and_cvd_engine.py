from __future__ import annotations

from typing import Any

from . import _order_flow_delta_and_cvd_engine_impl as _impl
from .order_flow_delta_and_cvd_engine_models import (
    Lot45MarketIdentityV1,
    _internal_checksum_construction,
)

CONFIG_PATH = _impl.CONFIG_PATH
STATE_PATH = _impl.STATE_PATH
AUDIT_PATH = _impl.AUDIT_PATH
ORDER_FLOW_PATH = _impl.ORDER_FLOW_PATH
CVD_PATH = _impl.CVD_PATH
EXPECTED_GATE_CHECKSUM = _impl.EXPECTED_GATE_CHECKSUM
EXPECTED_GATE_MERGE = _impl.EXPECTED_GATE_MERGE
EXPECTED_LOT44_STATE = _impl.EXPECTED_LOT44_STATE
EXPECTED_LOT44_AUDIT = _impl.EXPECTED_LOT44_AUDIT
EXPECTED_LOT44_CONFIDENCE = _impl.EXPECTED_LOT44_CONFIDENCE
EXPECTED_LOT44_CONFIG = _impl.EXPECTED_LOT44_CONFIG
EXPECTED_LOT44_POST_MERGE = _impl.EXPECTED_LOT44_POST_MERGE
ZERO_SHA256 = _impl.ZERO_SHA256
CALCULATION_DECIMAL_ROUNDING = _impl.CALCULATION_DECIMAL_ROUNDING
CODE_BOUND_PATHS = _impl.CODE_BOUND_PATHS
LOT45_REASON_CODES = _impl.LOT45_REASON_CODES
OrderFlowPolicy = _impl.OrderFlowPolicy
canonical_checksum = _impl.canonical_checksum
file_checksum = _impl.file_checksum
load_json_object = _impl.load_json_object
atomic_write_json = _impl.atomic_write_json


def _market_identity(classified_trades: tuple[Any, ...]) -> Lot45MarketIdentityV1 | None:
    if not classified_trades:
        return None
    first = classified_trades[0].trade
    return Lot45MarketIdentityV1(
        first.source_id,
        first.venue,
        first.instrument_id,
        first.market_type,
    )


def build_order_flow(classified_trades: Any, policy: OrderFlowPolicy) -> Any:
    trades = tuple(classified_trades)
    identity = _market_identity(trades)
    with _internal_checksum_construction(identity):
        return _impl.build_order_flow(trades, policy)


def _verified_lot44_inputs(root: Any, code_commit: str) -> tuple[Any, ...]:
    _impl._verify_code_tree(root, code_commit)
    config = _impl.load_json_object(root / CONFIG_PATH)
    policy = _impl._validate_config(config)
    _impl._verify_gate(root, config)
    state44, trades = _impl._verify_lot44(root, config, policy)
    return config, policy, state44, trades


def build_lot45_artifacts(root: Any, code_commit: str) -> Any:
    config, policy, state44, trades = _verified_lot44_inputs(root, code_commit)
    identity = _market_identity(trades)
    with _internal_checksum_construction(identity):
        order_flow, cvd = _impl.build_order_flow(trades, policy)
        state = _impl._build_engine_state(
            config,
            code_commit,
            state44,
            trades,
            order_flow,
            cvd,
        )
        audit = _impl._build_engine_audit(
            config,
            code_commit,
            state,
            order_flow,
            cvd,
        )
    return state.to_dict(), audit.to_dict(), order_flow.to_dict(), cvd.to_dict()


def write_lot45_artifacts(root: Any, code_commit: str) -> Any:
    state, audit, order_flow, cvd = build_lot45_artifacts(root, code_commit)
    _impl.atomic_write_json(root / STATE_PATH, state)
    _impl.atomic_write_json(root / AUDIT_PATH, audit)
    _impl.atomic_write_json(root / ORDER_FLOW_PATH, order_flow)
    _impl.atomic_write_json(root / CVD_PATH, cvd)
    return state, audit, order_flow, cvd


def _build_engine_audit(*args: Any, **kwargs: Any) -> Any:
    with _internal_checksum_construction():
        return _impl._build_engine_audit(*args, **kwargs)


_build_engine_state = _impl._build_engine_state
_verify_code_tree = _impl._verify_code_tree
_validate_config = _impl._validate_config
_verify_lot44_temporal = _impl._verify_lot44_temporal


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)
