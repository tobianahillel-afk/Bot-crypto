#!/usr/bin/env python3
"""Protect exact historical evidence while allowing declared status views to evolve."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "engineering" / "HISTORICAL_EVIDENCE_PROTECTION.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class EvidenceProtectionError(ValueError):
    pass


def _load() -> dict[str, Any]:
    try:
        value = json.loads(POLICY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceProtectionError(f"cannot load policy: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceProtectionError("policy must be an object")
    return value


APPROVED_PROTECTED_PATH_MIGRATION = {
    "approval_id": "REPOSITORY_OWNER_REMEDIATION_72",
    "issue_url": "https://github.com/tobianahillel-afk/Bot-crypto/issues/72",
    "path": ".github/workflows/lot44-frozen-evidence.yml",
    "source_commit": "2506278e3368c7cfadf34eb1e24490fb143d9e1c",
    "source_parent": "9eb63ae1b948842523eeaa723f802e0b919cb475",
    "from_blob": "03996c563bbdff7639ea669b383d709c4876f269",
    "to_blob": "c23a59b1d5223dccf412d5af87d8c52ea3327b68",
}


def _git(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _changed(base: str, *, cwd: Path = ROOT) -> set[str]:
    result = _git("diff", "--name-only", f"{base}...HEAD", cwd=cwd)
    if result.returncode != 0:
        raise EvidenceProtectionError(f"git diff failed: {result.stderr.strip()}")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _require_commit(sha: str, label: str, *, cwd: Path = ROOT) -> None:
    if SHA40.fullmatch(sha) is None:
        raise EvidenceProtectionError(f"{label} is not SHA-40")
    result = _git("cat-file", "-e", f"{sha}^{{commit}}", cwd=cwd)
    if result.returncode != 0:
        raise EvidenceProtectionError(f"{label} does not resolve to a Git commit: {sha}")


def _is_ancestor(older: str, newer: str, *, cwd: Path = ROOT) -> bool:
    return _git("merge-base", "--is-ancestor", older, newer, cwd=cwd).returncode == 0


def _blob(commit: str, path: str, *, cwd: Path = ROOT) -> str:
    result = _git("rev-parse", f"{commit}:{path}", cwd=cwd)
    if result.returncode != 0:
        raise EvidenceProtectionError(f"cannot resolve {path} at {commit}")
    return result.stdout.strip()


def _approved_migration_paths(
    policy: dict[str, Any],
    protected: set[str],
    *,
    cwd: Path = ROOT,
    expected_migration: dict[str, str] = APPROVED_PROTECTED_PATH_MIGRATION,
) -> set[str]:
    entries = policy.get("approved_protected_path_migrations", [])
    if not isinstance(entries, list):
        raise EvidenceProtectionError("approved protected-path migrations must be a list")
    if not entries:
        return set()
    if entries != [expected_migration]:
        raise EvidenceProtectionError("unrecognized or altered protected-path migration approval")

    migration = entries[0]
    path = migration["path"]
    if path not in protected:
        raise EvidenceProtectionError("approved migration path is not protected")
    for key in ("source_commit", "source_parent", "from_blob", "to_blob"):
        value = migration[key]
        if not isinstance(value, str) or SHA40.fullmatch(value) is None:
            raise EvidenceProtectionError(f"migration {key} is not SHA-40")

    comparison_base = policy.get("comparison_base")
    if not isinstance(comparison_base, str) or not comparison_base:
        raise EvidenceProtectionError("comparison_base is required")
    _require_commit(migration["source_commit"], "migration.source_commit", cwd=cwd)
    _require_commit(migration["source_parent"], "migration.source_parent", cwd=cwd)

    parent_line = _git(
        "rev-list", "--parents", "-n", "1", migration["source_commit"], cwd=cwd
    )
    if parent_line.returncode != 0:
        raise EvidenceProtectionError("cannot read migration commit parents")
    parent_fields = parent_line.stdout.split()
    if parent_fields != [migration["source_commit"], migration["source_parent"]]:
        raise EvidenceProtectionError("approved migration commit parent changed")

    changed = _git(
        "diff",
        "--name-only",
        migration["source_parent"],
        migration["source_commit"],
        cwd=cwd,
    )
    if changed.returncode != 0:
        raise EvidenceProtectionError("cannot inspect approved migration commit")
    if {line.strip() for line in changed.stdout.splitlines() if line.strip()} != {path}:
        raise EvidenceProtectionError("approved migration must change exactly its declared path")

    if _blob(comparison_base, path, cwd=cwd) != migration["from_blob"]:
        raise EvidenceProtectionError("approved migration no longer matches comparison-base blob")
    if _blob(migration["source_parent"], path, cwd=cwd) != migration["from_blob"]:
        raise EvidenceProtectionError("approved migration source blob changed")
    if _blob(migration["source_commit"], path, cwd=cwd) != migration["to_blob"]:
        raise EvidenceProtectionError("approved migration target blob changed")
    if not _is_ancestor(migration["source_commit"], "HEAD", cwd=cwd):
        raise EvidenceProtectionError("approved migration commit is not an ancestor of HEAD")
    if _blob("HEAD", path, cwd=cwd) != migration["to_blob"]:
        raise EvidenceProtectionError("current protected path differs from approved target blob")
    return {path}


def _validate_protected_drift(
    policy: dict[str, Any],
    protected: set[str],
    *,
    cwd: Path = ROOT,
    expected_migration: dict[str, str] = APPROVED_PROTECTED_PATH_MIGRATION,
) -> set[str]:
    base = policy.get("comparison_base")
    if not isinstance(base, str) or not base:
        raise EvidenceProtectionError("comparison_base is required")
    approved = _approved_migration_paths(
        policy, protected, cwd=cwd, expected_migration=expected_migration
    )
    drift = _changed(base, cwd=cwd) & protected
    unexpected = sorted(drift - approved)
    if unexpected:
        raise EvidenceProtectionError(f"protected historical evidence drift: {unexpected}")
    return drift


def validate(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise EvidenceProtectionError("unsupported schema version")
    if policy.get("policy_kind") != "historical_evidence_protection":
        raise EvidenceProtectionError("invalid policy kind")

    anchors = policy.get("anchors")
    if not isinstance(anchors, list) or len(anchors) != 2:
        raise EvidenceProtectionError("exactly Lot44 and Lot45 anchors are required")

    by_id: dict[str, dict[str, Any]] = {}
    for anchor in anchors:
        if not isinstance(anchor, dict):
            raise EvidenceProtectionError("anchor must be an object")
        anchor_id = anchor.get("id")
        if not isinstance(anchor_id, str) or not anchor_id:
            raise EvidenceProtectionError("anchor id is required")
        if anchor_id in by_id:
            raise EvidenceProtectionError(f"duplicate anchor id: {anchor_id}")
        by_id[anchor_id] = anchor
        for key, value in anchor.items():
            if key.endswith(("head", "merge", "anchor")):
                if not isinstance(value, str):
                    raise EvidenceProtectionError(f"{anchor_id}.{key} must be a SHA")
                _require_commit(value, f"{anchor_id}.{key}")

    lot44 = by_id.get("LOT44_POST_MERGE_CERTIFICATION")
    lot45 = by_id.get("LOT45_ENTRY_GATE")
    if lot44 is None or lot45 is None:
        raise EvidenceProtectionError("Lot44 and Lot45 anchor ids are mandatory")
    if lot44.get("verdict") != "GO_LOT44_POST_MERGE":
        raise EvidenceProtectionError("Lot44 verdict drift")
    if lot45.get("verdict") != "GO_LOT45_IMPLEMENTATION_ENTRY":
        raise EvidenceProtectionError("Lot45 entry verdict drift")
    if lot45.get("prerequisite_merge") != lot44.get("post_merge_audit_merge"):
        raise EvidenceProtectionError("Lot45 prerequisite does not bind Lot44 post-merge audit")
    if not _is_ancestor(
        str(lot44["post_merge_audit_merge"]),
        str(lot45["gate_merge"]),
    ):
        raise EvidenceProtectionError("Lot45 gate merge does not descend from Lot44 post-merge audit")

    protected = policy.get("protected_current_tree_paths")
    mutable = policy.get("intentionally_mutable_views")
    if not isinstance(protected, list) or not protected:
        raise EvidenceProtectionError("protected paths are required")
    if len(protected) != len(set(protected)):
        raise EvidenceProtectionError("protected paths contain duplicates")
    if not isinstance(mutable, list):
        raise EvidenceProtectionError("mutable views must be a list")
    overlap = set(protected) & set(mutable)
    if overlap:
        raise EvidenceProtectionError(f"protected/mutable overlap: {sorted(overlap)}")

    _validate_protected_drift(policy, set(protected))

    for required in (
        "data/audit/lot45_v4_entry_gate.json",
        "scripts/validate_lot44_post_merge.py",
        "data/audit/trades_and_aggressor_classification_schema_lot44.json",
    ):
        if required not in protected:
            raise EvidenceProtectionError(f"missing required protected path: {required}")


def main() -> int:
    try:
        validate(_load())
    except EvidenceProtectionError as exc:
        print(f"HISTORICAL_EVIDENCE_PROTECTION_INVALID: {exc}", file=sys.stderr)
        return 1
    print("HISTORICAL_EVIDENCE_PROTECTION_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
