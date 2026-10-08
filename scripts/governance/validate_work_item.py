#!/usr/bin/env python3
"""Validate bounded work-item manifests with Python standard library only."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"^[A-Z][A-Z0-9_-]*(?:[.-][A-Z0-9_-]+)*$")
KINDS = {
    "bootstrap_work_item",
    "engineering_work_item",
    "audit_work_item",
    "business_work_unit",
}
STATUSES = {"PLANNED", "IN_PROGRESS", "BLOCKED", "DONE"}
REQUIRED_KEYS = {
    "schema_version",
    "kind",
    "id",
    "title",
    "status",
    "objective",
    "depends_on",
    "allowed_paths",
    "forbidden_scope",
    "tasks",
    "done_when",
}
OPTIONAL_KEYS = {"extensions"}


class WorkItemError(ValueError):
    """Raised when a work-item manifest violates V1 semantics."""


def _load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkItemError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise WorkItemError(f"{path} must contain an object")
    return data


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkItemError(f"{field} must be a non-empty string")
    return value


def _unique_strings(value: Any, field: str, *, non_empty: bool) -> list[str]:
    if not isinstance(value, list) or (non_empty and not value):
        requirement = "a non-empty list" if non_empty else "a list"
        raise WorkItemError(f"{field} must be {requirement}")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise WorkItemError(f"{field} must contain non-empty strings")
    if len(value) != len(set(value)):
        raise WorkItemError(f"{field} must not contain duplicates")
    return value


def validate_manifest(manifest: dict[str, Any], *, source: str = "<manifest>") -> None:
    keys = set(manifest)
    missing = sorted(REQUIRED_KEYS - keys)
    unknown = sorted(keys - REQUIRED_KEYS - OPTIONAL_KEYS)
    if missing:
        raise WorkItemError(f"{source}: missing keys: {missing}")
    if unknown:
        raise WorkItemError(f"{source}: unknown top-level keys: {unknown}")
    if manifest["schema_version"] != 1:
        raise WorkItemError(f"{source}: schema_version must be 1")

    kind = manifest["kind"]
    if kind not in KINDS:
        raise WorkItemError(f"{source}: unsupported kind {kind!r}")

    item_id = _string(manifest["id"], f"{source}.id")
    if ID_RE.fullmatch(item_id) is None:
        raise WorkItemError(f"{source}: invalid work-item id {item_id!r}")

    _string(manifest["title"], f"{source}.title")
    _string(manifest["objective"], f"{source}.objective")

    status = manifest["status"]
    if status not in STATUSES:
        raise WorkItemError(f"{source}: invalid status {status!r}")

    dependencies = _unique_strings(
        manifest["depends_on"], f"{source}.depends_on", non_empty=False
    )
    if item_id in dependencies:
        raise WorkItemError(f"{source}: work item cannot depend on itself")

    _unique_strings(manifest["allowed_paths"], f"{source}.allowed_paths", non_empty=True)
    _unique_strings(manifest["forbidden_scope"], f"{source}.forbidden_scope", non_empty=True)
    _unique_strings(manifest["done_when"], f"{source}.done_when", non_empty=True)

    tasks = manifest["tasks"]
    if not isinstance(tasks, list) or not tasks:
        raise WorkItemError(f"{source}.tasks must be a non-empty list")

    task_ids: list[str] = []
    task_statuses: list[str] = []
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise WorkItemError(f"{source}.tasks[{index}] must be an object")
        if set(task) != {"id", "status", "description"}:
            raise WorkItemError(
                f"{source}.tasks[{index}] must contain only id/status/description"
            )
        task_id = _string(task["id"], f"{source}.tasks[{index}].id")
        if not task_id.startswith(f"{item_id}."):
            raise WorkItemError(f"{source}: task {task_id!r} must belong to {item_id}")
        if task_id in task_ids:
            raise WorkItemError(f"{source}: duplicate task id {task_id}")
        task_ids.append(task_id)
        task_status = task["status"]
        if task_status not in STATUSES:
            raise WorkItemError(f"{source}: invalid task status {task_status!r}")
        task_statuses.append(task_status)
        _string(task["description"], f"{source}.tasks[{index}].description")

    if status == "PLANNED" and any(value != "PLANNED" for value in task_statuses):
        raise WorkItemError(f"{source}: PLANNED work item must contain only PLANNED tasks")
    if status == "DONE" and any(value != "DONE" for value in task_statuses):
        raise WorkItemError(f"{source}: DONE work item requires every task DONE")
    if status == "IN_PROGRESS":
        active_indexes = [i for i, value in enumerate(task_statuses) if value == "IN_PROGRESS"]
        if len(active_indexes) != 1:
            raise WorkItemError(f"{source}: IN_PROGRESS work item requires one active task")
        active_index = active_indexes[0]
        if any(value != "DONE" for value in task_statuses[:active_index]):
            raise WorkItemError(f"{source}: tasks before active task must be DONE")
        if any(value != "PLANNED" for value in task_statuses[active_index + 1 :]):
            raise WorkItemError(f"{source}: tasks after active task must be PLANNED")
    if status == "BLOCKED":
        if "IN_PROGRESS" in task_statuses:
            raise WorkItemError(f"{source}: BLOCKED work item cannot contain IN_PROGRESS task")


def validate_set(manifests: dict[str, dict[str, Any]]) -> None:
    for item_id, manifest in manifests.items():
        validate_manifest(manifest, source=item_id)
        if manifest["id"] != item_id:
            raise WorkItemError(f"manifest key {item_id!r} disagrees with embedded id")

    for item_id, manifest in manifests.items():
        for dependency in manifest["depends_on"]:
            if dependency not in manifests:
                raise WorkItemError(f"{item_id}: unknown dependency {dependency}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in visited:
            return
        if item_id in visiting:
            raise WorkItemError(f"dependency cycle detected at {item_id}")
        visiting.add(item_id)
        for dependency in manifests[item_id]["depends_on"]:
            visit(dependency)
        visiting.remove(item_id)
        visited.add(item_id)

    for item_id in manifests:
        visit(item_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Manifest paths. Defaults to engineering/lots/*.json.",
    )
    args = parser.parse_args()

    paths = args.paths or sorted((root / "engineering" / "lots").glob("*.json"))
    try:
        manifests: dict[str, dict[str, Any]] = {}
        for path in paths:
            manifest = _load(path)
            item_id = str(manifest.get("id", path.stem))
            if item_id in manifests:
                raise WorkItemError(f"duplicate work-item id across files: {item_id}")
            manifests[item_id] = manifest
        if not manifests:
            raise WorkItemError("no work-item manifests found")
        validate_set(manifests)
    except WorkItemError as exc:
        print(f"WORK_ITEM_INVALID: {exc}", file=sys.stderr)
        return 1

    print(f"WORK_ITEMS_VALID count={len(manifests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
