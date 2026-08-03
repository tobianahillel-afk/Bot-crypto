from dataclasses import dataclass, field

from crypto_quant_bot.contracts.base import BaseContract
from crypto_quant_bot.core.enums import ModuleStatus, SystemDecision, TradingDecision

DEFAULT_EXPOSURE_BLOCK_REASONS = [
    "NO_CAPITAL_ALLOCATION",
    "NO_ACTIVE_EXPOSURE",
    "NO_ORDER_ROUTER",
    "NO_EXCHANGE_CONNECTOR",
    "RISK_ENGINE_BLOCKS_BY_DEFAULT",
    "EDUCATIONAL_MODE_ONLY",
    "LIVE_EXECUTION_DISABLED",
    "LEVERAGE_FORBIDDEN",
]


def default_exposure_block_reasons() -> list[str]:
    return list(DEFAULT_EXPOSURE_BLOCK_REASONS)


@dataclass(frozen=True)
class ExposurePolicy(BaseContract):
    timeframe: str = "multi"
    timestamp: str = ""
    policy_version: str = "lot12_exposure_guard_v0"
    live_execution: str = ModuleStatus.DISABLED.value
    leverage: str = ModuleStatus.FORBIDDEN.value
    trading_decision: str = TradingDecision.WAIT.value
    system_decision: str = SystemDecision.BLOCK_TRADING.value
    trade_allowed: bool = False
    used_for_decision: bool = False
    exposure_allowed: bool = False
    allocation_allowed: bool = False
    rebalance_allowed: bool = False
    current_exposure_units: int = 0
    max_exposure_units: int = 0
    capital_at_risk: int = 0
    exposure_block_reasons: list[str] = field(default_factory=default_exposure_block_reasons)
    source_artifacts: list[str] = field(default_factory=list)
    source: str = "lot12_exposure_policy_v0"
    validation_status: str = "validated_lot12"


@dataclass(frozen=True)
class ExposureCheck:
    check_name: str
    status: str = "BLOCK"
    expected_value: str = ""
    observed_value: str = ""
    block_reason: str = ""
    message: str = ""


@dataclass(frozen=True)
class ExposureGuardResult(BaseContract):
    timeframe: str = "multi"
    timestamp: str = ""
    policy_version: str = "lot12_exposure_guard_v0"
    live_execution: str = ModuleStatus.DISABLED.value
    leverage: str = ModuleStatus.FORBIDDEN.value
    trading_decision: str = TradingDecision.WAIT.value
    system_decision: str = SystemDecision.BLOCK_TRADING.value
    trade_allowed: bool = False
    used_for_decision: bool = False
    exposure_allowed: bool = False
    allocation_allowed: bool = False
    rebalance_allowed: bool = False
    current_exposure_units: int = 0
    max_exposure_units: int = 0
    capital_at_risk: int = 0
    exposure_block_reasons: list[str] = field(default_factory=default_exposure_block_reasons)
    exposure_checks: list[ExposureCheck] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    source: str = "lot12_exposure_guard_v0"
    validation_status: str = "validated_lot12"


@dataclass(frozen=True)
class ExposureSnapshot(ExposureGuardResult):
    reference_total_cost_bps: float = 0.0
    reference_risk_trade_allowed: bool = False
    reference_market_state_available_at: str = ""
