from __future__ import annotations

from typing import Any

from crypto_quant_bot.core.enums import ModuleStatus, SystemDecision, TradingDecision
from crypto_quant_bot.decision.models import (
    DEFAULT_DECISION_BLOCK_REASONS,
    DecisionFirewallCheck,
    DecisionFirewallPolicy,
    DecisionFirewallResult,
    FinalDecisionSnapshot,
)


class DecisionFirewall:
    def __init__(self, policy_version: str = "lot14_decision_firewall_v0") -> None:
        self.policy_version = policy_version

    def default_policy(self, *, source_artifacts: list[str] | None = None) -> DecisionFirewallPolicy:
        return DecisionFirewallPolicy(
            policy_version=self.policy_version,
            source_artifacts=list(source_artifacts or []),
        )

    def build_decision_checks(self) -> list[DecisionFirewallCheck]:
        return [
            DecisionFirewallCheck(
                check_name="decision_firewall_state",
                expected_value="ACTIVE",
                observed_value="ACTIVE",
                block_reason="FINAL_DECISION_FIREWALL_ACTIVE",
                message="Final Decision Firewall remains active.",
            ),
            DecisionFirewallCheck(
                check_name="trading_decision",
                expected_value=TradingDecision.WAIT.value,
                observed_value=TradingDecision.WAIT.value,
                block_reason="TRADING_DECISION_WAIT",
                message="Trading decision remains WAIT.",
            ),
            DecisionFirewallCheck(
                check_name="system_decision",
                expected_value=SystemDecision.BLOCK_TRADING.value,
                observed_value=SystemDecision.BLOCK_TRADING.value,
                block_reason="SYSTEM_DECISION_BLOCK_TRADING",
                message="System decision remains BLOCK_TRADING.",
            ),
            DecisionFirewallCheck(
                check_name="risk_default_block",
                expected_value="block",
                observed_value="block",
                block_reason="RISK_ENGINE_BLOCKS_BY_DEFAULT",
                message="Risk Engine blocks by default.",
            ),
            DecisionFirewallCheck(
                check_name="exposure_default_block",
                expected_value="block",
                observed_value="block",
                block_reason="EXPOSURE_GUARD_BLOCKS_BY_DEFAULT",
                message="Exposure Guard blocks by default.",
            ),
            DecisionFirewallCheck(
                check_name="portfolio_state",
                expected_value="FROZEN",
                observed_value="FROZEN",
                block_reason="PORTFOLIO_FROZEN",
                message="Portfolio remains frozen.",
            ),
            DecisionFirewallCheck(
                check_name="routing_stack",
                expected_value="not_available",
                observed_value="not_available",
                block_reason="NO_ORDER_ROUTER",
                message="Routing stack remains unavailable.",
            ),
            DecisionFirewallCheck(
                check_name="exchange_connectivity",
                expected_value="not_available",
                observed_value="not_available",
                block_reason="NO_EXCHANGE_CONNECTOR",
                message="External exchange connectivity remains unavailable.",
            ),
            DecisionFirewallCheck(
                check_name="live_execution",
                expected_value=ModuleStatus.DISABLED.value,
                observed_value=ModuleStatus.DISABLED.value,
                block_reason="LIVE_EXECUTION_DISABLED",
                message="Live execution remains disabled.",
            ),
            DecisionFirewallCheck(
                check_name="leverage",
                expected_value=ModuleStatus.FORBIDDEN.value,
                observed_value=ModuleStatus.FORBIDDEN.value,
                block_reason="LEVERAGE_FORBIDDEN",
                message="Leverage remains forbidden.",
            ),
            DecisionFirewallCheck(
                check_name="operating_mode",
                expected_value="educational_only",
                observed_value="educational_only",
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Project remains educational only.",
            ),
            DecisionFirewallCheck(
                check_name="human_review",
                expected_value="required",
                observed_value="required",
                block_reason="HUMAN_REVIEW_REQUIRED",
                message="Human review remains required.",
            ),
        ]

    def evaluate_default(
        self,
        *,
        timeframe: str = "multi",
        timestamp: str = "",
        available_at: str | None = None,
        source_artifacts: list[str] | None = None,
    ) -> DecisionFirewallResult:
        policy = self.default_policy(source_artifacts=source_artifacts)
        effective_available_at = available_at or timestamp
        return DecisionFirewallResult(
            timeframe=timeframe,
            timestamp=timestamp,
            available_at=effective_available_at,
            policy_version=policy.policy_version,
            live_execution=policy.live_execution,
            leverage=policy.leverage,
            trading_decision=policy.trading_decision,
            system_decision=policy.system_decision,
            final_decision=policy.final_decision,
            final_system_decision=policy.final_system_decision,
            decision_firewall_state=policy.decision_firewall_state,
            execution_allowed=False,
            trade_allowed=False,
            used_for_decision=False,
            risk_allowed=False,
            exposure_allowed=False,
            portfolio_state=policy.portfolio_state,
            allocation_state=policy.allocation_state,
            rebalance_state=policy.rebalance_state,
            capital_at_risk=0,
            allocation_allowed=False,
            portfolio_change_allowed=False,
            allocation_change_allowed=False,
            rebalance_allowed=False,
            order_routing_allowed=False,
            external_connectivity_allowed=False,
            human_review_required=True,
            decision_block_reasons=list(DEFAULT_DECISION_BLOCK_REASONS),
            decision_checks=self.build_decision_checks(),
            source_artifacts=list(source_artifacts or []),
        )

    def snapshot_from_documentary_rows(
        self,
        timeframe: str,
        *,
        market_state_row: dict[str, Any],
        cost_row: dict[str, Any],
        risk_row: dict[str, Any],
        exposure_row: dict[str, Any],
        portfolio_row: dict[str, Any],
        source_artifacts: list[str] | None = None,
    ) -> FinalDecisionSnapshot:
        decision = self.evaluate_default(
            timeframe=timeframe,
            timestamp=str(cost_row.get("timestamp", "")),
            available_at=str(cost_row.get("available_at", "")),
            source_artifacts=source_artifacts,
        )
        return FinalDecisionSnapshot(
            timeframe=decision.timeframe,
            timestamp=decision.timestamp,
            available_at=decision.available_at,
            policy_version=decision.policy_version,
            live_execution=decision.live_execution,
            leverage=decision.leverage,
            trading_decision=decision.trading_decision,
            system_decision=decision.system_decision,
            final_decision=decision.final_decision,
            final_system_decision=decision.final_system_decision,
            decision_firewall_state=decision.decision_firewall_state,
            execution_allowed=decision.execution_allowed,
            trade_allowed=decision.trade_allowed,
            used_for_decision=decision.used_for_decision,
            risk_allowed=decision.risk_allowed,
            exposure_allowed=decision.exposure_allowed,
            portfolio_state=decision.portfolio_state,
            allocation_state=decision.allocation_state,
            rebalance_state=decision.rebalance_state,
            capital_at_risk=decision.capital_at_risk,
            allocation_allowed=decision.allocation_allowed,
            portfolio_change_allowed=decision.portfolio_change_allowed,
            allocation_change_allowed=decision.allocation_change_allowed,
            rebalance_allowed=decision.rebalance_allowed,
            order_routing_allowed=decision.order_routing_allowed,
            external_connectivity_allowed=decision.external_connectivity_allowed,
            human_review_required=decision.human_review_required,
            decision_block_reasons=list(decision.decision_block_reasons),
            decision_checks=list(decision.decision_checks),
            source_artifacts=list(decision.source_artifacts),
            reference_market_state_available_at=str(market_state_row.get("available_at", "")),
            reference_total_cost_bps=float(cost_row.get("total_cost_bps", 0.0)),
            reference_risk_trade_allowed=bool(risk_row.get("trade_allowed", False)),
            reference_exposure_allowed=bool(exposure_row.get("exposure_allowed", False)),
            reference_portfolio_change_allowed=bool(portfolio_row.get("portfolio_change_allowed", False)),
        )

    def build_snapshots(
        self,
        timeframe: str,
        *,
        market_state_rows: list[dict[str, Any]],
        cost_rows: list[dict[str, Any]],
        risk_rows: list[dict[str, Any]],
        exposure_rows: list[dict[str, Any]],
        portfolio_rows: list[dict[str, Any]],
        source_artifacts: list[str] | None = None,
    ) -> list[FinalDecisionSnapshot]:
        if not (
            len(market_state_rows)
            == len(cost_rows)
            == len(risk_rows)
            == len(exposure_rows)
            == len(portfolio_rows)
        ):
            raise ValueError(f"row mismatch for {timeframe}")
        snapshots: list[FinalDecisionSnapshot] = []
        for market_state_row, cost_row, risk_row, exposure_row, portfolio_row in zip(
            market_state_rows,
            cost_rows,
            risk_rows,
            exposure_rows,
            portfolio_rows,
            strict=True,
        ):
            snapshots.append(
                self.snapshot_from_documentary_rows(
                    timeframe,
                    market_state_row=market_state_row,
                    cost_row=cost_row,
                    risk_row=risk_row,
                    exposure_row=exposure_row,
                    portfolio_row=portfolio_row,
                    source_artifacts=source_artifacts,
                )
            )
        return snapshots
