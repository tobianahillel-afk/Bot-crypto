"""Compatibility alias for the canonical Lot 39 model module."""

import sys

from . import order_book_delta_and_sequence_reconstructor_models as _canonical

sys.modules[__name__] = _canonical
