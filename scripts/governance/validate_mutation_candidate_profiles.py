#!/usr/bin/env python3
"""Validate lifecycle-gated read-only mutation candidate profiles."""

from __future__ import annotations

import fnmatch
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config/governance/mutation_candidate_profile_policy_v1.json"
REGISTRY_PATH = ROOT / "config/governance/mutation_candidate_profiles_v1.json"
ACTIVE_REGISTRY_PATH = ROOT / "config/governance/mutation_profiles_v1.json"

EXPECTED_ID = "LOT45_ORDER_FLOW_DELTA_CVD"
EXPECTED_CANDIDATE_HEAD = "ec2c4ab16f21b23e062b7fca0bb796c8db4a5133"
EXPECTED_BASE_SHA = "390d0779f2be257fa8134faf8f02193a760a09c3"
EXPECTED_SOURCE_HEAD = "c418338da86c49bd4b688d4a64893ee5042adc40"
EXPECTED_WORKFLOW_BLOB = "e5a569b79b70e42da7c9ce2cc96b8623a0040f1d"
EXPECTED_SUMMARY_BLOB = "26e49b1d1fc450a00ebc346541a69e82059f1119"
EXPECTED_PRELAUNCH_BLOB = "f9aec59ec03449702dc67cac98b020ffe64fe403"

EXPECTED_SELECTORS = [
    {
        "mode": "GLOB",
        "pattern": "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine*.py"
    },
    {
        "mode": "EXACT",
        "pattern": "scripts/lot45_trusted_prelaunch.sh"
    },
    {
        "mode": "GLOB",
        "pattern": "tests/test_lot45*.py"
    },
    {
        "mode": "EXACT",
        "pattern": "config/microstructure/order_flow_delta_and_cvd_engine_v1.json"
    },
    {
        "mode": "EXACT",
        "pattern": "contracts/schemas/order_flow_delta_cvd_engine_state_v1.schema.json"
    },
    {
        "mode": "EXACT",
        "pattern": "contracts/schemas/order_flow_delta_cvd_engine_audit_v1.schema.json"
    },
    {
        "mode": "EXACT",
        "pattern": "contracts/schemas/order_flow_state_v1.schema.json"
    },
    {
        "mode": "EXACT",
        "pattern": "contracts/schemas/cvd_series_v1.schema.json"
    },
    {
        "mode": "EXACT",
        "pattern": ".github/workflows/lot45-mutation-assurance.yml"
    },
    {
        "mode": "EXACT",
        "pattern": "requirements-dev.lock"
    }
]
EXPECTED_BASELINE_TESTS = [
    "tests/test_lot45_order_flow_delta_and_cvd_engine.py",
    "tests/test_lot45_policy_contract.py",
    "tests/test_lot45_runtime_binding_and_rounding.py",
    "tests/test_lot45_schema_contracts.py",
    "tests/test_lot45_checksum_binding_adversarial.py",
    "tests/test_lot45_untracked_executable_source_binding.py",
    "tests/test_lot45_decimal_context_and_pre_epoch.py",
    "tests/test_lot45_top_level_checksum_authenticity.py"
]
EXPECTED_MICROSTRUCTURE_COPY = [
    "src/crypto_quant_bot/microstructure/__init__.py",
    "src/crypto_quant_bot/microstructure/book_integrity_desynchronization_detector.py",
    "src/crypto_quant_bot/microstructure/book_integrity_desynchronization_detector_models.py",
    "src/crypto_quant_bot/microstructure/book_integrity_desynchronization_detector_validation.py",
    "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_analysis.py",
    "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine.py",
    "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_models.py",
    "src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_validation.py",
    "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_analysis.py",
    "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine.py",
    "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine_models.py",
    "src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine_validation.py",
    "src/crypto_quant_bot/microstructure/microstructure_scope_and_offline_data_contracts.py",
    "src/crypto_quant_bot/microstructure/microstructure_scope_and_offline_data_contracts_models.py",
    "src/crypto_quant_bot/microstructure/microstructure_scope_and_offline_data_contracts_validation.py",
    "src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor.py",
    "src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor_models.py",
    "src/crypto_quant_bot/microstructure/order_book_delta_sequence_reconstructor.py",
    "src/crypto_quant_bot/microstructure/order_book_delta_sequence_reconstructor_models.py",
    "src/crypto_quant_bot/microstructure/order_book_delta_sequence_reconstructor_validation.py",
    "src/crypto_quant_bot/microstructure/order_book_l2_snapshot_engine.py",
    "src/crypto_quant_bot/microstructure/order_book_l2_snapshot_engine_models.py",
    "src/crypto_quant_bot/microstructure/order_book_l2_snapshot_engine_validation.py",
    "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine.py",
    "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine_models.py",
    "src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine_validation.py",
    "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py",
    "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py",
    "src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_validation.py"
]
EXPECTED_SOURCE_BINDING = {
    "mode": "EXACT_HEAD_INPUT",
    "exact_head": EXPECTED_SOURCE_HEAD,
    "candidate_head": EXPECTED_CANDIDATE_HEAD,
    "trusted_prelaunch_required": True,
    "lot46_absence_checks_required": True,
}


