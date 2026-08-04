from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from crypto_quant_bot.contracts.base import BaseContract
from crypto_quant_bot.contracts.primitives import SystemDecision, TradingDecision


@dataclass(frozen=True)
class DecisionContract(BaseContract):
    timestamp: str = ""
    decision_id: str = field(default_factory=lambda: str(uuid4()))
    trading_decision: str = TradingDecision.WAIT.value
    system_decision: str = SystemDecision.BLOCK_TRADING.value
    trade_allowed: bool = False
    reasons: list[str] = field(default_factory=list)
    vetoes: list[str] = field(default_factory=list)
    config_version: str = "lot0_config_v1"
    replay_id: str = field(default_factory=lambda: f"replay_{uuid4()}")
