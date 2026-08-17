from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from . import _order_flow_delta_and_cvd_engine_models_impl as _impl
from .order_flow_delta_and_cvd_engine_policy import (
    MAX_INPUT_AGE_US,
    MAX_UNKNOWN_VOLUME_RATIO,
)
from .order_flow_delta_and_cvd_engine_validation import (
    Lot45ValidationError,
    duration_us,
    require,
)

EXPECTED_GATE_CHECKSUM = _impl.EXPECTED_GATE_CHECKSUM
EXPECTED_GATE_MERGE = _impl.EXPECTED_GATE_MERGE
EXPECTED_LOT44_STATE = _impl.EXPECTED_LOT44_STATE
EXPECTED_LOT44_AUDIT = _impl.EXPECTED_LOT44_AUDIT
EXPECTED_LOT44_CONFIDENCE = _impl.EXPECTED_LOT44_CONFIDENCE
EXPECTED_LOT44_CONFIG = _impl.EXPECTED_LOT44_CONFIG
EXPECTED_LOT44_POST_MERGE = _impl.EXPECTED_LOT44_POST_MERGE

Lot45RunContextV1 = _impl.Lot45RunContextV1
Lot45LineageEnvelopeV1 = _impl.Lot45LineageEnvelopeV1
CVDPointV1 = _impl.CVDPointV1

_ZERO_SHA256 = "0" * 64
_INTERNAL_CHECKSUM_CONSTRUCTION: ContextVar[bool] = ContextVar(
    "lot45_internal_checksum_construction",
    default=False,
)


@contextmanager
def _internal_checksum_construction() -> Iterator[None]:
    token = _INTERNAL_CHECKSUM_CONSTRUCTION.set(True)
    try:
        yield
    finally:
        _INTERNAL_CHECKSUM_CONSTRUCTION.reset(token)


def _is_internal_construction() -> bool:
    return _INTERNAL_CHECKSUM_CONSTRUCTION.get()


def _reject_completed_zero_sentinel(was_zero: bool, field: str) -> None:
    if was_zero and not _is_internal_construction():
        raise Lot45ValidationError(
            f"{field} zero sentinel forbidden at reconstruction boundary"
        )


@dataclass(frozen=True, slots=True)
class OrderFlowWindowV1(_impl.OrderFlowWindowV1):
    def __post_init__(self) -> None:
        was_zero = self.window_checksum == _ZERO_SHA256
        super().__post_init__()
        _reject_completed_zero_sentinel(was_zero, "window_checksum")


@dataclass(frozen=True, slots=True)
class OrderFlowStateV1(_impl.OrderFlowStateV1):
    def __post_init__(self) -> None:
        was_zero = self.order_flow_checksum == _ZERO_SHA256
        super().__post_init__()
        _reject_completed_zero_sentinel(was_zero, "order_flow_checksum")
        if not _is_internal_construction():
            require(
                self.unknown_volume_ratio <= MAX_UNKNOWN_VOLUME_RATIO,
                "unknown volume ratio exceeds Lot45 policy limit",
            )


@dataclass(frozen=True, slots=True)
class CVDSeriesV1(_impl.CVDSeriesV1):
    def __post_init__(self) -> None:
        was_zero = self.cvd_checksum == _ZERO_SHA256
        super().__post_init__()
        _reject_completed_zero_sentinel(was_zero, "cvd_checksum")


@dataclass(frozen=True, slots=True)
class OrderFlowDeltaCVDEngineStateV1(_impl.OrderFlowDeltaCVDEngineStateV1):
    def __post_init__(self) -> None:
        super().__post_init__()
        if not _is_internal_construction():
            require(
                duration_us(self.lineage.available_at, self.generated_at)
                <= MAX_INPUT_AGE_US,
                "Lot45 lineage input age exceeds policy limit",
            )


@dataclass(frozen=True, slots=True)
class OrderFlowDeltaCVDEngineAuditV1(_impl.OrderFlowDeltaCVDEngineAuditV1):
    def __post_init__(self) -> None:
        was_zero = self.audit_checksum == _ZERO_SHA256
        super().__post_init__()
        _reject_completed_zero_sentinel(was_zero, "audit_checksum")


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)
