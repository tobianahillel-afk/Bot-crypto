from __future__ import annotations

import json
import shutil
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

import crypto_quant_bot.microstructure.book_integrity_desynchronization_detector as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure import build_lot40_artifacts, evaluate_book_integrity
from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector import CONFIG_PATH
from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector_models import (
    BookHealthComponentV1,
    BookHealthVetoV1,
    Lot40LineageEnvelopeV1,
    Lot40MetricsV1,
    Lot40RunContextV1,
)
from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector_validation import (
    BookIntegrityValidationError,
    decimal_from_text,
    decimal_text,
    duration_us,
    lot40_safety,
    parse_utc_timestamp,
    require_boolean,
    require_git_sha,
    require_integer,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_consequence,
    validate_health_state,
    validate_lot40_safety,
    validate_reason_codes,
    validate_runtime_mode,
)

ROOT = Path(__file__).resolve().parents[1]
BOOK_PATH = ROOT / "data/audit/reconstructed_order_book_lot39.json"
REFERENCE_PATHS = (
    CONFIG_PATH,
    Path("data/audit/lot40_v4_entry_gate.json"),
    Path("data/audit/roadmap_lifecycle_overlay_lot39.json"),
    Path("data/audit/order_book_delta_and_sequence_reconstructor_lot39.json"),
    Path("data/audit/order_book_delta_and_sequence_reconstructor_audit_lot39.json"),
    Path("data/audit/reconstructed_order_book_lot39.json"),
    Path("tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json"),
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _book() -> dict[str, object]:
    return _load(BOOK_PATH)


def _config() -> dict[str, object]:
    return _load(ROOT / CONFIG_PATH)


def _copy_reference_tree(target: Path) -> None:
    for relative in REFERENCE_PATHS:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)


def _rewrite_checksum(payload: dict[str, object], field: str) -> None:
    body = dict(payload)
    body.pop(field, None)
    payload[field] = canonical_checksum(body)


@pytest.mark.parametrize("value", [None, "", "   ", 3])
def test_require_text_rejects_non_text(value: object) -> None:
    with pytest.raises(BookIntegrityValidationError, match="non-empty text"):
        require_text(value, "field")


@pytest.mark.parametrize("value", [True, "1", -1])
def test_require_integer_rejects_invalid_values(value: object) -> None:
    with pytest.raises(BookIntegrityValidationError, match="integer"):
        require_integer(value, "field")


def test_require_boolean_sha_and_runtime_guards() -> None:
    with pytest.raises(BookIntegrityValidationError, match="boolean"):
        require_boolean(1, "flag")
    with pytest.raises(BookIntegrityValidationError, match="git SHA"):
        require_git_sha("A" * 40, "commit")
    with pytest.raises(BookIntegrityValidationError, match="sha256"):
        require_sha256("z" * 64, "checksum")
    with pytest.raises(BookIntegrityValidationError, match="runtime"):
        validate_runtime_mode("LIVE")


def test_timestamp_duration_and_causal_guards() -> None:
    with pytest.raises(BookIntegrityValidationError, match="UTC Z"):
        parse_utc_timestamp("2026-08-06T19:18:40+00:00", "ts")
    with pytest.raises(BookIntegrityValidationError, match="ISO timestamp"):
        parse_utc_timestamp("not-a-dateZ", "ts")
    start = datetime(2026, 8, 6, 19, 18, 41, tzinfo=timezone.utc)
    end = datetime(2026, 8, 6, 19, 18, 40, tzinfo=timezone.utc)
    with pytest.raises(BookIntegrityValidationError, match="backwards"):
        duration_us(start, end)
    assert duration_us(end, start) == 1_000_000
    with pytest.raises(BookIntegrityValidationError, match="causal"):
        validate_causal_times(
            "2026-08-06T19:18:40.000000Z",
            "2026-08-06T19:18:40.200000Z",
            "2026-08-06T19:18:40.100000Z",
            "2026-08-06T19:18:40.300000Z",
        )


