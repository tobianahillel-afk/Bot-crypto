from dataclasses import dataclass, field

from crypto_quant_bot.contracts.base import BaseContract
from crypto_quant_bot.core.enums import ModuleStatus, SystemDecision, TradingDecision

DEFAULT_RISK_BLOCK_REASONS = [
    "LIVE_EXECUTION_DISABLED",
    "LEVERAGE_FORBIDDEN",
    "NO_ORDER_ROUTER",
    "NO_EXCHANGE_CONNECTOR",
    "EDUCATIONAL_MODE_ONLY",
    "RISK_ENGINE_BLOCKS_BY_DEFAULT",
]


def default_risk_block_reasons() -> list[str]:
    return list(DEFAULT_RISK_BLOCK_REASONS)


def default_vetoes() -> list[str]:
    return ["risk_veto"]


@dataclass(frozen=True)
class RiskPolicy(BaseContract):
    timeframe: str = "multi"
    timestamp: str = ""
    policy_version: str = "lot11_risk_engine_v0"
    live_execution: str = ModuleStatus.DISABLED.value
    leverage: str = ModuleStatus.FORBIDDEN.value
    trading_decision: str = TradingDecision.WAIT.value
    system_decision: str = SystemDecision.BLOCK_TRADING.value
    trade_allowed: bool = False
    used_for_decision: bool = False
    risk_block_reasons: list[str] = field(default_factory=default_risk_block_reasons)
    source_artifacts: list[str] = field(default_factory=list)
    source: str = "lot11_risk_policy_v0"
    validation_status: str = "validated_lot11"


@dataclass(frozen=True)
class RiskCheck:
    check_name: str
    status: str = "BLOCK"
    expected_value: str = ""
    observed_value: str = ""
    block_reason: str = ""
    message: str = ""


@dataclass(frozen=True)
class RiskDecision(BaseContract):
    timeframe: str = "multi"
    timestamp: str = ""
    policy_version: str = "lot11_risk_engine_v0"
    live_execution: str = ModuleStatus.DISABLED.value
    leverage: str = ModuleStatus.FORBIDDEN.value
    trading_decision: str = TradingDecision.WAIT.value
    system_decision: str = SystemDecision.BLOCK_TRADING.value
    trade_allowed: bool = False
    used_for_decision: bool = False
    risk_block_reasons: list[str] = field(default_factory=default_risk_block_reasons)
    risk_checks: list[RiskCheck] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    reason: str = "default_block_until_validated"
    vetoes: list[str] = field(default_factory=default_vetoes)
    source: str = "lot11_risk_engine_v0"
    validation_status: str = "validated_lot11"


@dataclass(frozen=True)
class RiskSnapshot(RiskDecision):
    reference_total_cost_bps: float = 0.0
    reference_fee_bps: float = 0.0
    reference_spread_bps: float = 0.0
    reference_slippage_bps: float = 0.0
