from __future__ import annotations

from typing import Any

from crypto_quant_bot.core.enums import ModuleStatus
from crypto_quant_bot.exposure.models import (
    DEFAULT_EXPOSURE_BLOCK_REASONS,
    ExposureCheck,
    ExposureGuardResult,
    ExposurePolicy,
    ExposureSnapshot,
)


class ExposureGuard:
    def __init__(self, policy_version: str = "lot12_exposure_guard_v0") -> None:
        self.policy_version = policy_version

    def default_policy(self, *, source_artifacts: list[str] | None = None) -> ExposurePolicy:
        return ExposurePolicy(
            policy_version=self.policy_version,
            source_artifacts=list(source_artifacts or []),
        )

    def build_exposure_checks(self) -> list[ExposureCheck]:
        return [
            ExposureCheck(
                check_name="capital_allocation",
                expected_value="0",
                observed_value="0",
                block_reason="NO_CAPITAL_ALLOCATION",
                message="No capital allocation is enabled.",
            ),
            ExposureCheck(
                check_name="active_exposure",
                expected_value="0",
                observed_value="0",
                block_reason="NO_ACTIVE_EXPOSURE",
                message="No active exposure is present.",
            ),
            ExposureCheck(
                check_name="routing_stack",
                expected_value="not_available",
                observed_value="not_available",
                block_reason="NO_ORDER_ROUTER",
                message="Routing stack is unavailable.",
            ),
            ExposureCheck(
                check_name="exchange_connectivity",
                expected_value="not_available",
                observed_value="not_available",
                block_reason="NO_EXCHANGE_CONNECTOR",
                message="No exchange connector is present.",
            ),
            ExposureCheck(
                check_name="risk_default_block",
                expected_value="block",
                observed_value="block",
                block_reason="RISK_ENGINE_BLOCKS_BY_DEFAULT",
                message="Risk Engine blocks by default.",
            ),
            ExposureCheck(
                check_name="operating_mode",
                expected_value="educational_only",
                observed_value="educational_only",
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Project remains educational only.",
            ),
            ExposureCheck(
                check_name="live_execution",
                expected_value=ModuleStatus.DISABLED.value,
                observed_value=ModuleStatus.DISABLED.value,
                block_reason="LIVE_EXECUTION_DISABLED",
                message="Live execution remains disabled.",
            ),
            ExposureCheck(
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
    ) -> ExposureGuardResult:
        policy = self.default_policy(source_artifacts=source_artifacts)
        effective_available_at = available_at or timestamp
        return ExposureGuardResult(
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
            exposure_allowed=False,
            allocation_allowed=False,
            rebalance_allowed=False,
            current_exposure_units=0,
            max_exposure_units=0,
            capital_at_risk=0,
            exposure_block_reasons=list(DEFAULT_EXPOSURE_BLOCK_REASONS),
            exposure_checks=self.build_exposure_checks(),
            source_artifacts=list(source_artifacts or []),
        )

    def snapshot_from_documentary_rows(
        self,
        timeframe: str,
        *,
        market_state_row: dict[str, Any],
        cost_row: dict[str, Any],
        risk_row: dict[str, Any],
        source_artifacts: list[str] | None = None,
    ) -> ExposureSnapshot:
        artifacts = list(source_artifacts or [])
        decision = self.evaluate_default(
            timeframe=timeframe,
            timestamp=str(cost_row.get("timestamp", "")),
            available_at=str(cost_row.get("available_at", "")),
            source_artifacts=artifacts,
        )
        return ExposureSnapshot(
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
            exposure_allowed=decision.exposure_allowed,
            allocation_allowed=decision.allocation_allowed,
            rebalance_allowed=decision.rebalance_allowed,
            current_exposure_units=decision.current_exposure_units,
            max_exposure_units=decision.max_exposure_units,
            capital_at_risk=decision.capital_at_risk,
            exposure_block_reasons=list(decision.exposure_block_reasons),
            exposure_checks=list(decision.exposure_checks),
            source_artifacts=list(decision.source_artifacts),
            reference_total_cost_bps=float(cost_row.get("total_cost_bps", 0.0)),
            reference_risk_trade_allowed=bool(risk_row.get("trade_allowed", False)),
            reference_market_state_available_at=str(market_state_row.get("available_at", "")),
        )

    def build_snapshots(
        self,
        timeframe: str,
        *,
        market_state_rows: list[dict[str, Any]],
        cost_rows: list[dict[str, Any]],
        risk_rows: list[dict[str, Any]],
        source_artifacts: list[str] | None = None,
    ) -> list[ExposureSnapshot]:
        if not (len(market_state_rows) == len(cost_rows) == len(risk_rows)):
            raise ValueError(f"row mismatch for {timeframe}")
        snapshots: list[ExposureSnapshot] = []
        for market_state_row, cost_row, risk_row in zip(market_state_rows, cost_rows, risk_rows, strict=True):
            snapshots.append(
                self.snapshot_from_documentary_rows(
                    timeframe,
                    market_state_row=market_state_row,
                    cost_row=cost_row,
                    risk_row=risk_row,
                    source_artifacts=source_artifacts,
                )
            )
        return snapshots
