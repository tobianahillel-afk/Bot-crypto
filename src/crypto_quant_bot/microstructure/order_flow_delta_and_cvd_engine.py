from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import _order_flow_delta_and_cvd_engine_impl as _impl
from .order_flow_delta_and_cvd_engine_models import _internal_checksum_construction
from .order_flow_delta_and_cvd_engine_policy import (
    MAX_INPUT_AGE_US,
    MAX_UNKNOWN_VOLUME_RATIO,
)
from .order_flow_delta_and_cvd_engine_validation import require

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
canonical_checksum = _impl.canonical_checksum
file_checksum = _impl.file_checksum
load_json_object = _impl.load_json_object
atomic_write_json = _impl.atomic_write_json


@dataclass(frozen=True, slots=True)
class OrderFlowPolicy(_impl.OrderFlowPolicy):
    def __post_init__(self) -> None:
        super().__post_init__()
        require(
            self.max_input_age_us == MAX_INPUT_AGE_US,
            "Lot45 max input age changed",
        )
        require(
            self.max_unknown_volume_ratio == MAX_UNKNOWN_VOLUME_RATIO,
            "Lot45 max unknown-volume ratio changed",
        )


setattr(_impl, "OrderFlowPolicy", OrderFlowPolicy)


def build_order_flow(classified_trades: Any, policy: OrderFlowPolicy) -> Any:
    with _internal_checksum_construction():
        return _impl.build_order_flow(classified_trades, policy)


def build_lot45_artifacts(root: Any, code_commit: str) -> Any:
    with _internal_checksum_construction():
        return _impl.build_lot45_artifacts(root, code_commit)


def write_lot45_artifacts(root: Any, code_commit: str) -> Any:
    with _internal_checksum_construction():
        return _impl.write_lot45_artifacts(root, code_commit)


def _build_engine_audit(*args: Any, **kwargs: Any) -> Any:
    with _internal_checksum_construction():
        return _impl._build_engine_audit(*args, **kwargs)


_build_engine_state = _impl._build_engine_state
_verify_code_tree = _impl._verify_code_tree
_validate_config = _impl._validate_config
_verify_lot44_temporal = _impl._verify_lot44_temporal


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)
