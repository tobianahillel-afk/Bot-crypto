#!/usr/bin/env python3
"""Run the universal zero-dependency T0 changed-file gate."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "validation_t0_policy_v1.json"


class T0Error(ValueError):
    pass


@dataclass(frozen=True)
class Change:
    status: str
    path: str
    old_path: str | None = None


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise T0Error(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise T0Error(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise T0Error(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise T0Error("unsupported T0 policy schema_version")
    if policy.get("policy_kind") != "validation_t0_policy_v1":
        raise T0Error("invalid T0 policy kind")
    if policy.get("semantics") != "CHEAP_CHANGED_FILE_GATE_ONLY":
        raise T0Error("T0 semantics drift")
    max_files = policy.get("max_changed_files")
    max_bytes = policy.get("max_parse_bytes_per_file")
    if not isinstance(max_files, int) or not 1 <= max_files <= 5000:
        raise T0Error("invalid max_changed_files")
    if not isinstance(max_bytes, int) or not 1024 <= max_bytes <= 16 * 1024 * 1024:
        raise T0Error("invalid max_parse_bytes_per_file")
    parsers = policy.get("parsers")
    expected = {
        ".py": "PYTHON_COMPILE",
        ".json": "JSON_PARSE",
        ".toml": "TOML_PARSE",
    }
    if parsers != expected:
        raise T0Error("T0 parser set must remain exact and standard-library only")
    escalation = policy.get("escalation")
    if not isinstance(escalation, dict):
        raise T0Error("T0 escalation policy missing")
    if "UNKNOWN_REQUIRES_REVIEW" not in escalation.get("classifier_critical_labels", []):
        raise T0Error("unknown diff classification must remain an escalation")


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=False, capture_output=True, text=True
    )


def _safe_repo_path(path: str) -> str:
    candidate = Path(path)
    if not path or candidate.is_absolute() or ".." in candidate.parts:
        raise T0Error(f"unsafe repository-relative path: {path!r}")
    return candidate.as_posix()


def changed_files(base: str, head: str = "HEAD") -> list[Change]:
    proc = _git("diff", "--name-status", "--find-renames", f"{base}...{head}")
    if proc.returncode != 0:
        raise T0Error(f"git diff failed: {proc.stderr.strip()}")
    changes: list[Change] = []
    for raw in proc.stdout.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        code = parts[0]
        kind = code[0]
        if kind in {"R", "C"}:
            if len(parts) != 3:
                raise T0Error(f"malformed rename/copy diff record: {raw!r}")
            changes.append(
                Change(status=code, old_path=_safe_repo_path(parts[1]), path=_safe_repo_path(parts[2]))
            )
        else:
            if len(parts) != 2:
                raise T0Error(f"malformed diff record: {raw!r}")
            changes.append(Change(status=code, path=_safe_repo_path(parts[1])))
    return changes


def _read_for_parse(path: Path, max_bytes: int) -> bytes:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise T0Error(f"cannot stat changed file {path}: {exc}") from exc
    if size > max_bytes:
        raise T0Error(f"changed parseable file exceeds T0 size limit: {path} ({size} bytes)")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise T0Error(f"cannot read changed file {path}: {exc}") from exc


def validate_present_file(path: str, policy: dict[str, Any]) -> dict[str, Any]:
    full = ROOT / path
    suffix = full.suffix.lower()
    parser = policy["parsers"].get(suffix)
    if parser is None:
        return {"path": path, "parser": "NONE", "status": "SKIPPED_NON_PARSEABLE"}
    data = _read_for_parse(full, policy["max_parse_bytes_per_file"])
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise T0Error(f"changed parseable file is not UTF-8: {path}: {exc}") from exc
    try:
        if parser == "PYTHON_COMPILE":
            compile(text, path, "exec", dont_inherit=True)
        elif parser == "JSON_PARSE":
            json.loads(text)
        elif parser == "TOML_PARSE":
            tomllib.loads(text)
        else:
            raise T0Error(f"unsupported parser policy value: {parser}")
    except (SyntaxError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        raise T0Error(f"{parser} failed for {path}: {exc}") from exc
    return {"path": path, "parser": parser, "status": "PASS"}


def run_t0_for_changes(
    changes: list[Change],
    policy: dict[str, Any],
    classifier: ModuleType,
    impact_mapper: ModuleType,
) -> dict[str, Any]:
    if not changes:
        raise T0Error("T0 requires at least one changed file")
    if len(changes) > policy["max_changed_files"]:
        raise T0Error(
            f"T0 changed-file count {len(changes)} exceeds limit {policy['max_changed_files']}"
        )

    current_paths = [change.path for change in changes]
    classification = classifier.classify_paths(current_paths, classifier._load_policy())
    impact_policy = impact_mapper._load(impact_mapper.POLICY_PATH)
    impact_mapper.validate_policy(impact_policy)
    impact = impact_mapper.map_impact(classification, impact_policy)

    parse_results: list[dict[str, Any]] = []
    for change in changes:
        if change.status.startswith("D"):
            parse_results.append(
                {"path": change.path, "parser": "NONE", "status": "SKIPPED_DELETED"}
            )
            continue
        parse_results.append(validate_present_file(change.path, policy))

    critical = set(classification["critical_labels"])
    critical_trigger = sorted(
        critical & set(policy["escalation"]["classifier_critical_labels"])
    )
    sensitivity_trigger = (
        impact["sensitivity"]
        if impact["sensitivity"] in policy["escalation"]["impact_sensitivities"]
        else None
    )
    reasons: list[str] = []
    if critical_trigger:
        reasons.append("CLASSIFIER_CRITICAL:" + ",".join(critical_trigger))
    if sensitivity_trigger:
        reasons.append("IMPACT_SENSITIVITY:" + sensitivity_trigger)

    return {
        "t0_version": 1,
        "changed_files": [
            {"status": c.status, "path": c.path, "old_path": c.old_path}
            for c in changes
        ],
        "parse_results": parse_results,
        "classification": classification,
        "impact": impact,
        "escalation_recommended": bool(reasons),
        "escalation_reasons": reasons,
        "selected_validation_tiers": ["T0"],
        "deeper_tiers_executed": [],
        "network_used": False,
        "test_suite_executed": False,
    }


def repository_run() -> dict[str, Any]:
    started = time.perf_counter()
    policy = _json(POLICY_PATH)
    validate_policy(policy)

    active = _module("t0_active_awu", ROOT / "scripts/governance/resolve_active_awu.py")
    classifier = _module("t0_diff_classifier", ROOT / "scripts/governance/classify_diff.py")
    impact = _module("t0_diff_impact", ROOT / "scripts/governance/map_diff_impact.py")

    try:
        _awu_path, awu, _evidence = active.resolve_active_awu()
    except active.ActiveAwuError as exc:
        raise T0Error(str(exc)) from exc

    base = awu.get("scope", {}).get("scope_base_sha")
    if not isinstance(base, str) or len(base) != 40:
        raise T0Error("active AWU has invalid scope_base_sha")
    changes = changed_files(base)
    result = run_t0_for_changes(changes, policy, classifier, impact)
    result["active_awu"] = awu["id"]
    result["scope_base_sha"] = base
    result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
    return result


def main() -> int:
    try:
        result = repository_run()
    except T0Error as exc:
        print(f"T0_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
