from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso

DEFAULT_CLOSURE_BLOCK_REASONS = [
    "V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
    "NO_EXECUTION_ALLOWED",
    "NO_EXTERNAL_CONNECTIVITY",
    "NO_EXCHANGE_CONNECTOR",
    "NO_ORDER_ROUTER",
    "NO_API_KEYS",
    "NO_WEBSOCKET",
    "NO_PAPER_TRADING",
    "NO_STRATEGY_ENGINE",
    "EDUCATIONAL_MODE_ONLY",
    "HUMAN_REVIEW_REQUIRED_BEFORE_V2",
]


def default_closure_block_reasons() -> list[str]:
    return list(DEFAULT_CLOSURE_BLOCK_REASONS)


@dataclass(frozen=True)
class ClosurePolicy:
    closure_version: str = "lot20_v1_closure_v0"
    policy_version: str = "lot20_v1_closure_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    closure_state: str = "V1_DEFENSIVE_AUDIT_CLOSED"
    archive_state: str = "ARCHIVE_CREATED"
    archive_created: bool = True
    release_candidate_state: str = "READY_FOR_LOCAL_AUDIT_REVIEW"
    acceptance_state: str = "ACCEPTANCE_BUNDLE_GENERATED"
    compliance_state: str = "COMPLIANT"
    no_trading_state: str = "ENFORCED"
    health_state: str = "HEALTHY_FOR_LOCAL_AUDIT"
    reproducibility_state: str = "REPRODUCIBLE_LOCALLY"
    pytest_state: str = "GREEN"
    exact_chain_state: str = "GREEN"
    live_execution: str = "DISABLED"
    leverage: str = "FORBIDDEN"
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
    closure_block_reasons: list[str] = field(default_factory=default_closure_block_reasons)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClosureCheck:
    check_name: str
    status: str = "PASS"
    expected_value: Any = ""
    observed_value: Any = ""
    block_reason: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArchiveManifest:
    closure_version: str
    policy_version: str
    project_name: str
    project_mode: str
    created_at: str
    closure_state: str
    archive_state: str
    archive_created: bool
    archive_path: str
    archive_sha256_path: str
    archive_sha256: str
    archive_size_bytes: int
    release_candidate_state: str
    acceptance_state: str
    compliance_state: str
    no_trading_state: str
    health_state: str
    reproducibility_state: str
    pytest_state: str
    exact_chain_state: str
    live_execution: str
    leverage: str
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
    source_artifacts: list[str] = field(default_factory=list)
    included_paths: list[str] = field(default_factory=list)
    excluded_paths: list[str] = field(default_factory=list)
    closure_checks: list[ClosureCheck] = field(default_factory=list)
    closure_block_reasons: list[str] = field(default_factory=default_closure_block_reasons)
    invariants: dict[str, str | bool | int] = field(default_factory=dict)
    closure_checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClosureResult:
    closure_version: str = "lot20_v1_closure_v0"
    policy_version: str = "lot20_v1_closure_v0"
    closure_state: str = "V1_DEFENSIVE_AUDIT_CLOSED"
    archive_state: str = "ARCHIVE_CREATED"
    archive_path: str = ""
    archive_sha256_path: str = ""
    archive_sha256: str = ""
    archive_size_bytes: int = 0
    closure_check_count: int = 0
    output_paths: list[str] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
