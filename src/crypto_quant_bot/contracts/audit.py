from dataclasses import dataclass, field
from typing import Any

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class FeatureAuditResult(BaseContract):
    audit_id: str = ""
    checked_at: str = ""
    registry_path: str = ""
    dataset_paths: list[str] = field(default_factory=list)
    registered_features: list[str] = field(default_factory=list)
    dataset_features: list[str] = field(default_factory=list)
    missing_from_registry: list[str] = field(default_factory=list)
    unused_registry_features: list[str] = field(default_factory=list)
    forbidden_feature_names: list[dict[str, Any]] = field(default_factory=list)
    lookahead_violations: list[dict[str, Any]] = field(default_factory=list)
    available_at_violations: list[dict[str, Any]] = field(default_factory=list)
    used_for_decision_violations: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LookaheadAuditResult(BaseContract):
    audit_id: str = ""
    checked_at: str = ""
    dataset_path: str = ""
    row_count: int = 0
    timestamp_field: str = "timestamp"
    available_at_field: str = "available_at"
    component_available_at_checked: bool = False
    violations: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
