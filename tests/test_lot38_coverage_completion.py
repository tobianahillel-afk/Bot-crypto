from __future__ import annotations

import copy
import json
import shutil
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

import crypto_quant_bot.microstructure.order_book_l2_snapshot_engine as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine import (
    AUDIT_PATH,
    CONFIG_PATH,
    HEALTH_PATH,
    SNAPSHOT_PATH,
    STATE_PATH,
    _load_raw_snapshot,
    _verify_gate,
    _verify_lot37,
    _verify_lot37_artifacts,
    _verify_payload_checksum,
    build_lot38_artifacts,
    write_lot38_artifacts,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import (
    OrderBookLevelV1,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_validation import (
    OrderBookL2SnapshotValidationError,
    decimal_text,
    require_text,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "c" * 40


def config() -> dict[str, object]:
    return json.loads((ROOT / CONFIG_PATH).read_text(encoding="utf-8"))


def gate() -> dict[str, object]:
    return json.loads(
        (ROOT / "data/audit/lot38_v4_entry_gate.json").read_text(encoding="utf-8")
    )


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def install_gate(
    tmp_path: Path,
    value: dict[str, object],
) -> dict[str, object]:
    write_json(tmp_path / "gate.json", value)
    result = config()
    result["entry_gate_path"] = "gate.json"
    return result


def test_gate_rejects_checksum_authorization_and_safety_tampering(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    damaged = gate()
    damaged["output_checksum"] = "0" * 64
    with pytest.raises(OrderBookL2SnapshotValidationError, match="checksum"):
        _verify_gate(tmp_path, install_gate(tmp_path, damaged))

    unauthorized = gate()
    unauthorized["gate_status"] = "NO_GO"
    body = dict(unauthorized)
    body.pop("output_checksum")
    checksum = canonical_checksum(body)
    unauthorized["output_checksum"] = checksum
    monkeypatch.setattr(engine, "EXPECTED_GATE_CHECKSUM", checksum)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="authorize"):
        _verify_gate(tmp_path, install_gate(tmp_path, unauthorized))

    unsafe = gate()
    unsafe["safety"] = dict(unsafe["safety"])
    unsafe["safety"]["trade_allowed"] = True
    body = dict(unsafe)
    body.pop("output_checksum")
    checksum = canonical_checksum(body)
    unsafe["output_checksum"] = checksum
    monkeypatch.setattr(engine, "EXPECTED_GATE_CHECKSUM", checksum)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="safety"):
        _verify_gate(tmp_path, install_gate(tmp_path, unsafe))


def test_payload_checksum_verifier_rejects_value_and_content_changes() -> None:
    payload = {"value": 1}
    checksum = canonical_checksum(payload)
    certified = {**payload, "checksum": checksum}
    _verify_payload_checksum(certified, "checksum", checksum, "fixture")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="checksum"):
        _verify_payload_checksum(certified, "checksum", "0" * 64, "fixture")
    changed = {"value": 2, "checksum": checksum}
    with pytest.raises(OrderBookL2SnapshotValidationError, match="checksum"):
        _verify_payload_checksum(changed, "checksum", checksum, "fixture")


def test_lifecycle_rejects_each_invalid_transition(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot37.json").read_text(
            encoding="utf-8"
        )
    )
    monkeypatch.setattr(engine, "_verify_lot37_artifacts", lambda root, cfg: None)
    cfg = config()
    cfg["lot37_lifecycle_overlay_path"] = "overlay.json"

    cases: list[tuple[dict[str, object], str]] = []
    latest = copy.deepcopy(source)
    latest["latest_implemented_lot"] = 36
    cases.append((latest, "latest lot 37"))
    missing_map = copy.deepcopy(source)
    missing_map["lots"] = []
    cases.append((missing_map, "lot map"))
    unlocked = copy.deepcopy(source)
    unlocked["lots"]["38"] = {"implementation_started": True, "status": "STARTED"}
    cases.append((unlocked, "pre-gate lock"))
    wrong_lot37 = copy.deepcopy(source)
    wrong_lot37["lots"]["37"]["status"] = "WRONG"
    cases.append((wrong_lot37, "Lot 37 lifecycle status"))

    for payload, message in cases:
        write_json(tmp_path / "overlay.json", payload)
        with pytest.raises(OrderBookL2SnapshotValidationError, match=message):
            _verify_lot37(tmp_path, cfg)


def copy_lot37_artifacts(tmp_path: Path) -> dict[str, object]:
    mapping = {
        "lot37_state_path": "data/audit/microstructure_scope_and_offline_data_contracts_lot37.json",
        "lot37_audit_path": "data/audit/microstructure_scope_and_offline_data_contracts_audit_lot37.json",
        "lot37_contract_registry_path": "data/audit/microstructure_contract_registry_lot37.json",
        "lot37_capability_matrix_path": "data/audit/microstructure_capability_matrix_lot37.json",
    }
    cfg = config()
    for field, source in mapping.items():
        target = Path(source).name
        shutil.copyfile(ROOT / source, tmp_path / target)
        cfg[field] = target
    return cfg


