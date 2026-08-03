from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso

DEFAULT_COMPLIANCE_BLOCK_REASONS = [
    "FINAL_NO_TRADING_COMPLIANCE_ONLY",
    "NO_EXECUTION_ALLOWED",
    "NO_EXTERNAL_CONNECTIVITY",
    "NO_EXCHANGE_CONNECTOR",
    "NO_ORDER_ROUTER",
    "NO_API_KEYS",
    "NO_WEBSOCKET",
    "NO_PAPER_TRADING",
    "NO_STRATEGY_ENGINE",
    "EDUCATIONAL_MODE_ONLY",
]


def default_compliance_block_reasons() -> list[str]:
    return list(DEFAULT_COMPLIANCE_BLOCK_REASONS)


@dataclass(frozen=True)
class CompliancePolicy:
    compliance_version: str = "lot18_no_trading_compliance_v0"
    policy_version: str = "lot18_no_trading_compliance_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    compliance_state: str = "COMPLIANT"
    no_trading_state: str = "ENFORCED"
    execution_state: str = "DISABLED"
    connectivity_state: str = "DISABLED"
    artifact_integrity_state: str = "VERIFIED"
    health_state: str = "HEALTHY_FOR_LOCAL_AUDIT"
    reproducibility_state: str = "REPRODUCIBLE_LOCALLY"
    live_execution: str = "DISABLED"
    leverage: str = "FORBIDDEN"
    trading_decision: str = "WAIT"
    system_decision: str = "BLOCK_TRADING"
    final_decision: str = "WAIT"
    final_system_decision: str = "BLOCK_TRADING"
    trade_allowed: bool = False
    execution_allowed: bool = False
    external_connectivity_allowed: bool = False
    exchange_connector_present: bool = False
    order_router_present: bool = False
    api_key_present: bool = False
    websocket_present: bool = False
    paper_trading_present: bool = False
    strategy_present: bool = False
    forbidden_semantics_present: bool = False
    critical_counts_valid: bool = True
    health_monitor_valid: bool = True
    reproducibility_manifest_valid: bool = True
    dataset_catalog_valid: bool = True
    required_artifacts_present: bool = True
    required_reports_present: bool = True
    required_scripts_present: bool = True
    compliance_block_reasons: list[str] = field(default_factory=default_compliance_block_reasons)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComplianceCheck:
    check_name: str
    status: str = "PASS"
    expected_value: Any = ""
    observed_value: Any = ""
    block_reason: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NoTradingComplianceSnapshot:
    compliance_version: str
    policy_version: str
    project_name: str
    project_mode: str
    created_at: str
    compliance_state: str
    no_trading_state: str
    execution_state: str
    connectivity_state: str
    artifact_integrity_state: str
    health_state: str
    reproducibility_state: str
    live_execution: str
    leverage: str
    trading_decision: str
    system_decision: str
    final_decision: str
    final_system_decision: str
    trade_allowed: bool
    execution_allowed: bool
    external_connectivity_allowed: bool
    exchange_connector_present: bool
    order_router_present: bool
    api_key_present: bool
    websocket_present: bool
    paper_trading_present: bool
    strategy_present: bool
    forbidden_semantics_present: bool
    critical_counts_valid: bool
    health_monitor_valid: bool
    reproducibility_manifest_valid: bool
    dataset_catalog_valid: bool
    required_artifacts_present: bool
    required_reports_present: bool
    required_scripts_present: bool
    compliance_checks: list[ComplianceCheck] = field(default_factory=list)
    compliance_block_reasons: list[str] = field(default_factory=default_compliance_block_reasons)
    invariants: dict[str, str | bool | int] = field(default_factory=dict)
    source_artifacts: list[str] = field(default_factory=list)
    compliance_checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NoTradingComplianceResult:
    compliance_version: str = "lot18_no_trading_compliance_v0"
    policy_version: str = "lot18_no_trading_compliance_v0"
    compliance_state: str = "COMPLIANT"
    no_trading_state: str = "ENFORCED"
    artifact_integrity_state: str = "VERIFIED"
    health_state: str = "HEALTHY_FOR_LOCAL_AUDIT"
    reproducibility_state: str = "REPRODUCIBLE_LOCALLY"
    artifact_count: int = 0
    compliance_check_count: int = 0
    output_paths: list[str] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
