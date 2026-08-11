from __future__ import annotations

import copy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

import crypto_quant_bot.microstructure.spread_depth_and_imbalance_engine as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.spread_depth_and_imbalance_engine import (
    CONFIG_PATH,
    _load_upstream,
    _validate_config,
    _verify_gate,
    _verify_health,
    _verify_lifecycle,
    _verify_upstream,
    build_lot41_artifacts,
    write_lot41_artifacts,
)
from crypto_quant_bot.microstructure.spread_depth_and_imbalance_engine_models import (
    BookQualityBindingV1,
    CumulativeDepthLevelV1,
    DepthBandV1,
    Lot41MetricsV1,
    TopOfBookV1,
)
from crypto_quant_bot.microstructure.spread_depth_and_imbalance_engine_validation import (
    IMBALANCE_DEFINED,
    Lot41ValidationError,
    lot41_safety,
    parse_book_levels,
    parse_depth_bands,
    symmetric_imbalance,
    validate_level_order,
    validate_lot41_safety,
    validate_reference_identity,
    validate_reference_times,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "b" * 40


def _config() -> dict[str, object]:
    return load_json_object(ROOT / CONFIG_PATH)


def _models():
    return build_lot41_artifacts(ROOT, CODE_COMMIT)


def _valid_gate() -> dict[str, object]:
    config = _config()
    return load_json_object(ROOT / str(config["entry_gate_path"]))


def _valid_upstream() -> tuple[dict[str, object], ...]:
    return _load_upstream(ROOT, _config())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("schema_version", "bad", "config schema"),
        ("config_version", "bad", "config version"),
        ("feature_horizon", "TRADE", "feature horizon"),
        ("calculation_decimal_precision", 49, "decimal precision"),
    ),
)
def test_lot41_config_contract_rejects_version_drift(
    field: str,
    value: object,
    message: str,
) -> None:
    config = _config()
    config[field] = value
    with pytest.raises(Lot41ValidationError, match=message):
        _validate_config(config)


def test_lot41_config_contract_rejects_unknown_field() -> None:
    config = _config()
    config["hidden_threshold"] = "1"
    with pytest.raises(Lot41ValidationError, match="fields differ"):
        _validate_config(config)


def _install_gate(
    monkeypatch: pytest.MonkeyPatch,
    gate: dict[str, object],
) -> None:
    body = dict(gate)
    body.pop("output_checksum", None)
    checksum = canonical_checksum(body)
    gate["output_checksum"] = checksum
    monkeypatch.setattr(engine, "EXPECTED_GATE", checksum)
    monkeypatch.setattr(engine, "load_json_object", lambda _path: gate)


def test_lot41_gate_rejects_authorization_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = _valid_gate()
    gate["owner"] = "OtherDomain"
    _install_gate(monkeypatch, gate)
    with pytest.raises(Lot41ValidationError, match="authorization"):
        _verify_gate(ROOT, _config())


def test_lot41_gate_rejects_safety_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = _valid_gate()
    safety = copy.deepcopy(gate["safety"])
    assert isinstance(safety, dict)
    safety["trade_allowed"] = True
    gate["safety"] = safety
    _install_gate(monkeypatch, gate)
    with pytest.raises(Lot41ValidationError, match="entry gate safety"):
        _verify_gate(ROOT, _config())


def test_lot41_gate_rejects_checksum_tamper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = _valid_gate()
    gate["output_checksum"] = "0" * 64
    monkeypatch.setattr(engine, "load_json_object", lambda _path: gate)
    with pytest.raises(Lot41ValidationError, match="checksum changed"):
        _verify_gate(ROOT, _config())


@pytest.mark.parametrize(
    ("mutator", "message"),
    (
        (lambda overlay: overlay.update(latest_implemented_lot=39), "latest lot 40"),
        (lambda overlay: overlay.update(lots=[]), "record missing"),
        (
            lambda overlay: overlay["lots"]["40"].update(status="BAD"),
            "status changed",
        ),
        (
            lambda overlay: overlay["lots"].update(
                {"41": {"implementation_started": True, "status": "STARTED"}}
            ),
            "gate lifecycle changed",
        ),
    ),
)
def test_lot41_lifecycle_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    mutator,
    message: str,
) -> None:
    config = _config()
    overlay = load_json_object(ROOT / str(config["lot40_lifecycle_overlay_path"]))
    mutator(overlay)
    monkeypatch.setattr(engine, "load_json_object", lambda _path: overlay)
    with pytest.raises(Lot41ValidationError, match=message):
        _verify_lifecycle(ROOT, config)


