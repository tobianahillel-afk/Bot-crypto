from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor import (
    _delta_from_payload,
    _levels_from_payload,
    _load_deltas,
    _validate_config,
    _validate_delta_identity,
    _verify_gate,
    _verify_lot38,
    _verify_payload_checksum,
    build_lot39_artifacts,
    reconstruct_sequence,
    write_lot39_artifacts,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_models import (
    BLOCKED_STATE,
    Lot39MetricsV1,
    OrderBookDeltaV1,
    ReconstructionOutcome if False else OrderBookDeltaV1,
)
from crypto_quant_bot.microstructure.order_book_delta_sequence_reconstructor_validation import (
    OrderBookDeltaSequenceValidationError,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "f" * 40


def _config() -> dict[str, object]:
    return json.loads((ROOT / engine.CONFIG_PATH).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _gate() -> dict[str, object]:
    return json.loads((ROOT / "data/audit/lot39_v4_entry_gate.json").read_text(encoding="utf-8"))


def _fixture() -> dict[str, object]:
    return json.loads(
        (ROOT / "tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json").read_text(
            encoding="utf-8"
        )
    )


def _reference_inputs():
    config = _config()
    snapshot = _verify_lot38(ROOT, config)
    deltas, fixture_checksum = _load_deltas(ROOT, config)
    return config, snapshot, deltas, fixture_checksum


def test_config_validator_rejects_shape_schema_version_and_age() -> None:
    config = _config()
    damaged = dict(config)
    damaged["extra"] = True
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="config fields"):
        _validate_config(damaged)
    damaged = dict(config)
    damaged["schema_version"] = "wrong"
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="config schema"):
        _validate_config(damaged)
    damaged = dict(config)
    damaged["config_version"] = "wrong"
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="config version"):
        _validate_config(damaged)
    damaged = dict(config)
    damaged["max_input_age_us"] = 0
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="max_input_age_us"):
        _validate_config(damaged)


def test_payload_checksum_verifier_rejects_field_and_body_tampering() -> None:
    body = {"value": 1}
    checksum = canonical_checksum(body)
    _verify_payload_checksum({**body, "checksum": checksum}, "checksum", checksum, "fixture")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="checksum"):
        _verify_payload_checksum({**body, "checksum": "0" * 64}, "checksum", checksum, "fixture")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="checksum"):
        _verify_payload_checksum({"value": 2, "checksum": checksum}, "checksum", checksum, "fixture")


def test_gate_verifier_rejects_checksum_scope_and_safety(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = _config()
    config["entry_gate_path"] = "gate.json"
    gate = _gate()

    bad_checksum = copy.deepcopy(gate)
    bad_checksum["output_checksum"] = "0" * 64
    _write_json(tmp_path / "gate.json", bad_checksum)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="checksum"):
        _verify_gate(tmp_path, config)

    unauthorized = copy.deepcopy(gate)
    unauthorized["gate_status"] = "NO_GO"
    body = dict(unauthorized)
    body.pop("output_checksum")
    unauthorized["output_checksum"] = canonical_checksum(body)
    monkeypatch.setattr(engine, "EXPECTED_GATE_CHECKSUM", unauthorized["output_checksum"])
    _write_json(tmp_path / "gate.json", unauthorized)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="authorize"):
        _verify_gate(tmp_path, config)

    unsafe = copy.deepcopy(gate)
    unsafe["safety"]["trade_allowed"] = True
    body = dict(unsafe)
    body.pop("output_checksum")
    unsafe["output_checksum"] = canonical_checksum(body)
    monkeypatch.setattr(engine, "EXPECTED_GATE_CHECKSUM", unsafe["output_checksum"])
    _write_json(tmp_path / "gate.json", unsafe)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="safety"):
        _verify_gate(tmp_path, config)


def test_lot38_lifecycle_verifier_rejects_invalid_transitions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = _config()
    overlay = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot38.json").read_text(encoding="utf-8")
    )
    config["lot38_lifecycle_overlay_path"] = "overlay.json"
    monkeypatch.setattr(engine, "_verify_payload_checksum", lambda *args, **kwargs: None)

    dummy_state = {"output_checksum": engine.EXPECTED_LOT38_STATE}
    dummy_audit = {"audit_checksum": engine.EXPECTED_LOT38_AUDIT}
    snapshot = json.loads(
        (ROOT / "data/audit/order_book_snapshot_lot38.json").read_text(encoding="utf-8")
    )
    health = json.loads((ROOT / "data/audit/book_health_state_lot38.json").read_text(encoding="utf-8"))
    for field, name, payload in (
        ("lot38_state_path", "state.json", dummy_state),
        ("lot38_audit_path", "audit.json", dummy_audit),
        ("lot38_snapshot_path", "snapshot.json", snapshot),
        ("lot38_health_path", "health.json", health),
    ):
        config[field] = name
        _write_json(tmp_path / name, payload)

    cases: list[tuple[dict[str, object], str]] = []
    latest = copy.deepcopy(overlay)
    latest["latest_implemented_lot"] = 37
    cases.append((latest, "latest lot 38"))
    no_map = copy.deepcopy(overlay)
    no_map["lots"] = []
    cases.append((no_map, "lot map"))
    unlocked = copy.deepcopy(overlay)
    unlocked["lots"]["39"] = {"implementation_started": True, "status": "STARTED"}
    cases.append((unlocked, "pre-gate lock"))
    wrong_status = copy.deepcopy(overlay)
    wrong_status["lots"]["38"]["status"] = "WRONG"
    cases.append((wrong_status, "lifecycle status"))
    for payload, message in cases:
        _write_json(tmp_path / "overlay.json", payload)
        with pytest.raises(OrderBookDeltaSequenceValidationError, match=message):
            _verify_lot38(tmp_path, config)

    _write_json(tmp_path / "overlay.json", overlay)
    unhealthy = copy.deepcopy(health)
    unhealthy["health_status"] = "BAD"
    _write_json(tmp_path / "health.json", unhealthy)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="healthy sequenced"):
        _verify_lot38(tmp_path, config)
    crossed = copy.deepcopy(health)
    crossed["crossed"] = True
    _write_json(tmp_path / "health.json", crossed)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="open and uncrossed"):
        _verify_lot38(tmp_path, config)


