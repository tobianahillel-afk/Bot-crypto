from pathlib import Path
from typing import Any

from crypto_quant_bot.audit.available_at import audit_available_at, audit_used_for_decision
from crypto_quant_bot.audit.forbidden_names import audit_forbidden_names, key_is_forbidden
from crypto_quant_bot.audit.lookahead import default_audited_dataset_paths, read_jsonl
from crypto_quant_bot.contracts.audit import FeatureAuditResult
from crypto_quant_bot.core.config_loader import load_simple_yaml


REQUIRED_FEATURES = {
    "close",
    "simple_return_1",
    "log_return_1",
    "hl_range",
    "oc_change",
    "typical_price",
    "true_range",
    "rolling_mean_close_3",
    "rolling_volatility_return_3",
    "volume_sum_3",
    "realized_volatility_3",
    "realized_volatility_6",
    "atr_3",
    "atr_6",
    "rolling_high_6",
    "rolling_low_6",
    "rolling_range_6",
    "rolling_mid_6",
    "close_position_in_range_6",
    "range_width_pct",
    "compression_score",
    "expansion_score",
    "range_state",
    "direction_score",
    "trend_score",
    "range_score",
    "volatility_score",
    "regime_state",
    "regime_confidence_score",
}

REQUIRED_REGISTRY_FIELDS = [
    "name",
    "description",
    "inputs",
    "formula",
    "timeframe",
    "available_at_rule",
    "lookahead_safe",
    "status",
]

SKIP_KEYS = {
    "id",
    "schema_version",
    "source",
    "created_at",
    "available_at",
    "lineage_id",
    "quality_flag",
    "validation_status",
    "used_for_decision",
    "pair",
    "timeframe",
    "timestamp",
    "feature_set_id",
    "source_dataset_id",
    "source_dataset_ids",
    "data_version",
    "market_state_id",
    "regime_id",
    "pivot_id",
    "zone_id",
    "anchor_id",
    "anchor_time",
    "anchor_type",
    "selected_at",
    "selection_rule",
    "source_object_id",
    "profile_id",
    "bin_id",
    "first_seen_at",
    "last_confirmed_at",
    "detected_at",
    "confirmed_at",
    "usable_from",
    "pivot_time",
    "method",
    "side",
    "left_window",
    "right_window",
    "lookback_window",
    "candle_index",
    "source_pivot_ids",
    "zone_type",
    "lower_bound",
    "upper_bound",
    "center_price",
    "touch_count",
    "price",
    "candle",
    "component_available_at",
    "data_quality",
    "nearest_pivots",
    "nearest_zones",
    "strength_components",
    "components",
    "open",
    "high",
    "low",
    "volume",
    "trades",
}

FEATURE_CONTAINERS = {
    "features",
    "basic_features",
    "vwap_state",
    "anchored_vwap_state",
    "volatility_state",
    "range_state",
    "regime_state",
}


def load_registry_entries(path: Path | str) -> dict[str, dict[str, Any]]:
    raw = load_simple_yaml(path)
    entries: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            entry = dict(value)
            entry.setdefault("name", str(key))
            entries[str(key)] = entry
        else:
            entries[str(key)] = {
                "name": str(key),
                "description": "legacy registry entry",
                "inputs": "legacy",
                "formula": "legacy",
                "timeframe": "5m/15m",
                "available_at_rule": "legacy",
                "lookahead_safe": True,
                "status": str(value),
            }
    return entries


def _collect_from_object(obj: Any, out: set[str], *, parent_key: str | None = None) -> None:
    if not isinstance(obj, dict):
        return
    for container in FEATURE_CONTAINERS:
        value = obj.get(container)
        if isinstance(value, dict):
            for key in value:
                key_text = str(key)
                if key_text not in SKIP_KEYS:
                    out.add(key_text)
    for key, value in obj.items():
        key_text = str(key)
        if key_text in SKIP_KEYS or key_text in FEATURE_CONTAINERS:
            continue
        if isinstance(value, (int, float, str, bool, type(None))):
            if key_text.endswith("_score") or key_text.endswith("_state") or key_text in {"vwap", "anchored_vwap", "cumulative_volume", "cumulative_price_volume"}:
                out.add(key_text)


