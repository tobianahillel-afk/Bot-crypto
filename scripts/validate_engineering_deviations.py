#!/usr/bin/env python3
"""Validate that every engineering-standard finding has an owned temporary deviation."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from quality_inventory import build_inventory

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "config" / "governance" / "legacy_engineering_deviations_v1.json"
DEFAULT_REPORT = ROOT / "reports" / "quality" / "engineering_deviation_gate.json"
REQUIRED_ENTRY_FIELDS = {
    "finding_id",
    "category",
    "owner",
    "justification",
    "strengthened_controls",
    "remediation_trigger",
    "review_by",
    "status",
}


def _load_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("engineering deviation registry must be a JSON object")
    return payload


def _finding_metadata(finding: dict[str, object]) -> tuple[str, str]:
    if finding["category"] == "DUPLICATE_FUNCTION":
        return str(finding["category"]), " | ".join(str(item) for item in finding["locations"])
    return str(finding["category"]), f"{finding['path']}:{finding['line']}:{finding['name']}"


def evaluate(registry_path: Path) -> dict[str, object]:
    inventory = build_inventory()
    findings = inventory["findings"]
    registry = _load_registry(registry_path)
    entries = registry.get("deviations")
    errors: list[str] = []
    if registry.get("schema_version") != "legacy-engineering-deviations-v1":
        errors.append("invalid registry schema_version")
    if not isinstance(entries, list):
        entries = []
        errors.append("deviations must be a list")

    indexed: dict[str, dict[str, Any]] = {}
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            errors.append("deviation entry must be an object")
            continue
        missing_fields = sorted(REQUIRED_ENTRY_FIELDS - set(raw_entry))
        if missing_fields:
            errors.append(f"deviation missing fields: {', '.join(missing_fields)}")
            continue
        finding_id = str(raw_entry["finding_id"])
        if finding_id in indexed:
            errors.append(f"duplicate deviation entry: {finding_id}")
            continue
        indexed[finding_id] = raw_entry

    current_ids = {str(item["finding_id"]) for item in findings}
    registry_ids = set(indexed)
    for finding in findings:
        finding_id = str(finding["finding_id"])
        entry = indexed.get(finding_id)
        category, location = _finding_metadata(finding)
        if entry is None:
            errors.append(f"unregistered engineering finding: {finding_id} ({location})")
            continue
        if str(entry["category"]) != category:
            errors.append(f"category mismatch for {finding_id}")
        if str(entry["status"]) != "ACCEPTED_TEMPORARY":
            errors.append(f"invalid status for {finding_id}")
        for field in ("owner", "justification", "remediation_trigger"):
            if not str(entry[field]).strip():
                errors.append(f"empty {field} for {finding_id}")
        controls = entry["strengthened_controls"]
        if not isinstance(controls, list) or not controls or not all(
            isinstance(item, str) and item.strip() for item in controls
        ):
            errors.append(f"invalid strengthened_controls for {finding_id}")
        try:
            review_by = date.fromisoformat(str(entry["review_by"]))
        except ValueError:
            errors.append(f"invalid review_by for {finding_id}")
        else:
            if review_by < date.today():
                errors.append(f"expired deviation: {finding_id} ({review_by.isoformat()})")

    for stale_id in sorted(registry_ids - current_ids):
        errors.append(f"stale deviation entry must be removed: {stale_id}")

    return {
        "schema_version": "engineering-deviation-gate-v1",
        "inventory_schema_version": inventory["schema_version"],
        "finding_count": len(findings),
        "registered_count": len(registry_ids & current_ids),
        "unregistered_count": len(current_ids - registry_ids),
        "stale_count": len(registry_ids - current_ids),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def bootstrap_registry(path: Path) -> None:
    inventory = build_inventory()
    controls = [
        "full Lots 0-25 deterministic replay",
        "repository-wide 90% line and 85% branch coverage gates",
        "changed-file Ruff and 90% differential coverage gates",
        "targeted and P0.6 extended mutation score gates >= 80%",
        "three complete anti-flake pytest repetitions",
    ]
    deviations = []
    for finding in inventory["findings"]:
        category, location = _finding_metadata(finding)
        deviations.append(
            {
                "finding_id": finding["finding_id"],
                "category": category,
                "location": location,
                "owner": "Hillel Tobiana — Project Owner",
                "justification": (
                    "Validated historical Lots 0-25 code is preserved to avoid an opportunistic "
                    "pre-Lot26 refactor; the finding remains visible and fail-closed controls are strengthened."
                ),
                "strengthened_controls": controls,
                "remediation_trigger": (
                    "Decompose before modifying the affected symbol, or before opening Lot 27, "
                    "whichever occurs first."
                ),
                "review_by": "2026-09-30",
                "status": "ACCEPTED_TEMPORARY",
            }
        )
    payload = {
        "schema_version": "legacy-engineering-deviations-v1",
        "project": "Crypto Quant Bot V3.1-Ops",
        "scope": "P0.6 pre-Lot26 inventory of validated historical runtime code",
        "policy": (
            "No listed deviation authorizes weaker safety, traceability, coverage, mutation, "
            "or no-trading controls. New or changed findings are blocked by CI."
        ),
        "deviations": deviations,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--bootstrap", action="store_true")
    args = parser.parse_args()
    if args.bootstrap:
        bootstrap_registry(args.registry)
    result = evaluate(args.registry)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