@pytest.mark.parametrize(
    ("value", "match"),
    [
        (1, "decimal text"),
        ("nope", "invalid decimal"),
        ("NaN", "finite"),
        ("-1", "non-negative"),
    ],
)
def test_decimal_input_guards(value: object, match: str) -> None:
    with pytest.raises(BookIntegrityValidationError, match=match):
        decimal_from_text(value, "number")


def test_decimal_positive_and_output_guards() -> None:
    with pytest.raises(BookIntegrityValidationError, match="positive"):
        decimal_from_text("0", "weight", allow_zero=False)
    with pytest.raises(BookIntegrityValidationError, match="finite"):
        decimal_text(Decimal("Infinity"))
    assert decimal_text(Decimal("100.00")) == "100"


def test_reason_health_consequence_and_safety_guards() -> None:
    with pytest.raises(BookIntegrityValidationError, match="requires reason"):
        validate_reason_codes(())
    with pytest.raises(BookIntegrityValidationError, match="unique"):
        validate_reason_codes(("LOT40_A", "LOT40_A"))
    with pytest.raises(BookIntegrityValidationError, match="invalid reason"):
        validate_reason_codes(("bad-reason",))
    with pytest.raises(BookIntegrityValidationError, match="health state"):
        validate_health_state("GREEN")
    with pytest.raises(BookIntegrityValidationError, match="consequence"):
        validate_consequence("TRADE")
    safety = lot40_safety()
    safety["trade_allowed"] = True
    with pytest.raises(BookIntegrityValidationError, match="safety boundary"):
        validate_lot40_safety(safety)


def test_run_context_and_lineage_contracts_fail_closed() -> None:
    with pytest.raises(BookIntegrityValidationError, match="runtime"):
        Lot40RunContextV1("run", "LIVE", "config", "a" * 40, "corr")
    with pytest.raises(BookIntegrityValidationError, match="sha256"):
        Lot40LineageEnvelopeV1(
            "lineage",
            "x" * 64,
            "1" * 64,
            "2" * 64,
            "3" * 64,
            "4" * 64,
            "2026-08-06T19:18:40Z",
        )


def test_component_contract_guards_name_weight_score_and_reason() -> None:
    with pytest.raises(BookIntegrityValidationError, match="unknown Lot 40 health component"):
        BookHealthComponentV1(
            "UNKNOWN", True, False, Decimal("1"), Decimal("1"), "LOT40_UNKNOWN"
        )
    with pytest.raises(BookIntegrityValidationError, match="weight"):
        BookHealthComponentV1(
            "FRESHNESS", True, False, Decimal("0"), Decimal("0"), "LOT40_BOOK_FRESH"
        )
    with pytest.raises(BookIntegrityValidationError, match="passed weight or zero"):
        BookHealthComponentV1(
            "FRESHNESS", True, False, Decimal("15"), Decimal("14"), "LOT40_BOOK_FRESH"
        )
    with pytest.raises(BookIntegrityValidationError, match="invalid reason"):
        BookHealthComponentV1(
            "FRESHNESS", True, False, Decimal("15"), Decimal("15"), "bad"
        )


def test_integrity_model_identity_measurement_and_component_guards() -> None:
    state, _ = build_lot40_artifacts(ROOT, "a" * 40)
    integrity = state.book_integrity
    with pytest.raises(BookIntegrityValidationError, match="SPOT"):
        replace(integrity, market_type="FUTURES")
    with pytest.raises(BookIntegrityValidationError, match="non-SYNCED"):
        replace(integrity, synchronization_state="RESYNC_REQUIRED")
    with pytest.raises(BookIntegrityValidationError, match="finite"):
        replace(integrity, book_health_score=Decimal("NaN"))
    with pytest.raises(BookIntegrityValidationError, match=r"\[0,100\]"):
        replace(integrity, book_health_score=Decimal("101"))
    with pytest.raises(BookIntegrityValidationError, match="component set"):
        replace(integrity, components=integrity.components[:-1])


