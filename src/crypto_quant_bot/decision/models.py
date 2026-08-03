from dataclasses import dataclass, field

from crypto_quant_bot.contracts.base import BaseContract
from crypto_quant_bot.core.enums import ModuleStatus, SystemDecision, TradingDecision

DEFAULT_DECISION_BLOCK_REASONS = [
    "FINAL_DECISION_FIREWALL_ACTIVE",
    "TRADING_DECISION_WAIT",
    "SYSTEM_DECISION_BLOCK_TRADING",
    "RISK_ENGINE_BLOCKS_BY_DEFAULT",
    "EXPOSURE_GUARD_BLOCKS_BY_DEFAULT",
    "PORTFOLIO_FROZEN",
    "NO_ORDER_ROUTER",
    "NO_EXCHANGE_CONNECTOR",
    "LIVE_EXECUTION_DISABLED",
    "LEVERAGE_FORBIDDEN",
    "EDUCATIONAL_MODE_ONLY",
    "HUMAN_REVIEW_REQUIRED",
]


def default_decision_block_reasons() -> list[str]:
    return list(DEFAULT_DECISION_BLOCK_REASONS)


@dataclass(frozen=True)
class DecisionFirewallPolicy(BaseContract):
    timeframe: str = "multi"
    timestamp: str = ""
    policy_version: str = "lot14_decision_firewall_v0"
    live_execution: str = ModuleStatus.DISABLED.value
    leverage: str = ModuleStatus.FORBIDDEN.value
    trading_decision: str = TradingDecision.WAIT.value
    system_decision: str = SystemDecision.BLOCK_TRADING.value
    final_decision: str = TradingDecision.WAIT.value
    final_system_decision: str = SystemDecision.BLOCK_TRADING.value
    decision_firewall_state: str = "ACTIVE"
    execution_allowed: bool = False
    trade_allowed: bool = False
    used_for_decision: bool = False
    risk_allowed: bool = False
    exposure_allowed: bool = False
    portfolio_state: str = "FROZEN"
    allocation_state: str = "DISABLED"
    rebalance_state: str = "DISABLED"
    capital_at_risk: int = 0
    allocation_allowed: bool = False
    portfolio_change_allowed: bool = False
    allocation_change_allowed: bool = False
    rebalance_allowed: bool = False
    order_routing_allowed: bool = False
    external_connectivity_allowed: bool = False
    human_review_required: bool = True
    decision_block_reasons: list[str] = field(default_factory=default_decision_block_reasons)
    source_artifacts: list[str] = field(default_factory=list)
    source: str = "lot14_decision_firewall_policy_v0"
    validation_status: str = "validated_lot14"


@dataclass(frozen=True)
class DecisionFirewallCheck:
    check_name: str
    status: str = "BLOCK"
    expected_value: str = ""
    observed_value: str = ""
    block_reason: str = ""
    message: str = ""


@dataclass(frozen=True)
class DecisionFirewallResult(BaseContract):
    timeframe: str = "multi"
    timestamp: str = ""
    policy_version: str = "lot14_decision_firewall_v0"
    live_execution: str = ModuleStatus.DISABLED.value
    leverage: str = ModuleStatus.FORBIDDEN.value
    trading_decision: str = TradingDecision.WAIT.value
    system_decision: str = SystemDecision.BLOCK_TRADING.value
    final_decision: str = TradingDecision.WAIT.value
    final_system_decision: str = SystemDecision.BLOCK_TRADING.value
    decision_firewall_state: str = "ACTIVE"
    execution_allowed: bool = False
    trade_allowed: bool = False
    used_for_decision: bool = False
    risk_allowed: bool = False
    exposure_allowed: bool = False
    portfolio_state: str = "FROZEN"
    allocation_state: str = "DISABLED"
    rebalance_state: str = "DISABLED"
    capital_at_risk: int = 0
    allocation_allowed: bool = False
    portfolio_change_allowed: bool = False
    allocation_change_allowed: bool = False
    rebalance_allowed: bool = False
    order_routing_allowed: bool = False
    external_connectivity_allowed: bool = False
    human_review_required: bool = True
    decision_block_reasons: list[str] = field(default_factory=default_decision_block_reasons)
    decision_checks: list[DecisionFirewallCheck] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    source: str = "lot14_decision_firewall_v0"
    validation_status: str = "validated_lot14"


@dataclass(frozen=True)
class FinalDecisionSnapshot(DecisionFirewallResult):
    reference_market_state_available_at: str = ""
    reference_total_cost_bps: float = 0.0
    reference_risk_trade_allowed: bool = False
    reference_exposure_allowed: bool = False
    reference_portfolio_change_allowed: bool = False
