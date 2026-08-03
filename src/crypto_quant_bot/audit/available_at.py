from pathlib import Path
from typing import Any


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _violation(dataset_path: Path | str, row_index: int, path: str, rule: str, value: Any, reference: Any) -> dict[str, Any]:
    return {
        "dataset_path": str(dataset_path),
        "row_index": row_index,
        "path": path,
        "rule": rule,
        "value": value,
        "reference": reference,
    }


def _walk_nested_temporal(
    obj: Any,
    *,
    dataset_path: Path | str,
    row_index: int,
    row_available_at: str,
    max_nodes: int = 50000,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    stack: list[tuple[Any, str]] = [(obj, "$")]
    seen = 0
    while stack:
        current, path = stack.pop()
        seen += 1
        if seen > max_nodes:
            violations.append(_violation(dataset_path, row_index, path, "nested temporal scan node limit", seen, max_nodes))
            return violations
        if isinstance(current, dict):
            usable_from = current.get("usable_from")
            if _is_text(usable_from) and _is_text(row_available_at) and str(usable_from) > row_available_at:
                violations.append(_violation(dataset_path, row_index, f"{path}.usable_from", "usable_from <= row.available_at", usable_from, row_available_at))
            local_available_at = current.get("available_at")
            if _is_text(local_available_at) and _is_text(row_available_at) and str(local_available_at) > row_available_at:
                violations.append(_violation(dataset_path, row_index, f"{path}.available_at", "nested available_at <= row.available_at", local_available_at, row_available_at))
            for key, value in current.items():
                if isinstance(value, (dict, list)):
                    stack.append((value, f"{path}.{key}"))
        elif isinstance(current, list):
            for index, item in enumerate(current):
                if isinstance(item, (dict, list)):
                    stack.append((item, f"{path}[{index}]"))
    return violations


def _check_nested_lists(row: dict[str, Any], dataset_path: Path | str, row_index: int, available_at: Any) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if not _is_text(available_at):
        return violations
    for container_name in ["nearest_pivots", "nearest_zones"]:
        value = row.get(container_name)
        if not isinstance(value, list):
            continue
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                continue
            usable_from = item.get("usable_from")
            if _is_text(usable_from) and str(usable_from) > str(available_at):
                violations.append(_violation(dataset_path, row_index, f"$.{container_name}[{index}].usable_from", "usable_from <= row.available_at", usable_from, available_at))
            local_available_at = item.get("available_at")
            if _is_text(local_available_at) and str(local_available_at) > str(available_at):
                violations.append(_violation(dataset_path, row_index, f"$.{container_name}[{index}].available_at", "nested available_at <= row.available_at", local_available_at, available_at))
    return violations


def audit_available_at(rows: list[dict[str, Any]], dataset_path: Path | str) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=1):
        available_at = row.get("available_at")
        timestamp = row.get("timestamp")
        if "available_at" in row and not _is_text(available_at):
            violations.append(_violation(dataset_path, row_index, "$.available_at", "available_at must be non-empty", available_at, None))
        if _is_text(timestamp) and _is_text(available_at) and str(timestamp) > str(available_at):
            violations.append(_violation(dataset_path, row_index, "$.timestamp", "timestamp <= available_at", timestamp, available_at))
        usable_from = row.get("usable_from")
        if _is_text(usable_from) and _is_text(available_at) and str(usable_from) > str(available_at):
            violations.append(_violation(dataset_path, row_index, "$.usable_from", "usable_from <= available_at", usable_from, available_at))
        component_available_at = row.get("component_available_at")
        if isinstance(component_available_at, dict):
            component_values: list[str] = []
            for name, value in component_available_at.items():
                if _is_text(value):
                    component_values.append(str(value))
                    if _is_text(available_at) and str(value) > str(available_at):
                        violations.append(_violation(dataset_path, row_index, f"$.component_available_at.{name}", "component_available_at <= available_at", value, available_at))
                else:
                    violations.append(_violation(dataset_path, row_index, f"$.component_available_at.{name}", "component_available_at must be non-empty string", value, available_at))
            if component_values and _is_text(available_at) and max(component_values) > str(available_at):
                violations.append(_violation(dataset_path, row_index, "$.available_at", "MarketStatePoint available_at >= max(component_available_at)", available_at, max(component_values)))
        violations.extend(_check_nested_lists(row, dataset_path, row_index, available_at))
    return violations


def audit_used_for_decision(rows: list[dict[str, Any]], dataset_path: Path | str) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=1):
        value = row.get("used_for_decision")
        if value is not False:
            violations.append(_violation(dataset_path, row_index, "$.used_for_decision", "used_for_decision must be false", value, False))
    return violations
