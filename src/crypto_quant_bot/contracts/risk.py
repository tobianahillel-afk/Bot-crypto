from dataclasses import dataclass, field

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class RiskDecision(BaseContract):
    trade_allowed: bool = False
    reason: str = "default_block_until_validated"
    vetoes: list[str] = field(default_factory=lambda: ["risk_veto"])
