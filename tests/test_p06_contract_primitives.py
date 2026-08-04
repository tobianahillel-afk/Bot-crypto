from __future__ import annotations

from datetime import datetime

import crypto_quant_bot.contracts as canonical
import crypto_quant_bot.core.enums as legacy_enums
from crypto_quant_bot.contracts.base import BaseContract
from crypto_quant_bot.contracts.decision import DecisionContract
from crypto_quant_bot.core.clock import utc_now_iso as legacy_utc_now_iso


def test_core_reexports_canonical_contract_primitives() -> None:
    assert legacy_enums.TradingDecision is canonical.TradingDecision
    assert legacy_enums.SystemDecision is canonical.SystemDecision
    assert legacy_enums.ModuleStatus is canonical.ModuleStatus
    assert legacy_utc_now_iso is canonical.utc_now_iso


def test_utc_now_iso_is_timezone_aware_utc() -> None:
    timestamp = canonical.utc_now_iso()
    parsed = datetime.fromisoformat(timestamp)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() is not None
    assert parsed.utcoffset().total_seconds() == 0


def test_base_contract_defaults_are_complete_and_serializable() -> None:
    contract = BaseContract()
    payload = contract.to_dict()
    assert payload["id"] == contract.id
    assert payload["lineage_id"] == contract.lineage_id
    assert payload["created_at"] == contract.created_at
    assert payload["available_at"] == contract.available_at
    assert payload["schema_version"] == "1.0.0"
    assert payload["used_for_decision"] is False
    assert contract.id != contract.lineage_id


def test_decision_contract_preserves_fail_closed_defaults() -> None:
    contract = DecisionContract()
    assert contract.trading_decision == canonical.TradingDecision.WAIT.value
    assert contract.system_decision == canonical.SystemDecision.BLOCK_TRADING.value
    assert contract.trade_allowed is False
    assert contract.reasons == []
    assert contract.vetoes == []
    assert contract.replay_id.startswith("replay_")


def test_contract_instances_do_not_share_mutable_lists() -> None:
    first = DecisionContract()
    second = DecisionContract()
    first.reasons.append("LOCAL_TEST")
    first.vetoes.append("BLOCKED")
    assert second.reasons == []
    assert second.vetoes == []


def test_enum_values_remain_backward_compatible() -> None:
    assert [item.value for item in canonical.TradingDecision] == [
        "WAIT",
        "LONG",
        "SHORT",
        "CLOSE",
        "REDUCE",
    ]
    assert [item.value for item in canonical.SystemDecision] == [
        "BLOCK_TRADING",
        "PAUSE",
        "RESUME",
        "KILL_SWITCH",
    ]
    assert canonical.ModuleStatus.FORBIDDEN.value == "FORBIDDEN"
