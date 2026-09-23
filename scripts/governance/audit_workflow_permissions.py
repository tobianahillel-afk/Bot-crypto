#!/usr/bin/env python3
"""Inventory workflow token permissions and gate only changed workflows."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "workflow_permission_policy_v1.json"
KEY_RE = re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$")
SCOPE_RE = re.compile(r"^[a-z][a-z0-9-]*$")


class WorkflowPermissionError(ValueError):
    pass


@dataclass(frozen=True)
class PermissionBlock:
    level: str
    job: str | None
    style: str
    scalar: str | None
    scopes: dict[str, str]
    line: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "job": self.job,
            "style": self.style,
            "scalar": self.scalar,
            "scopes": dict(sorted(self.scopes.items())),
            "line": self.line,
        }


@dataclass(frozen=True)
class WorkflowPermissionRecord:
    file: str
    top: PermissionBlock | None
    jobs: tuple[PermissionBlock, ...]
    parse_findings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "top": self.top.as_dict() if self.top else None,
            "jobs": [item.as_dict() for item in self.jobs],
            "parse_findings": list(self.parse_findings),
        }


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowPermissionError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowPermissionError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise WorkflowPermissionError("unsupported permission policy schema_version")
    if policy.get("policy_kind") != "workflow_permission_policy_v1":
        raise WorkflowPermissionError("invalid permission policy kind")
    if policy.get("semantics") != "INVENTORY_LEGACY_DEBT_BLOCK_CHANGED_PERMISSION_EXPANSION":
        raise WorkflowPermissionError("permission policy semantics drift")
    if policy.get("scan_root") != ".github/workflows":
        raise WorkflowPermissionError("workflow permission scan root drift")
    if policy.get("workflow_extensions") != [".yml", ".yaml"]:
        raise WorkflowPermissionError("workflow extensions drift")

    reads = policy.get("allowed_read_scopes")
    if not isinstance(reads, list) or not reads or len(reads) != len(set(reads)):
        raise WorkflowPermissionError("allowed read scopes must be a unique non-empty list")
    if any(not isinstance(scope, str) or SCOPE_RE.fullmatch(scope) is None for scope in reads):
        raise WorkflowPermissionError("invalid allowed read scope")

    changed = policy.get("changed_mode")
    required = {
        "require_top_level_permissions": True,
        "allow_empty_permissions": True,
        "allow_read_all": False,
        "allow_write_all": False,
        "allow_dynamic_permissions": False,
        "require_job_scope_subset_of_top_level": True,
        "deleted_files_ignored": True,
    }
    if changed != required:
        raise WorkflowPermissionError("changed-mode permission policy drift")

    approvals = policy.get("approved_write_scopes")
    if not isinstance(approvals, list):
        raise WorkflowPermissionError("approved_write_scopes must be a list")
    seen: set[tuple[str, str]] = set()
    for item in approvals:
        if not isinstance(item, dict) or set(item) != {"workflow", "scope", "rationale"}:
            raise WorkflowPermissionError("invalid write-scope approval shape")
        workflow = item["workflow"]
        scope = item["scope"]
        rationale = item["rationale"]
        if not isinstance(workflow, str) or not workflow.startswith(".github/workflows/"):
            raise WorkflowPermissionError("invalid approved write workflow path")
        if not isinstance(scope, str) or SCOPE_RE.fullmatch(scope) is None:
            raise WorkflowPermissionError("invalid approved write scope")
        if not isinstance(rationale, str) or len(rationale.strip()) < 20:
            raise WorkflowPermissionError("write approval requires substantive rationale")
        key = (workflow, scope)
        if key in seen:
            raise WorkflowPermissionError("duplicate write-scope approval")
        seen.add(key)

    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise WorkflowPermissionError("mandatory permission gate must remain offline and zero-cost")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _clean_value(value: str) -> str:
    value = value.strip()
    if " # " in value:
        value = value.split(" # ", 1)[0].rstrip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value


def _mapping_block(
    lines: list[str],
    start_index: int,
    parent_indent: int,
) -> tuple[dict[str, str], int, list[str]]:
    scopes: dict[str, str] = {}
    findings: list[str] = []
    index = start_index + 1
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        indent = _indent(raw)
        if indent <= parent_indent:
            break
        match = KEY_RE.match(stripped)
        if match is None:
            findings.append(f"UNPARSEABLE_PERMISSION_LINE:{index + 1}")
            index += 1
            continue
        scope = match.group(1)
        value = _clean_value(match.group(2))
        if scope in scopes:
            findings.append(f"DUPLICATE_PERMISSION_SCOPE:{scope}:{index + 1}")
        scopes[scope] = value
        index += 1
    return scopes, index, findings


def _parse_permissions_decl(
    lines: list[str],
    index: int,
    level: str,
    job: str | None,
) -> tuple[PermissionBlock, int, list[str]]:
    raw = lines[index]
    stripped = raw.strip()
    match = KEY_RE.match(stripped)
    if match is None or match.group(1) != "permissions":
        raise WorkflowPermissionError("internal permission parser misuse")
    value = _clean_value(match.group(2))
    line_no = index + 1
    if value:
        if value in {"{}", "{ }"}:
            return PermissionBlock(level, job, "EMPTY", None, {}, line_no), index + 1, []
        if "${{" in value:
            return PermissionBlock(level, job, "DYNAMIC", value, {}, line_no), index + 1, []
        return PermissionBlock(level, job, "SCALAR", value, {}, line_no), index + 1, []
    scopes, next_index, findings = _mapping_block(lines, index, _indent(raw))
    return PermissionBlock(level, job, "MAPPING", None, scopes, line_no), next_index, findings


def parse_workflow(path: Path, root: Path = ROOT) -> WorkflowPermissionRecord:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise WorkflowPermissionError(f"workflow path outside repository: {path}") from exc
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise WorkflowPermissionError(f"cannot read {relative}: {exc}") from exc

    top: PermissionBlock | None = None
    jobs: list[PermissionBlock] = []
    findings: list[str] = []
    in_jobs = False
    current_job: str | None = None
    index = 0

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        indent = _indent(raw)
        match = KEY_RE.match(stripped)
        if match is None:
            index += 1
            continue
        key = match.group(1)

        if indent == 0 and key == "jobs":
            in_jobs = True
            current_job = None
            index += 1
            continue
        if indent == 0 and key != "jobs":
            in_jobs = False
            current_job = None

        if indent == 0 and key == "permissions":
            if top is not None:
                findings.append(f"DUPLICATE_TOP_PERMISSIONS:{index + 1}")
            block, index, local = _parse_permissions_decl(lines, index, "workflow", None)
            top = block
            findings.extend(local)
            continue

        if in_jobs:
            if indent == 2 and key != "permissions":
                current_job = key
                index += 1
                continue
            if current_job is not None and indent == 4 and key == "permissions":
                block, index, local = _parse_permissions_decl(lines, index, "job", current_job)
                jobs.append(block)
                findings.extend(local)
                continue
        index += 1

    return WorkflowPermissionRecord(
        file=relative,
        top=top,
        jobs=tuple(jobs),
        parse_findings=tuple(findings),
    )


def discover_files(policy: dict[str, Any], root: Path = ROOT) -> list[Path]:
    base = root / policy["scan_root"]
    if not base.is_dir():
        raise WorkflowPermissionError(f"workflow root missing: {base}")
    extensions = set(policy["workflow_extensions"])
    return sorted(
        (path for path in base.rglob("*") if path.is_file() and path.suffix.lower() in extensions),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def _git_changed_files(base: str, head: str, policy: dict[str, Any]) -> list[Path]:
    if not base or not head:
        raise WorkflowPermissionError("changed mode requires --base and --head")
    if re.fullmatch(r"0{40}", base):
        proc = subprocess.run(
            ["git", "rev-parse", f"{head}^"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise WorkflowPermissionError("cannot derive parent for zero before-SHA")
        base = proc.stdout.strip()

    proc = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", base, head, "--", policy["scan_root"]],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise WorkflowPermissionError(f"git diff failed: {proc.stderr.strip()}")

    extensions = set(policy["workflow_extensions"])
    result: list[Path] = []
    for raw in proc.stdout.splitlines():
        if not raw.strip():
            continue
        rel = Path(raw.strip())
        if rel.is_absolute() or ".." in rel.parts:
            raise WorkflowPermissionError(f"unsafe changed path: {raw!r}")
        full = ROOT / rel
        if full.is_file() and full.suffix.lower() in extensions:
            result.append(full)
    return sorted(set(result), key=lambda path: path.relative_to(ROOT).as_posix())


def _approval_index(policy: dict[str, Any]) -> set[tuple[str, str]]:
    return {(item["workflow"], item["scope"]) for item in policy["approved_write_scopes"]}


def _block_violations(
    record: WorkflowPermissionRecord,
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    reads = set(policy["allowed_read_scopes"])
    approvals = _approval_index(policy)

    for finding in record.parse_findings:
        violations.append({"file": record.file, "reason": finding})

    top = record.top
    if top is None:
        violations.append({"file": record.file, "reason": "MISSING_TOP_LEVEL_PERMISSIONS"})
        return violations

    def inspect(block: PermissionBlock) -> None:
        context = {"file": record.file, "level": block.level, "job": block.job, "line": block.line}
        if block.style == "DYNAMIC":
            violations.append({**context, "reason": "DYNAMIC_PERMISSIONS"})
            return
        if block.style == "SCALAR":
            if block.scalar == "write-all":
                violations.append({**context, "reason": "WRITE_ALL_FORBIDDEN"})
            elif block.scalar == "read-all":
                violations.append({**context, "reason": "READ_ALL_FORBIDDEN"})
            else:
                violations.append({**context, "reason": "UNKNOWN_PERMISSION_SCALAR", "value": block.scalar})
            return
        for scope, access in sorted(block.scopes.items()):
            if access not in {"read", "write", "none"}:
                violations.append({**context, "reason": "INVALID_PERMISSION_ACCESS", "scope": scope, "access": access})
                continue
            if access == "read" and scope not in reads:
                violations.append({**context, "reason": "UNAPPROVED_READ_SCOPE", "scope": scope})
            if access == "write" and (record.file, scope) not in approvals:
                violations.append({**context, "reason": "UNAPPROVED_WRITE_SCOPE", "scope": scope})

    inspect(top)
    top_scopes = top.scopes if top.style in {"MAPPING", "EMPTY"} else {}

    for block in record.jobs:
        inspect(block)
        if block.style == "MAPPING":
            for scope, access in block.scopes.items():
                if access == "none":
                    continue
                top_access = top_scopes.get(scope, "none")
                rank = {"none": 0, "read": 1, "write": 2}
                if top_access in rank and access in rank and rank[access] > rank[top_access]:
                    violations.append({
                        "file": record.file,
                        "level": "job",
                        "job": block.job,
                        "line": block.line,
                        "reason": "JOB_PERMISSION_WIDENS_TOP_LEVEL",
                        "scope": scope,
                        "top_access": top_access,
                        "job_access": access,
                    })
    return violations


def audit(files: Iterable[Path], policy: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    records = [parse_workflow(path, root=root) for path in files]
    debt: list[dict[str, Any]] = []
    for record in records:
        if record.top is None:
            debt.append({"file": record.file, "reason": "MISSING_TOP_LEVEL_PERMISSIONS"})
        elif record.top.style in {"SCALAR", "DYNAMIC"}:
            debt.append({
                "file": record.file,
                "reason": "BROAD_OR_DYNAMIC_TOP_LEVEL_PERMISSIONS",
                "style": record.top.style,
                "value": record.top.scalar,
            })
        for block in record.jobs:
            if block.style in {"SCALAR", "DYNAMIC"} or any(value == "write" for value in block.scopes.values()):
                debt.append({
                    "file": record.file,
                    "reason": "JOB_PERMISSION_REVIEW_REQUIRED",
                    "job": block.job,
                    "line": block.line,
                })
        for finding in record.parse_findings:
            debt.append({"file": record.file, "reason": finding})

    return {
        "schema_version": 1,
        "workflow_files": len(records),
        "explicit_top_level": sum(record.top is not None for record in records),
        "missing_top_level": sum(record.top is None for record in records),
        "job_permission_blocks": sum(len(record.jobs) for record in records),
        "legacy_debt_count": len(debt),
        "legacy_debt": debt,
        "records": [record.as_dict() for record in records],
    }


def changed_gate(result: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for raw in result["records"]:
        top_raw = raw["top"]
        top = None if top_raw is None else PermissionBlock(
            level=top_raw["level"], job=top_raw["job"], style=top_raw["style"],
            scalar=top_raw["scalar"], scopes=top_raw["scopes"], line=top_raw["line"],
        )
        jobs = tuple(PermissionBlock(
            level=item["level"], job=item["job"], style=item["style"],
            scalar=item["scalar"], scopes=item["scopes"], line=item["line"],
        ) for item in raw["jobs"])
        record = WorkflowPermissionRecord(
            file=raw["file"], top=top, jobs=jobs,
            parse_findings=tuple(raw["parse_findings"]),
        )
        violations.extend(_block_violations(record, policy))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["inventory", "changed"], required=True)
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit-debt", action="store_true")
    args = parser.parse_args()

    try:
        policy = _json(POLICY_PATH)
        validate_policy(policy)
        files = discover_files(policy) if args.mode == "inventory" else _git_changed_files(args.base or "", args.head, policy)
        result = audit(files, policy)
        result["mode"] = args.mode
        summary = {
            "mode": args.mode,
            "workflow_files": result["workflow_files"],
            "explicit_top_level": result["explicit_top_level"],
            "missing_top_level": result["missing_top_level"],
            "job_permission_blocks": result["job_permission_blocks"],
            "legacy_debt_count": result["legacy_debt_count"],
        }
        print(json.dumps(summary, sort_keys=True))
        if args.mode == "inventory" and args.emit_debt:
            for item in result["legacy_debt"]:
                print(json.dumps({"legacy_permission_debt": item}, sort_keys=True))
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.mode == "changed":
            violations = changed_gate(result, policy)
            if violations:
                for item in violations:
                    print(json.dumps({"permission_violation": item}, sort_keys=True), file=sys.stderr)
                print(f"WORKFLOW_PERMISSION_CHANGED_GATE_FAIL count={len(violations)}", file=sys.stderr)
                return 1
            print("WORKFLOW_PERMISSION_CHANGED_GATE_PASS")
        else:
            print("WORKFLOW_PERMISSION_INVENTORY_PASS")
        return 0
    except (WorkflowPermissionError, OSError, KeyError) as exc:
        print(f"WORKFLOW_PERMISSION_INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
