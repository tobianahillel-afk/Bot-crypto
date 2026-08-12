from __future__ import annotations

import copy
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

import crypto_quant_bot.microstructure.book_resilience_and_replenishment_analysis as analysis
import crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    load_json_object,
)
from crypto_quant_bot.microstructure.book_integrity_desynchronization_detector_validation import (
    BookIntegrityValidationError,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_models import (
    BookResilienceReplenishmentEngineAuditV1,
    BookResilienceSliceV1,
    BookResilienceStateV1,
    Lot43MetricsV1,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (
    Lot43ValidationError,
    age_us,
    bps_distance,
    validate_max_window_status,
    validate_nonnegative,
    validate_nullable_nonnegative_decimal,
    validate_nullable_positive_decimal,
    validate_nullable_positive_integer,
    validate_positive,
    validate_replenishment_kind,
    validate_resilience_status,
    validate_volatility_regime,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_analysis import BookObservation
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import OrderBookLevelV1

ROOT = Path(__file__).resolve().parents[1]
ZERO_SHA256 = "0" * 64


def _config() -> dict[str, object]:
    return load_json_object(ROOT / engine.CONFIG_PATH)


def _observation(
    sequence: int,
    receive_time: str,
    *,
    source_id: str = "source",
) -> BookObservation:
    return BookObservation(
        source_id,
        "OFFLINE",
        "TEST-SPOT",
        "SPOT",
        sequence,
        "2026-08-06T19:18:40.000001Z",
        receive_time,
        (OrderBookLevelV1(Decimal("100"), Decimal("1")),),
        (OrderBookLevelV1(Decimal("102"), Decimal("1")),),
    )


def _reference_slice(**changes: object) -> BookResilienceSliceV1:
    values: dict[str, object] = {
        "side": "BID",
        "horizon_us": 10_000,
        "volatility_regime": "QUIET",
        "volatility_method": "OBSERVED_BOOK_MID_MAX_ABS_MOVE_BPS",
        "depletion_events_total": 1,
        "recovered_events_total": 0,
        "mid_shift_events_total": 0,
        "expired_events_total": 1,
        "pending_events_total": 0,
        "replenishment_min_recovery_ratio": Decimal("0.25"),
        "mean_recovered_fraction": Decimal("0"),
        "mean_replenishment_time_us": None,
        "resilience_status": "FRAGILE",
        "reason_codes": ("LOT43_TEST",),
        "slice_checksum": ZERO_SHA256,
    }
    values.update(changes)
    return BookResilienceSliceV1(**values)  # type: ignore[arg-type]


def _reference_resilience(**changes: object) -> BookResilienceStateV1:
    values: dict[str, object] = {
        "source_id": "source",
        "venue": "OFFLINE",
        "instrument_id": "TEST-SPOT",
        "market_type": "SPOT",
        "event_time": "2026-08-06T19:18:40.000001Z",
        "receive_time": "2026-08-06T19:18:40.000002Z",
        "decision_time": "2026-08-06T19:18:40.000003Z",
        "sequence_id": 2,
        "history_sequence_ids": (1, 2),
        "volatility_measure_bps": Decimal("0"),
        "volatility_regime": "QUIET",
        "volatility_method": "OBSERVED_BOOK_MID_MAX_ABS_MOVE_BPS",
        "depletion_events": (),
        "resilience_slices": (_reference_slice(),),
        "reason_codes": ("LOT43_TEST",),
        "resilience_checksum": ZERO_SHA256,
    }
    values.update(changes)
    return BookResilienceStateV1(**values)  # type: ignore[arg-type]


def test_config_contract_rejects_field_version_horizon_and_zero_thresholds() -> None:
    config = _config()
    engine._validate_config(config)

    extra = dict(config)
    extra["unexpected"] = True
    with pytest.raises(Lot43ValidationError, match="fields differ"):
        engine._validate_config(extra)

    bad_version = dict(config)
    bad_version["schema_version"] = "future"
    with pytest.raises(Lot43ValidationError, match="version changed"):
        engine._validate_config(bad_version)

    bad_horizons = dict(config)
    bad_horizons["resilience_horizons_us"] = "10000,25000"
    with pytest.raises(Lot43ValidationError, match="must be a list"):
        engine._validate_config(bad_horizons)

    zero_quantity = dict(config)
    zero_quantity["depletion_min_quantity"] = "0"
    with pytest.raises(Lot43ValidationError, match="must be positive"):
        engine._validate_config(zero_quantity)

    zero_recovery = dict(config)
    zero_recovery["replenishment_min_recovery_ratio"] = "0"
    with pytest.raises(Lot43ValidationError, match="recovery threshold"):
        engine._validate_config(zero_recovery)


def test_gate_authorization_and_safety_are_independent_fail_closed_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    gate = load_json_object(ROOT / str(config["entry_gate_path"]))
    monkeypatch.setattr(engine, "_verify_checksum", lambda *args: None)

    unauthorized = copy.deepcopy(gate)
    unauthorized["target_lot"] = 44
    monkeypatch.setattr(engine, "load_json_object", lambda path: unauthorized)
    with pytest.raises(Lot43ValidationError, match="authorization changed"):
        engine._verify_gate(ROOT, config)

    unsafe = copy.deepcopy(gate)
    unsafe["safety"]["trade_allowed"] = True
    monkeypatch.setattr(engine, "load_json_object", lambda path: unsafe)
    with pytest.raises(Lot43ValidationError, match="safety changed"):
        engine._verify_gate(ROOT, config)


def test_lifecycle_rejects_each_invalid_state(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config()
    valid = load_json_object(ROOT / str(config["lot42_lifecycle_overlay_path"]))

    wrong_latest = copy.deepcopy(valid)
    wrong_latest["latest_implemented_lot"] = 41
    monkeypatch.setattr(engine, "load_json_object", lambda path: wrong_latest)
    with pytest.raises(Lot43ValidationError, match="latest lot 42"):
        engine._verify_lifecycle(ROOT, config)

    no_lots = copy.deepcopy(valid)
    no_lots["lots"] = []
    monkeypatch.setattr(engine, "load_json_object", lambda path: no_lots)
    with pytest.raises(Lot43ValidationError, match="lots missing"):
        engine._verify_lifecycle(ROOT, config)

    wrong_lot42 = copy.deepcopy(valid)
    wrong_lot42["lots"]["42"]["status"] = "DRIFTED"
    monkeypatch.setattr(engine, "load_json_object", lambda path: wrong_lot42)
    with pytest.raises(Lot43ValidationError, match="Lot 42 lifecycle status"):
        engine._verify_lifecycle(ROOT, config)

    unlocked = copy.deepcopy(valid)
    unlocked["lots"]["43"] = {"implementation_started": True, "status": "ACTIVE"}
    monkeypatch.setattr(engine, "load_json_object", lambda path: unlocked)
    with pytest.raises(Lot43ValidationError, match="historical Lot 43 gate"):
        engine._verify_lifecycle(ROOT, config)


def test_lot42_linkage_safety_and_observed_only_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    paths = {
        str(config["lot42_state_path"]): load_json_object(ROOT / str(config["lot42_state_path"])),
        str(config["lot42_audit_path"]): load_json_object(ROOT / str(config["lot42_audit_path"])),
        str(config["lot42_zone_set_path"]): load_json_object(ROOT / str(config["lot42_zone_set_path"])),
        str(config["lot42_config_path"]): load_json_object(ROOT / str(config["lot42_config_path"])),
    }
    monkeypatch.setattr(engine, "_verify_checksum", lambda *args: None)
    monkeypatch.setattr(engine, "canonical_checksum", lambda payload: engine.EXPECTED_LOT42_CONFIG)

    def run_with(mutator: object, message: str) -> None:
        local = copy.deepcopy(paths)
        assert callable(mutator)
        mutator(local)
        monkeypatch.setattr(engine, "load_json_object", lambda path: local[str(path.relative_to(ROOT))])
        with pytest.raises(Lot43ValidationError, match=message):
            engine._verify_lot42(ROOT, config)

    run_with(
        lambda local: local[str(config["lot42_state_path"])].__setitem__("liquidity_zones", {}),
        "state/zone-set linkage",
    )
    run_with(
        lambda local: local[str(config["lot42_audit_path"])].__setitem__("state_output_checksum", "0" * 64),
        "audit/state linkage",
    )
    run_with(
        lambda local: local[str(config["lot42_audit_path"])].__setitem__("zone_set_checksum", "0" * 64),
        "audit/zone linkage",
    )
    run_with(
        lambda local: local[str(config["lot42_state_path"])]["safety"].__setitem__("trade_allowed", True),
        "safety boundary",
    )

    def disable_observed_book(local: dict[str, object]) -> None:
        zone = local[str(config["lot42_zone_set_path"])]
        state = local[str(config["lot42_state_path"])]
        zone["observed_book_only"] = False  # type: ignore[index]
        state["liquidity_zones"]["observed_book_only"] = False  # type: ignore[index]

    def enable_intent(local: dict[str, object]) -> None:
        zone = local[str(config["lot42_zone_set_path"])]
        state = local[str(config["lot42_state_path"])]
        zone["participant_intent_inferred"] = True  # type: ignore[index]
        state["liquidity_zones"]["participant_intent_inferred"] = True  # type: ignore[index]

    run_with(disable_observed_book, "observed-book-only")
    run_with(enable_intent, "participant-intent")


def test_lot42_config_checksum_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config()
    paths = {
        str(config["lot42_state_path"]): load_json_object(ROOT / str(config["lot42_state_path"])),
        str(config["lot42_audit_path"]): load_json_object(ROOT / str(config["lot42_audit_path"])),
        str(config["lot42_zone_set_path"]): load_json_object(ROOT / str(config["lot42_zone_set_path"])),
        str(config["lot42_config_path"]): load_json_object(ROOT / str(config["lot42_config_path"])),
    }
    monkeypatch.setattr(engine, "_verify_checksum", lambda *args: None)
    monkeypatch.setattr(engine, "load_json_object", lambda path: paths[str(path.relative_to(ROOT))])
    monkeypatch.setattr(engine, "canonical_checksum", lambda payload: "0" * 64)
    with pytest.raises(Lot43ValidationError, match="config checksum"):
        engine._verify_lot42(ROOT, config)


def test_snapshot_and_level_parsers_reject_invalid_shapes_and_values() -> None:
    state = load_json_object(ROOT / "data/audit/order_book_l2_snapshot_engine_lot38.json")
    snapshot = state["snapshot"]
    assert isinstance(snapshot, dict)
    parsed = engine._snapshot_from_payload(snapshot)
    assert parsed.sequence_id == 1001

    with pytest.raises(Lot43ValidationError, match="non-empty list"):
        engine._levels_from_payload([], "levels", allow_zero=False)
    with pytest.raises(Lot43ValidationError, match="fields changed"):
        engine._levels_from_payload([{"price": "1"}], "levels", allow_zero=False)
    with pytest.raises(Lot43ValidationError, match="price must be positive"):
        engine._levels_from_payload(
            [{"price": "0", "quantity": "1"}], "levels", allow_zero=False
        )
    with pytest.raises(Lot43ValidationError, match="quantity must be positive"):
        engine._levels_from_payload(
            [{"price": "1", "quantity": "0"}], "levels", allow_zero=False
        )
    allowed = engine._levels_from_payload(
        [{"price": "1", "quantity": "0"}], "levels", allow_zero=True
    )
    assert allowed[0].quantity == 0

    missing_source = dict(snapshot)
    missing_source["source_id"] = ""
    with pytest.raises(BookIntegrityValidationError, match="snapshot source_id"):
        engine._snapshot_from_payload(missing_source)


def test_lot38_snapshot_requires_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config()
    monkeypatch.setattr(engine, "_verify_checksum", lambda *args: None)
    monkeypatch.setattr(engine, "load_json_object", lambda path: {"snapshot": []})
    with pytest.raises(Lot43ValidationError, match="canonical snapshot missing"):
        engine._verify_lot38_snapshot(ROOT, config)


def test_delta_fixture_contract_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config()
    fixture = load_json_object(ROOT / "tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json")

    monkeypatch.setattr(engine, "file_checksum", lambda path: "0" * 64)
    with pytest.raises(Lot43ValidationError, match="file checksum"):
        engine._load_deltas(ROOT, config)

    monkeypatch.setattr(engine, "file_checksum", lambda path: engine.EXPECTED_DELTA_FIXTURE)

    bad_schema = copy.deepcopy(fixture)
    bad_schema["schema_version"] = "future"
    monkeypatch.setattr(engine, "load_json_object", lambda path: bad_schema)
    with pytest.raises(Lot43ValidationError, match="fixture schema"):
        engine._load_deltas(ROOT, config)

    bad_boundary = copy.deepcopy(fixture)
    bad_boundary["fixture_only"] = False
    monkeypatch.setattr(engine, "load_json_object", lambda path: bad_boundary)
    with pytest.raises(Lot43ValidationError, match="fixture boundary"):
        engine._load_deltas(ROOT, config)

    empty = copy.deepcopy(fixture)
    empty["deltas"] = []
    monkeypatch.setattr(engine, "load_json_object", lambda path: empty)
    with pytest.raises(Lot43ValidationError, match="fixture is empty"):
        engine._load_deltas(ROOT, config)


def test_delta_parser_rejects_non_object_and_bad_optional_checksum() -> None:
    with pytest.raises(Lot43ValidationError, match="must be an object"):
        engine._delta_from_payload([], 0)

    fixture = load_json_object(ROOT / "tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json")
    raw = copy.deepcopy(fixture["deltas"][0])
    raw["expected_book_checksum"] = "not-a-sha"
    with pytest.raises(BookIntegrityValidationError):
        engine._delta_from_payload(raw, 0)

    raw = copy.deepcopy(fixture["deltas"][0])
    raw["expected_book_checksum"] = "1" * 64
    parsed = engine._delta_from_payload(raw, 0)
    assert parsed.expected_book_checksum == "1" * 64


def test_lot39_replay_divergence_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config()
    book = load_json_object(ROOT / str(config["lot39_reconstructed_book_path"]))
    state38 = load_json_object(ROOT / str(config["lot38_state_path"]))
    snapshot = engine._snapshot_from_payload(state38["snapshot"])
    deltas = engine._load_deltas(ROOT, config)
    monkeypatch.setattr(engine, "_verify_checksum", lambda *args: None)
    monkeypatch.setattr(engine, "load_json_object", lambda path: book)
    monkeypatch.setattr(
        engine,
        "reconstruct_sequence",
        lambda snapshot, deltas: SimpleNamespace(reconstructed_book=None),
    )
    with pytest.raises(Lot43ValidationError, match="replay diverges"):
        engine._verify_lot39_book(ROOT, config, snapshot, deltas)


def test_identity_and_time_reject_mismatch_and_staleness() -> None:
    config = _config()
    zone_set = load_json_object(ROOT / str(config["lot42_zone_set_path"]))
    book = load_json_object(ROOT / str(config["lot39_reconstructed_book_path"]))
    engine._verify_identity_and_time(zone_set, book, config)

    mismatch = copy.deepcopy(book)
    mismatch["instrument_id"] = "OTHER"
    with pytest.raises(Lot43ValidationError, match="identity changed"):
        engine._verify_identity_and_time(zone_set, mismatch, config)

    stale = dict(config)
    stale["decision_time"] = "2026-08-06T19:18:41.000000Z"
    stale["generated_at"] = "2026-08-06T19:18:41.000000Z"
    with pytest.raises(Lot43ValidationError, match="stale"):
        engine._verify_identity_and_time(zone_set, book, stale)


def test_metrics_cover_all_outcome_counters() -> None:
    events = (
        SimpleNamespace(replenishment_kind="SAME_PRICE", max_window_status="REPLENISHED"),
        SimpleNamespace(replenishment_kind="ADJACENT_PRICE", max_window_status="REPLENISHED"),
        SimpleNamespace(replenishment_kind="MID_SHIFT", max_window_status="MID_SHIFTED"),
        SimpleNamespace(replenishment_kind="NONE", max_window_status="EXPIRED_NO_REPLENISHMENT"),
        SimpleNamespace(replenishment_kind="NONE", max_window_status="PENDING_WINDOW"),
    )
    resilience = SimpleNamespace(history_sequence_ids=(1, 2, 3), depletion_events=events)
    metrics = engine._build_metrics(resilience)
    assert metrics.same_price_replenishments_total == 1
    assert metrics.adjacent_price_replenishments_total == 1
    assert metrics.mid_shift_events_total == 1
    assert metrics.expired_max_window_events_total == 1
    assert metrics.pending_max_window_events_total == 1


def test_validation_enums_nullable_helpers_and_model_guards() -> None:
    for function, value in (
        (validate_volatility_regime, "UNKNOWN"),
        (validate_replenishment_kind, "UNKNOWN"),
        (validate_max_window_status, "UNKNOWN"),
        (validate_resilience_status, "UNKNOWN"),
    ):
        with pytest.raises(Lot43ValidationError):
            function(value)

    validate_nullable_positive_integer(None, "value")
    validate_nullable_nonnegative_decimal(None, "value")
    validate_nullable_positive_decimal(None, "value")
    validate_nullable_positive_integer(1, "value")
    validate_nullable_nonnegative_decimal(Decimal("0"), "value")
    validate_nullable_positive_decimal(Decimal("1"), "value")

    with pytest.raises(Lot43ValidationError):
        validate_nonnegative(Decimal("-1"), "value")
    with pytest.raises(Lot43ValidationError):
        validate_positive(Decimal("0"), "value")
    with pytest.raises(Lot43ValidationError):
        bps_distance(Decimal("0"), Decimal("1"), Decimal("1"))
    with pytest.raises(Lot43ValidationError):
        age_us("not-a-time", "2026-08-06T19:18:40.000010Z")

    with pytest.raises(Lot43ValidationError, match="volatility method"):
        _reference_slice(volatility_method="OTHER")
    with pytest.raises(Lot43ValidationError, match="empty slice"):
        _reference_slice(
            depletion_events_total=0,
            expired_events_total=0,
            mean_recovered_fraction=Decimal("0"),
            resilience_status="NO_EVENTS",
        )
    with pytest.raises(Lot43ValidationError, match="non-empty slice"):
        _reference_slice(mean_recovered_fraction=None)
    with pytest.raises(Lot43ValidationError, match="latest history sequence"):
        _reference_resilience(sequence_id=3)
    with pytest.raises(Lot43ValidationError, match="volatility method"):
        _reference_resilience(volatility_method="OTHER")
    with pytest.raises(Lot43ValidationError, match="require observations"):
        Lot43MetricsV1(0, 0, 0, 0, 0, 0, 0)


def test_audit_rejects_empty_or_duplicate_validation_checks() -> None:
    state, audit, _ = engine.build_lot43_artifacts(ROOT, "d" * 40)
    values = {
        "run_context": audit.run_context,
        "state_output_checksum": state.output_checksum,
        "resilience_checksum": audit.resilience_checksum,
        "lineage": audit.lineage,
        "reason_codes": ("LOT43_TEST",),
        "safety": audit.safety,
        "audit_checksum": ZERO_SHA256,
    }
    with pytest.raises(Lot43ValidationError, match="non-empty and unique"):
        BookResilienceReplenishmentEngineAuditV1(validation_checks=(), **values)
    with pytest.raises(Lot43ValidationError, match="non-empty and unique"):
        BookResilienceReplenishmentEngineAuditV1(
            validation_checks=("same", "same"), **values
        )


def test_analysis_history_rejects_short_duplicate_identity_time_and_side() -> None:
    first = _observation(1, "2026-08-06T19:18:40.000010Z")
    second = _observation(2, "2026-08-06T19:18:40.000020Z")
    policy = analysis.BookResiliencePolicy(
        50,
        Decimal("0.1"),
        Decimal("0.25"),
        Decimal("0.25"),
        Decimal("20"),
        Decimal("5"),
        (10_000, 25_000),
        Decimal("0.05"),
        Decimal("0.5"),
    )
    with pytest.raises(Lot43ValidationError, match="at least two"):
        analysis.analyze_book_resilience((first,), policy, "2026-08-06T19:18:40.000030Z")
    with pytest.raises(Lot43ValidationError, match="strictly increase"):
        analysis.analyze_book_resilience(
            (first, _observation(1, "2026-08-06T19:18:40.000020Z")),
            policy,
            "2026-08-06T19:18:40.000030Z",
        )
    with pytest.raises(Lot43ValidationError, match="identity changed"):
        analysis.analyze_book_resilience(
            (first, _observation(2, "2026-08-06T19:18:40.000020Z", source_id="other")),
            policy,
            "2026-08-06T19:18:40.000030Z",
        )
    with pytest.raises(Lot43ValidationError):
        analysis.analyze_book_resilience(
            (first, _observation(2, "2026-08-06T19:18:40.000010Z")),
            policy,
            "2026-08-06T19:18:40.000030Z",
        )
    with pytest.raises(Lot43ValidationError, match="unknown Lot 43 book side"):
        analysis._levels(first, "UNKNOWN")
    assert analysis.analyze_book_resilience(
        (first, second), policy, "2026-08-06T19:18:40.000030Z"
    ).observations == (first, second)
