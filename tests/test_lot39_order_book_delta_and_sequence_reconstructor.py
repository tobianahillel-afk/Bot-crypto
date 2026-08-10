from __future__ import annotations

from pathlib import Path

from crypto_quant_bot.microstructure.order_book_delta_and_sequence_reconstructor import (
    build_lot39_artifacts,
)
from crypto_quant_bot.microstructure.order_book_delta_and_sequence_reconstructor_models import (
    SUCCESS_STATE,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "e" * 40


def test_canonical_roadmap_surface_builds_synced_non_decisional_book() -> None:
    state, audit = build_lot39_artifacts(ROOT, CODE_COMMIT)
    assert state.validation_state == SUCCESS_STATE
    assert state.synchronization_state == "SYNCED"
    assert state.reconstructed_book is not None
    assert state.sequence_gap_event is None
    assert state.reconstructed_book.sequence_id == 1003
    assert state.metrics.deltas_applied_total == 2
    assert audit.reconstructed_book_checksum == state.reconstructed_book.book_checksum
    assert audit.sequence_gap_event_checksum is None
    assert state.safety["used_for_decision"] is False
    assert state.safety["trade_allowed"] is False
    assert state.safety["execution_allowed"] is False
    assert state.safety["approved_size"] == 0
    assert "LOT40_REMAINS_LOCKED" in state.reason_codes
