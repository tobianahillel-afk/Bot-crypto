from __future__ import annotations

import copy
import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest

import crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_analysis import (
    BookResiliencePolicy,
    analyze_book_resilience,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine import (
    CONFIG_PATH,
    build_lot43_artifacts,
    write_lot43_artifacts,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (
    Lot43ValidationError,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_analysis import BookObservation
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import OrderBookLevelV1

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "c" * 40


def _build() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return tuple(item.to_dict() for item in build_lot43_artifacts(ROOT, CODE_COMMIT))  # type: ignore[return-value]


def _policy(
    *,
    depletion_min_quantity: str = "0.1",
    depletion_min_ratio: str = "0.25",
    replenishment_min_recovery_ratio: str = "0.25",
    adjacent_distance_bps: str = "20",
    mid_shift_min_bps: str = "5",
    horizons: tuple[int, ...] = (10_000, 25_000),
    quiet_max: str = "0.05",
    stressed_min: str = "0.5",
) -> BookResiliencePolicy:
    return BookResiliencePolicy(
        50,
        Decimal(depletion_min_quantity),
        Decimal(depletion_min_ratio),
        Decimal(replenishment_min_recovery_ratio),
        Decimal(adjacent_distance_bps),
        Decimal(mid_shift_min_bps),
        horizons,
        Decimal(quiet_max),
        Decimal(stressed_min),
    )


def _time(microseconds: int) -> str:
    return f"2026-08-06T19:18:40.{microseconds:06d}Z"


def _observation(
    sequence: int,
    receive_us: int,
    bids: tuple[tuple[str, str], ...],
    asks: tuple[tuple[str, str], ...],
) -> BookObservation:
    return BookObservation(
        "synthetic-offline-source",
        "OFFLINE",
        "TEST-SPOT",
        "SPOT",
        sequence,
        _time(receive_us - 1),
        _time(receive_us),
        tuple(OrderBookLevelV1(Decimal(price), Decimal(quantity)) for price, quantity in bids),
        tuple(OrderBookLevelV1(Decimal(price), Decimal(quantity)) for price, quantity in asks),
    )


def _temporary_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutate: Callable[[dict[str, object]], None],
) -> dict[str, object]:
    config = load_json_object(ROOT / CONFIG_PATH)
    mutate(config)
    path = tmp_path / "lot43-config.json"
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    monkeypatch.setattr(engine, "CONFIG_PATH", path)
    return config


def test_lot43_reference_values_lineage_and_links() -> None:
    state, audit, resilience = _build()
    assert state["validation_state"] == "VALIDATED_OFFLINE_BOOK_RESILIENCE_REPLENISHMENT_ONLY"
    assert resilience["sequence_id"] == 1003
    assert resilience["history_sequence_ids"] == [1001, 1002, 1003]
    assert resilience["volatility_measure_bps"] == "0"
    assert resilience["volatility_regime"] == "QUIET"
    assert audit["state_output_checksum"] == state["output_checksum"]
    assert audit["resilience_checksum"] == resilience["resilience_checksum"]
    assert state["book_resilience"] == resilience
    assert state["lineage"] == audit["lineage"]


def test_lot43_reference_depletion_is_exact_and_non_intentional() -> None:
    _, _, resilience = _build()
    events = resilience["depletion_events"]
    assert len(events) == 1
    event = events[0]
    assert event["side"] == "BID"
    assert event["depleted_price"] == "50024.8"
    assert event["previous_quantity"] == "1.25"
    assert event["post_depletion_quantity"] == "0"
    assert event["depleted_quantity"] == "1.25"
    assert event["depletion_ratio"] == "1"
    assert event["depletion_sequence_id"] == 1003
    assert event["replenishment_kind"] == "NONE"
    assert event["replenishment_time_us"] is None
    assert event["max_window_status"] == "EXPIRED_NO_REPLENISHMENT"
    assert event["participant_intent"] == "NOT_INFERRED"
    assert resilience["participant_intent_inferred"] is False


def test_lot43_reference_resilience_slices_are_exact() -> None:
    _, _, resilience = _build()
    slices = {(item["side"], item["horizon_us"]): item for item in resilience["resilience_slices"]}
    for horizon in (10_000, 25_000):
        bid = slices[("BID", horizon)]
        assert bid["depletion_events_total"] == 1
        assert bid["expired_events_total"] == 1
        assert bid["mean_recovered_fraction"] == "0"
        assert bid["mean_replenishment_time_us"] is None
        assert bid["resilience_status"] == "FRAGILE"
        ask = slices[("ASK", horizon)]
        assert ask["depletion_events_total"] == 0
        assert ask["mean_recovered_fraction"] is None
        assert ask["resilience_status"] == "NO_EVENTS"


def test_lot43_build_is_deterministic_and_checksums_are_canonical() -> None:
    first = _build()
    second = _build()
    assert first == second
    for payload, field in zip(
        first,
        ("output_checksum", "audit_checksum", "resilience_checksum"),
        strict=True,
    ):
        body = dict(payload)
        checksum = body.pop(field)
        assert canonical_checksum(body) == checksum
    resilience = first[2]
    for event in resilience["depletion_events"]:
        body = dict(event)
        checksum = body.pop("event_checksum")
        assert canonical_checksum(body) == checksum
    for resilience_slice in resilience["resilience_slices"]:
        body = dict(resilience_slice)
        checksum = body.pop("slice_checksum")
        assert canonical_checksum(body) == checksum


def test_lot43_safety_is_offline_non_decisional_and_non_executable() -> None:
    state, _, resilience = _build()
    safety = state["safety"]
    assert safety["analysis_only"] is True
    assert safety["used_for_decision"] is False
    assert safety["trade_allowed"] is False
    assert safety["execution_allowed"] is False
    assert safety["approved_size"] == 0
    assert safety["external_connectivity_allowed"] is False
    assert safety["network_ingestion_allowed"] is False
    assert safety["real_credentials_allowed"] is False
    assert resilience["observed_book_only"] is True
    assert resilience["participant_intent_inferred"] is False


def test_same_price_replenishment_is_first_class_observed_outcome() -> None:
    history = (
        _observation(1, 10, (("100", "10"),), (("102", "10"),)),
        _observation(2, 20, (("100", "2"),), (("102", "10"),)),
        _observation(3, 30, (("100", "8"),), (("102", "10"),)),
    )
    result = analyze_book_resilience(history, _policy(), _time(50))
    event = result.depletion_events[0]
    assert event.replenishment_kind == "SAME_PRICE"
    assert event.replenishment_sequence_id == 3
    assert event.replenishment_time_us == 10
    assert event.replenished_quantity == Decimal("6")
    assert event.recovered_fraction == Decimal("0.75")
    assert event.max_window_status == "REPLENISHED"


def test_adjacent_price_replenishment_uses_positive_gain_only() -> None:
    history = (
        _observation(1, 10, (("100", "10"), ("99.9", "1")), (("102", "10"),)),
        _observation(2, 20, (("100", "2"), ("99.9", "1")), (("102", "10"),)),
        _observation(3, 30, (("100", "2"), ("99.9", "5")), (("102", "10"),)),
    )
    result = analyze_book_resilience(history, _policy(adjacent_distance_bps="20"), _time(50))
    event = result.depletion_events[0]
    assert event.replenishment_kind == "ADJACENT_PRICE"
    assert event.replenished_quantity == Decimal("4")
    assert event.recovered_fraction == Decimal("0.5")


def test_same_price_precedes_adjacent_price_at_same_observation() -> None:
    history = (
        _observation(1, 10, (("100", "10"), ("99.9", "1")), (("102", "10"),)),
        _observation(2, 20, (("100", "2"), ("99.9", "1")), (("102", "10"),)),
        _observation(3, 30, (("100", "5"), ("99.9", "5")), (("102", "10"),)),
    )
    result = analyze_book_resilience(history, _policy(adjacent_distance_bps="20"), _time(50))
    assert result.depletion_events[0].replenishment_kind == "SAME_PRICE"


def test_bid_mid_shift_is_structural_not_quantity_recovery() -> None:
    history = (
        _observation(1, 10, (("100", "10"),), (("102", "10"),)),
        _observation(2, 20, (("100", "2"),), (("102", "10"),)),
        _observation(3, 30, (("99", "2"),), (("101", "10"),)),
    )
    result = analyze_book_resilience(history, _policy(mid_shift_min_bps="1"), _time(50))
    event = result.depletion_events[0]
    assert event.replenishment_kind == "MID_SHIFT"
    assert event.replenished_quantity == Decimal("0")
    assert event.recovered_fraction == Decimal("0")
    assert event.directional_mid_shift_bps > 0
    assert event.max_window_status == "MID_SHIFTED"


def test_ask_mid_shift_is_directional() -> None:
    history = (
        _observation(1, 10, (("100", "10"),), (("102", "10"),)),
        _observation(2, 20, (("100", "10"),), (("102", "2"),)),
        _observation(3, 30, (("101", "10"),), (("103", "2"),)),
    )
    result = analyze_book_resilience(history, _policy(mid_shift_min_bps="1"), _time(50))
    event = next(item for item in result.depletion_events if item.side == "ASK")
    assert event.replenishment_kind == "MID_SHIFT"
    assert event.directional_mid_shift_bps > 0


def test_small_decrease_below_quantity_threshold_is_not_depletion() -> None:
    history = (
        _observation(1, 10, (("100", "1"),), (("102", "1"),)),
        _observation(2, 20, (("100", "0.95"),), (("102", "1"),)),
    )
    result = analyze_book_resilience(history, _policy(), _time(50))
    assert result.depletion_events == ()


def test_decrease_below_ratio_threshold_is_not_depletion() -> None:
    history = (
        _observation(1, 10, (("100", "10"),), (("102", "10"),)),
        _observation(2, 20, (("100", "8"),), (("102", "10"),)),
    )
    result = analyze_book_resilience(history, _policy(depletion_min_ratio="0.25"), _time(50))
    assert result.depletion_events == ()


def test_no_future_observation_can_remain_pending() -> None:
    history = (
        _observation(1, 10_000, (("100", "10"),), (("102", "10"),)),
        _observation(2, 20_000, (("100", "2"),), (("102", "10"),)),
    )
    result = analyze_book_resilience(history, _policy(), _time(30_000))
    event = result.depletion_events[0]
    assert event.max_window_status == "PENDING_WINDOW"
    by_horizon = {item.horizon_us: item for item in result.resilience_slices if item.side == "BID"}
    assert by_horizon[10_000].resilience_status == "FRAGILE"
    assert by_horizon[25_000].resilience_status == "PENDING"


def test_replenishment_after_max_window_is_not_counted() -> None:
    history = (
        _observation(1, 10, (("100", "10"),), (("102", "10"),)),
        _observation(2, 20, (("100", "2"),), (("102", "10"),)),
        _observation(3, 50_000, (("100", "10"),), (("102", "10"),)),
    )
    result = analyze_book_resilience(history, _policy(), _time(60_000))
    assert result.depletion_events[0].replenishment_kind == "NONE"
    assert result.depletion_events[0].max_window_status == "EXPIRED_NO_REPLENISHMENT"


def test_adjacent_gain_outside_configured_distance_is_ignored() -> None:
    history = (
        _observation(1, 10, (("100", "10"), ("90", "1")), (("102", "10"),)),
        _observation(2, 20, (("100", "2"), ("90", "1")), (("102", "10"),)),
        _observation(3, 30, (("100", "2"), ("90", "10")), (("102", "10"),)),
    )
    result = analyze_book_resilience(history, _policy(adjacent_distance_bps="20"), _time(50))
    assert result.depletion_events[0].replenishment_kind == "NONE"


def test_resilience_slice_becomes_resilient_when_all_events_recover() -> None:
    history = (
        _observation(1, 10, (("100", "10"),), (("102", "10"),)),
        _observation(2, 20, (("100", "2"),), (("102", "10"),)),
        _observation(3, 30, (("100", "10"),), (("102", "10"),)),
    )
    result = analyze_book_resilience(history, _policy(), _time(50))
    bid = next(
        item
        for item in result.resilience_slices
        if item.side == "BID" and item.horizon_us == 10_000
    )
    assert bid.resilience_status == "RESILIENT"
    assert bid.mean_recovered_fraction == Decimal("1")
    assert bid.mean_replenishment_time_us == Decimal("10")


def test_resilience_slice_becomes_shifted_when_all_events_shift() -> None:
    history = (
        _observation(1, 10, (("100", "10"),), (("102", "10"),)),
        _observation(2, 20, (("100", "2"),), (("102", "10"),)),
        _observation(3, 30, (("99", "2"),), (("101", "10"),)),
    )
    result = analyze_book_resilience(history, _policy(mid_shift_min_bps="1"), _time(50))
    bid = next(
        item
        for item in result.resilience_slices
        if item.side == "BID" and item.horizon_us == 10_000
    )
    assert bid.resilience_status == "SHIFTED"


def test_volatility_conditioning_has_quiet_normal_and_stressed_buckets() -> None:
    quiet = (
        _observation(1, 10, (("100", "1"),), (("102", "1"),)),
        _observation(2, 20, (("100", "1"),), (("102", "1"),)),
    )
    assert analyze_book_resilience(quiet, _policy(), _time(30)).volatility_regime == "QUIET"
    moving = (
        _observation(1, 10, (("100", "1"),), (("102", "1"),)),
        _observation(2, 20, (("100.01", "1"),), (("102.01", "1"),)),
    )
    assert (
        analyze_book_resilience(
            moving,
            _policy(quiet_max="0.05", stressed_min="5"),
            _time(30),
        ).volatility_regime
        == "NORMAL"
    )
    assert (
        analyze_book_resilience(
            moving,
            _policy(quiet_max="0.001", stressed_min="0.5"),
            _time(30),
        ).volatility_regime
        == "STRESSED"
    )


def test_atomic_persistence_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    audit_path = tmp_path / "audit.json"
    resilience_path = tmp_path / "resilience.json"
    monkeypatch.setattr(engine, "STATE_PATH", state_path)
    monkeypatch.setattr(engine, "AUDIT_PATH", audit_path)
    monkeypatch.setattr(engine, "RESILIENCE_PATH", resilience_path)
    first = write_lot43_artifacts(ROOT, CODE_COMMIT)
    second = write_lot43_artifacts(ROOT, CODE_COMMIT)
    assert first == second
    assert load_json_object(state_path) == first[0]
    assert load_json_object(audit_path) == first[1]
    assert load_json_object(resilience_path) == first[2]


def test_config_rejects_numeric_string_coercion(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def mutate(config: dict[str, object]) -> None:
        config["depletion_min_quantity"] = 0.1

    _temporary_config(monkeypatch, tmp_path, mutate)
    with pytest.raises(Lot43ValidationError):
        build_lot43_artifacts(ROOT, CODE_COMMIT)


def test_stale_lot42_input_is_fail_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def mutate(config: dict[str, object]) -> None:
        config["decision_time"] = "2026-08-06T19:18:41.000000Z"
        config["generated_at"] = "2026-08-06T19:18:41.000000Z"

    _temporary_config(monkeypatch, tmp_path, mutate)
    with pytest.raises(Lot43ValidationError, match="stale"):
        build_lot43_artifacts(ROOT, CODE_COMMIT)


def test_tampered_lot42_state_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    state = load_json_object(ROOT / "data/audit/liquidity_zones_walls_and_voids_engine_lot42.json")
    state["liquidity_zones"]["participant_intent_inferred"] = True
    path = tmp_path / "tampered-lot42-state.json"
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def mutate(config: dict[str, object]) -> None:
        config["lot42_state_path"] = str(path)

    _temporary_config(monkeypatch, tmp_path, mutate)
    with pytest.raises(Lot43ValidationError, match="state checksum"):
        build_lot43_artifacts(ROOT, CODE_COMMIT)


def test_resilience_checksum_is_tamper_evident() -> None:
    _, _, resilience = _build()
    tampered = copy.deepcopy(resilience)
    checksum = tampered.pop("resilience_checksum")
    assert canonical_checksum(tampered) == checksum
    tampered["participant_intent_inferred"] = True
    assert canonical_checksum(tampered) != checksum