def test_level_and_delta_parsers_reject_malformed_contracts() -> None:
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="valid level list"):
        _levels_from_payload(None, "bids", allow_empty=False)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="valid level list"):
        _levels_from_payload([], "bids", allow_empty=False)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="level shape"):
        _levels_from_payload([{"price": "1"}], "bids", allow_empty=True)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="duplicate price"):
        _levels_from_payload(
            [
                {"price": "1", "quantity": "1"},
                {"price": "1.0", "quantity": "2"},
            ],
            "bids",
            allow_empty=True,
        )
    assert _levels_from_payload([], "bids", allow_empty=True) == ()

    with pytest.raises(OrderBookDeltaSequenceValidationError, match="record must be an object"):
        _delta_from_payload([])
    payload = copy.deepcopy(_fixture()["deltas"][0])
    payload.pop("venue")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="shape changed"):
        _delta_from_payload(payload)
    payload = copy.deepcopy(_fixture()["deltas"][0])
    payload["expected_book_checksum"] = 7
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="expected_book_checksum"):
        _delta_from_payload(payload)


def test_delta_fixture_loader_rejects_identity_decision_empty_and_staleness(tmp_path: Path) -> None:
    config = _config()
    config["delta_fixture_path"] = "fixture.json"
    fixture = _fixture()

    cases: list[tuple[dict[str, object], str]] = []
    extra = copy.deepcopy(fixture)
    extra["extra"] = True
    cases.append((extra, "fixture fields"))
    schema = copy.deepcopy(fixture)
    schema["schema_version"] = "wrong"
    cases.append((schema, "fixture schema"))
    identity = copy.deepcopy(fixture)
    identity["fixture_only"] = False
    cases.append((identity, "fixture identity"))
    decision = copy.deepcopy(fixture)
    decision["used_for_decision"] = True
    cases.append((decision, "decision data"))
    empty = copy.deepcopy(fixture)
    empty["deltas"] = []
    cases.append((empty, "requires deltas"))
    for payload, message in cases:
        _write_json(tmp_path / "fixture.json", payload)
        with pytest.raises(OrderBookDeltaSequenceValidationError, match=message):
            _load_deltas(tmp_path, config)

    stale = copy.deepcopy(fixture)
    stale["deltas"][0]["receive_time"] = "2026-08-06T19:18:30.000000Z"
    _write_json(tmp_path / "fixture.json", stale)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="stale or future"):
        _load_deltas(tmp_path, config)
    future = copy.deepcopy(fixture)
    future["deltas"][0]["receive_time"] = "2026-08-06T19:18:41.000000Z"
    _write_json(tmp_path / "fixture.json", future)
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="stale or future"):
        _load_deltas(tmp_path, config)


def test_delta_identity_and_empty_book_integrity_failures() -> None:
    _, snapshot, deltas, _ = _reference_inputs()
    wrong_identity = replace(deltas[0], source_id="OTHER")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="identity differs"):
        _validate_delta_identity(snapshot, wrong_identity)
    deleting_all_bids = replace(
        deltas[0],
        bids=tuple(OrderBookLevelV1(level.price, 0) for level in snapshot.bids),
        asks=(),
    )
    outcome = reconstruct_sequence(snapshot, (deleting_all_bids,))
    assert outcome.synchronization_state == "RESYNC_REQUIRED"
    assert outcome.reconstructed_book is None
    assert "LOT39_EMPTY_BOOK_AFTER_DELTA" in outcome.reason_codes


def test_build_resync_requires_gap_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    _, _, _, fixture_checksum = _reference_inputs()
    outcome = engine.ReconstructionOutcome(
        "RESYNC_REQUIRED",
        None,
        None,
        Lot39MetricsV1(1, 0, 0, 0, 1, 1001),
        ("LOT39_RESYNC_REQUIRED",),
    )
    monkeypatch.setattr(engine, "reconstruct_sequence", lambda snapshot, deltas: outcome)
    monkeypatch.setattr(engine, "_load_deltas", lambda root, config: (_reference_inputs()[2], fixture_checksum))
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="missing gap evidence"):
        build_lot39_artifacts(ROOT, CODE_COMMIT)


def test_writer_rejects_resync_state_without_gap_event(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    state, audit = build_lot39_artifacts(ROOT, CODE_COMMIT)
    dummy_state = SimpleNamespace(
        reconstructed_book=None,
        sequence_gap_event=None,
        to_dict=lambda: state.to_dict(),
    )
    dummy_audit = SimpleNamespace(to_dict=lambda: audit.to_dict())
    monkeypatch.setattr(engine, "build_lot39_artifacts", lambda root, code_commit: (dummy_state, dummy_audit))
    monkeypatch.setattr(engine, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(engine, "AUDIT_PATH", tmp_path / "audit.json")
    monkeypatch.setattr(engine, "BOOK_PATH", tmp_path / "book.json")
    monkeypatch.setattr(engine, "GAP_EVENT_PATH", tmp_path / "gap.json")
    with pytest.raises(OrderBookDeltaSequenceValidationError, match="missing gap event"):
        write_lot39_artifacts(ROOT, CODE_COMMIT)
