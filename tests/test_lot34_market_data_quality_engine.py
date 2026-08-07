from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_quality_engine import (
    build_lot34_artifacts,
    detect_anomalies,
    persist_lot34_artifacts,
)
from crypto_quant_bot.data_governance.market_data_quality_engine_validation import (
    MarketDataQualityError,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/data_governance/market_data_quality_engine_v1.json").read_text())
CODE_SHA = "1" * 40


def anomaly_types(config: dict[str, object]) -> set[str]:
    return {item.anomaly_type for item in detect_anomalies(config)}


def test_reference_dataset_passes_and_is_deterministic(tmp_path: Path) -> None:
    state1, audit1 = build_lot34_artifacts(ROOT, CODE_SHA)
    state2, audit2 = build_lot34_artifacts(ROOT, CODE_SHA)
    assert state1.to_dict() == state2.to_dict()
    assert audit1.to_dict() == audit2.to_dict()
    assert state1.validation_state == "VALIDATED_DATA_QUALITY_ONLY"
    assert state1.veto.action == "ALLOW_ANALYSIS"
    assert state1.anomalies == ()
    assert state1.quarantine_record_ids == ()
    assert state1.quality_states[0].quality_score_bps >= 9500
    persist_lot34_artifacts(tmp_path, state1, audit1)
    assert (tmp_path / "data/audit/market_data_quality_engine_lot34.json").is_file()


def test_missing_interval_detected() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"].pop(1)
    assert "MISSING_INTERVAL" in anomaly_types(config)


def test_duplicate_detected() -> None:
    config = copy.deepcopy(CONFIG)
    duplicate = copy.deepcopy(config["records"][1])
    duplicate["record_id"] = "quality-candle-2-copy"
    config["records"].append(duplicate)
    assert "DUPLICATE" in anomaly_types(config)


def test_out_of_order_detected() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][1], config["records"][2] = config["records"][2], config["records"][1]
    assert "OUT_OF_ORDER" in anomaly_types(config)


def test_stale_detected() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][0]["available_at"] = "2026-08-06T19:15:00.000000Z"
    assert "STALE_DATA" in anomaly_types(config)


def test_invalid_ohlc_detected() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][1]["high"] = "57010.00"
    assert "INVALID_OHLC" in anomaly_types(config)


def test_negative_volume_detected() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][1]["volume"] = "-0.01"
    assert "NEGATIVE_VOLUME" in anomaly_types(config)


def test_impossible_spread_detected() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][1]["bid"] = "57100.00"
    config["records"][1]["ask"] = "57099.00"
    assert "IMPOSSIBLE_SPREAD" in anomaly_types(config)


def test_schema_drift_detected_for_extra_field_and_version() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][1]["unexpected"] = "x"
    config["records"][2]["source_schema_version"] = "ohlc-quality-record-v2"
    assert "SCHEMA_DRIFT" in anomaly_types(config)


def test_quarantine_is_reference_only_and_raw_input_unchanged() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][1]["volume"] = "-0.01"
    original = copy.deepcopy(config["records"])
    anomalies = detect_anomalies(config)
    assert config["records"] == original
    assert anomalies[0].correction_permitted is False
    assert anomalies[0].quarantined is True


def test_boundary_equal_staleness_is_not_stale() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][0]["available_at"] = "2026-08-06T19:16:00.100000Z"
    assert "STALE_DATA" not in anomaly_types(config)


def test_locked_spread_is_allowed() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][1]["bid"] = "57090.00"
    config["records"][1]["ask"] = "57090.00"
    assert "IMPOSSIBLE_SPREAD" not in anomaly_types(config)


def test_bad_decimal_fails_closed() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][1]["close"] = "not-a-number"
    with pytest.raises(MarketDataQualityError):
        detect_anomalies(config)


