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


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _changed(base: str) -> set[str]:
    result = _git("diff", "--name-only", f"{base}...HEAD")
    if result.returncode != 0:
        raise EvidenceProtectionError(f"git diff failed: {result.stderr.strip()}")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _require_commit(sha: str, label: str) -> None:
    if SHA40.fullmatch(sha) is None:
        raise EvidenceProtectionError(f"{label} is not SHA-40")
    result = _git("cat-file", "-e", f"{sha}^{{commit}}")
    if result.returncode != 0:
        raise EvidenceProtectionError(f"{label} does not resolve to a Git commit: {sha}")


def _is_ancestor(older: str, newer: str) -> bool:
    return _git("merge-base", "--is-ancestor", older, newer).returncode == 0


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

    base = policy.get("comparison_base")
    if not isinstance(base, str) or not base:
        raise EvidenceProtectionError("comparison_base is required")
    drift = sorted(_changed(base) & set(protected))
    if drift:
        raise EvidenceProtectionError(f"protected historical evidence drift: {drift}")

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
