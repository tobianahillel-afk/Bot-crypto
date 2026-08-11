from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path
from typing import Callable

import pytest

import crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_engine as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_analysis import (
    BookObservation,
    LiquidityAnalysisPolicy,
    analyze_observations,
    reconstruct_observation_history,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_engine import (
    CONFIG_PATH,
    build_lot42_artifacts,
    write_lot42_artifacts,
)
from crypto_quant_bot.microstructure.liquidity_zones_walls_and_voids_engine_validation import (
    DISPLAYED_WALL,
    HIGH_CONFIDENCE,
    LIQUIDITY_VOID,
    LOW_CONFIDENCE,
    PERSISTENT_ZONE,
    Lot42ValidationError,
)
from crypto_quant_bot.microstructure.order_book_l2_snapshot_engine_models import OrderBookLevelV1

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "b" * 40


def _build() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return tuple(item.to_dict() for item in build_lot42_artifacts(ROOT, CODE_COMMIT))  # type: ignore[return-value]


def _policy(
    *,
    cluster_distance_bps: str = "1",
    history_match_distance_bps: str = "2",
    wall_min_notional: str = "50",
    persistent_min_observations: int = 2,
    persistent_min_ratio: str = "0.5",
    void_min_gap_bps: str = "5",
    cancellation_threshold: str = "0.5",
) -> LiquidityAnalysisPolicy:
    return LiquidityAnalysisPolicy(
        50,
        Decimal(cluster_distance_bps),
        Decimal(history_match_distance_bps),
        Decimal(wall_min_notional),
        persistent_min_observations,
        Decimal(persistent_min_ratio),
        Decimal(void_min_gap_bps),
        Decimal(cancellation_threshold),
    )


def _observation(
    sequence: int,
    bids: tuple[tuple[str, str], ...],
    asks: tuple[tuple[str, str], ...],
) -> BookObservation:
    return BookObservation(
        "synthetic-offline-source",
        "OFFLINE",
        "TEST-SPOT",
        "SPOT",
        sequence,
        f"2026-08-06T19:18:40.{sequence:06d}Z",
        f"2026-08-06T19:18:40.{sequence + 1:06d}Z",
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
    path = tmp_path / "lot42-config.json"
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    monkeypatch.setattr(engine, "CONFIG_PATH", path)
    return config


def test_lot42_reference_values_lineage_and_links() -> None:
    state, audit, zone_set = _build()
    assert state["validation_state"] == "VALIDATED_OFFLINE_LIQUIDITY_ZONES_WALLS_VOIDS_ONLY"
    assert zone_set["sequence_id"] == 1003
    assert zone_set["history_sequence_ids"] == [1001, 1002, 1003]
    assert zone_set["mid_price"] == "50025"
    assert len(zone_set["zones"]) == 3
    assert len(zone_set["voids"]) == 1
    assert audit["state_output_checksum"] == state["output_checksum"]
    assert audit["zone_set_checksum"] == zone_set["zone_set_checksum"]
    assert state["liquidity_zones"] == zone_set
    assert state["lineage"] == audit["lineage"]


def test_lot42_reference_classifications_are_exact_and_non_intentional() -> None:
    _, _, zone_set = _build()
    zones = zone_set["zones"]
    assert all(DISPLAYED_WALL in zone["classifications"] for zone in zones)
    assert sum(PERSISTENT_ZONE in zone["classifications"] for zone in zones) == 2
    assert sum(zone["confidence_status"] == HIGH_CONFIDENCE for zone in zones) == 2
    assert sum(zone["confidence_status"] == LOW_CONFIDENCE for zone in zones) == 1
    assert all(zone["participant_intent"] == "NOT_INFERRED" for zone in zones)
    assert zone_set["participant_intent_inferred"] is False
    assert zone_set["voids"][0]["classification"] == LIQUIDITY_VOID
    assert zone_set["voids"][0]["side"] == "BID"
    assert zone_set["voids"][0]["participant_intent"] == "NOT_INFERRED"


def test_lot42_reference_history_is_reconstructed_only_from_certified_prefixes() -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    snapshot = engine._verify_lot38_snapshot(ROOT, config)
    deltas = engine._load_deltas(ROOT, config)
    history = reconstruct_observation_history(snapshot, deltas)
    assert [item.sequence_id for item in history] == [1001, 1002, 1003]
    assert history[-1].bids == (
        OrderBookLevelV1(Decimal("50024.9"), Decimal("0.9")),
        OrderBookLevelV1(Decimal("50024.7"), Decimal("0.5")),
    )
    assert history[-1].asks[-1] == OrderBookLevelV1(Decimal("50025.3"), Decimal("0.4"))


def test_lot42_run_is_deterministic_and_all_checksums_are_canonical() -> None:
    first = _build()
    second = _build()
    assert first == second
    for payload, field in zip(
        first,
        ("output_checksum", "audit_checksum", "zone_set_checksum"),
        strict=True,
    ):
        body = dict(payload)
        checksum = body.pop(field)
        assert canonical_checksum(body) == checksum
    zone_set = first[2]
    checked = [
        *((zone, "zone_checksum") for zone in zone_set["zones"]),
        *((void, "void_checksum") for void in zone_set["voids"]),
    ]
    for item, field in checked:
        body = dict(item)
        checksum = body.pop(field)
        assert canonical_checksum(body) == checksum


def test_lot42_safety_is_offline_non_decisional_and_non_executable() -> None:
    state, _, zone_set = _build()
    safety = state["safety"]
    assert safety["analysis_only"] is True
    assert safety["used_for_decision"] is False
    assert safety["trade_allowed"] is False
    assert safety["execution_allowed"] is False
    assert safety["approved_size"] == 0
    assert safety["external_connectivity_allowed"] is False
    assert safety["network_ingestion_allowed"] is False
    assert safety["real_credentials_allowed"] is False
    assert zone_set["observed_book_only"] is True
    assert zone_set["participant_intent_inferred"] is False


def test_lot42_bilateral_void_detection_works_on_observed_levels() -> None:
    history = (
        _observation(
            1,
            (("100", "1"), ("99", "1"), ("98", "1")),
            (("102", "1"), ("103", "1"), ("104", "1")),
        ),
        _observation(
            2,
            (("100", "1"), ("99", "1"), ("98", "1")),
            (("102", "1"), ("103", "1"), ("104", "1")),
        ),
    )
    result = analyze_observations(history, _policy(void_min_gap_bps="50"))
    assert {item.side for item in result.voids} == {"BID", "ASK"}
    assert all(item.classification == LIQUIDITY_VOID for item in result.voids)
    assert all(item.participant_intent == "NOT_INFERRED" for item in result.voids)


def test_lot42_instantly_cancelled_wall_is_low_confidence() -> None:
    history = (
        _observation(1, (("100", "10"),), (("102", "1"),)),
        _observation(2, (("100", "1"),), (("102", "1"),)),
    )
    result = analyze_observations(
        history,
        _policy(wall_min_notional="50", cancellation_threshold="0.5"),
    )
    bid_wall = next(item for item in result.zones if item.side == "BID")
    assert DISPLAYED_WALL in bid_wall.classifications
    assert PERSISTENT_ZONE in bid_wall.classifications
    assert bid_wall.cancelled_quantity == Decimal("9")
    assert bid_wall.cancellation_rate == Decimal("0.9")
    assert bid_wall.confidence_status == LOW_CONFIDENCE
    assert "LOT42_WALL_LOW_CONFIDENCE" in bid_wall.reason_codes


def test_lot42_top_of_book_may_change_without_changing_market_identity() -> None:
    history = (
        _observation(1, (("100", "2"),), (("102", "2"),)),
        _observation(2, (("101", "2"),), (("103", "2"),)),
    )
    result = analyze_observations(
        history,
        _policy(history_match_distance_bps="100"),
    )
    assert result.observations[-1].mid_price == Decimal("102")


def test_lot42_stale_current_feature_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def mutate(config: dict[str, object]) -> None:
        config["decision_time"] = "2026-08-06T19:18:41.000000Z"
        config["generated_at"] = "2026-08-06T19:18:41.000000Z"

    _temporary_config(monkeypatch, tmp_path, mutate)
    with pytest.raises(Lot42ValidationError, match="stale"):
        build_lot42_artifacts(ROOT, CODE_COMMIT)


def test_lot42_rejects_numeric_config_coercion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def mutate(config: dict[str, object]) -> None:
        config["wall_min_notional"] = 25000

    _temporary_config(monkeypatch, tmp_path, mutate)
    with pytest.raises(Lot42ValidationError):
        build_lot42_artifacts(ROOT, CODE_COMMIT)


def test_lot42_rejects_tampered_lot41_feature(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    feature = load_json_object(ROOT / "data/audit/book_feature_state_lot41.json")
    feature["mid_price"] = "50026"
    feature_path = tmp_path / "tampered-feature.json"
    feature_path.write_text(json.dumps(feature, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def mutate(config: dict[str, object]) -> None:
        config["lot41_feature_path"] = str(feature_path)

    _temporary_config(monkeypatch, tmp_path, mutate)
    with pytest.raises(Lot42ValidationError, match="feature checksum"):
        build_lot42_artifacts(ROOT, CODE_COMMIT)


def test_lot42_empty_detected_zone_set_is_valid_when_evidence_supports_none() -> None:
    history = (
        _observation(1, (("100", "1"),), (("102", "1"),)),
        _observation(2, (("90", "1"),), (("112", "1"),)),
    )
    policy = _policy(
        history_match_distance_bps="1",
        wall_min_notional="1000000",
        persistent_min_observations=2,
        persistent_min_ratio="1",
        void_min_gap_bps="5000",
    )
    result = analyze_observations(history, policy)
    assert result.zones == ()


def test_lot42_atomic_persistence_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    audit_path = tmp_path / "audit.json"
    zones_path = tmp_path / "zones.json"
    monkeypatch.setattr(engine, "STATE_PATH", state_path)
    monkeypatch.setattr(engine, "AUDIT_PATH", audit_path)
    monkeypatch.setattr(engine, "ZONE_SET_PATH", zones_path)
    first = write_lot42_artifacts(ROOT, CODE_COMMIT)
    second = write_lot42_artifacts(ROOT, CODE_COMMIT)
    assert first == second
    assert load_json_object(state_path) == first[0]
    assert load_json_object(audit_path) == first[1]
    assert load_json_object(zones_path) == first[2]


def test_lot42_zone_checksum_is_tamper_evident() -> None:
    _, _, zone_set = _build()
    zone = copy.deepcopy(zone_set["zones"][0])
    checksum = zone.pop("zone_checksum")
    assert canonical_checksum(zone) == checksum
    zone["participant_intent"] = "KNOWN"
    assert canonical_checksum(zone) != checksum
