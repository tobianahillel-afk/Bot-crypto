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

__all__ = [
    "DecisionEvidenceEnvelopeV1",
    "EvidenceReferenceV1",
    "ModuleStatus",
    "SystemDecision",
    "TradingDecision",
    "UncertaintyEnvelopeV1",
    "utc_now_iso",
]
