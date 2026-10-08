#!/usr/bin/env python3
"""Map classifier output to conservative validation-impact families without executing checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "diff_impact_policy_v1.json"


class DiffImpactError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DiffImpactError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DiffImpactError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise DiffImpactError("unsupported impact policy schema_version")
    if policy.get("policy_kind") != "diff_impact_policy_v1":
        raise DiffImpactError("invalid impact policy kind")
    if policy.get("semantics") != "LABEL_TO_IMPACT_UNION_NO_EXECUTION":
        raise DiffImpactError("impact mapping must remain union-only and execution-free")

    families = policy.get("impact_families")
    domains = policy.get("domains")
    mappings = policy.get("mappings")
    order = policy.get("sensitivity_order")
    if not isinstance(families, list) or len(families) != len(set(families)):
        raise DiffImpactError("impact_families must be unique")
    if not isinstance(domains, list) or len(domains) != len(set(domains)):
        raise DiffImpactError("domains must be unique")
    if order != ["LOW", "NORMAL", "ELEVATED", "CRITICAL"]:
        raise DiffImpactError("sensitivity order drift")
    if not isinstance(mappings, dict) or not mappings:
        raise DiffImpactError("mappings are required")

    family_set = set(families)
    domain_set = set(domains)
    for label, mapping in mappings.items():
        if not isinstance(label, str) or not label:
            raise DiffImpactError("mapping labels must be non-empty strings")
        if not isinstance(mapping, dict) or set(mapping) != {
            "impact_families", "domains", "sensitivity"
        }:
            raise DiffImpactError(f"mapping {label} has invalid shape")
        mapped_families = mapping["impact_families"]
        mapped_domains = mapping["domains"]
        if not isinstance(mapped_families, list) or not mapped_families:
            raise DiffImpactError(f"mapping {label} needs impact families")
        if any(item not in family_set for item in mapped_families):
            raise DiffImpactError(f"mapping {label} references unknown impact family")
        if not isinstance(mapped_domains, list) or not mapped_domains:
            raise DiffImpactError(f"mapping {label} needs domains")
        if any(item not in domain_set for item in mapped_domains):
            raise DiffImpactError(f"mapping {label} references unknown domain")
        if mapping["sensitivity"] not in order:
            raise DiffImpactError(f"mapping {label} has invalid sensitivity")

    unknown = mappings.get("UNKNOWN_REQUIRES_REVIEW", {})
    if not {
        "CONSERVATIVE_BROAD_IMPACT", "HUMAN_REVIEW_REQUIRED"
    } <= set(unknown.get("impact_families", [])):
        raise DiffImpactError("unknown mapping is not conservative")
    critical = mappings.get("RISK_EXECUTION_CRITICAL", {})
    if not {"RISK_INVARIANTS", "EXECUTION_SAFETY"} <= set(
        critical.get("impact_families", [])
    ):
        raise DiffImpactError("risk/execution mapping lacks critical invariants")


def validate_classification(classification: dict[str, Any], policy: dict[str, Any]) -> None:
    if classification.get("classifier_version") != 1:
        raise DiffImpactError("unsupported classifier output version")
    labels = classification.get("labels")
    files = classification.get("files")
    if not isinstance(labels, list) or not labels:
        raise DiffImpactError("classifier labels are missing")
    if not isinstance(files, list) or not files:
        raise DiffImpactError("classifier files are missing")
    unknown_labels = sorted(set(labels) - set(policy["mappings"]))
    if unknown_labels:
        raise DiffImpactError(f"unmapped classifier labels: {unknown_labels}")
    if "DOC_ONLY" in labels and classification.get("docs_only") is not True:
        raise DiffImpactError("DOC_ONLY label requires docs_only=true")
    if classification.get("docs_only") is True and "DOC_ONLY" not in labels:
        raise DiffImpactError("docs_only=true requires DOC_ONLY aggregate label")


def map_impact(classification: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    validate_classification(classification, policy)
    order = policy["sensitivity_order"]
    families: set[str] = set()
    domains: set[str] = set()
    sensitivity = "LOW"
    label_impacts: list[dict[str, Any]] = []

    for label in sorted(set(classification["labels"])):
        mapping = policy["mappings"][label]
        families.update(mapping["impact_families"])
        domains.update(mapping["domains"])
        if order.index(mapping["sensitivity"]) > order.index(sensitivity):
            sensitivity = mapping["sensitivity"]
        label_impacts.append({
            "label": label,
            "impact_families": sorted(mapping["impact_families"]),
            "domains": sorted(mapping["domains"]),
            "sensitivity": mapping["sensitivity"],
        })

    docs_only = classification.get("docs_only") is True
    if docs_only:
        if domains != {"DOCUMENTATION"}:
            raise DiffImpactError("documentation-only classification leaked non-doc domain")
        if set(families) != {"DOC_CONSISTENCY"}:
            raise DiffImpactError("documentation-only classification leaked non-doc impact")

    return {
        "impact_version": 1,
        "source_classifier_version": classification["classifier_version"],
        "source_labels": sorted(set(classification["labels"])),
        "label_impacts": label_impacts,
        "impact_families": sorted(families),
        "domains": sorted(domains),
        "sensitivity": sensitivity,
        "docs_only_candidate": docs_only,
        "requires_human_review": "HUMAN_REVIEW_REQUIRED" in families,
        "execution_commands": [],
        "validation_tiers": [],
    }


def _self_check(policy: dict[str, Any]) -> None:
    docs = {
        "classifier_version": 1,
        "files": [{"path": "docs/x.md", "labels": ["DOCUMENTATION"]}],
        "labels": ["DOCUMENTATION", "DOC_ONLY"],
        "critical_labels": [],
        "docs_only": True,
        "requires_review": False,
    }
    mapped = map_impact(docs, policy)
    assert mapped["impact_families"] == ["DOC_CONSISTENCY"]
    unknown = copy_classification("UNKNOWN_REQUIRES_REVIEW")
    assert "CONSERVATIVE_BROAD_IMPACT" in map_impact(unknown, policy)["impact_families"]


def copy_classification(label: str) -> dict[str, Any]:
    return {
        "classifier_version": 1,
        "files": [{"path": "example", "labels": [label]}],
        "labels": [label],
        "critical_labels": [label] if label in {
            "SECURITY", "RISK_EXECUTION_CRITICAL", "UNKNOWN_REQUIRES_REVIEW"
        } else [],
        "docs_only": False,
        "requires_review": label in {
            "SECURITY", "RISK_EXECUTION_CRITICAL", "UNKNOWN_REQUIRES_REVIEW"
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Classifier JSON output file.")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    try:
        policy = _load(POLICY_PATH)
        validate_policy(policy)
        if args.self_check:
            _self_check(policy)
            print("DIFF_IMPACT_SELF_CHECK_PASS")
            return 0
        if args.input is None:
            raise DiffImpactError("--input is required unless --self-check is used")
        classification = _load(args.input)
        result = map_impact(classification, policy)
    except DiffImpactError as exc:
        print(f"DIFF_IMPACT_INVALID: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
