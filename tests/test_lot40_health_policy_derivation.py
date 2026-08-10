from __future__ import annotations

from decimal import Decimal

from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector_validation import (
    derive_health_consequence,
    derive_health_status,
)


def test_health_status_derivation_is_critical_first() -> None:
    assert derive_health_status(((True, True), (False, True))) == "HEALTHY"
    assert derive_health_status(((True, True), (False, False))) == "DEGRADED"
    assert derive_health_status(((True, False), (False, True))) == "CRITICAL"
    assert derive_health_status(((True, False), (False, False))) == "CRITICAL"


def _consequence(score: str, *, critical: bool = False) -> str:
    return derive_health_consequence(
        critical_veto_active=critical,
        score=Decimal(score),
        system_threshold=Decimal("80"),
        trade_threshold=Decimal("90"),
        critical_consequence="BLOCK",
        system_consequence="PAUSE",
    )


def test_consequence_boundaries_are_exact() -> None:
    assert _consequence("100") == "NONE"
    assert _consequence("90") == "NONE"
    assert _consequence("89.999") == "WAIT"
    assert _consequence("80") == "WAIT"
    assert _consequence("79.999") == "PAUSE"
    assert _consequence("0") == "PAUSE"


def test_critical_consequence_dominates_high_score() -> None:
    assert _consequence("100", critical=True) == "BLOCK"
    assert _consequence("95", critical=True) == "BLOCK"