def test_lot41_upstream_checksum_tamper_is_rejected() -> None:
    upstream = list(_valid_upstream())
    upstream[0] = dict(upstream[0])
    upstream[0]["output_checksum"] = "0" * 64
    with pytest.raises(Lot41ValidationError, match="Lot 40 state checksum"):
        _verify_upstream(tuple(upstream), _config())


@pytest.mark.parametrize(
    ("index", "mutator", "message"),
    (
        (
            0,
            lambda payload: payload.update(book_integrity={}),
            "embedded health",
        ),
        (
            1,
            lambda payload: payload.update(state_output_checksum="f" * 64),
            "audit/state linkage",
        ),
        (
            1,
            lambda payload: payload.update(integrity_checksum="f" * 64),
            "audit health linkage",
        ),
    ),
)
def test_lot41_upstream_linkage_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    index: int,
    mutator,
    message: str,
) -> None:
    upstream = [copy.deepcopy(item) for item in _valid_upstream()]
    mutator(upstream[index])
    monkeypatch.setattr(engine, "_verify_checksum", lambda *_args: None)
    with pytest.raises(Lot41ValidationError, match=message):
        _verify_upstream(tuple(upstream), _config())


@pytest.mark.parametrize(
    ("veto_patch", "integrity_patch", "message"),
    (
        ({"critical_veto_active": True}, {}, "critical upstream veto"),
        ({}, {"crossed": True}, "crossed or locked"),
        ({}, {"locked": True}, "crossed or locked"),
    ),
)
def test_lot41_health_contract_rejects_critical_or_closed_book(
    veto_patch: dict[str, object],
    integrity_patch: dict[str, object],
    message: str,
) -> None:
    _, _, integrity, veto, _ = _valid_upstream()
    integrity = dict(integrity, **integrity_patch)
    veto = dict(veto, **veto_patch)
    with pytest.raises(Lot41ValidationError, match=message):
        _verify_health(integrity, veto, _config())


def test_lot41_validation_rejects_safety_and_negative_depth() -> None:
    unsafe = lot41_safety()
    unsafe["execution_allowed"] = True
    with pytest.raises(Lot41ValidationError, match="safety boundary"):
        validate_lot41_safety(unsafe)
    with pytest.raises(Lot41ValidationError, match="negative"):
        symmetric_imbalance(Decimal("-1"), Decimal("1"))


def test_lot41_level_shape_duplicate_ask_order_and_unknown_side() -> None:
    with pytest.raises(Lot41ValidationError, match="level fields"):
        parse_book_levels([{"price": "1"}], "bids")
    duplicate = ((Decimal("2"), Decimal("1")), (Decimal("2"), Decimal("2")))
    with pytest.raises(Lot41ValidationError, match="unique"):
        validate_level_order(duplicate, "bids")
    with pytest.raises(Lot41ValidationError, match="strictly monotonic"):
        parse_book_levels(
            [
                {"price": "3", "quantity": "1"},
                {"price": "2", "quantity": "1"},
            ],
            "asks",
        )
    with pytest.raises(Lot41ValidationError, match="unknown book side"):
        validate_level_order(((Decimal("1"), Decimal("1")),), "other")


def test_lot41_depth_bands_reject_empty_configuration() -> None:
    with pytest.raises(Lot41ValidationError, match="non-empty"):
        parse_depth_bands([])


def test_lot41_reference_identity_rejects_mismatch_and_unsynced() -> None:
    _, _, integrity, _, book = _valid_upstream()
    mismatch = dict(book, venue="OTHER")
    with pytest.raises(Lot41ValidationError, match="identity mismatch"):
        validate_reference_identity(mismatch, integrity)
    unsynced_book = dict(book, synchronization_state="DESYNCED")
    with pytest.raises(Lot41ValidationError, match="SYNCED reconstructed"):
        validate_reference_identity(unsynced_book, integrity)
    unsynced_integrity = dict(integrity, synchronization_state="DESYNCED")
    with pytest.raises(Lot41ValidationError, match="SYNCED integrity"):
        validate_reference_identity(book, unsynced_integrity)


def test_lot41_reference_times_reject_upstream_timestamp_drift() -> None:
    _, _, integrity, _, book = _valid_upstream()
    decision = str(integrity["decision_time"])
    mismatch = dict(integrity, receive_time="2026-08-06T19:18:40.071000Z")
    with pytest.raises(Lot41ValidationError, match="timestamps mismatch"):
        validate_reference_times(book, mismatch, decision, decision)
    wrong_decision = dict(integrity, decision_time="2026-08-06T19:18:40.099000Z")
    with pytest.raises(Lot41ValidationError, match="decision_time mismatch"):
        validate_reference_times(book, wrong_decision, decision, decision)