def test_integrity_model_weight_score_status_reason_and_checksum_guards() -> None:
    state, _ = build_lot40_artifacts(ROOT, "a" * 40)
    integrity = state.book_integrity
    modified = tuple(
        replace(item, weight=Decimal("14"), score=Decimal("14"))
        if item.name == "FRESHNESS"
        else item
        for item in integrity.components
    )
    with pytest.raises(BookIntegrityValidationError, match="weights must total 100"):
        replace(integrity, components=modified, book_health_score=Decimal("99"))
    with pytest.raises(BookIntegrityValidationError, match="component total mismatch"):
        replace(integrity, book_health_score=Decimal("99"))
    with pytest.raises(BookIntegrityValidationError, match="status/component mismatch"):
        replace(integrity, health_status="DEGRADED")
    with pytest.raises(BookIntegrityValidationError, match="requires reason"):
        replace(integrity, reason_codes=())
    with pytest.raises(BookIntegrityValidationError, match="sha256"):
        replace(integrity, integrity_checksum="bad")


def test_veto_model_threshold_consequence_flag_and_checksum_guards() -> None:
    state, _ = build_lot40_artifacts(ROOT, "a" * 40)
    veto = state.book_health_veto
    with pytest.raises(BookIntegrityValidationError, match="finite"):
        replace(veto, trade_health_threshold=Decimal("NaN"))
    with pytest.raises(BookIntegrityValidationError, match="threshold ordering"):
        replace(veto, system_health_threshold=Decimal("95"))
    with pytest.raises(BookIntegrityValidationError, match="veto score"):
        replace(veto, book_health_score=Decimal("101"))
    with pytest.raises(BookIntegrityValidationError, match="must BLOCK"):
        replace(veto, critical_failure_consequence="WAIT")
    with pytest.raises(BookIntegrityValidationError, match="must PAUSE"):
        replace(veto, system_threshold_consequence="WAIT")
    with pytest.raises(BookIntegrityValidationError, match="veto_active mismatch"):
        replace(veto, veto_active=True)
    with pytest.raises(BookIntegrityValidationError, match="sha256"):
        replace(veto, veto_checksum="bad")


def test_metrics_contract_guards_counts_latency_and_status() -> None:
    with pytest.raises(BookIntegrityValidationError, match="failed components"):
        Lot40MetricsV1(1, 2, 0, 1, 1, 0)
    with pytest.raises(BookIntegrityValidationError, match="critical failures"):
        Lot40MetricsV1(2, 1, 2, 1, 1, 0)
    with pytest.raises(BookIntegrityValidationError, match="integer"):
        Lot40MetricsV1(2, 0, 0, 1, 1, 0, processing_latency_us=-1)
    with pytest.raises(BookIntegrityValidationError, match="non-empty text"):
        Lot40MetricsV1(2, 0, 0, 1, 1, 0, latency_measurement_status="")


def test_detector_state_and_audit_contract_guards() -> None:
    state, audit = build_lot40_artifacts(ROOT, "a" * 40)
    with pytest.raises(BookIntegrityValidationError, match="validation state"):
        replace(state, validation_state="UNKNOWN")
    mismatched_veto = replace(
        state.book_health_veto,
        book_health_score=Decimal("85"),
        consequence="WAIT",
        veto_active=True,
    )
    with pytest.raises(BookIntegrityValidationError, match="score mismatch"):
        replace(state, book_health_veto=mismatched_veto)
    with pytest.raises(BookIntegrityValidationError, match="safety boundary"):
        replace(state, safety={})
    with pytest.raises(BookIntegrityValidationError, match="sha256"):
        replace(state, output_checksum="bad")
    with pytest.raises(BookIntegrityValidationError, match="git SHA"):
        replace(audit, code_commit="bad")
    with pytest.raises(BookIntegrityValidationError, match="health state"):
        replace(audit, health_status="GREEN")
    with pytest.raises(BookIntegrityValidationError, match="consequence"):
        replace(audit, consequence="TRADE")
    with pytest.raises(BookIntegrityValidationError, match="safety boundary"):
        replace(audit, safety={})


