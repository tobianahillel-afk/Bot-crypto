from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso

DEFAULT_HEALTH_BLOCK_REASONS = [
    "LOCAL_HEALTH_MONITOR_ONLY",
    "NO_EXTERNAL_CONNECTIVITY",
    "NO_EXECUTION_ALLOWED",
    "NO_EXCHANGE_CONNECTOR",
    "NO_ORDER_ROUTER",
    "EDUCATIONAL_MODE_ONLY",
    "REPRODUCIBILITY_MANIFEST_REQUIRED",
]


def default_health_block_reasons() -> list[str]:
    return list(DEFAULT_HEALTH_BLOCK_REASONS)


@dataclass(frozen=True)
class HealthPolicy:
    health_version: str = "lot17_health_monitor_v0"
    policy_version: str = "lot17_health_monitor_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    health_state: str = "HEALTHY_FOR_LOCAL_AUDIT"
    integrity_state: str = "VERIFIED"
    reproducibility_state: str = "REPRODUCIBLE_LOCALLY"
    monitoring_mode: str = "LOCAL_STATIC_ONLY"
    external_connectivity_allowed: bool = False
    execution_allowed: bool = False
    trade_allowed: bool = False
    health_block_reasons: list[str] = field(default_factory=default_health_block_reasons)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HealthCheck:
    check_name: str
    status: str = "PASS"
    expected_value: Any = ""
    observed_value: Any = ""
    block_reason: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HealthSnapshot:
    health_version: str
    policy_version: str
    project_name: str
    project_mode: str
    created_at: str
    health_state: str
    integrity_state: str
    reproducibility_state: str
    monitoring_mode: str
    external_connectivity_allowed: bool
    execution_allowed: bool
    trade_allowed: bool
    dataset_catalog_path: str
    dataset_catalog_readable: bool
    dataset_catalog_checksum: str
    lot16_manifest_path: str
    lot16_manifest_readable: bool
    lot16_manifest_checksum: str
    lot16_artifacts_path: str
    lot16_artifacts_readable: bool
    artifact_count: int
    required_artifacts_present: bool
    required_reports_present: bool
    required_scripts_present: bool
    required_diagnostics_present: bool
    critical_counts_valid: bool
    checksum_references_valid: bool
    pytest_expected: str
    exact_chain_expected: str
    health_checks: list[HealthCheck] = field(default_factory=list)
    health_block_reasons: list[str] = field(default_factory=default_health_block_reasons)
    invariants: dict[str, str | bool | int] = field(default_factory=dict)
    source_artifacts: list[str] = field(default_factory=list)
    health_checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HealthMonitorResult:
    health_version: str = "lot17_health_monitor_v0"
    policy_version: str = "lot17_health_monitor_v0"
    artifact_count: int = 0
    health_check_count: int = 0
    health_state: str = "HEALTHY_FOR_LOCAL_AUDIT"
    integrity_state: str = "VERIFIED"
    reproducibility_state: str = "REPRODUCIBLE_LOCALLY"
    output_paths: list[str] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
