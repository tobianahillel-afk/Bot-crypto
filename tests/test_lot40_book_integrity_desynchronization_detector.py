from __future__ import annotations

import copy
import json
import shutil
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure import (
    BookHealthComponentV1,
    BookHealthVetoV1,
    build_lot40_artifacts,
    evaluate_book_integrity,
    write_lot40_artifacts,
)
from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector import (
    AUDIT_PATH,
    CONFIG_PATH,
    INTEGRITY_PATH,
    STATE_PATH,
    VETO_PATH,
)
from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector_validation import (
    BookIntegrityValidationError,
)

ROOT = Path(__file__).resolve().parents[1]
BOOK_PATH = ROOT / "data/audit/reconstructed_order_book_lot39.json"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _config() -> dict[str, object]:
    return _load(ROOT / CONFIG_PATH)


def _book() -> dict[str, object]:
    return _load(BOOK_PATH)


def _rechecksum(book: dict[str, object]) -> dict[str, object]:
    body = dict(book)
    body.pop("book_checksum", None)
    book["book_checksum"] = canonical_checksum(body)
    return book


def _component(state: object, name: str) -> object:
    components = getattr(state, "components")
    return next(component for component in components if component.name == name)


def test_reference_book_is_healthy_without_veto() -> None:
    integrity, veto = evaluate_book_integrity(_book(), _config())
    assert integrity.health_status == "HEALTHY"
    assert integrity.book_health_score == Decimal("100")
    assert integrity.stale_age_us == 30_000
    assert (integrity.bid_depth_levels, integrity.ask_depth_levels) == (2, 3)
    assert integrity.crossed is False
    assert integrity.locked is False
    assert integrity.checksum_valid is True
    assert integrity.level_monotonicity_valid is True
    assert all(component.passed for component in integrity.components)
    assert veto.consequence == "NONE"
    assert veto.veto_active is False
    assert veto.critical_veto_active is False


def test_freshness_failure_alone_yields_wait() -> None:
    config = _config()
    config["decision_time"] = "2026-08-06T19:18:41.100000Z"
    config["generated_at"] = "2026-08-06T19:18:41.100000Z"
    integrity, veto = evaluate_book_integrity(_book(), config)
    assert integrity.health_status == "DEGRADED"
    assert integrity.book_health_score == Decimal("85")
    assert _component(integrity, "FRESHNESS").passed is False
    assert veto.consequence == "WAIT"
    assert veto.veto_active is True
    assert veto.critical_veto_active is False


def test_depth_collapse_alone_yields_wait_at_score_80() -> None:
    book = _book()
    book["bids"] = list(book["bids"])[:1]
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, _config())
    assert integrity.health_status == "DEGRADED"
    assert integrity.book_health_score == Decimal("80")
    assert _component(integrity, "DEPTH_INTEGRITY").passed is False
    assert veto.consequence == "WAIT"
    assert veto.critical_veto_active is False


def test_freshness_plus_depth_collapse_yields_pause() -> None:
    config = _config()
    config["decision_time"] = "2026-08-06T19:18:41.100000Z"
    config["generated_at"] = "2026-08-06T19:18:41.100000Z"
    book = _book()
    book["bids"] = list(book["bids"])[:1]
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, config)
    assert integrity.health_status == "DEGRADED"
    assert integrity.book_health_score == Decimal("65")
    assert veto.consequence == "PAUSE"
    assert veto.veto_active is True
    assert veto.critical_veto_active is False


def test_monotonicity_critical_veto_blocks_even_with_score_95() -> None:
    book = _book()
    bids = list(book["bids"])
    book["bids"] = [bids[1], bids[0]]
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, _config())
    assert integrity.book_health_score == Decimal("95")
    assert integrity.health_status == "CRITICAL"
    assert _component(integrity, "LEVEL_MONOTONICITY").passed is False
    assert _component(integrity, "CROSSED_LOCKED_STATE").passed is True
    assert veto.consequence == "BLOCK"
    assert veto.critical_veto_active is True


def test_checksum_failure_is_critical_block() -> None:
    book = _book()
    bids = list(book["bids"])
    changed = dict(bids[0])
    changed["quantity"] = "9.9"
    bids[0] = changed
    book["bids"] = bids
    integrity, veto = evaluate_book_integrity(book, _config())
    assert integrity.book_health_score == Decimal("80")
    assert integrity.checksum_valid is False
    assert _component(integrity, "CHECKSUM_INTEGRITY").passed is False
    assert veto.consequence == "BLOCK"
    assert veto.critical_veto_active is True


def test_crossed_book_is_critical_block() -> None:
    book = _book()
    bids = list(book["bids"])
    changed = dict(bids[0])
    changed["price"] = "50026"
    bids[0] = changed
    book["bids"] = bids
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, _config())
    assert integrity.crossed is True
    assert integrity.locked is False
    assert integrity.health_status == "CRITICAL"
    assert _component(integrity, "CROSSED_LOCKED_STATE").passed is False
    assert veto.consequence == "BLOCK"


def test_locked_book_is_critical_block() -> None:
    book = _book()
    bids = list(book["bids"])
    asks = list(book["asks"])
    changed = dict(bids[0])
    changed["price"] = asks[0]["price"]
    bids[0] = changed
    book["bids"] = bids
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, _config())
    assert integrity.locked is True
    assert integrity.crossed is False
    assert veto.consequence == "BLOCK"
    assert veto.critical_veto_active is True


