from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso

DEFAULT_LEDGER_BLOCK_REASONS = [
    "DECISION_RECORDED_FOR_AUDIT_ONLY",
    "FINAL_DECISION_WAIT",
    "SYSTEM_DECISION_BLOCK_TRADING",
    "EXECUTION_NOT_ALLOWED",
    "ORDER_ROUTING_NOT_ALLOWED",
    "EXTERNAL_CONNECTIVITY_DISABLED",
    "RISK_ENGINE_BLOCKS_BY_DEFAULT",
    "EXPOSURE_GUARD_BLOCKS_BY_DEFAULT",
    "PORTFOLIO_FROZEN",
    "EDUCATIONAL_MODE_ONLY",
    "HUMAN_REVIEW_REQUIRED",
]


def default_ledger_block_reasons() -> list[str]:
    return list(DEFAULT_LEDGER_BLOCK_REASONS)


@dataclass(frozen=True)
class DecisionLedgerPolicy:
    timeframe: str = "multi"
    timestamp: str = ""
    policy_version: str = "lot15_decision_ledger_v0"
    ledger_version: str = "lot15_decision_ledger_v0"
    trading_decision: str = "WAIT"
    system_decision: str = "BLOCK_TRADING"
    final_decision: str = "WAIT"
    final_system_decision: str = "BLOCK_TRADING"
    decision_firewall_state: str = "ACTIVE"
    execution_allowed: bool = False
    trade_allowed: bool = False
    used_for_decision: bool = False
    risk_allowed: bool = False
    exposure_allowed: bool = False
    portfolio_change_allowed: bool = False
    allocation_change_allowed: bool = False
    rebalance_allowed: bool = False
    order_routing_allowed: bool = False
    external_connectivity_allowed: bool = False
    human_review_required: bool = True
    ledger_state: str = "RECORDED"
    audit_trail_state: str = "ACTIVE"
    immutability_mode: str = "APPEND_ONLY_SIMULATED"
    ledger_block_reasons: list[str] = field(default_factory=default_ledger_block_reasons)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionLedgerCheck:
    check_name: str
    status: str = "BLOCK"
    expected_value: str | bool = ""
    observed_value: str | bool = ""
    block_reason: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionLedgerEntry:
    timeframe: str
    timestamp: str
    policy_version: str
    ledger_version: str
    ledger_entry_id: str
    ledger_sequence: int
    source_decision_id: str
    source_timeframe: str
    source_timestamp: str
    trading_decision: str = "WAIT"
    system_decision: str = "BLOCK_TRADING"
    final_decision: str = "WAIT"
    final_system_decision: str = "BLOCK_TRADING"
    decision_firewall_state: str = "ACTIVE"
    execution_allowed: bool = False
    trade_allowed: bool = False
    used_for_decision: bool = False
    risk_allowed: bool = False
    exposure_allowed: bool = False
    portfolio_change_allowed: bool = False
    allocation_change_allowed: bool = False
    rebalance_allowed: bool = False
    order_routing_allowed: bool = False
    external_connectivity_allowed: bool = False
    human_review_required: bool = True
    ledger_state: str = "RECORDED"
    audit_trail_state: str = "ACTIVE"
    immutability_mode: str = "APPEND_ONLY_SIMULATED"
    ledger_block_reasons: list[str] = field(default_factory=default_ledger_block_reasons)
    ledger_checks: list[DecisionLedgerCheck] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    source_checksums: dict[str, str] = field(default_factory=dict)
    entry_checksum: str = ""
    previous_entry_checksum: str = ""
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionLedgerResult:
    policy_version: str = "lot15_decision_ledger_v0"
    ledger_version: str = "lot15_decision_ledger_v0"
    counts_by_timeframe: dict[str, int] = field(default_factory=dict)
    total_entries: int = 0
    ledger_state: str = "RECORDED"
    audit_trail_state: str = "ACTIVE"
    immutability_mode: str = "APPEND_ONLY_SIMULATED"
    source_artifacts: list[str] = field(default_factory=list)
    output_paths: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
