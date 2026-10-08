#!/usr/bin/env python3
"""Adversarial qualification for proof-reuse effectiveness measurement."""

from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _must_execute(
    measure: ModuleType,
    engine: ModuleType,
    proof_policy: dict[str, Any],
    material: dict[str, Any],
    candidate: dict[str, Any],
    expected_status: str,
) -> None:
    calls = {"count": 0}

    def executor() -> str:
        calls["count"] += 1
        return "PASS"

    event, _proof = measure.process_request(
        engine=engine,
        proof_policy=proof_policy,
        material=material,
        candidate=candidate,
        executor=executor,
    )
    assert event["reuse_status"] == expected_status
    assert event["executor_called"] is True
    assert calls["count"] == 1


def main() -> int:
    measure = _module(
        "proof_reuse_effectiveness_selftest_measure",
        ROOT / "scripts" / "governance" / "measure_proof_reuse_effectiveness.py",
    )
    engine = _module(
        "proof_reuse_effectiveness_selftest_engine",
        ROOT / "scripts" / "governance" / "proof_reuse.py",
    )
    effectiveness_policy = measure._json(measure.POLICY_PATH)
    proof_policy = measure._json(measure.PROOF_POLICY_PATH)
    measure.validate_policy(effectiveness_policy)
    engine.validate_policy(proof_policy)
    probes = 2

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "input.txt").write_text("alpha\n", encoding="utf-8")
        (root / "policy.json").write_text('{"version":1}\n', encoding="utf-8")
        (root / "implementation.py").write_text("VALUE = 1\n", encoding="utf-8")

        base = measure._material(engine, proof_policy, root)
        candidate = engine.issue_proof(base, result="PASS")

        exact_calls = {"count": 0}

        def exact_executor() -> str:
            exact_calls["count"] += 1
            return "PASS"

        exact_event, _ = measure.process_request(
            engine=engine,
            proof_policy=proof_policy,
            material=base,
            candidate=candidate,
            executor=exact_executor,
        )
        assert exact_event["reuse_status"] == "HIT"
        assert exact_event["executor_called"] is False
        assert exact_calls["count"] == 0
        probes += 3

        (root / "input.txt").write_text("beta\n", encoding="utf-8")
        input_changed = measure._material(engine, proof_policy, root)
        _must_execute(measure, engine, proof_policy, input_changed, candidate, "MISS")
        probes += 1
        (root / "input.txt").write_text("alpha\n", encoding="utf-8")

        (root / "policy.json").write_text('{"version":2}\n', encoding="utf-8")
        policy_changed = measure._material(engine, proof_policy, root)
        _must_execute(measure, engine, proof_policy, policy_changed, candidate, "MISS")
        probes += 1
        (root / "policy.json").write_text('{"version":1}\n', encoding="utf-8")

        (root / "implementation.py").write_text("VALUE = 2\n", encoding="utf-8")
        implementation_changed = measure._material(engine, proof_policy, root)
        _must_execute(
            measure, engine, proof_policy, implementation_changed, candidate, "MISS"
        )
        probes += 1
        (root / "implementation.py").write_text("VALUE = 1\n", encoding="utf-8")

        parameter_changed = measure._material(
            engine,
            proof_policy,
            root,
            parameters={"mode": "different"},
        )
        _must_execute(measure, engine, proof_policy, parameter_changed, candidate, "MISS")
        probes += 1

        environment_changed = measure._material(
            engine,
            proof_policy,
            root,
            environment={
                "python_implementation": "CPython",
                "python_version": "3.12.0",
                "platform": "linux",
                "machine": "x86_64",
            },
        )
        _must_execute(measure, engine, proof_policy, environment_changed, candidate, "MISS")
        probes += 1

        fail_proof = engine.issue_proof(base, result="FAIL")
        _must_execute(measure, engine, proof_policy, base, fail_proof, "REJECTED")
        probes += 1

        tampered = copy.deepcopy(candidate)
        tampered["material"]["parameters"]["mode"] = "tampered"
        _must_execute(measure, engine, proof_policy, base, tampered, "REJECTED")
        probes += 1

        metadata_only = copy.deepcopy(candidate)
        metadata_only["metadata"] = {
            "measurement_only": True,
            "observed_head": "f" * 40,
            "created_at_utc": "2099-01-01T00:00:00Z",
        }
        metadata_event, _ = measure.process_request(
            engine=engine,
            proof_policy=proof_policy,
            material=base,
            candidate=metadata_only,
            executor=lambda: "FAIL",
        )
        assert metadata_event["reuse_status"] == "HIT"
        assert metadata_event["executor_called"] is False
        probes += 2

        for tier, subject in (
            ("T0", "SELFTEST_ENTRYPOINT_CHECK"),
            ("T3", "SELFTEST_ENTRYPOINT_CHECK"),
            ("T4", "EXACT_HEAD_CERTIFICATION"),
        ):
            assert engine.subject_reusable(tier, subject, proof_policy) is False
            probes += 1

        generic = measure.measure_exact_pair(
            engine=engine,
            proof_policy=proof_policy,
            material=base,
            executor=lambda: "PASS",
            effectiveness_policy=effectiveness_policy,
        )
        assert generic["actual_executions"] == 1
        assert generic["avoided_executions"] == 1
        assert generic["saved_elapsed_ms"] is None
        probes += 3

    print(f"SELFTEST_PROOF_REUSE_EFFECTIVENESS_PASS probes={probes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
