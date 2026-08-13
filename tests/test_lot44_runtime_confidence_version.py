from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema import (
    build_lot44_artifacts,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_validation import (
    TradesAggressorClassificationValidationError,
)


ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "a" * 40


@pytest.mark.parametrize(
    "invalid_version",
    (
        "v2",
        "foo",
        "lot44-aggressor-confidence-v2",
    ),
)
def test_runtime_confidence_models_reject_non_v1_identifiers(
    invalid_version: str,
) -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)

    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="Lot 44 confidence policy version changed",
    ):
        replace(state.confidence_state, policy_version=invalid_version)

    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="Lot 44 classified trade confidence version changed",
    ):
        replace(
            state.classified_trades[0],
            confidence_version=invalid_version,
        )
