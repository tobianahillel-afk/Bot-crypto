"""Canonical Lot 39 Order Book Delta & Sequence Reconstructor surface.

The implementation lives in the focused internal module
``order_book_delta_sequence_reconstructor``. This module is the canonical
roadmap-facing import surface and contains no duplicate business logic.
"""

from .order_book_delta_sequence_reconstructor import (
    AUDIT_PATH,
    BOOK_PATH,
    CONFIG_PATH,
    GAP_EVENT_PATH,
    STATE_PATH,
    ReconstructionOutcome,
    build_lot39_artifacts,
    reconstruct_sequence,
    write_lot39_artifacts,
)

__all__ = [
    "AUDIT_PATH",
    "BOOK_PATH",
    "CONFIG_PATH",
    "GAP_EVENT_PATH",
    "STATE_PATH",
    "ReconstructionOutcome",
    "build_lot39_artifacts",
    "reconstruct_sequence",
    "write_lot39_artifacts",
]
