#!/usr/bin/env python3
"""Gate zizmor findings only when they touch added/modified HEAD lines."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


class ZizmorChangedFindingError(ValueError):
    pass


def parse_changed_head_lines(diff_text: str) -> dict[str, set[int]]:
    changed: dict[str, set[int]] = {}
    current: str | None = None
    new_line: int | None = None
    for raw in diff_text.splitlines():
        if raw.startswith("+++ "):
            marker = raw[4:].strip()
            if marker == "/dev/null":
                current = None
            else:
                current = marker[2:] if marker.startswith("b/") else marker
                changed.setdefault(current, set())
            new_line = None
            continue
        match = HUNK_RE.match(raw)
        if match is not None:
            new_line = int(match.group(1))
            continue
        if current is None or new_line is None:
            continue
        if raw.startswith("\\"):
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            changed[current].add(new_line)
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            continue
        else:
            new_line += 1
    return changed


def _safe_target(path: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ZizmorChangedFindingError(f"unsafe target path: {path!r}")
    normalized = candidate.as_posix()
    if not (
        normalized.startswith(".github/workflows/")
        or normalized.startswith(".github/actions/")
    ):
        raise ZizmorChangedFindingError(f"target outside workflow security roots: {path}")
    return normalized


def load_targets(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ZizmorChangedFindingError(f"cannot read targets file: {exc}") from exc
    targets = [_safe_target(line.strip()) for line in lines if line.strip()]
    if len(targets) != len(set(targets)):
        raise ZizmorChangedFindingError("duplicate workflow security target")
    return targets


def changed_head_lines(base: str, head: str, targets: list[str]) -> dict[str, set[int]]:
    if not head:
        raise ZizmorChangedFindingError("head is required")
    if not targets:
        return {}
    if not base:
        result: dict[str, set[int]] = {}
        for target in targets:
            full = ROOT / target
            if not full.is_file():
                raise ZizmorChangedFindingError(f"target missing at HEAD: {target}")
            count = len(full.read_text(encoding="utf-8").splitlines())
            result[target] = set(range(1, count + 1))
        return result
    proc = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", "--no-ext-diff",
         "--diff-filter=ACMR", base, head, "--", *targets],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise ZizmorChangedFindingError(f"git diff failed: {proc.stderr.strip()}")
    parsed = parse_changed_head_lines(proc.stdout)
    return {target: parsed.get(target, set()) for target in targets}


def _finding_location(item: dict[str, Any]) -> tuple[str, int]:
    locations = item.get("locations")
    if not isinstance(locations, list) or not locations:
        raise ZizmorChangedFindingError("zizmor finding lacks concrete location")
    location = locations[0]
    if not isinstance(location, dict):
        raise ZizmorChangedFindingError("zizmor finding location is malformed")
    symbolic = location.get("symbolic")
    concrete = location.get("concrete")
    if not isinstance(symbolic, dict) or not isinstance(concrete, dict):
        raise ZizmorChangedFindingError("zizmor finding location metadata is incomplete")
    key = symbolic.get("key")
    if not isinstance(key, dict):
        raise ZizmorChangedFindingError("zizmor finding symbolic key is missing")
    local = key.get("Local")
    if not isinstance(local, dict) or not isinstance(local.get("verbatim_path"), str):
        raise ZizmorChangedFindingError("zizmor finding is not repository-local")
    point = concrete.get("location", {}).get("start_point")
    if not isinstance(point, dict):
        raise ZizmorChangedFindingError("zizmor finding start point is missing")
    row = point.get("row")
    if not isinstance(row, int) or isinstance(row, bool) or row < 0:
        raise ZizmorChangedFindingError("zizmor finding row is invalid")
    return _safe_target(local["verbatim_path"]), row + 1


def evaluate_findings(
    findings: list[dict[str, Any]],
    changed: dict[str, set[int]],
    targets: list[str],
    zizmor_status: int,
) -> dict[str, Any]:
    if not isinstance(zizmor_status, int) or zizmor_status < 0:
        raise ZizmorChangedFindingError("invalid zizmor status")
    if zizmor_status != 0 and not findings:
        raise ZizmorChangedFindingError(
            "zizmor failed without machine-readable findings"
        )
    target_set = set(targets)
    legacy: list[dict[str, Any]] = []
    blocking: list[dict[str, Any]] = []
    for item in findings:
        if not isinstance(item, dict):
            raise ZizmorChangedFindingError("zizmor finding is not an object")
        try:
            path, line = _finding_location(item)
            if path not in target_set:
                raise ZizmorChangedFindingError(
                    f"zizmor finding references untargeted path: {path}"
                )
            decision = (
                "BLOCK_CHANGED_HEAD_LINE"
                if line in changed.get(path, set())
                else "LEGACY_UNCHANGED_LINE"
            )
        except ZizmorChangedFindingError:
            path = None
            line = None
            decision = "BLOCK_UNLOCATED"
        determinations = item.get("determinations")
        if not isinstance(determinations, dict):
            determinations = {}
        safe = {
            "ident": item.get("ident"),
            "severity": determinations.get("severity"),
            "confidence": determinations.get("confidence"),
            "file": path,
            "line_one_based": line,
            "decision": decision,
        }
        if decision.startswith("BLOCK_"):
            blocking.append(safe)
        else:
            legacy.append(safe)
    return {
        "total_findings": len(findings),
        "legacy_findings": legacy,
        "blocking_findings": blocking,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--base", default="")
    parser.add_argument("--head", required=True)
    parser.add_argument("--targets-file", type=Path, required=True)
    parser.add_argument("--zizmor-status", type=int, required=True)
    args = parser.parse_args()
    try:
        targets = load_targets(args.targets_file)
        try:
            findings = json.loads(args.report.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ZizmorChangedFindingError(f"cannot load zizmor report: {exc}") from exc
        if not isinstance(findings, list):
            raise ZizmorChangedFindingError("zizmor report must be a JSON list")
        changed = changed_head_lines(args.base, args.head, targets)
        result = evaluate_findings(findings, changed, targets, args.zizmor_status)
        print(f"ZIZMOR_FINDINGS={result['total_findings']}")
        print(f"ZIZMOR_LEGACY_FINDINGS={len(result['legacy_findings'])}")
        print(f"ZIZMOR_BLOCKING_FINDINGS={len(result['blocking_findings'])}")
        for item in result["legacy_findings"] + result["blocking_findings"]:
            print(json.dumps(item, sort_keys=True))
        if result["blocking_findings"]:
            print("ZIZMOR_CHANGED_FINDING_GATE_FAIL", file=sys.stderr)
            return 1
        print("ZIZMOR_CHANGED_FINDING_GATE_PASS")
        return 0
    except (ZizmorChangedFindingError, OSError, KeyError) as exc:
        print(f"ZIZMOR_CHANGED_FINDING_GATE_INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