@pytest.mark.parametrize(
    "kwargs",
    (
        {"best_bid_price": Decimal("0")},
        {"best_bid_price": Decimal("2"), "best_ask_price": Decimal("2")},
    ),
)
def test_lot41_top_of_book_model_fail_closed(kwargs: dict[str, Decimal]) -> None:
    values = {
        "best_bid_price": Decimal("1"),
        "best_bid_quantity": Decimal("1"),
        "best_ask_price": Decimal("2"),
        "best_ask_quantity": Decimal("1"),
    }
    values.update(kwargs)
    with pytest.raises(Lot41ValidationError):
        TopOfBookV1(**values)


@pytest.mark.parametrize(
    "factory",
    (
        lambda: DepthBandV1(
            Decimal("0"), Decimal("1"), Decimal("1"), 1, 1, Decimal("0"), IMBALANCE_DEFINED
        ),
        lambda: DepthBandV1(
            Decimal("1"), Decimal("-1"), Decimal("1"), 1, 1, Decimal("0"), IMBALANCE_DEFINED
        ),
        lambda: DepthBandV1(
            Decimal("1"), Decimal("0"), Decimal("0"), 0, 0, Decimal("0"), IMBALANCE_DEFINED
        ),
        lambda: DepthBandV1(
            Decimal("1"), Decimal("2"), Decimal("1"), 1, 1, Decimal("0"), IMBALANCE_DEFINED
        ),
    ),
)
def test_lot41_depth_band_model_fail_closed(factory) -> None:
    with pytest.raises(Lot41ValidationError):
        factory()


@pytest.mark.parametrize(
    "values",
    (
        (Decimal("NaN"), Decimal("1"), Decimal("1"), Decimal("0")),
        (Decimal("1"), Decimal("0"), Decimal("1"), Decimal("0")),
        (Decimal("1"), Decimal("1"), Decimal("1"), Decimal("-1")),
    ),
)
def test_lot41_cumulative_depth_model_fail_closed(values) -> None:
    with pytest.raises(Lot41ValidationError):
        CumulativeDepthLevelV1(*values)


def test_lot41_quality_binding_model_fail_closed() -> None:
    zero = "0" * 64
    with pytest.raises(Lot41ValidationError, match="healthy"):
        BookQualityBindingV1("DEGRADED", Decimal("100"), "NONE", 1, zero, zero)
    with pytest.raises(Lot41ValidationError, match="consequence"):
        BookQualityBindingV1("HEALTHY", Decimal("100"), "WAIT", 1, zero, zero)


def test_lot41_feature_model_fail_closed() -> None:
    _, _, feature = _models()
    with pytest.raises(Lot41ValidationError, match="market type or horizon"):
        replace(feature, horizon="TRADE")
    with pytest.raises(Lot41ValidationError, match="finite and positive"):
        replace(feature, spread_absolute=Decimal("0"))
    with pytest.raises(Lot41ValidationError, match="bilateral observed depth"):
        replace(feature, cumulative_bids=())
    with pytest.raises(Lot41ValidationError, match="not increasing"):
        replace(feature, depth_bands=(feature.depth_bands[1], feature.depth_bands[0]))
    bad_quality = replace(feature.book_quality, sequence_id=feature.sequence_id + 1)
    with pytest.raises(Lot41ValidationError, match="sequence mismatch"):
        replace(feature, book_quality=bad_quality)


def test_lot41_metrics_state_and_audit_models_fail_closed() -> None:
    state, audit, _ = _models()
    with pytest.raises(Lot41ValidationError, match="exceeds band count"):
        Lot41MetricsV1(1, 2, 1, 1)
    unsafe = dict(state.safety)
    unsafe["trade_allowed"] = True
    with pytest.raises(Lot41ValidationError, match="safety boundary"):
        replace(state, safety=unsafe)
    with pytest.raises(Lot41ValidationError, match="requires validation checks"):
        replace(audit, validation_checks=())


def test_lot41_write_path_is_atomic_and_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writes: list[tuple[Path, object]] = []
    monkeypatch.setattr(
        engine,
        "atomic_write_json",
        lambda path, payload: writes.append((path, payload)),
    )
    payloads = write_lot41_artifacts(ROOT, CODE_COMMIT)
    assert len(payloads) == 3
    assert [path for path, _ in writes] == [
        ROOT / engine.STATE_PATH,
        ROOT / engine.AUDIT_PATH,
        ROOT / engine.FEATURE_PATH,
    ]


def test_lot41_final_state_lineage_mismatch_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = engine._build_lineage

    def bad_lineage(config, feature):
        lineage = original(config, feature)
        return replace(lineage, lot40_state_checksum="f" * 64)

    monkeypatch.setattr(engine, "_build_lineage", bad_lineage)
    with pytest.raises(Lot41ValidationError, match="state lineage mismatch"):
        build_lot41_artifacts(ROOT, CODE_COMMIT)
