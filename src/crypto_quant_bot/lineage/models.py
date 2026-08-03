from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso

DEFAULT_LINEAGE_BLOCK_REASONS = [
    "REPRODUCIBILITY_MANIFEST_ONLY",
    "LOCAL_ARTIFACTS_ONLY",
    "NO_EXTERNAL_CONNECTIVITY",
    "NO_EXECUTION_ALLOWED",
    "NO_EXCHANGE_CONNECTOR",
    "NO_ORDER_ROUTER",
    "EDUCATIONAL_MODE_ONLY",
]


def default_lineage_block_reasons() -> list[str]:
    return list(DEFAULT_LINEAGE_BLOCK_REASONS)


@dataclass(frozen=True)
class LineagePolicy:
    manifest_version: str = "lot16_reproducibility_manifest_v0"
    policy_version: str = "lot16_reproducibility_manifest_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    reproducibility_state: str = "REPRODUCIBLE_LOCALLY"
    lineage_state: str = "RECORDED"
    external_connectivity_allowed: bool = False
    execution_allowed: bool = False
    trade_allowed: bool = False
    lineage_block_reasons: list[str] = field(default_factory=default_lineage_block_reasons)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LineageArtifact:
    artifact_id: str
    lot: str
    artifact_type: str
    path: str
    checksum_sha256: str
    size_bytes: int
    line_count: int
    required: bool
    produced_by: str
    consumes: list[str] = field(default_factory=list)
    validation_command: str = ""
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LineageCheck:
    check_name: str
    status: str = "BLOCK"
    expected_value: str | bool | int = ""
    observed_value: str | bool | int = ""
    block_reason: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReproducibilityManifest:
    manifest_version: str
    policy_version: str
    project_name: str
    project_mode: str
    created_at: str
    reproducibility_state: str
    lineage_state: str
    external_connectivity_allowed: bool
    execution_allowed: bool
    trade_allowed: bool
    source_catalog_path: str
    reproducibility_scope_lot16: str
    source_catalog_scope: str
    source_catalog_entry_count: int
    source_catalog_checksum: str
    artifact_count: int
    artifacts: list[LineageArtifact] = field(default_factory=list)
    critical_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    replay_commands: list[str] = field(default_factory=list)
    validation_commands: list[str] = field(default_factory=list)
    lineage_checks: list[LineageCheck] = field(default_factory=list)
    lineage_block_reasons: list[str] = field(default_factory=default_lineage_block_reasons)
    invariants: dict[str, str | bool | int] = field(default_factory=dict)
    source_artifacts: list[str] = field(default_factory=list)
    manifest_checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LineageResult:
    manifest_version: str = "lot16_reproducibility_manifest_v0"
    policy_version: str = "lot16_reproducibility_manifest_v0"
    artifact_count: int = 0
    critical_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    reproducibility_state: str = "REPRODUCIBLE_LOCALLY"
    lineage_state: str = "RECORDED"
    output_paths: list[str] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
