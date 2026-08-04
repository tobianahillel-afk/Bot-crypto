"""Canonical cross-domain contracts.

This package must remain free of business-domain dependencies.
"""

from crypto_quant_bot.contracts.decision_evidence import (
    DecisionEvidenceEnvelopeV1,
    EvidenceReferenceV1,
    UncertaintyEnvelopeV1,
)

__all__ = [
    "DecisionEvidenceEnvelopeV1",
    "EvidenceReferenceV1",
    "UncertaintyEnvelopeV1",
]