class MutationCandidateProfileError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MutationCandidateProfileError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MutationCandidateProfileError(f"{path} must contain an object")
    return value


def _safe_path(value: str, *, allow_glob: bool = False) -> None:
    if not isinstance(value, str) or not value:
        raise MutationCandidateProfileError("repository path must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        raise MutationCandidateProfileError(f"unsafe repository path: {value!r}")
    if not allow_glob and any(ch in value for ch in "*?["):
        raise MutationCandidateProfileError(f"unexpected glob in exact path: {value!r}")


def _walk_forbidden(value: Any, forbidden: set[str], path: str = "profile") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden:
                raise MutationCandidateProfileError(f"forbidden executable key at {path}.{key}")
            _walk_forbidden(child, forbidden, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden(child, forbidden, f"{path}[{index}]")


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise MutationCandidateProfileError("unsupported candidate policy schema_version")
    if policy.get("policy_kind") != "mutation_candidate_profile_policy_v1":
        raise MutationCandidateProfileError("invalid candidate policy kind")
    if policy.get("semantics") != "READ_ONLY_LIFECYCLE_GATED_NO_EXECUTION":
        raise MutationCandidateProfileError("candidate policy semantics drift")
    if policy.get("registry_path") != "config/governance/mutation_candidate_profiles_v1.json":
        raise MutationCandidateProfileError("candidate registry path drift")
    if policy.get("active_registry_path") != "config/governance/mutation_profiles_v1.json":
        raise MutationCandidateProfileError("active registry path drift")
    if policy.get("allowed_selector_modes") != ["EXACT", "GLOB"]:
        raise MutationCandidateProfileError("selector mode drift")
    if policy.get("allowed_lifecycles") != ["READ_ONLY_QUALIFIED_NOT_ADOPTED"]:
        raise MutationCandidateProfileError("candidate lifecycle drift")
    if policy.get("allowed_source_binding_modes") != ["EXACT_HEAD_INPUT"]:
        raise MutationCandidateProfileError("candidate source-binding mode drift")
    if policy.get("required_false_flags") != [
        "execution_allowed", "active_registry_adopted",
        "production_selector_visible", "generic_runner_executable"
    ]:
        raise MutationCandidateProfileError("candidate false-flag floor drift")


def _validate_selectors(profile: dict[str, Any], policy: dict[str, Any]) -> None:
    selectors = profile.get("selectors")
    if not isinstance(selectors, list) or not selectors:
        raise MutationCandidateProfileError("candidate selectors missing")
    if len(selectors) > policy["bounds"]["max_selectors_per_profile"]:
        raise MutationCandidateProfileError("candidate selector count exceeds policy")
    seen: set[tuple[str, str]] = set()
    for item in selectors:
        if not isinstance(item, dict) or set(item) != {"mode", "pattern"}:
            raise MutationCandidateProfileError("candidate selector shape invalid")
        mode, pattern = item["mode"], item["pattern"]
        if mode not in policy["allowed_selector_modes"]:
            raise MutationCandidateProfileError(f"unsupported selector mode: {mode}")
        _safe_path(pattern, allow_glob=(mode == "GLOB"))
        key = (mode, pattern)
        if key in seen:
            raise MutationCandidateProfileError(f"duplicate selector: {key}")
        seen.add(key)
    if selectors != EXPECTED_SELECTORS:
        raise MutationCandidateProfileError("Lot45 selector identity/order drift")


def _validate_candidate_binding(profile: dict[str, Any]) -> None:
    b = profile.get("candidate_binding")
    expected = {
        "pull_request": 66,
        "candidate_head_sha": EXPECTED_CANDIDATE_HEAD,
        "base_branch": "main",
        "base_sha": EXPECTED_BASE_SHA,
        "mutation_workflow": ".github/workflows/lot45-mutation-assurance.yml",
        "mutation_workflow_blob_sha": EXPECTED_WORKFLOW_BLOB,
        "mutation_summary": "reports/lot45/mutation_summary.json",
        "mutation_summary_blob_sha": EXPECTED_SUMMARY_BLOB,
        "source_head_sha": EXPECTED_SOURCE_HEAD,
        "trusted_prelaunch": "scripts/lot45_trusted_prelaunch.sh",
        "trusted_prelaunch_blob_sha": EXPECTED_PRELAUNCH_BLOB,
    }
    if b != expected:
        raise MutationCandidateProfileError("Lot45 candidate Git binding drift")


def _validate_source_binding(profile: dict[str, Any], policy: dict[str, Any]) -> None:
    binding = profile.get("source_binding")
    if binding != EXPECTED_SOURCE_BINDING:
        raise MutationCandidateProfileError("Lot45 exact-head source binding drift")
    if binding["mode"] not in policy["allowed_source_binding_modes"]:
        raise MutationCandidateProfileError("Lot45 source-binding mode is not allowed")


def _validate_score(profile: dict[str, Any]) -> None:
    score = profile.get("score")
    if score != {
        "minimum_percent": 80.0,
        "numerator": ["killed"],
        "denominator": ["killed", "timeout", "suspicious", "survived"],
        "require_zero": ["timeout", "suspicious"],
        "rounding_digits": 2,
    }:
        raise MutationCandidateProfileError("Lot45 score semantics drift")
    ev = profile.get("evidence")
    expected_counts = {
        "schema_version": "lot45-mutation-summary-v1",
        "status": "PASS",
        "killed": 1341,
        "timeout": 0,
        "suspicious": 0,
        "survived": 324,
        "evaluated": 1665,
        "completed": 1665,
        "total": 1665,
        "score_percent": 80.54,
        "mutmut_run_exit_code": 0,
        "mutmut_results_exit_code": 0,
    }
    if ev != expected_counts:
        raise MutationCandidateProfileError("Lot45 mutation evidence drift")
    denominator = sum(ev[name] for name in score["denominator"])
    numerator = sum(ev[name] for name in score["numerator"])
    if denominator != ev["evaluated"] or ev["evaluated"] != ev["total"]:
        raise MutationCandidateProfileError("Lot45 evaluated-mutant arithmetic drift")
    computed = round(100.0 * numerator / denominator, score["rounding_digits"])
    if not math.isclose(computed, ev["score_percent"], rel_tol=0.0, abs_tol=1e-9):
        raise MutationCandidateProfileError(
            f"Lot45 score mismatch: {computed} != {ev['score_percent']}"
        )
    if computed < score["minimum_percent"]:
        raise MutationCandidateProfileError("Lot45 evidence below minimum mutation score")
    for term in score["require_zero"]:
        if ev[term] != 0:
            raise MutationCandidateProfileError(f"Lot45 required-zero term is nonzero: {term}")
    if ev["mutmut_run_exit_code"] != 0 or ev["mutmut_results_exit_code"] != 0:
        raise MutationCandidateProfileError("Lot45 mutation process status drift")


def _validate_mutation_semantics(profile: dict[str, Any], policy: dict[str, Any]) -> None:
    baseline = profile.get("baseline_tests")
    mutation = profile.get("mutation")
    if not isinstance(baseline, list) or not isinstance(mutation, dict):
        raise MutationCandidateProfileError("Lot45 baseline/mutation semantics missing")
    if baseline != EXPECTED_BASELINE_TESTS or baseline != mutation.get("tests"):
        raise MutationCandidateProfileError("Lot45 baseline and mutation test set identity drift")
    targets = mutation.get("targets")
    if not isinstance(targets, list) or len(targets) != 3:
        raise MutationCandidateProfileError("Lot45 target set drift")
    if len(targets) > policy["bounds"]["max_mutation_targets_per_profile"]:
        raise MutationCandidateProfileError("Lot45 target count exceeds policy")
    for path in [*baseline, *targets]:
        _safe_path(path)
    expected_targets = [
        "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine.py",
        "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_models.py",
        "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_validation.py",
    ]
    if targets != expected_targets:
        raise MutationCandidateProfileError("Lot45 mutation target identity drift")
    if mutation.get("workspace_root") != ".tmp-lot45-mutants":
        raise MutationCandidateProfileError("Lot45 isolated workspace drift")
    expected_exclusion = (
        "not test_reference_frozen_lot44_builds_expected_order_flow "
        "and not test_artifacts_reject_nonexistent_and_mismatched_code_commits "
        "and not test_real_code_commit_validation_invokes_executable_source_guard"
    )
    if mutation.get("pytest_exclusion_expression") != expected_exclusion:
        raise MutationCandidateProfileError("Lot45 pytest exclusion expression drift")
    settings = mutation.get("settings")
    if settings != {
        "mutate_only_covered_lines": True,
        "timeout_factor": 8.0,
        "max_children": 1,
        "python_hash_seed": "0",
        "do_not_mutate_patterns": ["raise \\w+", "logger\\.\\w+"],
    }:
        raise MutationCandidateProfileError("Lot45 mutation setting drift")
    copies = mutation.get("copy_semantics")
    if not isinstance(copies, dict):
        raise MutationCandidateProfileError("Lot45 workspace copy semantics missing")
    if copies.get("exact_files") != ["src/crypto_quant_bot/__init__.py"]:
        raise MutationCandidateProfileError("Lot45 exact-copy file drift")
    if copies.get("whole_directories") != ["src/crypto_quant_bot/data_governance/"]:
        raise MutationCandidateProfileError("Lot45 data-governance copy drift")
    if copies.get("static_directories") != ["config/", "data/audit/", "contracts/", "tests/fixtures/"]:
        raise MutationCandidateProfileError("Lot45 static-copy directory drift")
    other = copies.get("microstructure_python_except_targets")
    if other != EXPECTED_MICROSTRUCTURE_COPY:
        raise MutationCandidateProfileError("Lot45 observed microstructure dependency identity/order drift")
    if len(other) != len(set(other)):
        raise MutationCandidateProfileError("Lot45 observed microstructure dependency duplicates")
    for path in other:
        _safe_path(path)
        if path in targets or not path.startswith("src/crypto_quant_bot/microstructure/"):
            raise MutationCandidateProfileError("Lot45 microstructure dependency binding invalid")


def validate_registry(policy: dict[str, Any], registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != 1 or registry.get("registry_kind") != "mutation_candidate_profiles_v1":
        raise MutationCandidateProfileError("invalid candidate registry identity")
    profiles = registry.get("profiles")
    if not isinstance(profiles, list) or len(profiles) != 1:
        raise MutationCandidateProfileError("WU13 requires exactly one Lot45 candidate profile")
    if len(profiles) > policy["bounds"]["max_profiles"]:
        raise MutationCandidateProfileError("candidate profile count exceeds policy")
    profile = profiles[0]
    if not isinstance(profile, dict) or profile.get("id") != EXPECTED_ID:
        raise MutationCandidateProfileError("Lot45 candidate profile identity drift")
    if profile.get("profile_version") != 1:
        raise MutationCandidateProfileError("Lot45 candidate profile version drift")
    if profile.get("lifecycle") != "READ_ONLY_QUALIFIED_NOT_ADOPTED":
        raise MutationCandidateProfileError("Lot45 candidate lifecycle drift")
    for flag in policy["required_false_flags"]:
        if profile.get(flag) is not False:
            raise MutationCandidateProfileError(f"Lot45 candidate {flag} must remain false")
    _walk_forbidden(profile, set(policy["forbidden_profile_keys"]))
    _validate_selectors(profile, policy)
    _validate_candidate_binding(profile)
    _validate_source_binding(profile, policy)
    _validate_mutation_semantics(profile, policy)
    _validate_score(profile)


def validate_active_registry_isolation(active: dict[str, Any]) -> None:
    profiles = active.get("profiles")
    if not isinstance(profiles, list):
        raise MutationCandidateProfileError("active mutation registry invalid")
    active_ids = {item.get("id") for item in profiles if isinstance(item, dict)}
    if EXPECTED_ID in active_ids:
        raise MutationCandidateProfileError("Lot45 candidate leaked into active mutation registry")


def validate_all(
    policy: dict[str, Any],
    registry: dict[str, Any],
    active_registry: dict[str, Any],
) -> None:
    validate_policy(policy)
    validate_registry(policy, registry)
    validate_active_registry_isolation(active_registry)


def main() -> int:
    try:
        policy = _load(POLICY_PATH)
        registry = _load(REGISTRY_PATH)
        active = _load(ACTIVE_REGISTRY_PATH)
        validate_all(policy, registry, active)
    except MutationCandidateProfileError as exc:
        print(f"MUTATION_CANDIDATE_PROFILE_INVALID: {exc}", file=sys.stderr)
        return 1
    print("MUTATION_CANDIDATE_PROFILE_VALID id=LOT45_ORDER_FLOW_DELTA_CVD lifecycle=READ_ONLY_QUALIFIED_NOT_ADOPTED execution_allowed=false score=80.54")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
