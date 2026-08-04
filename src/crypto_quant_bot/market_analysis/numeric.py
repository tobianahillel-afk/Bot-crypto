from __future__ import annotations

import math
from typing import Final

DATA_QUALITY_ERROR_CODE: Final[str] = "DATA_QUALITY_INVALID_NUMERIC"


class DataQualityError(ValueError):
    """Raised when financial input cannot be interpreted without guessing."""

    def __init__(self, field_name: str, value: object, reason: str) -> None:
        self.field_name = field_name
        self.value = value
        self.reason = reason
        super().__init__(f"{DATA_QUALITY_ERROR_CODE}:{field_name}:{reason}:{value!r}")


def require_finite_float(value: object, *, field_name: str = "numeric_value") -> float:
    """Return a finite float or fail closed.

    Booleans, strings, missing values, NaN and infinities are rejected.  The
    previous silent fallback to 0.0 could turn corrupted market data into a
    plausible price, volume or score and is therefore forbidden.
    """

    if isinstance(value, bool):
        raise DataQualityError(field_name, value, "boolean_is_not_numeric_market_data")
    if not isinstance(value, (int, float)):
        raise DataQualityError(field_name, value, "expected_int_or_float")
    result = float(value)
    if not math.isfinite(result):
        raise DataQualityError(field_name, value, "non_finite_numeric_value")
    return result
