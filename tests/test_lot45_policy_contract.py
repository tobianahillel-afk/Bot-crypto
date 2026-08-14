from __future__ import annotations

from decimal import Decimal

import pytest

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import OrderFlowPolicy
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    CALCULATION_DECIMAL_PRECISION,
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    WINDOW_POLICY_VERSION,
    Lot45ValidationError,
)


def _policy(precision: int) -> OrderFlowPolicy:
    return OrderFlowPolicy(
        precision,
        1_000_000,
        2_000_000,
        Decimal("0.5"),
        WINDOW_POLICY_VERSION,
        SESSION_POLICY_VERSION,
        POLICY_VERSION,
    )


def test_calculation_decimal_precision_is_exactly_frozen() -> None:
    assert _policy(CALCULATION_DECIMAL_PRECISION).decimal_precision == 50
    with pytest.raises(Lot45ValidationError, match="precision"):
        _policy(49)
    with pytest.raises(Lot45ValidationError, match="precision"):
        _policy(51)
