#!/usr/bin/env python3
"""Deterministically classify Git diff paths with conservative multi-label semantics."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "diff_classifier_policy_v1.json"


class DiffClassifierError(ValueError):
    pass


def _load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DiffClassifierError(f"cannot load classifier policy: {exc}") from exc
    if not isinstance(value, dict):
        raise DiffClassifierError("classifier policy must be an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise DiffClassifierError("unsupported classifier policy schema_version")
    if policy.get("policy_kind") != "diff_classifier_policy_v1":
        raise DiffClassifierError("invalid classifier policy kind")
    if policy.get("classifier_semantics") != "MULTI_LABEL_CONSERVATIVE":
        raise DiffClassifierError("classifier must remain multi-label and conservative")

    labels = policy.get("labels")
    if not isinstance(labels, list) or not labels or len(labels) != len(set(labels)):
        raise DiffClassifierError("labels must be a non-empty unique list")
    label_set = set(labels)
    if "UNKNOWN_REQUIRES_REVIEW" not in label_set:
        raise DiffClassifierError("unknown fallback label is mandatory")
    if "RISK_EXECUTION_CRITICAL" not in label_set:
        raise DiffClassifierError("critical risk/execution label is mandatory")

    critical = policy.get("critical_labels")
    if not isinstance(critical, list) or any(item not in label_set for item in critical):
        raise DiffClassifierError("critical_labels reference unknown labels")

    rules = policy.get("rules")
    if not isinstance(rules, list) or not rules:
        raise DiffClassifierError("classification rules are required")
    codes: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"code", "label", "patterns"}:
            raise DiffClassifierError("invalid classifier rule shape")
        code = rule["code"]
        label = rule["label"]
        patterns = rule["patterns"]
        if not isinstance(code, str) or not code or code in codes:
            raise DiffClassifierError("classifier rule codes must be unique non-empty strings")
        codes.add(code)
        if label not in label_set:
            raise DiffClassifierError(f"rule {code} references unknown label {label}")
        if not isinstance(patterns, list) or not patterns:
            raise DiffClassifierError(f"rule {code} patterns must be non-empty")
        if any(not isinstance(pattern, str) or not pattern for pattern in patterns):
            raise DiffClassifierError(f"rule {code} has invalid pattern")

    aggregate = policy.get("aggregate_rules")
    if not isinstance(aggregate, dict):
        raise DiffClassifierError("aggregate_rules are required")
    docs = aggregate.get("docs_only")
    if not isinstance(docs, dict):
        raise DiffClassifierError("docs_only aggregate rule is required")
    if aggregate.get("unknown_fallback") != "UNKNOWN_REQUIRES_REVIEW":
        raise DiffClassifierError("unknown fallback must remain conservative")


def _matches(path: str, patterns: list[str]) -> bool:
    return any(path == pattern or fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def classify_path(path: str, policy: dict[str, Any]) -> list[str]:
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
        raise DiffClassifierError(f"invalid repository-relative path: {path!r}")
    labels: set[str] = set()
    for rule in policy["rules"]:
        if _matches(path, rule["patterns"]):
            labels.add(rule["label"])
    if not labels:
        labels.add(policy["aggregate_rules"]["unknown_fallback"])
    return sorted(labels)


def classify_paths(paths: list[str], policy: dict[str, Any]) -> dict[str, Any]:
    if not paths:
        raise DiffClassifierError("at least one changed path is required")
    normalized = sorted(set(paths))
    files = [
        {"path": path, "labels": classify_path(path, policy)}
        for path in normalized
    ]
    all_labels = sorted({label for item in files for label in item["labels"]})

    docs_rule = policy["aggregate_rules"]["docs_only"]
    allowed_docs = set(docs_rule["allowed_file_labels"])
    docs_only = all(
        set(item["labels"]) <= allowed_docs and "DOCUMENTATION" in item["labels"]
        for item in files
    )
    aggregate_labels = list(all_labels)
    if docs_only:
        aggregate_labels.append(docs_rule["output_label"])
    aggregate_labels = sorted(set(aggregate_labels))

    critical = sorted(set(aggregate_labels) & set(policy["critical_labels"]))
    return {
        "classifier_version": 1,
        "files": files,
        "labels": aggregate_labels,
        "critical_labels": critical,
        "docs_only": docs_only,
        "requires_review": bool(critical),
    }


def changed_paths(base: str, head: str = "HEAD") -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DiffClassifierError(f"git diff failed: {result.stderr.strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _self_check(policy: dict[str, Any]) -> None:
    assert classify_paths(["docs/example.md"], policy)["docs_only"] is True
    critical = classify_paths(["src/crypto_quant_bot/risk/example.py"], policy)
    assert "RISK_EXECUTION_CRITICAL" in critical["labels"]
    unknown = classify_paths(["unmapped/new.extension"], policy)
    assert unknown["labels"] == ["UNKNOWN_REQUIRES_REVIEW"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Explicit repository-relative changed paths.")
    parser.add_argument("--base", help="Git base ref/SHA for --name-only classification.")
    parser.add_argument("--head", default="HEAD", help="Git head ref when --base is used.")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    try:
        policy = _load_policy()
        validate_policy(policy)
        if args.self_check:
            _self_check(policy)
            print("DIFF_CLASSIFIER_SELF_CHECK_PASS")
            return 0
        paths = args.paths
        if args.base:
            if paths:
                raise DiffClassifierError("explicit paths and --base are mutually exclusive")
            paths = changed_paths(args.base, args.head)
        result = classify_paths(paths, policy)
    except DiffClassifierError as exc:
        print(f"DIFF_CLASSIFIER_INVALID: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
