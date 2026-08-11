from __future__ import annotations

import copy
import json
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.spread_depth_and_imbalance_engine import (
    CONFIG_PATH,
    EXPECTED_INTEGRITY,
    EXPECTED_VETO,
    _build_feature,
    _verify_health,
    build_lot41_artifacts,
)
from crypto_quant_bot.microstructure.spread_depth_and_imbalance_engine_models import DepthBandV1
from crypto_quant_bot.microstructure.spread_depth_and_imbalance_engine_validation import (
    IMBALANCE_DEFINED,
    IMBALANCE_UNDEFINED,
    Lot41ValidationError,
    parse_book_levels,
    parse_depth_bands,
    symmetric_imbalance,
    validate_book_open,
    validate_reference_times,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "a" * 40


def _build() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return tuple(item.to_dict() for item in build_lot41_artifacts(ROOT, CODE_COMMIT))  # type: ignore[return-value]


def test_lot41_reference_values_and_lineage() -> None:
    state, audit, feature = _build()
    assert state["validation_state"] == "VALIDATED_OFFLINE_SPREAD_DEPTH_IMBALANCE_ONLY"
    assert feature["spread_absolute"] == "0.2"
    assert feature["mid_price"] == "50025"
    assert feature["spread_bps"] == "0.03998000999500249875062468766"
    assert feature["microprice"] == "50025.01612903225806451612903"
    assert audit["state_output_checksum"] == state["output_checksum"]
    assert audit["feature_checksum"] == feature["feature_checksum"]
    assert state["book_features"] == feature
    lineage = state["lineage"]
    assert lineage["lot40_integrity_checksum"] == EXPECTED_INTEGRITY
    assert lineage["lot40_veto_checksum"] == EXPECTED_VETO


def test_lot41_reference_depth_bands_are_exact_observed_depth_only() -> None:
    _, _, feature = _build()
    bands = feature["depth_bands"]
    assert [item["band_bps"] for item in bands] == ["0.025", "0.05", "0.1"]
    assert [item["bid_quantity"] for item in bands] == ["0.9", "0.9", "1.4"]
    assert [item["ask_quantity"] for item in bands] == ["0.65", "1.75", "2.15"]
    assert [item["bid_levels_observed"] for item in bands] == [1, 1, 2]
    assert [item["ask_levels_observed"] for item in bands] == [1, 2, 3]
    assert all(item["coverage_status"] == "OBSERVED_LEVELS_ONLY" for item in bands)
    assert feature["observed_depth_only"] is True
    assert feature["extrapolated"] is False


def test_lot41_imbalance_is_symmetric_bounded_and_zero_denominator_explicit() -> None:
    value, status = symmetric_imbalance(Decimal("0.9"), Decimal("0.65"))
    assert status == IMBALANCE_DEFINED
    assert value == Decimal("0.25") / Decimal("1.55")
    assert value is not None and Decimal("-1") <= value <= Decimal("1")
    undefined, undefined_status = symmetric_imbalance(Decimal("0"), Decimal("0"))
    assert undefined is None
    assert undefined_status == IMBALANCE_UNDEFINED
    band = DepthBandV1(Decimal("1"), Decimal("0"), Decimal("0"), 0, 0, None, undefined_status)
    assert band.to_dict()["imbalance"] is None


def test_lot41_cumulative_depth_is_exact_prefix_sum() -> None:
    _, _, feature = _build()
    bids = feature["cumulative_depth"]["bids"]
    asks = feature["cumulative_depth"]["asks"]
    assert [item["cumulative_quantity"] for item in bids] == ["0.9", "1.4"]
    assert [item["cumulative_quantity"] for item in asks] == ["0.65", "1.75", "2.15"]
    assert all(Decimal(item["distance_bps"]) >= 0 for item in bids + asks)


def test_lot41_run_is_deterministic_and_checksums_are_canonical() -> None:
    first = _build()
    second = _build()
    assert first == second
    for payload, field in zip(first, ("output_checksum", "audit_checksum", "feature_checksum"), strict=True):
        body = dict(payload)
        checksum = body.pop(field)
        assert canonical_checksum(body) == checksum


def test_lot41_safety_is_non_executable() -> None:
    state, _, _ = _build()
    safety = state["safety"]
    assert safety["analysis_only"] is True
    assert safety["used_for_decision"] is False
    assert safety["trade_allowed"] is False
    assert safety["execution_allowed"] is False
    assert safety["approved_size"] == 0
    assert safety["external_connectivity_allowed"] is False
    assert safety["network_ingestion_allowed"] is False
    assert safety["real_credentials_allowed"] is False


def test_lot41_rejects_numeric_coercion_zero_negative_and_non_finite_levels() -> None:
    invalid = (
        [{"price": 50024.9, "quantity": "0.9"}],
        [{"price": "50024.9", "quantity": 0.9}],
        [{"price": "50024.9", "quantity": "0"}],
        [{"price": "-1", "quantity": "1"}],
        [{"price": "NaN", "quantity": "1"}],
    )
    for levels in invalid:
        with pytest.raises(Lot41ValidationError):
            parse_book_levels(levels, "bids")


def test_lot41_rejects_empty_unilateral_unordered_and_crossed_books() -> None:
    with pytest.raises(Lot41ValidationError, match="non-empty"):
        parse_book_levels([], "bids")
    with pytest.raises(Lot41ValidationError, match="strictly monotonic"):
        parse_book_levels(
            [{"price": "2", "quantity": "1"}, {"price": "3", "quantity": "1"}],
            "bids",
        )
    with pytest.raises(Lot41ValidationError, match="crossed or locked"):
        validate_book_open(Decimal("10"), Decimal("10"))
    with pytest.raises(Lot41ValidationError, match="crossed or locked"):
        validate_book_open(Decimal("11"), Decimal("10"))


def test_lot41_depth_band_configuration_is_strict_and_versioned() -> None:
    assert parse_depth_bands(["0.025", "0.05", "0.10"]) == (
        Decimal("0.025"), Decimal("0.05"), Decimal("0.10")
    )
    for invalid in (["0.1", "0.05"], ["0.1", "0.1"], [0.1], ["0"]):
        with pytest.raises(Lot41ValidationError):
            parse_depth_bands(invalid)


def test_lot41_future_or_mismatched_time_is_rejected() -> None:
    book = {
        "event_time": "2026-08-06T19:18:40.065000Z",
        "receive_time": "2026-08-06T19:18:40.070000Z",
    }
    integrity = {
        "event_time": book["event_time"],
        "receive_time": book["receive_time"],
        "decision_time": "2026-08-06T19:18:40.100000Z",
    }
    validate_reference_times(book, integrity, integrity["decision_time"], integrity["decision_time"])
    with pytest.raises(Lot41ValidationError):
        validate_reference_times(book, integrity, "2026-08-06T19:18:40.060000Z", integrity["decision_time"])


def test_lot41_active_or_degraded_health_is_fail_closed() -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    healthy = {"health_status": "HEALTHY", "book_health_score": "100", "crossed": False, "locked": False}
    veto = {"consequence": "NONE", "veto_active": False, "critical_veto_active": False}
    _verify_health(healthy, veto, config)
    degraded = dict(healthy, health_status="DEGRADED")
    with pytest.raises(Lot41ValidationError, match="healthy"):
        _verify_health(degraded, veto, config)
    active = dict(veto, consequence="WAIT", veto_active=True)
    with pytest.raises(Lot41ValidationError, match="active upstream"):
        _verify_health(healthy, active, config)


def test_lot41_price_unit_scaling_preserves_bps_and_imbalance() -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    book = load_json_object(ROOT / config["reconstructed_book_path"])
    integrity = load_json_object(ROOT / config["lot40_book_integrity_path"])
    veto = load_json_object(ROOT / config["lot40_book_health_veto_path"])
    bands = parse_depth_bands(config["depth_bands_bps"])
    original = _build_feature(book, integrity, veto, bands, 50, config["decision_time"])
    scaled = copy.deepcopy(book)
    factor = Decimal("100")
    for side in ("bids", "asks"):
        for level in scaled[side]:
            level["price"] = str(Decimal(level["price"]) * factor)
    with localcontext() as context:
        context.prec = 50
        scaled_feature = _build_feature(scaled, integrity, veto, bands, 50, config["decision_time"])
        expected_spread = original.spread_absolute * factor
        expected_mid = original.mid_price * factor
        expected_microprice = original.microprice * factor
    assert scaled_feature.spread_bps == original.spread_bps
    assert [item.imbalance for item in scaled_feature.depth_bands] == [item.imbalance for item in original.depth_bands]
    assert scaled_feature.spread_absolute == expected_spread
    assert scaled_feature.mid_price == expected_mid
    assert scaled_feature.microprice == expected_microprice


def test_lot41_feature_checksum_is_tamper_evident_roundtrip() -> None:
    _, _, feature = _build()
    encoded = json.dumps(feature, sort_keys=True)
    decoded = json.loads(encoded)
    assert decoded == feature
    body = dict(decoded)
    checksum = body.pop("feature_checksum")
    assert canonical_checksum(body) == checksum
    body["spread_absolute"] = "0.3"
    assert canonical_checksum(body) != checksum