def test_lot37_artifact_verifier_rejects_registry_and_matrix_tampering(
    tmp_path: Path,
) -> None:
    cfg = copy_lot37_artifacts(tmp_path)
    _verify_lot37_artifacts(tmp_path, cfg)

    registry_path = tmp_path / str(cfg["lot37_contract_registry_path"])
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["entries"][0]["status"] = "TAMPERED"
    write_json(registry_path, registry)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="registry"):
        _verify_lot37_artifacts(tmp_path, cfg)

    cfg = copy_lot37_artifacts(tmp_path)
    matrix_path = tmp_path / str(cfg["lot37_capability_matrix_path"])
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix["entries"][0]["implementation_status"] = "TAMPERED"
    write_json(matrix_path, matrix)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="matrix"):
        _verify_lot37_artifacts(tmp_path, cfg)


def test_raw_loader_rejects_gate_fixture_path_and_checksum_changes() -> None:
    cfg = config()
    certified_gate = gate()
    _load_raw_snapshot(ROOT, cfg, certified_gate)

    wrong_path = copy.deepcopy(certified_gate)
    wrong_path["prerequisites"]["offline_l2_fixture_path"] = "wrong.json"
    with pytest.raises(OrderBookL2SnapshotValidationError, match="path"):
        _load_raw_snapshot(ROOT, cfg, wrong_path)

    wrong_checksum = copy.deepcopy(certified_gate)
    wrong_checksum["prerequisites"]["offline_l2_fixture_sha256"] = "0" * 64
    with pytest.raises(OrderBookL2SnapshotValidationError, match="checksum"):
        _load_raw_snapshot(ROOT, cfg, wrong_checksum)


def test_model_rejects_nonfinite_levels_and_all_remaining_state_inconsistencies() -> None:
    with pytest.raises(OrderBookL2SnapshotValidationError, match="price"):
        OrderBookLevelV1(Decimal("NaN"), Decimal("1"))
    with pytest.raises(OrderBookL2SnapshotValidationError, match="quantity"):
        OrderBookLevelV1(Decimal("1"), Decimal("NaN"))

    state, audit = build_lot38_artifacts(ROOT, CODE_COMMIT)
    snapshot = state.snapshot
    health = state.book_health

    with pytest.raises(OrderBookL2SnapshotValidationError, match="SPOT"):
        replace(snapshot, market_type="PERP")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="empty"):
        replace(snapshot, bids=())
    with pytest.raises(OrderBookL2SnapshotValidationError, match="ask depth mismatch"):
        replace(snapshot, published_ask_depth=1)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="bid depth exceeds"):
        replace(snapshot, normalized_bid_depth=1)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="crossed"):
        replace(
            snapshot,
            bids=(OrderBookLevelV1(Decimal("200"), Decimal("1")),),
            asks=(OrderBookLevelV1(Decimal("100"), Decimal("1")),),
            published_bid_depth=1,
            published_ask_depth=1,
        )

    with pytest.raises(OrderBookL2SnapshotValidationError, match="crossed health"):
        replace(health, crossed=True)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="lock flag"):
        replace(health, locked=True)
    with pytest.raises(OrderBookL2SnapshotValidationError, match="sequence anchor"):
        replace(health, sequence_present=False)

    with pytest.raises(OrderBookL2SnapshotValidationError, match="validation state"):
        replace(state, validation_state="WRONG")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="lineage input"):
        replace(
            state,
            lineage=replace(state.lineage, input_fixture_checksum="0" * 64),
        )
    with pytest.raises(OrderBookL2SnapshotValidationError, match="audit state"):
        replace(audit, validation_state="WRONG")


def test_validation_primitives_reject_blank_text_and_nonfinite_output() -> None:
    with pytest.raises(OrderBookL2SnapshotValidationError, match="non-empty"):
        require_text("   ", "field")
    with pytest.raises(OrderBookL2SnapshotValidationError, match="finite"):
        decimal_text(Decimal("Infinity"))


def test_write_lot38_artifacts_persists_exact_four_documents() -> None:
    paths = (STATE_PATH, AUDIT_PATH, SNAPSHOT_PATH, HEALTH_PATH)
    backups: dict[Path, bytes | None] = {}
    for path in paths:
        target = ROOT / path
        backups[target] = target.read_bytes() if target.exists() else None
        if target.exists():
            target.unlink()
    try:
        state, audit = write_lot38_artifacts(ROOT, CODE_COMMIT)
        assert json.loads((ROOT / STATE_PATH).read_text(encoding="utf-8")) == state.to_dict()
        assert json.loads((ROOT / AUDIT_PATH).read_text(encoding="utf-8")) == audit.to_dict()
        assert json.loads((ROOT / SNAPSHOT_PATH).read_text(encoding="utf-8")) == state.snapshot.to_dict()
        assert json.loads((ROOT / HEALTH_PATH).read_text(encoding="utf-8")) == state.book_health.to_dict()
    finally:
        for target, original in backups.items():
            if original is None:
                if target.exists():
                    target.unlink()
            else:
                target.write_bytes(original)
