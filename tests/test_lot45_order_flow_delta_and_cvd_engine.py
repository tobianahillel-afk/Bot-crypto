from __future__ import annotations

from pathlib import Path

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    build_lot45_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "a" * 40


def test_reference_order_flow_preserves_unknown_and_conserves_volume() -> None:
    state, audit = build_lot45_artifacts(ROOT, code_commit=CODE_COMMIT)

    assert state.order_flow.trades_total == 3
    assert state.order_flow.buy_trades_total == 1
    assert state.order_flow.sell_trades_total == 1
    assert state.order_flow.unknown_trades_total == 1
    assert str(state.order_flow.total_volume) == "0.16"
    assert str(state.order_flow.buy_volume) == "0.08"
    assert str(state.order_flow.sell_volume) == "0.03"
    assert str(state.order_flow.unknown_volume) == "0.05"
    assert str(state.order_flow.signed_delta) == "0.05"
    assert str(state.order_flow.unknown_volume_ratio) == "0.3125"
    assert audit.state_output_checksum == state.output_checksum


def test_reference_cvd_is_source_ordered_and_unknown_is_unsigned() -> None:
    state, _ = build_lot45_artifacts(ROOT, code_commit=CODE_COMMIT)
    points = state.cvd.points

    assert tuple(point.trade_id for point in points) == (
        "fixture-trade-001",
        "fixture-trade-002",
        "fixture-trade-003",
    )
    assert tuple(str(point.signed_trade_delta) for point in points) == ("0", "0.08", "-0.03")
    assert tuple(str(point.cumulative_delta) for point in points) == ("0", "0.08", "0.05")
    assert str(state.cvd.starting_cvd) == "0"
    assert str(state.cvd.final_cvd) == "0.05"
    assert state.order_flow.signed_delta == state.cvd.final_cvd


def test_reference_artifacts_are_deterministic() -> None:
    first_state, first_audit = build_lot45_artifacts(ROOT, code_commit=CODE_COMMIT)
    second_state, second_audit = build_lot45_artifacts(ROOT, code_commit=CODE_COMMIT)

    assert first_state.to_dict() == second_state.to_dict()
    assert first_audit.to_dict() == second_audit.to_dict()
    assert first_state.output_checksum == second_state.output_checksum
    assert first_state.order_flow.order_flow_checksum == second_state.order_flow.order_flow_checksum
    assert first_state.cvd.cvd_checksum == second_state.cvd.cvd_checksum


def test_reference_state_remains_research_only_fail_closed() -> None:
    state, audit = build_lot45_artifacts(ROOT, code_commit=CODE_COMMIT)

    for payload in (state.safety, audit.safety):
        assert payload["analysis_only"] is True
        assert payload["used_for_decision"] is False
        assert payload["signal_generation_allowed"] is False
        assert payload["risk_approval_allowed"] is False
        assert payload["order_routing_allowed"] is False
        assert payload["trade_allowed"] is False
        assert payload["execution_allowed"] is False
        assert payload["approved_size"] == 0
