from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

import crypto_quant_bot.microstructure.order_book_delta_and_sequence_reconstructor as engine
from crypto_quant_bot.microstructure.order_book_delta_and_sequence_reconstructor_models import (
    Lot39RunContextV1,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_validation import (
    OrderBookDeltaSequenceValidationError,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "2" * 40


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_lot38_snapshot_json_model_round_trip_is_exact() -> None:
    payload = _load(ROOT / "data/audit/order_book_snapshot_lot38.json")
    snapshot = engine._snapshot_from_payload(payload)
    assert snapshot.to_dict() == payload


def test_delta_fixture_records_json_model_round_trip_are_exact() -> None:
    fixture = _load(ROOT / "tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json")
    raw_deltas = fixture["deltas"]
    assert isinstance(raw_deltas, list)
    assert len(raw_deltas) == 2
    for raw in raw_deltas:
        assert isinstance(raw, dict)
        delta = engine._delta_from_payload(raw)
        assert delta.to_dict() == raw


def test_verified_lot38_snapshot_matches_frozen_artifact_exactly() -> None:
    config = _load(ROOT / engine.CONFIG_PATH)
    expected = _load(ROOT / "data/audit/order_book_snapshot_lot38.json")
    snapshot = engine._verify_lot38(ROOT, config)
    assert snapshot.to_dict() == expected
    assert snapshot.snapshot_checksum == engine.EXPECTED_LOT38_SNAPSHOT
    assert snapshot.sequence_id == 1001
    assert snapshot.event_time == "2026-08-06T19:18:40.000000Z"
    assert snapshot.receive_time == "2026-08-06T19:18:40.050000Z"


def test_sequence_anchor_binds_exact_base_sequence_and_event_time() -> None:
    config = _load(ROOT / engine.CONFIG_PATH)
    snapshot = engine._verify_lot38(ROOT, config)
    assert engine._sequence_anchor(
        snapshot,
        1003,
        "2026-08-06T19:18:40.065000Z",
    ) == "13ccdc94cac0f5408b1494e8bbb4e1b76d5532f7adbad5f4976a1d9266af6396"
    assert engine._sequence_anchor(
        snapshot,
        1002,
        "2026-08-06T19:18:40.055000Z",
    ) != engine._sequence_anchor(
        snapshot,
        1003,
        "2026-08-06T19:18:40.065000Z",
    )


def test_built_context_and_lineage_bind_every_expected_identifier() -> None:
    state, audit = engine.build_lot39_artifacts(ROOT, CODE_COMMIT)
    assert state.run_context.to_dict() == {
        "schema_version": "lot39-run-context-v1",
        "run_id": "lot39-reference-run-001",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "config_version": "lot39-order-book-delta-sequence-config-v1",
        "code_commit": CODE_COMMIT,
        "correlation_id": "lot39-reference-correlation-001",
    }
    assert state.lineage.entry_gate_checksum == engine.EXPECTED_GATE_CHECKSUM
    assert state.lineage.lot38_state_checksum == engine.EXPECTED_LOT38_STATE
    assert state.lineage.lot38_audit_checksum == engine.EXPECTED_LOT38_AUDIT
    assert state.lineage.lot38_snapshot_checksum == engine.EXPECTED_LOT38_SNAPSHOT
    assert state.lineage.lot38_health_checksum == engine.EXPECTED_LOT38_HEALTH
    assert state.lineage.delta_fixture_checksum == state.delta_fixture_checksum
    assert audit.code_commit == CODE_COMMIT
    assert audit.entry_gate_checksum == engine.EXPECTED_GATE_CHECKSUM


def test_lot38_lifecycle_and_health_are_strictly_fail_closed() -> None:
    overlay = _load(ROOT / "data/audit/roadmap_lifecycle_overlay_lot38.json")
    bad_overlay = json.loads(json.dumps(overlay))
    bad_overlay["latest_implemented_lot"] = 39
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="latest lot 38"):
        engine._verify_lot38_lifecycle(bad_overlay)

    health = _load(ROOT / "data/audit/book_health_state_lot38.json")
    bad_health = dict(health)
    bad_health["sequence_present"] = False
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="healthy sequenced"):
        engine._verify_lot38_health(bad_health)

    bad_health = dict(health)
    bad_health["locked"] = True
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="open and uncrossed"):
        engine._verify_lot38_health(bad_health)


