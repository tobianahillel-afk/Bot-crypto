from __future__ import annotations

import copy
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

import crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_analysis as analysis
import crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_engine as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_analysis import (
    BookObservation,
    LiquidityAnalysisPolicy,
    PriceCluster,
    analyze_observations,
    cluster_observation,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_engine import (
    CONFIG_PATH,
    build_lot42_artifacts,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_engine_models import (
    LiquidityVoidV1,
    Lot42MetricsV1,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_engine_validation import (
    ACTIVE,
    DISPLAYED_WALL,
    HIGH_CONFIDENCE,
    LIQUIDITY_VOID,
    NOT_APPLICABLE,
    PARTICIPANT_INTENT,
    PERSISTENT_ZONE,
    Lot42ValidationError,
    age_us,
    bps_distance,
    lot42_safety,
    nonnegative_decimal_text,
    parse_utc_timestamp,
    positive_decimal_text,
    validate_checksum_fields,
    validate_classifications,
    validate_confidence,
    validate_lot42_safety,
    validate_nonnegative,
    validate_positive,
    validate_ratio,
    validate_sequence_ids,
    validate_side,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import OrderBookLevelV1

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "c" * 40
ZERO_SHA256 = "0" * 64


def _policy(**overrides: object) -> LiquidityAnalysisPolicy:
    values: dict[str, object] = {
        "decimal_precision": 50,
        "cluster_distance_bps": Decimal("1"),
        "history_match_distance_bps": Decimal("2"),
        "wall_min_notional": Decimal("50"),
        "persistent_min_observations": 2,
        "persistent_min_ratio": Decimal("0.5"),
        "void_min_gap_bps": Decimal("5"),
        "wall_high_confidence_max_cancellation_rate": Decimal("0.5"),
    }
    values.update(overrides)
    return LiquidityAnalysisPolicy(**values)  # type: ignore[arg-type]


def _observation(
    sequence: int,
    *,
    source: str = "source",
    bids: tuple[tuple[str, str], ...] = (("100", "2"), ("99", "1")),
    asks: tuple[tuple[str, str], ...] = (("102", "2"), ("103", "1")),
) -> BookObservation:
    return BookObservation(
        source,
        "OFFLINE",
        "TEST-SPOT",
        "SPOT",
        sequence,
        f"2026-08-06T19:18:40.{sequence:06d}Z",
        f"2026-08-06T19:18:40.{sequence + 1:06d}Z",
        tuple(OrderBookLevelV1(Decimal(price), Decimal(quantity)) for price, quantity in bids),
        tuple(OrderBookLevelV1(Decimal(price), Decimal(quantity)) for price, quantity in asks),
    )


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_lot42_validation_helpers_accept_reference_boundaries() -> None:
    assert positive_decimal_text("1.25", "value") == Decimal("1.25")
    assert nonnegative_decimal_text("0", "value") == Decimal("0")
    validate_ratio(Decimal("0"), "ratio")
    validate_ratio(Decimal("1"), "ratio")
    validate_nonnegative(Decimal("0"), "value")
    validate_positive(Decimal("1"), "value")
    validate_side("BID")
    validate_side("ASK")
    validate_classifications((DISPLAYED_WALL, PERSISTENT_ZONE))
    validate_confidence(HIGH_CONFIDENCE)
    validate_lot42_safety(lot42_safety())
    assert age_us("2026-08-06T00:00:00.000001Z", "2026-08-06T00:00:00.000003Z") == 2
    assert bps_distance(Decimal("100"), Decimal("101"), Decimal("100")) == Decimal("100")
    validate_sequence_ids((1, 2, 3))
    validate_checksum_fields((("a" * 64, "checksum"),))


@pytest.mark.parametrize("value", [0, 1, Decimal("1"), None])
def test_lot42_positive_decimal_rejects_non_text(value: object) -> None:
    with pytest.raises(Lot42ValidationError):
        positive_decimal_text(value, "value")


def test_lot42_validation_helpers_fail_closed() -> None:
    with pytest.raises(Lot42ValidationError):
        nonnegative_decimal_text("-1", "value")
    with pytest.raises(Lot42ValidationError):
        validate_ratio(Decimal("-0.1"), "ratio")
    with pytest.raises(Lot42ValidationError):
        validate_ratio(Decimal("1.1"), "ratio")
    with pytest.raises(Lot42ValidationError):
        validate_nonnegative(Decimal("-1"), "value")
    with pytest.raises(Lot42ValidationError):
        validate_positive(Decimal("0"), "value")
    with pytest.raises(Lot42ValidationError):
        validate_side("BOTH")
    with pytest.raises(Lot42ValidationError):
        validate_classifications(())
    with pytest.raises(Lot42ValidationError):
        validate_classifications((DISPLAYED_WALL, DISPLAYED_WALL))
    with pytest.raises(Lot42ValidationError):
        validate_classifications(("UNKNOWN",))
    with pytest.raises(Lot42ValidationError):
        validate_confidence("CERTAIN")
    bad_safety = lot42_safety()
    bad_safety["trade_allowed"] = True
    with pytest.raises(Lot42ValidationError):
        validate_lot42_safety(bad_safety)


def test_lot42_time_validation_fails_closed() -> None:
    with pytest.raises(Lot42ValidationError, match="Z suffix"):
        parse_utc_timestamp("2026-08-06T00:00:00+00:00", "time")
    with pytest.raises(Lot42ValidationError, match="valid ISO"):
        parse_utc_timestamp("not-a-timeZ", "time")
    with pytest.raises(Lot42ValidationError, match="cannot exceed"):
        age_us("2026-08-06T00:00:01Z", "2026-08-06T00:00:00Z")


def test_lot42_sequence_validation_rejects_empty_duplicate_and_ordering() -> None:
    with pytest.raises(Lot42ValidationError):
        validate_sequence_ids(())
    with pytest.raises(Exception):
        validate_sequence_ids((0,))
    with pytest.raises(Lot42ValidationError):
        validate_sequence_ids((1, 1))
    with pytest.raises(Lot42ValidationError):
        validate_sequence_ids((2, 1))


def test_lot42_model_invariants_fail_closed() -> None:
    state, audit, zone_set = build_lot42_artifacts(ROOT, CODE_COMMIT)
    zone = zone_set.zones[0]
    liquidity_void = zone_set.voids[0]
    with pytest.raises(Lot42ValidationError):
        replace(zone, lower_price=Decimal("0"))
    with pytest.raises(Lot42ValidationError):
        replace(zone, replenished_quantity=Decimal("-1"))
    with pytest.raises(Lot42ValidationError):
        replace(zone, replenishment_ratio=Decimal("2"))
    with pytest.raises(Lot42ValidationError):
        replace(zone, persistence_observations=zone.total_observations + 1)
    with pytest.raises(Lot42ValidationError):
        replace(zone, persistence_ratio=Decimal("0.1"))
    with pytest.raises(Lot42ValidationError):
        replace(zone, anchor_price=zone.upper_price + Decimal("1"))
    with pytest.raises(Lot42ValidationError):
        replace(zone, classifications=("UNKNOWN",))
    with pytest.raises(Lot42ValidationError):
        replace(zone, confidence_status="CERTAIN")
    with pytest.raises(Lot42ValidationError):
        replace(zone, lifecycle_status="EXPIRED")
    with pytest.raises(Lot42ValidationError):
        replace(zone, participant_intent="KNOWN")
    with pytest.raises(Lot42ValidationError):
        replace(zone, classifications=(PERSISTENT_ZONE,), confidence_status=HIGH_CONFIDENCE)
    with pytest.raises(Lot42ValidationError):
        replace(liquidity_void, gap_bps=Decimal("0"))
    with pytest.raises(Lot42ValidationError):
        replace(liquidity_void, classification="GAP")
    with pytest.raises(Lot42ValidationError):
        replace(liquidity_void, lifecycle_status="EXPIRED")
    with pytest.raises(Lot42ValidationError):
        replace(zone_set, sequence_id=zone_set.sequence_id + 1)
    with pytest.raises(Exception):
        replace(zone_set, expired_candidates_total=-1)
    with pytest.raises(Lot42ValidationError):
        replace(state, safety={})
    with pytest.raises(Lot42ValidationError):
        replace(audit, validation_checks=("same", "same"))


def test_lot42_metrics_invariants_fail_closed() -> None:
    with pytest.raises(Lot42ValidationError):
        Lot42MetricsV1(0, 0, 0, 0, 0, 0, 0)
    with pytest.raises(Lot42ValidationError):
        Lot42MetricsV1(1, 1, 2, 0, 0, 0, 0)
    with pytest.raises(Lot42ValidationError):
        Lot42MetricsV1(1, 1, 0, 2, 0, 0, 0)


def test_lot42_void_constructor_rejects_invalid_side_and_intent() -> None:
    common = dict(
        void_id="void",
        side="BID",
        near_price=Decimal("100"),
        far_price=Decimal("99"),
        gap_bps=Decimal("10"),
        distance_to_mid_bps=Decimal("1"),
        classification=LIQUIDITY_VOID,
        lifecycle_status=ACTIVE,
        participant_intent=PARTICIPANT_INTENT,
        reason_codes=("LOT42_VOID",),
        void_checksum=ZERO_SHA256,
    )
    LiquidityVoidV1(**common)
    with pytest.raises(Lot42ValidationError):
        LiquidityVoidV1(**{**common, "side": "BOTH"})
    with pytest.raises(Lot42ValidationError):
        LiquidityVoidV1(**{**common, "participant_intent": "KNOWN"})


def test_lot42_book_observation_rejects_unilateral_and_crossed() -> None:
    unilateral = _observation(1, bids=())
    with pytest.raises(Lot42ValidationError, match="bilateral"):
        _ = unilateral.mid_price
    crossed = _observation(1, bids=(("103", "1"),), asks=(("102", "1"),))
    with pytest.raises(Lot42ValidationError, match="crossed or locked"):
        _ = crossed.mid_price


def test_lot42_cluster_validation_rejects_unknown_or_empty_side() -> None:
    observation = _observation(1)
    with pytest.raises(Lot42ValidationError):
        cluster_observation(observation, "UNKNOWN", Decimal("1"), 50)
    empty_bid = _observation(1, bids=())
    with pytest.raises(Lot42ValidationError):
        cluster_observation(empty_bid, "BID", Decimal("1"), 50)


def test_lot42_history_policy_rejects_insufficient_or_invalid_evidence() -> None:
    one = (_observation(1),)
    with pytest.raises(Lot42ValidationError, match="insufficient"):
        analyze_observations(one, _policy(persistent_min_observations=2))
    duplicate = (_observation(1), _observation(1))
    with pytest.raises(Lot42ValidationError, match="strictly increasing"):
        analyze_observations(duplicate, _policy())
    changed_identity = (_observation(1), _observation(2, source="other"))
    with pytest.raises(Lot42ValidationError, match="identity changed"):
        analyze_observations(changed_identity, _policy())
    with pytest.raises(Lot42ValidationError, match="persistence"):
        analyze_observations(
            (_observation(1), _observation(2)),
            _policy(persistent_min_ratio=Decimal("2")),
        )
    with pytest.raises(Lot42ValidationError, match="cancellation"):
        analyze_observations(
            (_observation(1), _observation(2)),
            _policy(wall_high_confidence_max_cancellation_rate=Decimal("-1")),
        )


def test_lot42_analysis_zero_flow_and_expiry_edges() -> None:
    assert analysis._ratio(1, 2, 50) == Decimal("0.5")
    with pytest.raises(Lot42ValidationError):
        analysis._ratio(1, 0, 50)
    assert analysis._flow_metrics((None, None), 50) == (
        Decimal("0"),
        Decimal("0"),
        Decimal("0"),
        Decimal("0"),
    )
    cluster = PriceCluster("BID", Decimal("100"), Decimal("100"), Decimal("100"), Decimal("1"), Decimal("100"), 1)
    assert analysis._wall_confidence((PERSISTENT_ZONE,), Decimal("1"), Decimal("0"), _policy()) == NOT_APPLICABLE
    assert analysis._zone_reason_codes((PERSISTENT_ZONE,), NOT_APPLICABLE) == (
        "LOT42_OBSERVED_LEVEL_CLUSTER",
        "LOT42_PARTICIPANT_INTENT_NOT_INFERRED",
        "LOT42_PERSISTENCE_CONFIRMED",
    )
    assert analysis._expired_wall_candidates(((cluster,),), Decimal("101"), _policy()) == 0
    assert analysis._expired_wall_candidates(((cluster,), ()), Decimal("101"), _policy()) == 1


def test_lot42_history_reconstruction_rejects_unsynced_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    snapshot = engine._verify_lot38_snapshot(ROOT, config)
    deltas = engine._load_deltas(ROOT, config)
    monkeypatch.setattr(
        analysis,
        "reconstruct_sequence",
        lambda *_args, **_kwargs: SimpleNamespace(
            reconstructed_book=None,
            synchronization_state="RESYNC_REQUIRED",
        ),
    )
    with pytest.raises(Lot42ValidationError, match="SYNCED"):
        analysis.reconstruct_observation_history(snapshot, deltas)


def test_lot42_engine_config_validation_rejects_shape_version_precision_and_policy() -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    bad = copy.deepcopy(config)
    bad["extra"] = True
    with pytest.raises(Lot42ValidationError, match="fields"):
        engine._validate_config(bad)
    bad = copy.deepcopy(config)
    bad["config_version"] = "other"
    with pytest.raises(Lot42ValidationError, match="version"):
        engine._validate_config(bad)
    bad = copy.deepcopy(config)
    bad["calculation_decimal_precision"] = 49
    with pytest.raises(Lot42ValidationError, match="precision"):
        engine._validate_config(bad)
    bad = copy.deepcopy(config)
    bad["history_match_distance_bps"] = "0.001"
    with pytest.raises(Lot42ValidationError, match="match distance"):
        engine._validate_config(bad)
    bad = copy.deepcopy(config)
    bad["persistent_min_ratio"] = "2"
    with pytest.raises(Lot42ValidationError):
        engine._validate_config(bad)


def test_lot42_engine_checksum_and_gate_semantics_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    with pytest.raises(Lot42ValidationError, match="checksum"):
        engine._verify_checksum({"value": 1, "checksum": ZERO_SHA256}, "checksum", ZERO_SHA256, "test")
    gate = load_json_object(ROOT / "data/audit/lot42_v4_entry_gate.json")
    config = load_json_object(ROOT / CONFIG_PATH)
    gate["trade_allowed"] = True
    body = dict(gate)
    body.pop("output_checksum", None)
    gate["output_checksum"] = canonical_checksum(body)
    path = tmp_path / "gate.json"
    _write(path, gate)
    config["entry_gate_path"] = str(path)
    monkeypatch.setattr(engine, "EXPECTED_GATE", gate["output_checksum"])
    with pytest.raises(Lot42ValidationError, match="authorization"):
        engine._verify_gate(ROOT, config)


def test_lot42_lifecycle_semantics_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    lifecycle = load_json_object(ROOT / "data/audit/roadmap_lifecycle_overlay_lot41.json")
    lifecycle["latest_implemented_lot"] = 40
    path = tmp_path / "lifecycle.json"
    _write(path, lifecycle)
    config["lot41_lifecycle_overlay_path"] = str(path)
    with pytest.raises(Lot42ValidationError, match="latest lot 41"):
        engine._verify_lifecycle(ROOT, config)
    lifecycle["latest_implemented_lot"] = 41
    lifecycle["lots"]["42"] = {"implementation_started": True, "status": "IMPLEMENTING"}
    _write(path, lifecycle)
    with pytest.raises(Lot42ValidationError, match="historical Lot 42"):
        engine._verify_lifecycle(ROOT, config)


def test_lot42_feature_safety_semantics_fail_closed() -> None:
    feature = load_json_object(ROOT / "data/audit/book_feature_state_lot41.json")
    state = load_json_object(ROOT / "data/audit/spread_depth_and_imbalance_engine_lot41.json")
    bad = copy.deepcopy(feature)
    bad.pop("book_quality")
    with pytest.raises(Lot42ValidationError, match="quality missing"):
        engine._verify_feature_safety(bad, state)
    bad = copy.deepcopy(feature)
    bad["book_quality"]["health_status"] = "DEGRADED"
    with pytest.raises(Lot42ValidationError, match="healthy"):
        engine._verify_feature_safety(bad, state)
    bad = copy.deepcopy(feature)
    bad["book_quality"]["consequence"] = "WAIT"
    with pytest.raises(Lot42ValidationError, match="consequence"):
        engine._verify_feature_safety(bad, state)
    bad = copy.deepcopy(feature)
    bad["extrapolated"] = True
    with pytest.raises(Lot42ValidationError, match="observed"):
        engine._verify_feature_safety(bad, state)
    bad_state = copy.deepcopy(state)
    bad_state["safety"]["trade_allowed"] = True
    with pytest.raises(Lot42ValidationError, match="safety"):
        engine._verify_feature_safety(feature, bad_state)


def test_lot42_snapshot_payload_validation_rejects_missing_or_malformed_levels() -> None:
    state = load_json_object(ROOT / "data/audit/order_book_l2_snapshot_engine_lot38.json")
    snapshot = state["snapshot"]
    bad = copy.deepcopy(snapshot)
    bad["bids"] = []
    with pytest.raises(Lot42ValidationError):
        engine._snapshot_from_payload(bad)
    with pytest.raises(Lot42ValidationError, match="non-empty list"):
        engine._levels_from_payload([], "levels", False)
    with pytest.raises(Lot42ValidationError, match="fields changed"):
        engine._levels_from_payload([{"price": "1", "quantity": "1", "extra": 1}], "levels", False)
    with pytest.raises(Lot42ValidationError):
        engine._levels_from_payload([{"price": "1", "quantity": 1}], "levels", False)


def test_lot42_delta_fixture_and_payload_validation_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    fixture = load_json_object(ROOT / "tests/fixtures/lot39/order_book_delta_sequence_fixture_v1.json")
    path = tmp_path / "fixture.json"
    config["lot39_delta_fixture_path"] = str(path)
    monkeypatch.setattr(engine, "file_checksum", lambda _path: engine.EXPECTED_DELTA_FIXTURE)
    bad = copy.deepcopy(fixture)
    bad["schema_version"] = "bad"
    _write(path, bad)
    with pytest.raises(Lot42ValidationError, match="schema"):
        engine._load_deltas(ROOT, config)
    bad = copy.deepcopy(fixture)
    bad["fixture_only"] = False
    _write(path, bad)
    with pytest.raises(Lot42ValidationError, match="boundary"):
        engine._load_deltas(ROOT, config)
    bad = copy.deepcopy(fixture)
    bad["deltas"] = []
    _write(path, bad)
    with pytest.raises(Lot42ValidationError, match="empty"):
        engine._load_deltas(ROOT, config)
    with pytest.raises(Lot42ValidationError, match="object"):
        engine._delta_from_payload("bad", 0)


def test_lot42_current_identity_and_freshness_fail_closed() -> None:
    feature = load_json_object(ROOT / "data/audit/book_feature_state_lot41.json")
    book = load_json_object(ROOT / "data/audit/reconstructed_order_book_lot39.json")
    config = load_json_object(ROOT / CONFIG_PATH)
    bad = copy.deepcopy(feature)
    bad["source_id"] = "other"
    with pytest.raises(Lot42ValidationError, match="identity"):
        engine._verify_current_identity(bad, book, config)
    bad_config = copy.deepcopy(config)
    bad_config["max_input_age_us"] = 1
    with pytest.raises(Lot42ValidationError, match="stale"):
        engine._verify_current_identity(feature, book, bad_config)
