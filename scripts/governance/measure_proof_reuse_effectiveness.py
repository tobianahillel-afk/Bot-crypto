#!/usr/bin/env python3
"""Measure exact-input proof-reuse effectiveness without integrating a production cache."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "proof_reuse_effectiveness_policy_v1.json"
PROOF_ENGINE_PATH = ROOT / "scripts" / "governance" / "proof_reuse.py"
PROOF_POLICY_PATH = ROOT / "config" / "governance" / "proof_reuse_policy_v1.json"


class ProofReuseEffectivenessError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProofReuseEffectivenessError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProofReuseEffectivenessError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ProofReuseEffectivenessError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise ProofReuseEffectivenessError("unsupported effectiveness policy version")
    if policy.get("policy_kind") != "proof_reuse_effectiveness_policy_v1":
        raise ProofReuseEffectivenessError("invalid effectiveness policy kind")
    if policy.get("semantics") != "MEASURE_EXECUTOR_SUPPRESSION_WITH_EXACT_INPUT_PROOFS":
        raise ProofReuseEffectivenessError("effectiveness semantics drift")
    if policy.get("certified_engine") != "scripts/governance/proof_reuse.py":
        raise ProofReuseEffectivenessError("certified proof engine path drift")
    if policy.get("certified_policy") != "config/governance/proof_reuse_policy_v1.json":
        raise ProofReuseEffectivenessError("certified proof policy path drift")
    if policy.get("measurement_subject") != {
        "tier": "T1",
        "subject_id": "SELFTEST_ENTRYPOINT_CHECK",
    }:
        raise ProofReuseEffectivenessError("measurement subject drift")
    scenario = policy.get("exact_match_scenario")
    if scenario != {
        "request_count": 2,
        "baseline_executions": 2,
        "expected_actual_executions": 1,
        "minimum_avoided_executions": 1,
        "expected_reuse_hits": 1,
    }:
        raise ProofReuseEffectivenessError("exact-match scenario drift")
    if policy.get("forbidden_reuse_tiers") != ["T0", "T3", "T4"]:
        raise ProofReuseEffectivenessError("forbidden reuse tier floor drift")
    costs = policy.get("cost_policy")
    if not isinstance(costs, dict) or any(costs.values()):
        raise ProofReuseEffectivenessError("effectiveness measurement must remain zero-cost")
    claims = policy.get("claims_policy")
    if not isinstance(claims, dict) or claims.get("saved_elapsed_ms") != "FORBIDDEN_NOT_MEASURED":
        raise ProofReuseEffectivenessError("saved-time claim must remain forbidden")


def _evaluate_candidate(
    engine: ModuleType,
    candidate: dict[str, Any] | None,
    material: dict[str, Any],
    proof_policy: dict[str, Any],
) -> tuple[str, dict[str, Any] | None, float]:
    if candidate is None:
        return "NO_CANDIDATE", None, 0.0
    started = time.perf_counter()
    try:
        decision = engine.evaluate_reuse(candidate, material, proof_policy)
    except engine.ProofReuseError:
        elapsed = round((time.perf_counter() - started) * 1000, 6)
        return "REJECTED", None, elapsed
    elapsed = round((time.perf_counter() - started) * 1000, 6)
    return ("HIT" if decision["reusable"] else "MISS"), decision, elapsed


def process_request(
    *,
    engine: ModuleType,
    proof_policy: dict[str, Any],
    material: dict[str, Any],
    candidate: dict[str, Any] | None,
    executor: Callable[[], str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    reuse_status, decision, lookup_ms = _evaluate_candidate(
        engine, candidate, material, proof_policy
    )
    if reuse_status == "HIT":
        return (
            {
                "reuse_status": "HIT",
                "executor_called": False,
                "lookup_elapsed_ms": lookup_ms,
                "executor_elapsed_ms": 0.0,
                "reuse_reason": decision["reason"],
            },
            candidate,
        )

    started = time.perf_counter()
    result = executor()
    executor_ms = round((time.perf_counter() - started) * 1000, 6)
    if result not in {"PASS", "FAIL"}:
        raise ProofReuseEffectivenessError("executor must return PASS or FAIL")
    proof = engine.issue_proof(
        material,
        result=result,
        metadata={"measurement_only": True},
    )
    return (
        {
            "reuse_status": reuse_status,
            "executor_called": True,
            "lookup_elapsed_ms": lookup_ms,
            "executor_elapsed_ms": executor_ms,
            "reuse_reason": None if decision is None else decision.get("reason"),
        },
        proof,
    )


def measure_exact_pair(
    *,
    engine: ModuleType,
    proof_policy: dict[str, Any],
    material: dict[str, Any],
    executor: Callable[[], str],
    effectiveness_policy: dict[str, Any],
) -> dict[str, Any]:
    scenario = effectiveness_policy["exact_match_scenario"]
    events: list[dict[str, Any]] = []
    candidate: dict[str, Any] | None = None
    for _index in range(scenario["request_count"]):
        event, candidate = process_request(
            engine=engine,
            proof_policy=proof_policy,
            material=material,
            candidate=candidate,
            executor=executor,
        )
        events.append(event)

    actual = sum(1 for event in events if event["executor_called"])
    hits = sum(1 for event in events if event["reuse_status"] == "HIT")
    misses = sum(1 for event in events if event["reuse_status"] in {"NO_CANDIDATE", "MISS"})
    rejections = sum(1 for event in events if event["reuse_status"] == "REJECTED")
    candidate_lookups = sum(1 for event in events if event["reuse_status"] != "NO_CANDIDATE")
    avoided = scenario["baseline_executions"] - actual
    result = {
        "measurement_version": 1,
        "subject": dict(material["subject"]),
        "request_count": len(events),
        "baseline_executions": scenario["baseline_executions"],
        "actual_executions": actual,
        "avoided_executions": avoided,
        "reuse_hits": hits,
        "reuse_misses": misses,
        "reuse_rejections": rejections,
        "request_reuse_hit_rate": round(hits / len(events), 6),
        "candidate_hit_rate": round(hits / candidate_lookups, 6) if candidate_lookups else 0.0,
        "lookup_elapsed_ms": round(sum(event["lookup_elapsed_ms"] for event in events), 6),
        "executor_elapsed_ms": round(sum(event["executor_elapsed_ms"] for event in events), 6),
        "saved_elapsed_ms": None,
        "network_used": False,
        "external_storage_used": False,
        "events": events,
    }
    if actual != scenario["expected_actual_executions"]:
        raise ProofReuseEffectivenessError(
            f"exact-match executor count drift: {actual} != {scenario['expected_actual_executions']}"
        )
    if hits != scenario["expected_reuse_hits"]:
        raise ProofReuseEffectivenessError(
            f"exact-match reuse hit drift: {hits} != {scenario['expected_reuse_hits']}"
        )
    if avoided < scenario["minimum_avoided_executions"]:
        raise ProofReuseEffectivenessError("proof reuse did not avoid required redundant execution")
    if avoided != result["baseline_executions"] - result["actual_executions"]:
        raise ProofReuseEffectivenessError("avoided execution accounting drift")
    if result["saved_elapsed_ms"] is not None:
        raise ProofReuseEffectivenessError("unmeasured saved wall-clock time was claimed")
    return result


def _material(
    engine: ModuleType,
    proof_policy: dict[str, Any],
    root: Path,
    *,
    parameters: dict[str, Any] | None = None,
    environment: dict[str, str] | None = None,
    tier: str = "T1",
    subject_id: str = "SELFTEST_ENTRYPOINT_CHECK",
) -> dict[str, Any]:
    return engine.build_material(
        tier=tier,
        subject_id=subject_id,
        input_paths=["input.txt"],
        policy_paths=["policy.json"],
        implementation_paths=["implementation.py"],
        parameters=parameters or {"mode": "measurement"},
        environment=environment or {
            "python_implementation": "CPython",
            "python_version": "3.11.9",
            "platform": "linux",
            "machine": "x86_64",
        },
        policy=proof_policy,
        root=root,
    )


def _self_check() -> dict[str, Any]:
    effectiveness_policy = _json(POLICY_PATH)
    validate_policy(effectiveness_policy)
    engine = _module("proof_reuse_effectiveness_engine", PROOF_ENGINE_PATH)
    proof_policy = _json(PROOF_POLICY_PATH)
    engine.validate_policy(proof_policy)
    probes = 1

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "input.txt").write_text("alpha\n", encoding="utf-8")
        (root / "policy.json").write_text('{"version":1}\n', encoding="utf-8")
        (root / "implementation.py").write_text("VALUE = 1\n", encoding="utf-8")

        calls = {"count": 0}

        def executor() -> str:
            calls["count"] += 1
            return "PASS"

        material = _material(engine, proof_policy, root)
        measured = measure_exact_pair(
            engine=engine,
            proof_policy=proof_policy,
            material=material,
            executor=executor,
            effectiveness_policy=effectiveness_policy,
        )
        assert calls["count"] == 1
        assert measured["baseline_executions"] == 2
        assert measured["actual_executions"] == 1
        assert measured["avoided_executions"] == 1
        assert measured["reuse_hits"] == 1
        assert measured["request_reuse_hit_rate"] == 0.5
        assert measured["candidate_hit_rate"] == 1.0
        assert measured["saved_elapsed_ms"] is None
        probes += 8

        seed_event, pass_proof = process_request(
            engine=engine,
            proof_policy=proof_policy,
            material=material,
            candidate=None,
            executor=lambda: "PASS",
        )
        assert seed_event["executor_called"] is True

        (root / "input.txt").write_text("beta\n", encoding="utf-8")
        changed = _material(engine, proof_policy, root)
        changed_calls = {"count": 0}

        def changed_executor() -> str:
            changed_calls["count"] += 1
            return "PASS"

        miss, _replacement = process_request(
            engine=engine,
            proof_policy=proof_policy,
            material=changed,
            candidate=pass_proof,
            executor=changed_executor,
        )
        assert miss["reuse_status"] == "MISS"
        assert miss["executor_called"] is True
        assert changed_calls["count"] == 1
        probes += 3

        parameter_changed = _material(
            engine,
            proof_policy,
            root,
            parameters={"mode": "different"},
        )
        parameter_calls = {"count": 0}

        def parameter_executor() -> str:
            parameter_calls["count"] += 1
            return "PASS"

        parameter_miss, _ = process_request(
            engine=engine,
            proof_policy=proof_policy,
            material=parameter_changed,
            candidate=pass_proof,
            executor=parameter_executor,
        )
        assert parameter_miss["executor_called"] is True
        assert parameter_calls["count"] == 1
        probes += 2

        fail_proof = engine.issue_proof(changed, result="FAIL")
        rejected_calls = {"count": 0}

        def rejected_executor() -> str:
            rejected_calls["count"] += 1
            return "PASS"

        rejected, _ = process_request(
            engine=engine,
            proof_policy=proof_policy,
            material=changed,
            candidate=fail_proof,
            executor=rejected_executor,
        )
        assert rejected["reuse_status"] == "REJECTED"
        assert rejected["executor_called"] is True
        assert rejected_calls["count"] == 1
        probes += 3

        try:
            _material(
                engine,
                proof_policy,
                root,
                tier="T4",
                subject_id="EXACT_HEAD_CERTIFICATION",
            )
        except engine.ProofReuseError:
            probes += 1
        else:
            raise ProofReuseEffectivenessError("T4 exact-head proof unexpectedly reusable")

    summary = {
        "status": "PASS",
        "probes": probes,
        "exact_match": measured,
    }
    return summary



def repository_qualification() -> dict[str, Any]:
    effectiveness_policy = _json(POLICY_PATH)
    validate_policy(effectiveness_policy)
    engine = _module("proof_reuse_repository_engine", PROOF_ENGINE_PATH)
    proof_policy = _json(PROOF_POLICY_PATH)
    engine.validate_policy(proof_policy)

    active = _module(
        "proof_reuse_repository_active",
        ROOT / "scripts" / "governance" / "resolve_active_awu.py",
    )
    t0 = _module(
        "proof_reuse_repository_t0",
        ROOT / "scripts" / "governance" / "run_t0.py",
    )
    t1 = _module(
        "proof_reuse_repository_t1",
        ROOT / "scripts" / "governance" / "run_t1.py",
    )
    try:
        awu_path, awu, _evidence = active.resolve_active_awu()
    except active.ActiveAwuError as exc:
        raise ProofReuseEffectivenessError(str(exc)) from exc

    if awu.get("id") != "ENG-08.3-WU02":
        raise ProofReuseEffectivenessError(
            f"repository qualification requires ENG-08.3-WU02, got {awu.get('id')!r}"
        )
    base = awu.get("scope", {}).get("scope_base_sha")
    if not isinstance(base, str) or len(base) != 40:
        raise ProofReuseEffectivenessError("active AWU scope base is invalid")

    changes = t0.changed_files(base)
    changed_selftests = sorted(
        change.path
        for change in changes
        if not change.status.startswith("D")
        and change.path.startswith("scripts/governance/selftest_")
        and change.path.endswith(".py")
    )
    expected_selftest = "scripts/governance/selftest_proof_reuse_effectiveness.py"
    if expected_selftest not in changed_selftests:
        raise ProofReuseEffectivenessError(
            "repository qualification requires the WU02 effectiveness selftest in the active diff"
        )

    awu_rel = awu_path.relative_to(ROOT).as_posix()
    input_paths = [
        "config/governance/project_state.json",
        awu_rel,
        *changed_selftests,
    ]
    policy_paths = [
        "config/governance/validation_t1_policy_v1.json",
        "config/governance/proof_reuse_policy_v1.json",
        "config/governance/proof_reuse_effectiveness_policy_v1.json",
        "config/governance/awu_complexity_policy_v1.json",
        "config/governance/awu_split_policy_v1.json",
        "config/governance/awu_risk_policy_v1.json",
        "config/governance/awu_context_policy_v1.json",
    ]
    implementation_paths = [
        "scripts/governance/run_t1.py",
        "scripts/governance/run_t0.py",
        "scripts/governance/resolve_active_awu.py",
        "scripts/governance/validate_agent_work_unit.py",
        "scripts/governance/validate_awu_complexity.py",
        "scripts/governance/validate_awu_split.py",
        "scripts/governance/validate_awu_risk.py",
        "scripts/governance/validate_awu_context.py",
    ]
    parameters = {
        "check_id": "SELFTEST_ENTRYPOINT_CHECK",
        "active_awu_id": awu["id"],
        "scope_base_sha": base,
        "changed_selftest_paths": changed_selftests,
    }
    material = engine.build_material(
        tier="T1",
        subject_id="SELFTEST_ENTRYPOINT_CHECK",
        input_paths=input_paths,
        policy_paths=policy_paths,
        implementation_paths=implementation_paths,
        parameters=parameters,
        environment=engine.current_environment(),
        policy=proof_policy,
        root=ROOT,
    )

    executor_details: list[dict[str, Any]] = []

    def executor() -> str:
        try:
            detail = t1.CHECKS["SELFTEST_ENTRYPOINT_CHECK"](base)
        except t1.T1Error as exc:
            raise ProofReuseEffectivenessError(
                f"real SELFTEST_ENTRYPOINT_CHECK failed: {exc}"
            ) from exc
        inspected = sorted(detail.get("inspected", []))
        if inspected != changed_selftests:
            raise ProofReuseEffectivenessError(
                f"real T1 inspected-set drift: {inspected} != {changed_selftests}"
            )
        executor_details.append(detail)
        return "PASS"

    measured = measure_exact_pair(
        engine=engine,
        proof_policy=proof_policy,
        material=material,
        executor=executor,
        effectiveness_policy=effectiveness_policy,
    )
    if len(executor_details) != 1:
        raise ProofReuseEffectivenessError(
            f"real T1 executor was called {len(executor_details)} times, expected exactly 1"
        )
    if expected_selftest not in executor_details[0].get("inspected", []):
        raise ProofReuseEffectivenessError("real T1 did not inspect the WU02 effectiveness selftest")
    if measured["events"][1]["reuse_reason"] != "EXACT_INPUT_MATCH":
        raise ProofReuseEffectivenessError("second real-subject request was not an exact-input hit")

    return {
        "qualification_version": 1,
        "qualification_kind": "REAL_T1_SELFTEST_ENTRYPOINT_CHECK",
        "active_awu": awu["id"],
        "scope_base_sha": base,
        "changed_selftest_paths": changed_selftests,
        "executor_inspected_paths": sorted(executor_details[0]["inspected"]),
        "proof_key": engine.proof_key(material),
        "binding_counts": {
            "inputs": len(input_paths),
            "policies": len(policy_paths),
            "implementations": len(implementation_paths),
        },
        "measurement": measured,
        "production_cache_integrated": False,
        "canonical_t1_suppressed": False,
        "network_used": False,
        "external_storage_used": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-check", action="store_true")
    group.add_argument("--repository-qualification", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_check:
            summary = _self_check()
            print(
                "PROOF_REUSE_EFFECTIVENESS_SELF_CHECK_PASS "
                f"probes={summary['probes']} "
                + json.dumps(summary["exact_match"], sort_keys=True, separators=(",", ":"))
            )
        else:
            qualification = repository_qualification()
            print(
                "PROOF_REUSE_REPOSITORY_QUALIFICATION_PASS "
                + json.dumps(qualification, sort_keys=True, separators=(",", ":"))
            )
    except (ProofReuseEffectivenessError, OSError, KeyError, AssertionError) as exc:
        print(f"PROOF_REUSE_EFFECTIVENESS_INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