def test_fixture_identity_flags_are_all_mandatory() -> None:
    fixture = _load(ROOT / "tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json")
    for field, bad_value in (
        ("fixture_only", False),
        ("canonical_contract_records", False),
        ("used_for_decision", True),
    ):
        tampered = dict(fixture)
        tampered[field] = bad_value
        with pytest.raises(OrderBookDeltaSequenceValidationError):
            engine._validate_fixture_identity(tampered)


def test_config_contract_rejects_each_structural_boundary() -> None:
    config = _load(ROOT / engine.CONFIG_PATH)
    engine._validate_config(config)

    missing = dict(config)
    missing.pop("lineage_id")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="fields differ"):
        engine._validate_config(missing)

    for field, value, message in (
        ("schema_version", "bad", "schema changed"),
        ("config_version", "bad", "version changed"),
        ("max_input_age_us", 0, "integer"),
    ):
        tampered = dict(config)
        tampered[field] = value
        with pytest.raises(OrderBookDeltaSequenceValidationError, match=message):
            engine._validate_config(tampered)

    noncausal = dict(config)
    noncausal["generated_at"] = "2026-08-06T19:18:40.000000Z"
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="causal"):
        engine._validate_config(noncausal)


def test_delta_freshness_enforces_future_stale_and_exact_boundary() -> None:
    config = _load(ROOT / engine.CONFIG_PATH)
    fixture = _load(ROOT / "tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json")
    raw_deltas = fixture["deltas"]
    assert isinstance(raw_deltas, list) and raw_deltas
    first = engine._delta_from_payload(raw_deltas[0])

    future_reference = dict(config)
    future_reference["input_reference_time"] = "2026-08-06T19:18:40.059999Z"
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="stale or future-dated"):
        engine._validate_delta_freshness((first,), future_reference)

    stale_reference = dict(config)
    stale_reference["input_reference_time"] = "2026-08-06T19:18:40.560001Z"
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="stale or future-dated"):
        engine._validate_delta_freshness((first,), stale_reference)

    exact_boundary = dict(config)
    exact_boundary["input_reference_time"] = "2026-08-06T19:18:40.560000Z"
    engine._validate_delta_freshness((first,), exact_boundary)

    exact_receive = replace(first, receive_time="2026-08-06T19:18:40.080000Z")
    current_reference = dict(config)
    engine._validate_delta_freshness((exact_receive,), current_reference)


def test_run_context_rejects_every_invalid_identity_field() -> None:
    valid = {
        "run_id": "run",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "config_version": "cfg",
        "code_commit": CODE_COMMIT,
        "correlation_id": "corr",
    }
    assert Lot39RunContextV1(**valid).to_dict()["code_commit"] == CODE_COMMIT
    for field, value in (
        ("run_id", ""),
        ("runtime_mode", "LIVE"),
        ("config_version", ""),
        ("code_commit", "bad"),
        ("correlation_id", ""),
    ):
        tampered = dict(valid)
        tampered[field] = value
        with pytest.raises(OrderBookDeltaSequenceValidationError):
            Lot39RunContextV1(**tampered)


def test_reconstructed_sequence_requires_exact_checksum_and_positive_advance() -> None:
    state, _ = engine.build_lot39_artifacts(ROOT, CODE_COMMIT)
    book = state.reconstructed_book
    assert book is not None
    for field, value in (
        ("base_snapshot_checksum", "bad"),
        ("sequence_anchor", "bad"),
        ("book_checksum", "bad"),
        ("applied_delta_count", 0),
        ("base_sequence_id", True),
        ("sequence_id", True),
    ):
        with pytest.raises(OrderBookDeltaSequenceValidationError):
            replace(book, **{field: value})