def test_config_schema_version_policy_and_weight_set_are_strict() -> None:
    book = _book()
    for field in ("schema_version", "config_version"):
        config = _config()
        config[field] = "wrong"
        with pytest.raises(BookIntegrityValidationError, match="config"):
            evaluate_book_integrity(book, config)
    config = _config()
    config["critical_failure_consequence"] = "WAIT"
    with pytest.raises(BookIntegrityValidationError, match="critical consequence"):
        evaluate_book_integrity(book, config)
    config = _config()
    config["system_threshold_consequence"] = "WAIT"
    with pytest.raises(BookIntegrityValidationError, match="system threshold consequence"):
        evaluate_book_integrity(book, config)
    config = _config()
    weights = dict(config["component_weights"])
    weights.pop("FRESHNESS")
    config["component_weights"] = weights
    with pytest.raises(BookIntegrityValidationError, match="weight set"):
        evaluate_book_integrity(book, config)


def test_level_shapes_and_invalid_numeric_values_are_critical() -> None:
    malformed = _book()
    malformed["bids"] = [{"price": "50024.9"}]
    integrity, veto = evaluate_book_integrity(malformed, _config())
    assert integrity.health_status == "CRITICAL"
    assert veto.consequence == "BLOCK"

    invalid_decimal = _book()
    invalid_decimal["asks"] = [{"price": "bad", "quantity": "1"}]
    integrity, veto = evaluate_book_integrity(invalid_decimal, _config())
    assert integrity.health_status == "CRITICAL"
    assert veto.consequence == "BLOCK"


def test_invalid_sequence_type_is_rejected_before_publication() -> None:
    book = _book()
    book["sequence_id"] = True
    _rewrite_checksum(book, "book_checksum")
    with pytest.raises(BookIntegrityValidationError, match="sequence_id must be an integer"):
        evaluate_book_integrity(book, _config())


def test_invalid_checksum_shapes_are_critical_blocks() -> None:
    for checksum in (None, "x" * 64, "a" * 63):
        book = _book()
        book["book_checksum"] = checksum
        integrity, veto = evaluate_book_integrity(book, _config())
        assert integrity.checksum_valid is False
        assert veto.consequence == "BLOCK"


def test_gate_identity_and_lifecycle_tamper_stop_reference_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_gate_checksum = engine.EXPECTED_GATE_CHECKSUM
    _copy_reference_tree(tmp_path)
    gate_path = tmp_path / "data/audit/lot40_v4_entry_gate.json"
    gate = _load(gate_path)
    gate["gate_status"] = "NO_GO"
    _rewrite_checksum(gate, "output_checksum")
    gate_path.write_text(json.dumps(gate), encoding="utf-8")
    monkeypatch.setattr(engine, "EXPECTED_GATE_CHECKSUM", gate["output_checksum"])
    with pytest.raises(BookIntegrityValidationError, match="gate does not authorize"):
        build_lot40_artifacts(tmp_path, "a" * 40)

    monkeypatch.setattr(engine, "EXPECTED_GATE_CHECKSUM", original_gate_checksum)
    _copy_reference_tree(tmp_path)
    lifecycle_path = tmp_path / "data/audit/roadmap_lifecycle_overlay_lot39.json"
    lifecycle = _load(lifecycle_path)
    lifecycle["latest_implemented_lot"] = 38
    lifecycle_path.write_text(json.dumps(lifecycle), encoding="utf-8")
    with pytest.raises(BookIntegrityValidationError, match="latest lot 39"):
        build_lot40_artifacts(tmp_path, "a" * 40)


def test_fixture_and_gate_checksum_tamper_stop_reference_build(tmp_path: Path) -> None:
    _copy_reference_tree(tmp_path)
    fixture = tmp_path / "tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json"
    fixture.write_text("{}\n", encoding="utf-8")
    with pytest.raises(BookIntegrityValidationError, match="fixture changed"):
        build_lot40_artifacts(tmp_path, "a" * 40)

    _copy_reference_tree(tmp_path)
    gate_path = tmp_path / "data/audit/lot40_v4_entry_gate.json"
    gate = _load(gate_path)
    gate["output_checksum"] = "0" * 64
    gate_path.write_text(json.dumps(gate), encoding="utf-8")
    with pytest.raises(BookIntegrityValidationError, match="entry gate checksum"):
        build_lot40_artifacts(tmp_path, "a" * 40)
