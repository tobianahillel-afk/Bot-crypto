"""Canonical cross-domain contracts.

This package must remain free of business-domain dependencies.
"""

from crypto_quant_bot.contracts.decision_evidence import (
    DecisionEvidenceEnvelopeV1,
    EvidenceReferenceV1,
    UncertaintyEnvelopeV1,
)
from crypto_quant_bot.contracts.primitives import (
    ModuleStatus,
    SystemDecision,
    TradingDecision,
    utc_now_iso,
)
from crypto_quant_bot.contracts.timeframe_alignment import (
    ClosedBarAvailabilityV1,
    MultiTimeframeAlignmentStateV1,
    TimeframeMarketContextStateV1,
)

__all__ = [
    "ClosedBarAvailabilityV1",
    "DecisionEvidenceEnvelopeV1",
    "EvidenceReferenceV1",
    "ModuleStatus",
    "MultiTimeframeAlignmentStateV1",
    "SystemDecision",
    "TimeframeMarketContextStateV1",
    "TradingDecision",
    "UncertaintyEnvelopeV1",
    "utc_now_iso",
]
