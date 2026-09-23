#!/usr/bin/env python3
"""Inventory GitHub Actions uses clauses and block unsafe refs in changed workflows."""

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
POLICY_PATH = ROOT / "config" / "governance" / "action_supply_chain_policy_v1.json"
USES_RE = re.compile(r"^\s*(?:-\s*)?uses\s*:\s*(.*?)\s*$")


class ActionSupplyChainError(ValueError):
    pass


@dataclass(frozen=True)
class UseRecord:
    file: str
    line: int
    raw_value: str
    classification: str
    owner: str | None = None
    repo: str | None = None
    subpath: str | None = None
    ref: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "raw_value": self.raw_value,
            "classification": self.classification,
            "owner": self.owner,
            "repo": self.repo,
            "subpath": self.subpath,
            "ref": self.ref,
        }


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ActionSupplyChainError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ActionSupplyChainError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise ActionSupplyChainError("unsupported supply-chain policy schema_version")
    if policy.get("policy_kind") != "action_supply_chain_policy_v1":
        raise ActionSupplyChainError("invalid supply-chain policy kind")
    if policy.get("semantics") != "INVENTORY_LEGACY_DEBT_BLOCK_CHANGED_FLOATING_REFS":
        raise ActionSupplyChainError("supply-chain semantics drift")
    if policy.get("scan_roots") != [".github/workflows", ".github/actions"]:
        raise ActionSupplyChainError("scan roots drift")
    if policy.get("workflow_extensions") != [".yml", ".yaml"]:
        raise ActionSupplyChainError("workflow extensions drift")
    if policy.get("immutable_remote_ref_regex") != "^[0-9a-fA-F]{40}$":
        raise ActionSupplyChainError("immutable remote ref rule drift")
    changed = policy.get("changed_mode")
    if not isinstance(changed, dict):
        raise ActionSupplyChainError("changed-mode policy missing")
    if changed.get("fail_on_remote_floating") is not True:
        raise ActionSupplyChainError("changed floating refs must fail closed")
    if changed.get("fail_on_dynamic_or_malformed") is not True:
        raise ActionSupplyChainError("changed dynamic/malformed uses must fail closed")
    if changed.get("require_registered_remote_sha") is not True:
        raise ActionSupplyChainError("changed remote SHA pins must require registry approval")
    if policy.get("approved_pin_registry") != "config/governance/action_pin_registry_v1.json":
        raise ActionSupplyChainError("approved pin registry path drift")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise ActionSupplyChainError("mandatory supply-chain path must remain zero-cost")


