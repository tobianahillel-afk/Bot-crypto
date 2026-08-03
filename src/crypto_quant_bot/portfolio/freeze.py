from __future__ import annotations

from typing import Any

from crypto_quant_bot.core.enums import ModuleStatus
from crypto_quant_bot.portfolio.models import (
    DEFAULT_PORTFOLIO_BLOCK_REASONS,
    PortfolioFreezeCheck,
    PortfolioFreezePolicy,
    PortfolioFreezeResult,
    PortfolioFreezeSnapshot,
)


class PortfolioFreeze:
    def __init__(self, policy_version: str = "lot13_portfolio_freeze_v0") -> None:
        self.policy_version = policy_version

    def default_policy(self, *, source_artifacts: list[str] | None = None) -> PortfolioFreezePolicy:
        return PortfolioFreezePolicy(
            policy_version=self.policy_version,
            source_artifacts=list(source_artifacts or []),
        )

    def build_portfolio_checks(self) -> list[PortfolioFreezeCheck]:
        return [
            PortfolioFreezeCheck(
                check_name="portfolio_state",
                expected_value="FROZEN",
                observed_value="FROZEN",
                block_reason="PORTFOLIO_FROZEN",
                message="Portfolio state remains frozen.",
            ),
            PortfolioFreezeCheck(
                check_name="allocation_state",
                expected_value="DISABLED",
                observed_value="DISABLED",
                block_reason="ALLOCATION_DISABLED",
                message="Allocation state remains disabled.",
            ),
            PortfolioFreezeCheck(
                check_name="rebalance_state",
                expected_value="DISABLED",
                observed_value="DISABLED",
                block_reason="REBALANCE_DISABLED",
                message="Rebalance state remains disabled.",
            ),
            PortfolioFreezeCheck(
                check_name="capital_allocation",
                expected_value="0",
                observed_value="0",
                block_reason="NO_CAPITAL_ALLOCATION",
                message="No capital allocation is enabled.",
            ),
            PortfolioFreezeCheck(
                check_name="active_exposure",
                expected_value="0",
                observed_value="0",
                block_reason="NO_ACTIVE_EXPOSURE",
                message="No active exposure is present.",
            ),
            PortfolioFreezeCheck(
                check_name="routing_stack",
                expected_value="not_available",
                observed_value="not_available",
                block_reason="NO_ORDER_ROUTER",
                message="Executable routing stack is unavailable.",
            ),
            PortfolioFreezeCheck(
                check_name="exchange_connectivity",
                expected_value="not_available",
                observed_value="not_available",
                block_reason="NO_EXCHANGE_CONNECTOR",
                message="No exchange connector is present.",
            ),
            PortfolioFreezeCheck(
                check_name="risk_default_block",
                expected_value="block",
                observed_value="block",
                block_reason="RISK_ENGINE_BLOCKS_BY_DEFAULT",
                message="Risk Engine blocks by default.",
            ),
            PortfolioFreezeCheck(
                check_name="exposure_default_block",
                expected_value="block",
                observed_value="block",
                block_reason="EXPOSURE_GUARD_BLOCKS_BY_DEFAULT",
                message="Exposure Guard blocks by default.",
            ),
            PortfolioFreezeCheck(
                check_name="operating_mode",
                expected_value="educational_only",
                observed_value="educational_only",
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Project remains educational only.",
            ),
            PortfolioFreezeCheck(
                check_name="live_execution",
                expected_value=ModuleStatus.DISABLED.value,
                observed_value=ModuleStatus.DISABLED.value,
                block_reason="LIVE_EXECUTION_DISABLED",
                message="Live execution remains disabled.",
            ),
            PortfolioFreezeCheck(
                check_name="leverage",
                expected_value=ModuleStatus.FORBIDDEN.value,
                observed_value=ModuleStatus.FORBIDDEN.value,
                block_reason="LEVERAGE_FORBIDDEN",
                message="Leverage remains forbidden.",
            ),
        ]

    def evaluate_default(
        self,
        *,
        timeframe: str = "multi",
        timestamp: str = "",
        available_at: str | None = None,
        source_artifacts: list[str] | None = None,
    ) -> PortfolioFreezeResult:
        policy = self.default_policy(source_artifacts=source_artifacts)
        effective_available_at = available_at or timestamp
        return PortfolioFreezeResult(
            timeframe=timeframe,
            timestamp=timestamp,
            available_at=effective_available_at,
            policy_version=policy.policy_version,
            live_execution=policy.live_execution,
            leverage=policy.leverage,
            trading_decision=policy.trading_decision,
            system_decision=policy.system_decision,
            trade_allowed=False,
            used_for_decision=False,
            portfolio_state="FROZEN",
            allocation_state="DISABLED",
            rebalance_state="DISABLED",
            portfolio_change_allowed=False,
            allocation_change_allowed=False,
            allocation_allowed=False,
            rebalance_allowed=False,
            new_exposure_allowed=False,
            exposure_allowed=False,
            current_exposure_units=0,
            max_exposure_units=0,
            capital_at_risk=0,
            portfolio_block_reasons=list(DEFAULT_PORTFOLIO_BLOCK_REASONS),
            portfolio_checks=self.build_portfolio_checks(),
            source_artifacts=list(source_artifacts or []),
        )

    def snapshot_from_documentary_rows(
        self,
        timeframe: str,
        *,
        cost_row: dict[str, Any],
        risk_row: dict[str, Any],
        exposure_row: dict[str, Any],
        source_artifacts: list[str] | None = None,
    ) -> PortfolioFreezeSnapshot:
        decision = self.evaluate_default(
            timeframe=timeframe,
            timestamp=str(cost_row.get("timestamp", "")),
            available_at=str(cost_row.get("available_at", "")),
            source_artifacts=source_artifacts,
        )
        return PortfolioFreezeSnapshot(
            timeframe=decision.timeframe,
            timestamp=decision.timestamp,
            available_at=decision.available_at,
            policy_version=decision.policy_version,
            live_execution=decision.live_execution,
            leverage=decision.leverage,
            trading_decision=decision.trading_decision,
            system_decision=decision.system_decision,
            trade_allowed=decision.trade_allowed,
            used_for_decision=decision.used_for_decision,
            portfolio_state=decision.portfolio_state,
            allocation_state=decision.allocation_state,
            rebalance_state=decision.rebalance_state,
            portfolio_change_allowed=decision.portfolio_change_allowed,
            allocation_change_allowed=decision.allocation_change_allowed,
            allocation_allowed=decision.allocation_allowed,
            rebalance_allowed=decision.rebalance_allowed,
            new_exposure_allowed=decision.new_exposure_allowed,
            exposure_allowed=decision.exposure_allowed,
            current_exposure_units=decision.current_exposure_units,
            max_exposure_units=decision.max_exposure_units,
            capital_at_risk=decision.capital_at_risk,
            portfolio_block_reasons=list(decision.portfolio_block_reasons),
            portfolio_checks=list(decision.portfolio_checks),
            source_artifacts=list(decision.source_artifacts),
            reference_total_cost_bps=float(cost_row.get("total_cost_bps", 0.0)),
            reference_risk_trade_allowed=bool(risk_row.get("trade_allowed", False)),
            reference_exposure_allowed=bool(exposure_row.get("exposure_allowed", False)),
        )

    def build_snapshots(
        self,
        timeframe: str,
        *,
        cost_rows: list[dict[str, Any]],
        risk_rows: list[dict[str, Any]],
        exposure_rows: list[dict[str, Any]],
        source_artifacts: list[str] | None = None,
    ) -> list[PortfolioFreezeSnapshot]:
        if not (len(cost_rows) == len(risk_rows) == len(exposure_rows)):
            raise ValueError(f"row mismatch for {timeframe}")
        snapshots: list[PortfolioFreezeSnapshot] = []
        for cost_row, risk_row, exposure_row in zip(cost_rows, risk_rows, exposure_rows, strict=True):
            snapshots.append(
                self.snapshot_from_documentary_rows(
                    timeframe,
                    cost_row=cost_row,
                    risk_row=risk_row,
                    exposure_row=exposure_row,
                    source_artifacts=source_artifacts,
                )
            )
        return snapshots
