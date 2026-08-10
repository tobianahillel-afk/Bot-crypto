from __future__ import annotations

import json
from pathlib import Path

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure import evaluate_book_integrity
from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector import CONFIG_PATH

ROOT = Path(__file__).resolve().parents[1]
BOOK_PATH = ROOT / "data/audit/reconstructed_order_book_lot39.json"


def _load(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _book() -> dict[str, object]:
    return _load(BOOK_PATH)


def _config() -> dict[str, object]:
    return _load(ROOT / CONFIG_PATH)


def _rechecksum(book: dict[str, object]) -> None:
    body = dict(book)
    body.pop("book_checksum", None)
    book["book_checksum"] = canonical_checksum(body)


def test_numeric_price_is_not_silently_coerced() -> None:
    book = _book()
    bids = list(book["bids"])
    changed = dict(bids[0])
    changed["price"] = 50024.9
    bids[0] = changed
    book["bids"] = bids
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, _config())
    assert integrity.level_monotonicity_valid is False
    assert integrity.health_status == "CRITICAL"
    assert veto.consequence == "BLOCK"


def test_numeric_quantity_is_not_silently_coerced() -> None:
    book = _book()
    asks = list(book["asks"])
    changed = dict(asks[0])
    changed["quantity"] = 0.65
    asks[0] = changed
    book["asks"] = asks
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, _config())
    assert integrity.level_monotonicity_valid is False
    assert integrity.health_status == "CRITICAL"
    assert veto.consequence == "BLOCK"


def test_zero_quantity_level_is_invalid_after_lot39_deletion_semantics() -> None:
    book = _book()
    asks = list(book["asks"])
    changed = dict(asks[0])
    changed["quantity"] = "0"
    asks[0] = changed
    book["asks"] = asks
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, _config())
    assert integrity.level_monotonicity_valid is False
    assert integrity.health_status == "CRITICAL"
    assert veto.consequence == "BLOCK"
