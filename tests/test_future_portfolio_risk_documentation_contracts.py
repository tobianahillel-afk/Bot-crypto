from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / "docs/CANONICAL_PORTFOLIO_RISK_SIZING_AND_EXIT_STANDARD.md"
ADDENDUM = ROOT / "docs/roadmap/V07_V09_PORTFOLIO_RISK_NORMATIVE_ADDENDUM.md"
SNAPSHOT_SCHEMA = ROOT / "contracts/schemas/portfolio_decision_snapshot_v1.schema.json"
RESERVATION_SCHEMA = ROOT / "contracts/schemas/risk_reservation_v1.schema.json"


def test_canonical_portfolio_risk_standard_covers_required_controls() -> None:
    content = STANDARD.read_text(encoding="utf-8")
    required_terms = (
        "PortfolioDecisionSnapshotV1",
        "RiskReservationV1",
        "R_trade(q)",
        "PortfolioHeat(P)",
        "DeltaR(q)",
        "MaxWeight",
        "HHI",
        "Drawdown_t",
        "q_liquidity",
        "q_approved",
        "SNAPSHOT_CONFLICT",
        "AVERAGING_DOWN_FORBIDDEN",
        "NetLiquidationPnL <= 0",
        "KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE",
    )
    assert not [term for term in required_terms if term not in content]


def test_v7_v9_addendum_binds_required_lots_to_parent_standard() -> None:
    content = ADDENDUM.read_text(encoding="utf-8")
    required_terms = (
        "CANONICAL_PORTFOLIO_RISK_SIZING_AND_EXIT_STANDARD.md",
        "Lot 74",
        "Lot 75",
        "Lot 76",
        "Lot 77",
        "Lot 78",
        "Lot 79",
        "Lot 80",
        "Lot 88",
        "Lot 89",
        "Lot 90",
        "Lot 93",
        "atomic",
        "AVERAGING_DOWN_FORBIDDEN",
    )
    assert not [term for term in required_terms if term not in content]


def test_portfolio_decision_snapshot_schema_requires_consistent_state_ids() -> None:
    schema = json.loads(SNAPSHOT_SCHEMA.read_text(encoding="utf-8"))
    required = set(schema["required"])
    expected = {
        "snapshot_id",
        "snapshot_sequence",
        "ledger_watermark",
        "portfolio_state_id",
        "position_state_ids",
        "open_order_state_ids",
        "pending_intent_state_ids",
        "reservation_ids",
        "valuation_time",
        "decision_time",
        "cash_reserved",
        "cash_available",
        "portfolio_risk",
        "reserved_risk",
        "portfolio_heat",
        "drawdown",
        "reconciliation_state",
        "state_hash",
    }
    assert expected <= required
    assert schema["additionalProperties"] is False


def test_risk_reservation_schema_is_bound_to_intent_snapshot_and_decision() -> None:
    schema = json.loads(RESERVATION_SCHEMA.read_text(encoding="utf-8"))
    required = set(schema["required"])
    expected = {
        "reservation_id",
        "intent_id",
        "intent_hash",
        "snapshot_id",
        "snapshot_sequence",
        "portfolio_state_version_before",
        "portfolio_state_version_after",
        "reserved_capital",
        "reserved_risk",
        "reserved_notional",
        "reserved_quantity",
        "idempotency_key",
        "decision_hash",
        "status",
        "state_hash",
    }
    assert expected <= required
    assert schema["additionalProperties"] is False


def test_readme_and_roadmap_expose_standard_without_enabling_trading() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/ROADMAP_V1_TO_V21.md").read_text(encoding="utf-8")
    standard_name = "CANONICAL_PORTFOLIO_RISK_SIZING_AND_EXIT_STANDARD.md"
    addendum_name = "V07_V09_PORTFOLIO_RISK_NORMATIVE_ADDENDUM.md"

    assert standard_name in readme
    assert addendum_name in readme
    assert standard_name in roadmap
    assert addendum_name in roadmap
    assert "risk reservation ≠ order intent" in roadmap
    assert "trade_allowed = false" in readme
    assert "execution_allowed = false" in readme
    assert "approved_size = 0" in readme
