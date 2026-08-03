from dataclasses import dataclass, field

from crypto_quant_bot.contracts.base import BaseContract
from crypto_quant_bot.core.enums import ModuleStatus, SystemDecision, TradingDecision

DEFAULT_PORTFOLIO_BLOCK_REASONS = [
    "PORTFOLIO_FROZEN",
    "ALLOCATION_DISABLED",
    "REBALANCE_DISABLED",
    "NO_CAPITAL_ALLOCATION",
    "NO_ACTIVE_EXPOSURE",
    "NO_ORDER_ROUTER",
    "NO_EXCHANGE_CONNECTOR",
    "RISK_ENGINE_BLOCKS_BY_DEFAULT",
    "EXPOSURE_GUARD_BLOCKS_BY_DEFAULT",
    "EDUCATIONAL_MODE_ONLY",
    "LIVE_EXECUTION_DISABLED",
    "LEVERAGE_FORBIDDEN",
]


def default_portfolio_block_reasons() -> list[str]:
    return list(DEFAULT_PORTFOLIO_BLOCK_REASONS)


@dataclass(frozen=True)
class PortfolioFreezePolicy(BaseContract):
    timeframe: str = "multi"
    timestamp: str = ""
    policy_version: str = "lot13_portfolio_freeze_v0"
    live_execution: str = ModuleStatus.DISABLED.value
    leverage: str = ModuleStatus.FORBIDDEN.value
    trading_decision: str = TradingDecision.WAIT.value
    system_decision: str = SystemDecision.BLOCK_TRADING.value
    trade_allowed: bool = False
    used_for_decision: bool = False
    portfolio_state: str = "FROZEN"
    allocation_state: str = "DISABLED"
    rebalance_state: str = "DISABLED"
    portfolio_change_allowed: bool = False
    allocation_change_allowed: bool = False
    allocation_allowed: bool = False
    rebalance_allowed: bool = False
    new_exposure_allowed: bool = False
    exposure_allowed: bool = False
    current_exposure_units: int = 0
    max_exposure_units: int = 0
    capital_at_risk: int = 0
    portfolio_block_reasons: list[str] = field(default_factory=default_portfolio_block_reasons)
    source_artifacts: list[str] = field(default_factory=list)
    source: str = "lot13_portfolio_freeze_policy_v0"
    validation_status: str = "validated_lot13"


@dataclass(frozen=True)
class PortfolioFreezeCheck:
    check_name: str
    status: str = "BLOCK"
    expected_value: str = ""
    observed_value: str = ""
    block_reason: str = ""
    message: str = ""


@dataclass(frozen=True)
class PortfolioFreezeResult(BaseContract):
    timeframe: str = "multi"
    timestamp: str = ""
    policy_version: str = "lot13_portfolio_freeze_v0"
    live_execution: str = ModuleStatus.DISABLED.value
    leverage: str = ModuleStatus.FORBIDDEN.value
    trading_decision: str = TradingDecision.WAIT.value
    system_decision: str = SystemDecision.BLOCK_TRADING.value
    trade_allowed: bool = False
    used_for_decision: bool = False
    portfolio_state: str = "FROZEN"
    allocation_state: str = "DISABLED"
    rebalance_state: str = "DISABLED"
    portfolio_change_allowed: bool = False
    allocation_change_allowed: bool = False
    allocation_allowed: bool = False
    rebalance_allowed: bool = False
    new_exposure_allowed: bool = False
    exposure_allowed: bool = False
    current_exposure_units: int = 0
    max_exposure_units: int = 0
    capital_at_risk: int = 0
    portfolio_block_reasons: list[str] = field(default_factory=default_portfolio_block_reasons)
    portfolio_checks: list[PortfolioFreezeCheck] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    source: str = "lot13_portfolio_freeze_v0"
    validation_status: str = "validated_lot13"


@dataclass(frozen=True)
class PortfolioFreezeSnapshot(PortfolioFreezeResult):
    reference_total_cost_bps: float = 0.0
    reference_risk_trade_allowed: bool = False
    reference_exposure_allowed: bool = False
