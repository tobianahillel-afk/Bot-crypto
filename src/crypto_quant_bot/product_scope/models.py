from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso

DEFAULT_SCOPE_BLOCK_REASONS = [
    "V2_SCOPE_LOCK_ONLY",
    "NO_EXECUTION_ALLOWED",
    "NO_EXTERNAL_CONNECTIVITY",
    "NO_EXCHANGE_CONNECTOR",
    "NO_ORDER_ROUTER",
    "NO_API_KEYS",
    "NO_WEBSOCKET",
    "NO_PAPER_TRADING_ACTIVE",
    "NO_LIVE_TRADING_ACTIVE",
    "EDUCATIONAL_MODE_ONLY",
    "HUMAN_REVIEW_REQUIRED_BEFORE_IMPLEMENTATION",
]


def default_scope_block_reasons() -> list[str]:
    return list(DEFAULT_SCOPE_BLOCK_REASONS)


@dataclass(frozen=True)
class ProductScopePolicy:
    scope_version: str = "lot21_product_scope_v0"
    policy_version: str = "lot21_product_scope_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_identity: str = "SAME_PROJECT_NO_V4"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    v1_closure_state: str = "V1_DEFENSIVE_AUDIT_CLOSED"
    v2_scope_state: str = "OPENED_AS_PLANNING_ONLY"
    scope_state: str = "FUNCTIONAL_SCOPE_LOCKED"
    execution_allowed: bool = False
    trade_allowed: bool = False
    external_connectivity_allowed: bool = False
    live_execution: str = "DISABLED"
    leverage: str = "FORBIDDEN"
    scope_block_reasons: list[str] = field(default_factory=default_scope_block_reasons)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FunctionalCapability:
    capability_id: str
    title: str
    status: str
    phase: str
    description: str
    depends_on: list[str] = field(default_factory=list)
    not_yet_implemented: bool = True
    execution_allowed: bool = False
    external_connectivity_allowed: bool = False
    risk_level: str = "MEDIUM"
    acceptance_required_before_activation: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoadmapPhase:
    phase_id: str
    title: str
    objective: str
    start_lot_estimate: str
    end_lot_estimate: str
    status: str
    activation_constraints: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoadmapLot:
    lot_number: int
    lot_id: str
    phase_id: str
    title: str
    objective: str
    status: str
    planning_only: bool = True
    activation_constraints: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProductScopeRegistry:
    scope_version: str
    policy_version: str
    project_name: str
    project_identity: str
    project_mode: str
    created_at: str
    source_v1_archive_path: str
    source_v1_archive_frozen: bool
    source_v1_archive_sha256: str
    source_v1_archive_size_bytes: int
    v1_closure_state: str
    v2_scope_state: str
    scope_state: str
    execution_allowed: bool
    trade_allowed: bool
    external_connectivity_allowed: bool
    live_execution: str
    leverage: str
    capability_count: int
    phase_count: int
    future_lot_count: int
    capabilities: list[FunctionalCapability] = field(default_factory=list)
    roadmap_phases: list[RoadmapPhase] = field(default_factory=list)
    roadmap_lots: list[RoadmapLot] = field(default_factory=list)
    safety_boundaries: list[str] = field(default_factory=list)
    research_boundaries: list[str] = field(default_factory=list)
    live_trading_boundaries: list[str] = field(default_factory=list)
    ui_boundaries: list[str] = field(default_factory=list)
    api_boundaries: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    scope_checks: list[dict[str, Any]] = field(default_factory=list)
    scope_block_reasons: list[str] = field(default_factory=default_scope_block_reasons)
    source_artifacts: list[str] = field(default_factory=list)
    scope_checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProductScopeResult:
    scope_version: str = "lot21_product_scope_v0"
    policy_version: str = "lot21_product_scope_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_identity: str = "SAME_PROJECT_NO_V4"
    scope_state: str = "FUNCTIONAL_SCOPE_LOCKED"
    v2_scope_state: str = "OPENED_AS_PLANNING_ONLY"
    capability_count: int = 0
    phase_count: int = 0
    future_lot_count: int = 0
    output_paths: list[str] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
