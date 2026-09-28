#!/usr/bin/env python3
"""Validate declarative mutation profiles and exact P0.6 parity."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "mutation_profile_policy_v1.json"
REGISTRY_PATH = ROOT / "config" / "governance" / "mutation_profiles_v1.json"
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
PROFILE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

P06_ID = "P06_DECISION_EVIDENCE"
P06_PROFILE_VERSION = 2
P06_RETIRED_WORKFLOW = ".github/workflows/p06-extended-mutation.yml"
P06_GENERIC_WORKFLOW = ".github/workflows/ci-mutation.yml"
P06_WORKFLOW_BLOB = "b1653c0c392e74ea7f50b7b922fd8750fa402bb7"
P06_WU11_EVIDENCE = "engineering/ENG09_WU11_P06_PARITY_EVIDENCE.json"
P06_PARITY_HEAD = "af93cac4387b93865080a732c88ab8fd6eebeea0"
P06_ENGINEERING_BRANCH = "engineering/bootstrap-development-engine"
P06_SELECTORS = [
    {"mode": "EXACT", "pattern": "src/crypto_quant_bot/contracts/decision_evidence.py"},
    {"mode": "GLOB", "pattern": "tests/test_p06_decision_evidence*.py"},
    {"mode": "EXACT", "pattern": P06_GENERIC_WORKFLOW},
    {"mode": "EXACT", "pattern": "requirements-dev.lock"},
    {"mode": "EXACT", "pattern": "pyproject.toml"},
]
P06_MAINTENANCE_PATHS = [
    "scripts/governance/run_mutation_profile.py",
    "scripts/governance/selftest_mutation_runner.py",
    "scripts/governance/validate_mutation_profiles.py",
    "scripts/governance/selftest_mutation_profiles.py",
    "scripts/governance/select_mutation_profile.py",
    "config/governance/mutation_profile_policy_v1.json",
    "config/governance/mutation_profiles_v1.json",
]
P06_TARGETS = ["src/crypto_quant_bot/contracts/decision_evidence.py"]
P06_TESTS = [
    "tests/test_p06_decision_evidence.py",
    "tests/test_p06_decision_evidence_properties.py",
]
P06_SOURCE_PATHS = ["src/crypto_quant_bot/contracts/"]
P06_ALSO_COPY = [
    "src/crypto_quant_bot/__init__.py",
    "src/crypto_quant_bot/core/",
    "src/crypto_quant_bot/data/",
    "config/",
    "contracts/",
    "pyproject.toml",
]
P06_SETTINGS = {
    "mutate_only_covered_lines": True,
    "max_stack_depth": 10,
    "timeout_multiplier": 8.0,
    "timeout_constant": 1.0,
    "do_not_mutate_patterns": [r"raise \\w+", r"logger\\.\\w+"],
}


class MutationProfileError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MutationProfileError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MutationProfileError(f"{path} must contain an object")
    return value


def _safe_repo_path(value: str, *, allow_glob: bool = False) -> str:
    if not isinstance(value, str) or not value:
        raise MutationProfileError("repository path must be a non-empty string")
    if "\\" in value:
        raise MutationProfileError(f"repository path must use POSIX separators: {value!r}")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise MutationProfileError(f"repository path escapes root: {value!r}")
    if not allow_glob and any(char in value for char in "*?["):
        raise MutationProfileError(f"wildcards forbidden in explicit repository path: {value!r}")
    if value.startswith("./") or "//" in value:
        raise MutationProfileError(f"non-canonical repository path: {value!r}")
    return value


def _reject_forbidden_keys(value: Any, forbidden: set[str], trail: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise MutationProfileError(f"non-string profile key at {'.'.join(trail) or '<root>'}")
            if key.lower() in forbidden:
                location = ".".join((*trail, key))
                raise MutationProfileError(f"forbidden executable profile key: {location}")
            _reject_forbidden_keys(child, forbidden, (*trail, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_keys(child, forbidden, (*trail, str(index)))


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise MutationProfileError("unsupported mutation-profile policy schema_version")
    if policy.get("policy_kind") != "mutation_profile_policy_v1":
        raise MutationProfileError("invalid mutation-profile policy kind")
    if policy.get("semantics") != "DATA_ONLY_DETERMINISTIC_FAIL_CLOSED":
        raise MutationProfileError("mutation-profile semantics drift")
    if policy.get("registry_path") != "config/governance/mutation_profiles_v1.json":
        raise MutationProfileError("mutation-profile registry path drift")
    if policy.get("allowed_selector_modes") != ["EXACT", "GLOB"]:
        raise MutationProfileError("selector-mode allowlist drift")
    if policy.get("allowed_source_binding_modes") != ["CURRENT_CHECKOUT", "EXACT_HEAD_INPUT"]:
        raise MutationProfileError("source-binding mode allowlist drift")
    if policy.get("allowed_score_terms") != ["killed", "timeout", "suspicious", "survived"]:
        raise MutationProfileError("score-term allowlist drift")

    forbidden = policy.get("forbidden_profile_keys")
    if not isinstance(forbidden, list) or len(forbidden) != len(set(forbidden)):
        raise MutationProfileError("forbidden profile keys must be a unique list")
    if any(not isinstance(key, str) or not key for key in forbidden):
        raise MutationProfileError("forbidden profile keys contain invalid entry")

    bounds = policy.get("bounds")
    required_bounds = {
        "max_profiles",
        "max_selectors_per_profile",
        "max_mutation_targets_per_profile",
        "max_tests_per_profile",
        "max_also_copy_per_profile",
        "max_do_not_mutate_patterns",
    }
    if not isinstance(bounds, dict) or set(bounds) != required_bounds:
        raise MutationProfileError("mutation-profile bounds shape drift")
    for key, value in bounds.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > 256:
            raise MutationProfileError(f"invalid mutation-profile bound {key}: {value!r}")


def _validate_string_list(
    value: Any,
    *,
    label: str,
    maximum: int,
    path_values: bool = False,
    must_exist: bool = False,
    root: Path = ROOT,
) -> list[str]:
    if not isinstance(value, list) or not value or len(value) > maximum:
        raise MutationProfileError(f"{label} must contain 1..{maximum} entries")
    if len(value) != len(set(value)):
        raise MutationProfileError(f"{label} contains duplicates")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise MutationProfileError(f"{label} contains invalid string")
        if path_values:
            _safe_repo_path(item)
            if must_exist and not (root / item.rstrip("/")).exists():
                raise MutationProfileError(f"{label} path does not exist: {item}")
        result.append(item)
    return result


def _validate_selectors(profile: dict[str, Any], policy: dict[str, Any]) -> None:
    selectors = profile.get("selectors")
    maximum = policy["bounds"]["max_selectors_per_profile"]
    if not isinstance(selectors, list) or not selectors or len(selectors) > maximum:
        raise MutationProfileError(f"{profile['id']}: selectors must contain 1..{maximum} entries")
    seen: set[tuple[str, str]] = set()
    for selector in selectors:
        if not isinstance(selector, dict) or set(selector) != {"mode", "pattern"}:
            raise MutationProfileError(f"{profile['id']}: selector shape invalid")
        mode = selector["mode"]
        pattern = selector["pattern"]
        if mode not in policy["allowed_selector_modes"]:
            raise MutationProfileError(f"{profile['id']}: unsupported selector mode {mode!r}")
        _safe_repo_path(pattern, allow_glob=mode == "GLOB")
        if mode == "EXACT" and any(char in pattern for char in "*?["):
            raise MutationProfileError(f"{profile['id']}: EXACT selector contains wildcard")
        if mode == "GLOB" and not any(char in pattern for char in "*?["):
            raise MutationProfileError(f"{profile['id']}: GLOB selector has no wildcard")
        key = (mode, pattern)
        if key in seen:
            raise MutationProfileError(f"{profile['id']}: duplicate selector {key}")
        seen.add(key)


def _validate_score(profile: dict[str, Any], policy: dict[str, Any]) -> None:
    score = profile.get("score")
    if not isinstance(score, dict) or set(score) != {
        "minimum_percent", "numerator", "denominator", "require_zero"
    }:
        raise MutationProfileError(f"{profile['id']}: score shape invalid")
    minimum = score["minimum_percent"]
    if not isinstance(minimum, (int, float)) or isinstance(minimum, bool) or not 0 <= minimum <= 100:
        raise MutationProfileError(f"{profile['id']}: score minimum invalid")
    allowed = set(policy["allowed_score_terms"])
    numerator = score["numerator"]
    denominator = score["denominator"]
    require_zero = score["require_zero"]
    for label, terms, allow_empty in (
        ("numerator", numerator, False),
        ("denominator", denominator, False),
        ("require_zero", require_zero, True),
    ):
        if not isinstance(terms, list) or (not allow_empty and not terms):
            raise MutationProfileError(f"{profile['id']}: {label} invalid")
        if len(terms) != len(set(terms)) or any(term not in allowed for term in terms):
            raise MutationProfileError(f"{profile['id']}: {label} uses invalid score terms")
    if not set(numerator) <= set(denominator):
        raise MutationProfileError(f"{profile['id']}: numerator must be subset of denominator")
    if not set(require_zero) <= set(denominator):
        raise MutationProfileError(f"{profile['id']}: require_zero must be subset of denominator")


def _validate_source_binding(profile: dict[str, Any], policy: dict[str, Any]) -> None:
    binding = profile.get("source_binding")
    if not isinstance(binding, dict) or set(binding) != {"mode", "exact_head"}:
        raise MutationProfileError(f"{profile['id']}: source_binding shape invalid")
    mode = binding["mode"]
    head = binding["exact_head"]
    if mode not in policy["allowed_source_binding_modes"]:
        raise MutationProfileError(f"{profile['id']}: unsupported source-binding mode")
    if mode == "CURRENT_CHECKOUT" and head is not None:
        raise MutationProfileError(f"{profile['id']}: CURRENT_CHECKOUT cannot bind exact_head")
    if mode == "EXACT_HEAD_INPUT":
        if not isinstance(head, str) or HEX40_RE.fullmatch(head) is None:
            raise MutationProfileError(f"{profile['id']}: EXACT_HEAD_INPUT requires 40-hex exact_head")


def _validate_profile(profile: dict[str, Any], policy: dict[str, Any], root: Path) -> None:
    required = {
        "id", "profile_version", "enabled", "selectors", "mutation", "score",
        "source_binding", "evidence", "source_immutability", "legacy_reference"
    }
    if not isinstance(profile, dict) or set(profile) != required:
        raise MutationProfileError("mutation profile has invalid top-level shape")
    profile_id = profile["id"]
    if not isinstance(profile_id, str) or PROFILE_ID_RE.fullmatch(profile_id) is None:
        raise MutationProfileError(f"invalid mutation profile id: {profile_id!r}")
    if not isinstance(profile["profile_version"], int) or isinstance(profile["profile_version"], bool) or profile["profile_version"] < 1:
        raise MutationProfileError(f"{profile_id}: profile_version invalid")
    if not isinstance(profile["enabled"], bool):
        raise MutationProfileError(f"{profile_id}: enabled must be boolean")

    _validate_selectors(profile, policy)

    mutation = profile["mutation"]
    if not isinstance(mutation, dict) or set(mutation) != {
        "source_paths", "targets", "tests", "also_copy", "settings"
    }:
        raise MutationProfileError(f"{profile_id}: mutation shape invalid")
    _validate_string_list(
        mutation["source_paths"], label=f"{profile_id}.source_paths", maximum=8,
        path_values=True, must_exist=True, root=root
    )
    targets = _validate_string_list(
        mutation["targets"], label=f"{profile_id}.targets",
        maximum=policy["bounds"]["max_mutation_targets_per_profile"],
        path_values=True, must_exist=True, root=root
    )
    if any(not target.endswith(".py") for target in targets):
        raise MutationProfileError(f"{profile_id}: mutation targets must be Python files")
    tests = _validate_string_list(
        mutation["tests"], label=f"{profile_id}.tests",
        maximum=policy["bounds"]["max_tests_per_profile"],
        path_values=True, must_exist=True, root=root
    )
    if any(not Path(test).name.startswith("test_") or not test.endswith(".py") for test in tests):
        raise MutationProfileError(f"{profile_id}: mutation tests must be explicit test_*.py files")
    _validate_string_list(
        mutation["also_copy"], label=f"{profile_id}.also_copy",
        maximum=policy["bounds"]["max_also_copy_per_profile"],
        path_values=True, must_exist=True, root=root
    )

    settings = mutation["settings"]
    if not isinstance(settings, dict) or set(settings) != {
        "mutate_only_covered_lines", "max_stack_depth", "timeout_multiplier",
        "timeout_constant", "do_not_mutate_patterns"
    }:
        raise MutationProfileError(f"{profile_id}: mutation settings shape invalid")
    if not isinstance(settings["mutate_only_covered_lines"], bool):
        raise MutationProfileError(f"{profile_id}: mutate_only_covered_lines invalid")
    if not isinstance(settings["max_stack_depth"], int) or isinstance(settings["max_stack_depth"], bool) or settings["max_stack_depth"] < 1:
        raise MutationProfileError(f"{profile_id}: max_stack_depth invalid")
    for key in ("timeout_multiplier", "timeout_constant"):
        value = settings[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise MutationProfileError(f"{profile_id}: {key} invalid")
    patterns = settings["do_not_mutate_patterns"]
    _validate_string_list(
        patterns, label=f"{profile_id}.do_not_mutate_patterns",
        maximum=policy["bounds"]["max_do_not_mutate_patterns"]
    )
    for pattern in patterns:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise MutationProfileError(f"{profile_id}: invalid do-not-mutate regex {pattern!r}") from exc

    _validate_score(profile, policy)
    _validate_source_binding(profile, policy)

    evidence = profile["evidence"]
    if not isinstance(evidence, dict) or set(evidence) != {
        "directory", "run_log", "results_log", "score_file", "schema_version"
    }:
        raise MutationProfileError(f"{profile_id}: evidence shape invalid")
    _safe_repo_path(evidence["directory"])
    for key in ("run_log", "results_log", "score_file"):
        name = evidence[key]
        if not isinstance(name, str) or not name or "/" in name or "\\" in name or name in {".", ".."}:
            raise MutationProfileError(f"{profile_id}: evidence {key} must be a basename")
    if not isinstance(evidence["schema_version"], str) or not evidence["schema_version"]:
        raise MutationProfileError(f"{profile_id}: evidence schema_version invalid")

    immutability = profile["source_immutability"]
    if not isinstance(immutability, dict) or set(immutability) != {
        "enabled", "restore_paths", "verify_paths"
    }:
        raise MutationProfileError(f"{profile_id}: source_immutability shape invalid")
    if not isinstance(immutability["enabled"], bool):
        raise MutationProfileError(f"{profile_id}: source_immutability enabled invalid")
    for key in ("restore_paths", "verify_paths"):
        _validate_string_list(
            immutability[key], label=f"{profile_id}.source_immutability.{key}",
            maximum=32, path_values=True, must_exist=True, root=root
        )

    legacy = profile["legacy_reference"]
    if legacy != {
        "workflow": P06_RETIRED_WORKFLOW,
        "workflow_blob_sha": P06_WORKFLOW_BLOB,
        "canonical_mutmut_defaults": "pyproject.toml",
        "lifecycle": "GENERIC_CONTROL_ACTIVE_AFTER_WU12",
    }:
        raise MutationProfileError("P0.6 legacy-reference drift")

    _verify_retired_provenance(root)
    workflow_text = (root / P06_GENERIC_WORKFLOW).read_text(encoding="utf-8")
    validate_p06_migrated_workflow(workflow_text)

    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    defaults = pyproject.get("tool", {}).get("mutmut")
    if not isinstance(defaults, dict):
        raise MutationProfileError("canonical [tool.mutmut] missing")
    inherited = {
        "also_copy": defaults.get("also_copy"),
        "mutate_only_covered_lines": defaults.get("mutate_only_covered_lines"),
        "max_stack_depth": defaults.get("max_stack_depth"),
        "timeout_multiplier": defaults.get("timeout_multiplier"),
        "timeout_constant": defaults.get("timeout_constant"),
        "do_not_mutate_patterns": defaults.get("do_not_mutate_patterns"),
    }
    expected_inherited = {
        "also_copy": P06_ALSO_COPY,
        **P06_SETTINGS,
    }
    if inherited != expected_inherited:
        raise MutationProfileError(
            f"canonical mutmut defaults no longer match P0.6 profile: {inherited!r}"
        )


def validate_all(
    policy: dict[str, Any],
    registry: dict[str, Any],
    root: Path = ROOT,
    *,
    verify_p06_parity: bool = True,
) -> None:
    validate_policy(policy)
    validate_registry(policy, registry, root)
    if verify_p06_parity:
        validate_p06_parity(registry, root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    args = parser.parse_args()
    try:
        policy = _load_json(args.policy)
        registry = _load_json(args.registry)
        validate_all(policy, registry)
    except (MutationProfileError, OSError, KeyError, TypeError) as exc:
        print(f"MUTATION_PROFILES_INVALID: {exc}", file=sys.stderr)
        return 1
    print("MUTATION_PROFILES_VALID profiles=1 lifecycle=GENERIC_CONTROL_ACTIVE_AFTER_WU12")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
