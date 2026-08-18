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
    parse_utc_timestamp,
    require,
    require_text,
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


@dataclass(frozen=True, slots=True)
class Lot45MarketIdentityV1:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str

    def __post_init__(self) -> None:
        require_text(self.source_id, "market identity source_id")
        require_text(self.venue, "market identity venue")
        require_text(self.instrument_id, "market identity instrument_id")
        require_text(self.market_type, "market identity market_type")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "lot45-market-identity-v1",
            "source_id": self.source_id,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_type": self.market_type,
        }


_INTERNAL_CHECKSUM_CONSTRUCTION: ContextVar[bool] = ContextVar(
    "lot45_internal_checksum_construction",
    default=False,
)
_INTERNAL_MARKET_IDENTITY: ContextVar[Lot45MarketIdentityV1 | None] = ContextVar(
    "lot45_internal_market_identity",
    default=None,
)


@contextmanager
def _internal_checksum_construction(
    market_identity: Lot45MarketIdentityV1 | None = None,
) -> Iterator[None]:
    checksum_token = _INTERNAL_CHECKSUM_CONSTRUCTION.set(True)
    identity_token = _INTERNAL_MARKET_IDENTITY.set(market_identity)
    try:
        yield
    finally:
        _INTERNAL_MARKET_IDENTITY.reset(identity_token)
        _INTERNAL_CHECKSUM_CONSTRUCTION.reset(checksum_token)


def _is_internal_construction() -> bool:
    return _INTERNAL_CHECKSUM_CONSTRUCTION.get()


def _bind_internal_identity(instance: Any) -> None:
    if getattr(instance, "market_identity", None) is None:
        identity = _INTERNAL_MARKET_IDENTITY.get()
        if identity is not None:
            object.__setattr__(instance, "market_identity", identity)


def _market_identity_payload(identity: object) -> dict[str, str] | None:
    if isinstance(identity, Lot45MarketIdentityV1):
        return identity.to_dict()
    return None


def _require_market_identity(identity: object) -> Lot45MarketIdentityV1:
    require(
        isinstance(identity, Lot45MarketIdentityV1),
        "Lot45 market_identity is required",
    )
    return identity


def _reject_completed_zero_sentinel(was_zero: bool, field: str) -> None:
    if was_zero and not _is_internal_construction():
        raise Lot45ValidationError(
            f"{field} zero sentinel forbidden at reconstruction boundary"
        )


@dataclass(frozen=True, slots=True)
class OrderFlowWindowV1(_impl.OrderFlowWindowV1):
    def __post_init__(self) -> None:
        was_zero = self.window_checksum == _ZERO_SHA256
        _impl.OrderFlowWindowV1.__post_init__(self)
        _reject_completed_zero_sentinel(was_zero, "window_checksum")


@dataclass(frozen=True, slots=True)
class OrderFlowStateV1(_impl.OrderFlowStateV1):
    market_identity: Lot45MarketIdentityV1 | None = None

    def __post_init__(self) -> None:
        _bind_internal_identity(self)
        was_zero = self.order_flow_checksum == _ZERO_SHA256
        _impl.OrderFlowStateV1.__post_init__(self)
        _require_market_identity(self.market_identity)
        _reject_completed_zero_sentinel(was_zero, "order_flow_checksum")
        if not _is_internal_construction():
            require(
                self.unknown_volume_ratio <= MAX_UNKNOWN_VOLUME_RATIO,
                "unknown volume ratio exceeds Lot45 policy limit",
            )

    def to_dict(self) -> dict[str, Any]:
        payload = _impl.OrderFlowStateV1.to_dict(self)
        payload["market_identity"] = _market_identity_payload(self.market_identity)
        return payload


@dataclass(frozen=True, slots=True)
class CVDSeriesV1(_impl.CVDSeriesV1):
    market_identity: Lot45MarketIdentityV1 | None = None

    def __post_init__(self) -> None:
        _bind_internal_identity(self)
        was_zero = self.cvd_checksum == _ZERO_SHA256
        _impl.CVDSeriesV1.__post_init__(self)
        _require_market_identity(self.market_identity)
        _reject_completed_zero_sentinel(was_zero, "cvd_checksum")

    def to_dict(self) -> dict[str, Any]:
        payload = _impl.CVDSeriesV1.to_dict(self)
        payload["market_identity"] = _market_identity_payload(self.market_identity)
        return payload


@dataclass(frozen=True, slots=True)
class OrderFlowDeltaCVDEngineStateV1(_impl.OrderFlowDeltaCVDEngineStateV1):
    def __post_init__(self) -> None:
        _impl.OrderFlowDeltaCVDEngineStateV1.__post_init__(self)
        order_flow_identity = _require_market_identity(
            getattr(self.order_flow, "market_identity", None)
        )
        cvd_identity = _require_market_identity(
            getattr(self.cvd_series, "market_identity", None)
        )
        require(
            order_flow_identity == cvd_identity,
            "Lot45 Order Flow and CVD market identities differ",
        )
        if not _is_internal_construction():
            actual_receive = parse_utc_timestamp(
                self.receive_time,
                "state receive_time",
            )
            lineage_available = parse_utc_timestamp(
                self.lineage.available_at,
                "lineage available_at",
            )
            require(
                actual_receive <= lineage_available,
                "Lot45 lineage available_at cannot precede latest source receive_time",
            )
            require(
                duration_us(self.lineage.available_at, self.generated_at)
                <= MAX_INPUT_AGE_US,
                "Lot45 lineage input age exceeds policy limit",
            )


@dataclass(frozen=True, slots=True)
class OrderFlowDeltaCVDEngineAuditV1(_impl.OrderFlowDeltaCVDEngineAuditV1):
    def __post_init__(self) -> None:
        was_zero = self.audit_checksum == _ZERO_SHA256
        _impl.OrderFlowDeltaCVDEngineAuditV1.__post_init__(self)
        _reject_completed_zero_sentinel(was_zero, "audit_checksum")


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)