def test_bad_gate_checksum_fails_closed(tmp_path: Path) -> None:
    for relative in (
        "config/data_governance/market_data_quality_engine_v1.json",
        "data/audit/lot34_v3_entry_gate.json",
        "data/audit/timestamp_clock_and_timezone_governance_lot33.json",
        "data/audit/timestamp_clock_and_timezone_governance_audit_lot33.json",
        "data/audit/canonical_time_envelopes_lot33.json",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    gate_path = tmp_path / "data/audit/lot34_v3_entry_gate.json"
    gate = json.loads(gate_path.read_text())
    gate["output_checksum"] = "0" * 64
    gate_path.write_text(json.dumps(gate))
    with pytest.raises(MarketDataQualityError):
        build_lot34_artifacts(tmp_path, CODE_SHA)


def test_config_unknown_field_fails_closed() -> None:
    from crypto_quant_bot.data_governance.market_data_quality_engine import _validate_config

    config = copy.deepcopy(CONFIG)
    config["unexpected"] = 1
    with pytest.raises(MarketDataQualityError):
        _validate_config(config)


def test_config_schema_and_version_must_match() -> None:
    from crypto_quant_bot.data_governance.market_data_quality_engine import _validate_config

    config = copy.deepcopy(CONFIG)
    config["schema_version"] = "wrong"
    with pytest.raises(MarketDataQualityError):
        _validate_config(config)
    config = copy.deepcopy(CONFIG)
    config["config_version"] = "wrong"
    with pytest.raises(MarketDataQualityError):
        _validate_config(config)


def test_config_causal_order_must_hold() -> None:
    from crypto_quant_bot.data_governance.market_data_quality_engine import _validate_config

    config = copy.deepcopy(CONFIG)
    config["available_at"] = "2026-08-06T19:17:59.000000Z"
    with pytest.raises(MarketDataQualityError):
        _validate_config(config)


def test_config_quality_threshold_bounds() -> None:
    from crypto_quant_bot.data_governance.market_data_quality_engine import _validate_config

    config = copy.deepcopy(CONFIG)
    config["minimum_quality_bps"] = 10001
    with pytest.raises(MarketDataQualityError):
        _validate_config(config)


def test_config_requires_timeframe_map_and_records() -> None:
    from crypto_quant_bot.data_governance.market_data_quality_engine import _validate_config

    config = copy.deepcopy(CONFIG)
    config["timeframe_seconds"] = {}
    with pytest.raises(MarketDataQualityError):
        _validate_config(config)
    config = copy.deepcopy(CONFIG)
    config["records"] = []
    with pytest.raises(MarketDataQualityError):
        _validate_config(config)


def test_unknown_timeframe_fails_closed() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][0]["timeframe"] = "5m"
    with pytest.raises(MarketDataQualityError):
        detect_anomalies(config)


def test_available_before_event_fails_closed() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][0]["available_at"] = "2026-08-06T19:14:59.000000Z"
    with pytest.raises(MarketDataQualityError):
        detect_anomalies(config)


def test_negative_bid_is_impossible_spread() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][0]["bid"] = "-1"
    assert "IMPOSSIBLE_SPREAD" in anomaly_types(config)


def test_high_below_low_is_invalid_ohlc() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"][0]["high"] = "56900"
    assert "INVALID_OHLC" in anomaly_types(config)


def test_schema_drift_missing_group_identity_fails_closed() -> None:
    from crypto_quant_bot.data_governance.market_data_quality_engine import (
        _build_quality_states,
    )

    config = copy.deepcopy(CONFIG)
    del config["records"][0]["source_id"]
    anomalies = detect_anomalies(config)
    with pytest.raises(MarketDataQualityError):
        _build_quality_states(config, anomalies)


def test_veto_blocks_anomaly_and_unknown_quality() -> None:
    from crypto_quant_bot.data_governance.market_data_quality_engine import (
        _build_quality_states,
        _build_veto,
    )

    config = copy.deepcopy(CONFIG)
    config["records"][1]["volume"] = "-1"
    anomalies = detect_anomalies(config)
    states = _build_quality_states(config, anomalies)
    veto = _build_veto(states, anomalies, 9500)
    assert veto.action == "BLOCK_ANALYSIS_OR_TRADING"
    assert veto.reason_codes == ("DATA_QUALITY_ANOMALY_PRESENT",)
    unknown = _build_veto((), (), 9500)
    assert unknown.action == "BLOCK_ANALYSIS_OR_TRADING"
    assert unknown.reason_codes == ("DATA_QUALITY_UNKNOWN",)


def test_veto_blocks_low_score_without_anomaly() -> None:
    from dataclasses import replace

    from crypto_quant_bot.data_governance.market_data_quality_engine import (
        _build_quality_states,
        _build_veto,
    )

    states = _build_quality_states(copy.deepcopy(CONFIG), ())
    low = (replace(states[0], quality_score_bps=9000, status="BLOCKED"),)
    veto = _build_veto(low, (), 9500)
    assert veto.reason_codes == ("DATA_QUALITY_SCORE_BELOW_THRESHOLD",)


def test_zero_staleness_threshold_handles_fresh_record() -> None:
    from crypto_quant_bot.data_governance.market_data_quality_engine import (
        _build_quality_states,
    )

    config = copy.deepcopy(CONFIG)
    config["max_staleness_seconds"] = 0
    config["generated_at"] = config["records"][-1]["available_at"]
    states = _build_quality_states(config, ())
    assert states[0].freshness_bps == 10000


def test_records_must_be_objects() -> None:
    config = copy.deepcopy(CONFIG)
    config["records"] = ["bad"]
    with pytest.raises(MarketDataQualityError):
        detect_anomalies(config)
