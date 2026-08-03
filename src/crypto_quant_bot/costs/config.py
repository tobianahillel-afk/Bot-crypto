from pathlib import Path
from typing import Any

from crypto_quant_bot.contracts.costs import TransactionCostConfig
from crypto_quant_bot.core.clock import utc_now_iso
from crypto_quant_bot.core.config_loader import load_simple_yaml


class TransactionCostConfigError(RuntimeError):
    pass


def _get_nested(payload: dict[str, Any], section: str, key: str) -> Any:
    value = payload.get(section)
    if not isinstance(value, dict):
        raise TransactionCostConfigError(f"missing section {section}")
    if key not in value:
        raise TransactionCostConfigError(f"missing {section}.{key}")
    return value[key]


def load_transaction_cost_config(path: Path | str) -> TransactionCostConfig:
    payload = load_simple_yaml(path)
    safety = payload.get("safety")
    if not isinstance(safety, dict):
        raise TransactionCostConfigError("missing safety section")
    trade_allowed = safety.get("trade_allowed")
    used_for_decision = safety.get("used_for_decision")
    if trade_allowed is not False or used_for_decision is not False:
        raise TransactionCostConfigError("Lot 10 cost config must be non-trading and not used for decision")
    created_at = utc_now_iso()
    return TransactionCostConfig(
        config_id="lot10_transaction_cost_config_v0",
        pair=str(payload.get("pair", "BTC/EUR")),
        currency=str(payload.get("currency", "EUR")),
        maker_fee_bps=float(_get_nested(payload, "fee_model", "maker_fee_bps")),
        taker_fee_bps=float(_get_nested(payload, "fee_model", "taker_fee_bps")),
        default_spread_bps=float(_get_nested(payload, "spread_model", "default_spread_bps")),
        base_slippage_bps=float(_get_nested(payload, "slippage_model", "base_slippage_bps")),
        max_slippage_bps=float(_get_nested(payload, "slippage_model", "max_slippage_bps")),
        created_at=created_at,
        available_at=created_at,
        config_version=str(payload.get("version", "lot10_v0")),
        trade_allowed=False,
        source="lot10_transaction_cost_model_v0",
        quality_flag="valid",
        validation_status="validated_lot10",
        used_for_decision=False,
    )


def load_raw_transaction_cost_config(path: Path | str) -> dict[str, Any]:
    return load_simple_yaml(path)
