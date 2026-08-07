from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_quality_engine import build_lot34_artifacts
from crypto_quant_bot.data_governance.market_data_quality_engine_models import (
    DataAnomalyV1,
    DataQualityStateV1,
    DataQualityVetoV1,
    Lot34MetricsV1,
    Lot34RunContextV1,
)
from crypto_quant_bot.data_governance.market_data_quality_engine_validation import (
    MarketDataQualityError,
    decimal_from_string,
    lot34_safety,
    parse_utc_timestamp,
    require_git_sha,
    require_identifier,
    require_integer,
    require_sha256,
    require_string_list,
    require_text,
    validate_lot34_safety,
)

ROOT = Path(__file__).resolve().parents[1]
SHA = "1" * 40


def valid_anomaly() -> DataAnomalyV1:
    return DataAnomalyV1(
        "anomaly-1",
        "STALE_DATA",
        "ERROR",
        ("record-1",),
        "2026-08-06T19:15:00Z",
        "2026-08-06T19:15:00Z",
        False,
        True,
        "DQ_STALE_DATA",
    )


def valid_quality() -> DataQualityStateV1:
    return DataQualityStateV1(
        "source-1",
        "instrument-1",
        "1m",
        1,
        1,
        1,
        0,
        10_000,
        10_000,
        10_000,
        10_000,
        10_000,
        "PASS",
    )


def valid_veto() -> DataQualityVetoV1:
    return DataQualityVetoV1("ALLOW_ANALYSIS", True, 9500, 10_000, (), ("OK",))


def test_validation_helpers_reject_bad_values() -> None:
    for value in (None, "", " padded "):
        with pytest.raises(MarketDataQualityError):
            require_text(value, "field")
    with pytest.raises(MarketDataQualityError):
        require_identifier("bad/id", "identifier")
    for value in (True, "1"):
        with pytest.raises(MarketDataQualityError):
            require_integer(value, "integer")
    with pytest.raises(MarketDataQualityError):
        require_integer(-1, "integer", minimum=0)
    with pytest.raises(MarketDataQualityError):
        require_sha256("a" * 63, "hash")
    with pytest.raises(MarketDataQualityError):
        require_git_sha("a" * 39)
    with pytest.raises(MarketDataQualityError):
        parse_utc_timestamp("2026-08-06T19:15:00+00:00", "time")
    with pytest.raises(MarketDataQualityError):
        parse_utc_timestamp("not-a-dateZ", "time")
    with pytest.raises(MarketDataQualityError):
        decimal_from_string("NaN", "decimal")
    with pytest.raises(MarketDataQualityError):
        require_string_list("bad", "values")
    assert require_string_list(["a", "b"], "values") == ("a", "b")
    with pytest.raises(MarketDataQualityError):
        validate_lot34_safety({})
    assert validate_lot34_safety(lot34_safety()) == lot34_safety()


def test_run_context_rejects_wrong_runtime() -> None:
    with pytest.raises(MarketDataQualityError):
        Lot34RunContextV1("run", "PAPER", "config", SHA, "corr")


@pytest.mark.parametrize(
    "changes",
    [
        {"anomaly_type": "UNKNOWN"},
        {"severity": "BOGUS"},
        {"record_ids": ()},
        {"interval_end": "2026-08-06T19:14:59Z"},
        {"correction_permitted": True},
        {"quarantined": False},
    ],
)
def test_anomaly_contract_rejects_invalid_states(changes: dict[str, object]) -> None:
    with pytest.raises(MarketDataQualityError):
        replace(valid_anomaly(), **changes)


def test_quality_state_rejects_bounds_and_status() -> None:
    with pytest.raises(MarketDataQualityError):
        replace(valid_quality(), record_count=-1)
    with pytest.raises(MarketDataQualityError):
        replace(valid_quality(), quality_score_bps=10_001)
    with pytest.raises(MarketDataQualityError):
        replace(valid_quality(), status="INVALID")


@pytest.mark.parametrize(
    "changes",
    [
        {"action": "INVALID"},
        {"minimum_quality_bps": -1},
        {"observed_quality_bps": 10_001},
        {"blocking_anomaly_types": ("UNKNOWN",)},
        {"reason_codes": ()},
    ],
)
def test_veto_contract_rejects_invalid_states(changes: dict[str, object]) -> None:
    with pytest.raises(MarketDataQualityError):
        replace(valid_veto(), **changes)


def test_metrics_reject_negative_values() -> None:
    with pytest.raises(MarketDataQualityError):
        Lot34MetricsV1(-1, 0, 0, 0, 0)


def test_state_contract_rejects_invalid_states() -> None:
    state, _ = build_lot34_artifacts(ROOT, SHA)
    with pytest.raises(MarketDataQualityError):
        replace(state, event_time="2026-08-06T19:19:00Z")
    with pytest.raises(MarketDataQualityError):
        replace(state, validation_state="INVALID")
    with pytest.raises(MarketDataQualityError):
        replace(state, quality_states=())
    with pytest.raises(MarketDataQualityError):
        replace(state, quarantine_record_ids=("z", "a"))


def test_audit_contract_rejects_invalid_veto() -> None:
    _, audit = build_lot34_artifacts(ROOT, SHA)
    with pytest.raises(MarketDataQualityError):
        replace(audit, veto_action="INVALID")