def test_sequence_discontinuity_is_critical_block() -> None:
    book = _book()
    book["applied_delta_count"] = 1
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, _config())
    assert _component(integrity, "SEQUENCE_CONTINUITY").passed is False
    assert integrity.book_health_score == Decimal("80")
    assert veto.consequence == "BLOCK"


def test_duplicate_price_level_fails_monotonicity() -> None:
    book = _book()
    bids = list(book["bids"])
    duplicate = dict(bids[1])
    duplicate["price"] = bids[0]["price"]
    bids[1] = duplicate
    book["bids"] = bids
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, _config())
    assert integrity.level_monotonicity_valid is False
    assert veto.consequence == "BLOCK"


def test_negative_quantity_is_fail_closed_as_critical_integrity() -> None:
    book = _book()
    bids = list(book["bids"])
    changed = dict(bids[0])
    changed["quantity"] = "-1"
    bids[0] = changed
    book["bids"] = bids
    _rechecksum(book)
    integrity, veto = evaluate_book_integrity(book, _config())
    assert integrity.level_monotonicity_valid is False
    assert veto.consequence == "BLOCK"


def test_future_receive_time_is_rejected_fail_closed() -> None:
    book = _book()
    book["receive_time"] = "2026-08-06T19:18:41.000000Z"
    _rechecksum(book)
    with pytest.raises(BookIntegrityValidationError, match="causal"):
        evaluate_book_integrity(book, _config())


def test_component_weights_must_total_100() -> None:
    config = _config()
    weights = dict(config["component_weights"])
    weights["FRESHNESS"] = "14"
    config["component_weights"] = weights
    with pytest.raises(BookIntegrityValidationError, match="weights must total 100"):
        evaluate_book_integrity(_book(), config)


def test_threshold_ordering_is_rejected() -> None:
    config = _config()
    config["system_health_threshold"] = "95"
    config["trade_health_threshold"] = "90"
    with pytest.raises(BookIntegrityValidationError, match="threshold ordering"):
        evaluate_book_integrity(_book(), config)


def test_unknown_config_field_is_rejected() -> None:
    config = _config()
    config["hidden_live_threshold"] = "1"
    with pytest.raises(BookIntegrityValidationError, match="config fields"):
        evaluate_book_integrity(_book(), config)


def test_component_contract_rejects_partial_score() -> None:
    with pytest.raises(BookIntegrityValidationError, match="passed weight or zero"):
        BookHealthComponentV1(
            "FRESHNESS",
            True,
            False,
            Decimal("15"),
            Decimal("14"),
            "LOT40_BOOK_FRESH",
        )


def test_veto_contract_enforces_critical_block() -> None:
    with pytest.raises(BookIntegrityValidationError, match="veto consequence"):
        BookHealthVetoV1(
            "NONE",
            False,
            True,
            Decimal("90"),
            Decimal("80"),
            "BLOCK",
            "PAUSE",
            Decimal("95"),
            ("LOT40_NO_HEALTH_VETO",),
            "0" * 64,
        )


def test_reference_build_is_deterministic() -> None:
    code_commit = "a" * 40
    state1, audit1 = build_lot40_artifacts(ROOT, code_commit)
    state2, audit2 = build_lot40_artifacts(ROOT, code_commit)
    assert state1.to_dict() == state2.to_dict()
    assert audit1.to_dict() == audit2.to_dict()
    assert state1.book_integrity.health_status == "HEALTHY"
    assert state1.book_health_veto.consequence == "NONE"
    assert state1.book_integrity.book_health_score == Decimal("100")
    assert state1.safety["trade_allowed"] is False
    assert state1.safety["execution_allowed"] is False
    assert state1.safety["approved_size"] == 0


def _copy_reference_tree(target: Path) -> None:
    paths = (
        CONFIG_PATH,
        Path("data/audit/lot40_v4_entry_gate.json"),
        Path("data/audit/roadmap_lifecycle_overlay_lot39.json"),
        Path("data/audit/order_book_delta_and_sequence_reconstructor_lot39.json"),
        Path("data/audit/order_book_delta_and_sequence_reconstructor_audit_lot39.json"),
        Path("data/audit/reconstructed_order_book_lot39.json"),
        Path("tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json"),
    )
    for relative in paths:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)


def test_atomic_persistence_writes_four_linked_artifacts(tmp_path: Path) -> None:
    _copy_reference_tree(tmp_path)
    state, audit = write_lot40_artifacts(tmp_path, "b" * 40)
    for relative in (STATE_PATH, AUDIT_PATH, INTEGRITY_PATH, VETO_PATH):
        assert (tmp_path / relative).is_file()
    persisted_state = _load(tmp_path / STATE_PATH)
    persisted_audit = _load(tmp_path / AUDIT_PATH)
    persisted_integrity = _load(tmp_path / INTEGRITY_PATH)
    persisted_veto = _load(tmp_path / VETO_PATH)
    assert persisted_state == state.to_dict()
    assert persisted_audit == audit.to_dict()
    assert persisted_integrity == state.book_integrity.to_dict()
    assert persisted_veto == state.book_health_veto.to_dict()
    assert persisted_audit["state_output_checksum"] == persisted_state["output_checksum"]
    assert persisted_audit["integrity_checksum"] == persisted_integrity["integrity_checksum"]
    assert persisted_audit["veto_checksum"] == persisted_veto["veto_checksum"]


def test_lot41_production_files_remain_absent() -> None:
    forbidden = (
        ROOT / "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine.py",
        ROOT / "scripts/run_lot41_spread_depth_and_imbalance_engine.py",
        ROOT / "scripts/validate_lot41.py",
    )
    assert all(not path.exists() for path in forbidden)
