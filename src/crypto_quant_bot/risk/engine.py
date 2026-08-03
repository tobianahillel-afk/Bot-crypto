from __future__ import annotations

from typing import Any

from crypto_quant_bot.core.enums import ModuleStatus
from crypto_quant_bot.risk.models import (
    DEFAULT_RISK_BLOCK_REASONS,
    RiskCheck,
    RiskDecision,
    RiskPolicy,
    RiskSnapshot,
)


class RiskEngine:
    def __init__(self, policy_version: str = "lot11_risk_engine_v0") -> None:
        self.policy_version = policy_version

    def default_policy(self, *, source_artifacts: list[str] | None = None) -> RiskPolicy:
        return RiskPolicy(
            policy_version=self.policy_version,
            source_artifacts=list(source_artifacts or []),
        )

    def build_risk_checks(self) -> list[RiskCheck]:
        return [
            RiskCheck(
                check_name="live_execution",
                expected_value=ModuleStatus.DISABLED.value,
                observed_value=ModuleStatus.DISABLED.value,
                block_reason="LIVE_EXECUTION_DISABLED",
                message="Live execution remains disabled.",
            ),
            RiskCheck(
                check_name="leverage",
                expected_value=ModuleStatus.FORBIDDEN.value,
                observed_value=ModuleStatus.FORBIDDEN.value,
                block_reason="LEVERAGE_FORBIDDEN",
                message="Leverage remains forbidden.",
            ),
            RiskCheck(
                check_name="routing_stack",
                expected_value="not_available",
                observed_value="not_available",
                block_reason="NO_ORDER_ROUTER",
                message="No order router is present.",
            ),
            RiskCheck(
                check_name="exchange_connectivity",
                expected_value="not_available",
                observed_value="not_available",
                block_reason="NO_EXCHANGE_CONNECTOR",
                message="No exchange connector is present.",
            ),
            RiskCheck(
                check_name="operating_mode",
                expected_value="educational_only",
                observed_value="educational_only",
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Project remains educational only.",
            ),
            RiskCheck(
                check_name="default_firewall",
                expected_value="block",
                observed_value="block",
                block_reason="RISK_ENGINE_BLOCKS_BY_DEFAULT",
                message="Risk engine blocks by default.",
            ),
        ]

    def evaluate_default(
        self,
        *,
        timeframe: str = "multi",
        timestamp: str = "",
        available_at: str | None = None,
        source_artifacts: list[str] | None = None,
    ) -> RiskDecision:
        policy = self.default_policy(source_artifacts=source_artifacts)
        effective_available_at = available_at or timestamp
        return RiskDecision(
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
            risk_block_reasons=list(DEFAULT_RISK_BLOCK_REASONS),
            risk_checks=self.build_risk_checks(),
            source_artifacts=list(source_artifacts or []),
            reason="default_block_until_validated",
            vetoes=["risk_veto"],
        )

    def snapshot_from_documentary_row(
        self,
        timeframe: str,
        row: dict[str, Any],
        *,
        source_artifacts: list[str] | None = None,
    ) -> RiskSnapshot:
        artifacts = list(source_artifacts or [])
        source_dataset_ids = row.get("source_dataset_ids")
        if isinstance(source_dataset_ids, list):
            for dataset_id in source_dataset_ids:
                if isinstance(dataset_id, str) and dataset_id not in artifacts:
                    artifacts.append(dataset_id)
        decision = self.evaluate_default(
            timeframe=timeframe,
            timestamp=str(row.get("timestamp", "")),
            available_at=str(row.get("available_at", "")),
            source_artifacts=artifacts,
        )
        return RiskSnapshot(
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
            risk_block_reasons=list(decision.risk_block_reasons),
            risk_checks=list(decision.risk_checks),
            source_artifacts=list(decision.source_artifacts),
            reason=decision.reason,
            vetoes=list(decision.vetoes),
            reference_total_cost_bps=float(row.get("total_cost_bps", 0.0)),
            reference_fee_bps=float(row.get("fee_bps", 0.0)),
            reference_spread_bps=float(row.get("spread_bps", 0.0)),
            reference_slippage_bps=float(row.get("slippage_bps", 0.0)),
        )

    def build_snapshots_from_documentary_rows(
        self,
        timeframe: str,
        rows: list[dict[str, Any]],
        *,
        source_artifacts: list[str] | None = None,
    ) -> list[RiskSnapshot]:
        return [
            self.snapshot_from_documentary_row(timeframe, row, source_artifacts=source_artifacts)
            for row in rows
        ]
