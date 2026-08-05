from __future__ import annotations

import json

import pytest

from crypto_quant_bot.market_analysis.alignment_adapter import adapt_lot25_rows, adapt_lot25_summary
from crypto_quant_bot.market_analysis.alignment_audit import (
    assert_no_forbidden_capabilities,
    build_alignment_evidence,
    replay_matches,
)
from crypto_quant_bot.market_analysis.alignment_common import Lot26ValidationError, checksum
from crypto_quant_bot.market_analysis.alignment_engine import build_alignment_state
from crypto_quant_bot.market_analysis.alignment_io import load_jsonl
from tests.lot26_fixtures import ROOT, load_clock, load_config, load_registry

LOT25 = ROOT / "data/audit/volatility_regime_confluence_timeframes_lot25.jsonl"


def _rows() -> list[dict[str, object]]:
    return load_jsonl(LOT25)


def _built():
    states, availability = adapt_lot25_rows(
        _rows(),
        decision_time="2026-05-25T03:00:00Z",
        code_commit="abcdef1",
    )
    local = next(state for state in states if state.timeframe == "5m")
    higher = next(state for state in states if state.timeframe == "15m")
    alignment = build_alignment_state(
        local,
        [higher],
        availability,
        load_config(),
        load_registry(),
        load_clock(),
        "abcdef1",
    )
    return states, availability, local, higher, alignment


def test_lot25_adapter_is_deterministic_and_temporally_exact() -> None:
    first = adapt_lot25_rows(_rows(), decision_time="2026-05-25T03:00:00Z", code_commit="abcdef1")
    second = adapt_lot25_rows(_rows(), decision_time="2026-05-25T03:00:00Z", code_commit="abcdef1")
    assert [item.to_dict() for item in first[0]] == [item.to_dict() for item in second[0]]
    assert [item.to_dict() for item in first[1]] == [item.to_dict() for item in second[1]]
    assert {state.bar_close_time for state in first[0]} == {"2026-05-25T03:00:00Z"}


def test_lot25_adapter_rejects_bad_scale_future_and_missing_fields() -> None:
    row = dict(_rows()[0])
    row["timeframe"] = "1m"
    with pytest.raises(Lot26ValidationError, match="MTF_SCALE_RELATION_NOT_ALLOWED"):
        adapt_lot25_summary(row, decision_time="2026-05-25T03:00:00Z", code_commit="abcdef1", sequence_id=0)
    row = dict(_rows()[0])
    with pytest.raises(Lot26ValidationError, match="MTF_FUTURE_STATE_REJECTED"):
        adapt_lot25_summary(row, decision_time="2026-05-25T02:59:00Z", code_commit="abcdef1", sequence_id=0)
    row = dict(_rows()[0])
    row.pop("trend_state")
    with pytest.raises(Lot26ValidationError, match="trend_state"):
        adapt_lot25_summary(row, decision_time="2026-05-25T03:00:00Z", code_commit="abcdef1", sequence_id=0)


def test_lot25_adapter_rejects_bad_scores_and_incomplete_pair() -> None:
    row = dict(_rows()[0])
    row["trend_context_score"] = "high"
    with pytest.raises(Lot26ValidationError, match="trend_context_score"):
        adapt_lot25_summary(row, decision_time="2026-05-25T03:00:00Z", code_commit="abcdef1", sequence_id=0)
    with pytest.raises(Lot26ValidationError, match="MTF_SCALE_RELATION_NOT_ALLOWED"):
        adapt_lot25_rows([_rows()[0]], decision_time="2026-05-25T03:00:00Z", code_commit="abcdef1")


def test_real_lot25_to_lot26_oracle() -> None:
    _, _, _, _, alignment = _built()
    assert alignment.component_alignment_scores == {
        "trend": 1.0,
        "range": 1.0,
        "momentum": 1.0,
        "volatility": 0.0,
        "regime": 0.25,
        "confluence": 0.5,
    }
    assert alignment.overall_agreement_score == 0.65
    assert alignment.weighted_coverage_ratio == 1.0
    assert alignment.available_component_count == 6
    assert alignment.alignment_state == "MTF_DIVERGENT"
    assert alignment.divergence_state == "MTF_MULTI_COMPONENT_MISMATCH"
    assert alignment.coherence_state == "MTF_INCOHERENT"
    assert alignment.hard_mismatch_components == ("regime", "volatility")
    assert alignment.trade_allowed is False


def test_alignment_output_checksum_and_replay_are_deterministic() -> None:
    states, availability, local, higher, first = _built()
    second = build_alignment_state(
        local,
        [higher],
        availability,
        load_config(),
        load_registry(),
        load_clock(),
        "abcdef1",
    )
    expected = checksum({key: value for key, value in first.to_dict().items() if key != "output_checksum"})
    assert first.output_checksum == expected
    assert replay_matches(first, second) is True
    assert replay_matches(first, first.__class__(**{**first.to_dict(), "output_checksum": "c" * 64})) is False
    assert len(states) == 2


def test_decision_evidence_is_closed_non_predictive_and_linked() -> None:
    _, _, local, higher, alignment = _built()
    evidence = build_alignment_evidence(alignment, local, higher, run_id="run-1")
    payload = evidence.to_dict()
    assert payload["decision_state"] == "NOT_APPLICABLE"
    assert payload["output_checksum"] == alignment.output_checksum
    assert payload["risk_decision_id"] is None
    assert payload["final_consequence"] == "DESCRIPTIVE_ALIGNMENT_ONLY_NO_TRADING"
    assert len(payload["supporting_evidence"]) == 2
    assert len(evidence.envelope_checksum()) == 64
    assert_no_forbidden_capabilities(alignment.to_dict())


@pytest.mark.parametrize(
    "payload",
    [
        {"probability": 0.8},
        {"nested": {"expected_return": 0.1}},
        [{"order": {}}],
        {"forecast_horizon": "5m"},
    ],
)
def test_forbidden_capabilities_are_rejected(payload: object) -> None:
    with pytest.raises(Lot26ValidationError, match="MTF_FORECAST_FIELD_FORBIDDEN"):
        assert_no_forbidden_capabilities(payload)


def test_schema_files_are_closed_and_match_contract_payloads() -> None:
    states, availability, _, _, alignment = _built()
    pairs = [
        (states[0].to_dict(), ROOT / "contracts/schemas/timeframe_market_context_state_v1.schema.json"),
        (availability[0].to_dict(), ROOT / "contracts/schemas/closed_bar_availability_v1.schema.json"),
        (alignment.to_dict(), ROOT / "contracts/schemas/multi_timeframe_alignment_state_v1.schema.json"),
    ]
    for payload, path in pairs:
        schema = json.loads(path.read_text())
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])
        assert set(payload) == set(schema["properties"])
