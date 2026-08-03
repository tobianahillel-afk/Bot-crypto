from dataclasses import dataclass, field

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class TransactionCostConfig(BaseContract):
    config_id: str = "lot10_transaction_cost_config_v0"
    pair: str = "BTC/EUR"
    currency: str = "EUR"
    maker_fee_bps: int | float = 16
    taker_fee_bps: int | float = 26
    default_spread_bps: int | float = 10
    base_slippage_bps: int | float = 5
    max_slippage_bps: int | float = 150
    config_version: str = "lot10_v0"
    trade_allowed: bool = False
    used_for_decision: bool = False


@dataclass(frozen=True)
class TransactionCostEstimate(BaseContract):
    estimate_id: str = ""
    run_id: str = ""
    step_id: str = ""
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    timestamp: str = ""
    market_state_id: str = ""
    notional_amount: int | float = 1000.0
    side: str = "neutral"
    order_type: str = "hypothetical_noop"
    fee_bps: int | float = 0
    spread_bps: int | float = 0
    slippage_bps: int | float = 0
    total_cost_bps: int | float = 0
    estimated_fee_amount: int | float = 0
    estimated_spread_cost: int | float = 0
    estimated_slippage_cost: int | float = 0
    estimated_total_cost: int | float = 0
    currency: str = "EUR"
    source_dataset_ids: list[str] = field(default_factory=list)
    trade_allowed: bool = False
    used_for_decision: bool = False


@dataclass(frozen=True)
class TransactionCostRunResult(BaseContract):
    run_id: str = ""
    pair: str = "BTC/EUR"
    timeframes: list[str] = field(default_factory=lambda: ["5m", "15m"])
    estimate_count: int = 0
    started_at: str = ""
    finished_at: str = ""
    fee_model_version: str = "lot10_fee_model_v0"
    spread_model_version: str = "lot10_spread_model_v0"
    slippage_model_version: str = "lot10_slippage_model_v0"
    average_total_cost_bps: int | float = 0
    max_total_cost_bps: int | float = 0
    min_total_cost_bps: int | float = 0
    trade_allowed: bool = False
    orders_created_count: int = 0
    fills_created_count: int = 0
    pnl_total: int | float = 0
    reports: list[str] = field(default_factory=list)
    used_for_decision: bool = False