def collect_dataset_features(paths: list[Path]) -> list[str]:
    features: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        rows = read_jsonl(path)
        for row in rows:
            _collect_from_object(row, features)
    return sorted(features)


def audit_registry_structure(entries: dict[str, dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for feature_name, entry in sorted(entries.items()):
        missing = [field for field in REQUIRED_REGISTRY_FIELDS if field not in entry]
        if missing:
            errors.append(f"registry entry {feature_name} missing fields: {', '.join(missing)}")
        if entry.get("name") != feature_name:
            errors.append(f"registry entry {feature_name} has inconsistent name")
        if not isinstance(entry.get("lookahead_safe"), bool):
            errors.append(f"registry entry {feature_name} lookahead_safe must be boolean")
        if not entry.get("status"):
            errors.append(f"registry entry {feature_name} status must be non-empty")
        if not entry.get("available_at_rule"):
            errors.append(f"registry entry {feature_name} available_at_rule must be non-empty")
        if key_is_forbidden(feature_name):
            errors.append(f"registry entry {feature_name} uses a forbidden feature name")
    if not entries:
        errors.append("feature registry is empty")
    return errors, warnings


def audit_feature_registry(root: Path, dataset_paths: list[Path] | None = None) -> FeatureAuditResult:
    registry_path = root / "config" / "feature_registry.yaml"
    docs_path = root / "docs" / "FEATURE_REGISTRY.md"
    paths = dataset_paths or default_audited_dataset_paths(root)
    errors: list[str] = []
    warnings: list[str] = []
    if not registry_path.exists():
        errors.append(f"missing registry: {registry_path}")
    if not docs_path.exists():
        errors.append(f"missing docs: {docs_path}")
    entries: dict[str, dict[str, Any]] = {}
    if not errors:
        entries = load_registry_entries(registry_path)
        structure_errors, structure_warnings = audit_registry_structure(entries)
        errors.extend(structure_errors)
        warnings.extend(structure_warnings)
    registered = sorted(entries)
    dataset_features = collect_dataset_features(paths)
    missing = [feature for feature in dataset_features if feature not in entries]
    missing_required = sorted(feature for feature in REQUIRED_FEATURES if feature not in entries)
    if missing_required:
        missing.extend(feature for feature in missing_required if feature not in missing)
    unused = [feature for feature in registered if feature not in dataset_features]
    forbidden: list[dict[str, Any]] = []
    available_violations: list[dict[str, Any]] = []
    used_for_decision_violations: list[dict[str, Any]] = []
    lookahead_violations: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            errors.append(f"missing audited dataset: {path}")
            continue
        rows = read_jsonl(path)
        forbidden.extend(audit_forbidden_names(rows, path))
        available_violations.extend(audit_available_at(rows, path))
        used_for_decision_violations.extend(audit_used_for_decision(rows, path))
    if missing:
        errors.append(f"dataset features missing from registry: {', '.join(missing)}")
    if unused:
        warnings.append(f"registry entries not observed in audited datasets: {', '.join(unused)}")
    validation_status = "validated_lot8" if not errors and not forbidden and not available_violations and not used_for_decision_violations else "failed_lot8"
    quality_flag = "valid" if validation_status == "validated_lot8" else "invalid"
    return FeatureAuditResult(
        audit_id="lot8_feature_registry_static",
        checked_at="lot8_static_check",
        registry_path=str(registry_path),
        dataset_paths=[str(path) for path in paths],
        registered_features=registered,
        dataset_features=dataset_features,
        missing_from_registry=missing,
        unused_registry_features=unused,
        forbidden_feature_names=forbidden,
        lookahead_violations=lookahead_violations,
        available_at_violations=available_violations,
        used_for_decision_violations=used_for_decision_violations,
        errors=errors,
        warnings=warnings,
        source="lot8_feature_registry_audit",
        quality_flag=quality_flag,
        validation_status=validation_status,
        used_for_decision=False,
    )
