from crypto_quant_bot.contracts.decision import DecisionContract
from crypto_quant_bot.core.clock import utc_now_iso
from crypto_quant_bot.core.enums import SystemDecision, TradingDecision
from crypto_quant_bot.risk.risk_engine import RiskEngine


class DecisionEngine:
    def __init__(self, risk_engine: RiskEngine | None = None, config_version: str = "lot0_config_v1") -> None:
        self.risk_engine = risk_engine or RiskEngine()
        self.config_version = config_version

    def decide_default(self) -> DecisionContract:
        risk = self.risk_engine.evaluate_default()
        reasons = [
            "no_market_data_in_lot0",
            risk.reason,
            "trade_allowed_false_by_default",
        ]
        vetoes = list(dict.fromkeys([*risk.vetoes, "data_quality_veto"]))
        return DecisionContract(
            timestamp=utc_now_iso(),
            trading_decision=TradingDecision.WAIT.value,
            system_decision=SystemDecision.BLOCK_TRADING.value,
            trade_allowed=False,
            reasons=reasons,
            vetoes=vetoes,
            config_version=self.config_version,
            validation_status="validated_lot0",
            used_for_decision=True,
        )