def _strip_inline_comment(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    if value[0] in {'"', "'"}:
        quote = value[0]
        escaped = False
        for index in range(1, len(value)):
            ch = value[index]
            if quote == '"' and ch == "\\" and not escaped:
                escaped = True
                continue
            if ch == quote and not escaped:
                tail = value[index + 1 :].strip()
                if tail and not tail.startswith("#"):
                    return value
                return value[: index + 1]
            escaped = False
        return value
    marker = value.find(" #")
    return value[:marker].rstrip() if marker >= 0 else value


def _unquote(value: str) -> str:
    value = _strip_inline_comment(value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def classify_uses(value: str, policy: dict[str, Any]) -> dict[str, Any]:
    scalar = _unquote(value)
    if not scalar or scalar in {"|", ">", "|-", ">-", "|+", ">+"}:
        return {"classification": "MALFORMED_USES"}
    if "${{" in scalar or "}}" in scalar:
        return {"classification": "DYNAMIC_EXPRESSION"}
    if scalar.startswith("./"):
        return {"classification": "LOCAL_ACTION_OR_WORKFLOW"}
    if scalar.startswith("docker://"):
        return {"classification": "DOCKER_IMAGE"}

    match = re.fullmatch(policy["remote_uses_regex"], scalar)
    if match is None:
        return {"classification": "MALFORMED_USES"}

    ref = match.group(1)
    repository_part = scalar.rsplit("@", 1)[0]
    pieces = repository_part.split("/")
    owner, repo = pieces[0], pieces[1]
    subpath = "/".join(pieces[2:]) or None
    pinned = re.fullmatch(policy["immutable_remote_ref_regex"], ref) is not None
    return {
        "classification": "REMOTE_PINNED_SHA" if pinned else "REMOTE_FLOATING_REF",
        "owner": owner,
        "repo": repo,
        "subpath": subpath,
        "ref": ref,
    }


def parse_file(path: Path, policy: dict[str, Any], root: Path = ROOT) -> list[UseRecord]:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ActionSupplyChainError(f"path is outside repository: {path}") from exc
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ActionSupplyChainError(f"cannot read {relative}: {exc}") from exc

    records: list[UseRecord] = []
    for line_no, line in enumerate(lines, 1):
        if line.lstrip().startswith("#"):
            continue
        match = USES_RE.match(line)
        if match is None:
            continue
        raw = match.group(1).strip()
        classified = classify_uses(raw, policy)
        records.append(
            UseRecord(
                file=relative,
                line=line_no,
                raw_value=_unquote(raw),
                classification=classified["classification"],
                owner=classified.get("owner"),
                repo=classified.get("repo"),
                subpath=classified.get("subpath"),
                ref=classified.get("ref"),
            )
        )
    return records


def discover_files(policy: dict[str, Any], root: Path = ROOT) -> list[Path]:
    found: set[Path] = set()
    extensions = set(policy["workflow_extensions"])
    for root_text in policy["scan_roots"]:
        scan_root = root / root_text
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in extensions:
                found.add(path)
    return sorted(found, key=lambda path: path.relative_to(root).as_posix())


def _git_changed_files(base: str, head: str, policy: dict[str, Any]) -> list[Path]:
    if not base or not head:
        raise ActionSupplyChainError("changed mode requires --base and --head")
    if re.fullmatch(r"0{40}", base):
        proc = subprocess.run(
            ["git", "rev-parse", f"{head}^"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise ActionSupplyChainError("cannot derive parent for zero before-SHA")
        base = proc.stdout.strip()

    proc = subprocess.run(
        [
            "git", "diff", "--name-only", "--diff-filter=ACMR",
            base, head, "--", ".github/workflows", ".github/actions",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise ActionSupplyChainError(f"git diff failed: {proc.stderr.strip()}")

    extensions = set(policy["workflow_extensions"])
    result: list[Path] = []
    for raw in proc.stdout.splitlines():
        if not raw.strip():
            continue
        rel = Path(raw.strip())
        if rel.is_absolute() or ".." in rel.parts:
            raise ActionSupplyChainError(f"unsafe changed path: {raw!r}")
        full = ROOT / rel
        if full.suffix.lower() in extensions and full.is_file():
            result.append(full)
    return sorted(set(result), key=lambda path: path.relative_to(ROOT).as_posix())


def audit(
    files: Iterable[Path],
    policy: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any]:
    file_list = list(files)
    records: list[UseRecord] = []
    for path in file_list:
        records.extend(parse_file(path, policy, root=root))

    counts = {name: 0 for name in policy["classifications"]}
    for record in records:
        counts[record.classification] += 1

    debt_classes = {"REMOTE_FLOATING_REF", "DYNAMIC_EXPRESSION", "MALFORMED_USES"}
    debt = [record.as_dict() for record in records if record.classification in debt_classes]
    remote_repositories = sorted({
        f"{record.owner}/{record.repo}"
        for record in records
        if record.owner is not None and record.repo is not None
    })
    return {
        "schema_version": 1,
        "files_scanned": len(file_list),
        "uses_total": len(records),
        "counts": counts,
        "remote_repositories": remote_repositories,
        "debt_count": len(debt),
        "debt": debt,
        "records": [record.as_dict() for record in records],
    }


def load_pin_registry(policy: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    registry = _json(root / policy["approved_pin_registry"])
    if registry.get("schema_version") != 1:
        raise ActionSupplyChainError("unsupported action pin registry schema_version")
    if registry.get("registry_kind") != "action_pin_registry_v1":
        raise ActionSupplyChainError("invalid action pin registry kind")
    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ActionSupplyChainError("action pin registry entries missing")
    return registry


def approved_pin_index(registry: dict[str, Any]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for entry in registry.get("entries", []):
        repository = entry.get("repository")
        sha = entry.get("approved_commit_sha")
        if not isinstance(repository, str) or not isinstance(sha, str):
            raise ActionSupplyChainError("invalid action pin registry entry")
        index.setdefault(repository, set()).add(sha)
    return index


def unapproved_pins(
    result: dict[str, Any],
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    approved = approved_pin_index(registry)
    violations: list[dict[str, Any]] = []
    for record in result["records"]:
        if record["classification"] != "REMOTE_PINNED_SHA":
            continue
        repository = f"{record['owner']}/{record['repo']}"
        if record["ref"] not in approved.get(repository, set()):
            item = dict(record)
            item["blocked_reason"] = "UNAPPROVED_REMOTE_SHA"
            violations.append(item)
    return violations


def changed_gate(
    result: dict[str, Any],
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    blocked = {"REMOTE_FLOATING_REF", "DYNAMIC_EXPRESSION", "MALFORMED_USES"}
    violations: list[dict[str, Any]] = []
    for record in result["records"]:
        if record["classification"] in blocked:
            item = dict(record)
            item["blocked_reason"] = record["classification"]
            violations.append(item)
    violations.extend(unapproved_pins(result, registry))
    return violations


def _print_summary(mode: str, result: dict[str, Any], emit_debt: bool) -> None:
    summary = {
        "mode": mode,
        "files_scanned": result["files_scanned"],
        "uses_total": result["uses_total"],
        "counts": result["counts"],
        "debt_count": result["debt_count"],
        "unapproved_pinned_count": result.get("unapproved_pinned_count", 0),
        "remote_repository_count": len(result["remote_repositories"]),
    }
    print(json.dumps(summary, sort_keys=True))
    if mode == "inventory" and emit_debt:
        for item in result["debt"]:
            print(json.dumps({"legacy_debt": item}, sort_keys=True))


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
        registry = load_pin_registry(policy)
        files = (
            discover_files(policy)
            if args.mode == "inventory"
            else _git_changed_files(args.base or "", args.head, policy)
        )
        result = audit(files, policy)
        result["mode"] = args.mode
        result["unapproved_pinned"] = unapproved_pins(result, registry)
        result["unapproved_pinned_count"] = len(result["unapproved_pinned"])
        _print_summary(args.mode, result, args.emit_debt)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        if args.mode == "changed":
            blocked = changed_gate(result, registry)
            if blocked:
                for item in blocked:
                    print(json.dumps({"blocked_uses": item}, sort_keys=True), file=sys.stderr)
                print(
                    f"ACTION_SUPPLY_CHAIN_CHANGED_GATE_FAIL count={len(blocked)}",
                    file=sys.stderr,
                )
                return 1
            print("ACTION_SUPPLY_CHAIN_CHANGED_GATE_PASS")
        else:
            print("ACTION_SUPPLY_CHAIN_INVENTORY_PASS")
        return 0
    except (ActionSupplyChainError, OSError, KeyError) as exc:
        print(f"ACTION_SUPPLY_CHAIN_INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
