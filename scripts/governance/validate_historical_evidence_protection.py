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


def _changed(base: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise EvidenceProtectionError(f"git diff failed: {result.stderr.strip()}")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def validate(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise EvidenceProtectionError("unsupported schema version")
    if policy.get("policy_kind") != "historical_evidence_protection":
        raise EvidenceProtectionError("invalid policy kind")

    anchors = policy.get("anchors")
    if not isinstance(anchors, list) or len(anchors) < 2:
        raise EvidenceProtectionError("Lot44 and Lot45 anchors are required")
    for anchor in anchors:
        if not isinstance(anchor, dict):
            raise EvidenceProtectionError("anchor must be an object")
        for key, value in anchor.items():
            if key.endswith(("head", "merge", "anchor")) and key not in {"type"}:
                if isinstance(value, str) and SHA40.fullmatch(value) is None:
                    raise EvidenceProtectionError(f"{anchor.get('id')}.{key} is not SHA-40")

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
