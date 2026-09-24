#!/usr/bin/env python3
"""Adversarial qualification for ENG-06.2 exact-head evidence binding."""

from __future__ import annotations

import copy
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts/governance/validate_certification_exact_head_binding.py"
    spec = importlib.util.spec_from_file_location("exact_head_binding_selftest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout.strip()


def _commit(root: Path, message: str) -> str:
    _run(root, "add", "-A")
    _run(root, "commit", "-m", message)
    return _run(root, "rev-parse", "HEAD")


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"exact-head negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy, lifecycle, evidence, proof, assurance = mod._load_policies()
    mod.validate_policy(policy, lifecycle, evidence, proof, assurance)

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        _run(root, "init", "-q")
        _run(root, "config", "user.name", "Exact Head Selftest")
        _run(root, "config", "user.email", "selftest@example.invalid")
        (root / "input.txt").write_text("alpha\n", encoding="utf-8")
        (root / "policy.json").write_text('{"mode":"safe"}\n', encoding="utf-8")
        head1 = _commit(root, "initial")

        candidate1 = {
            "candidate_id": "ENG06-EXACT-1",
            "head_sha": head1,
            "risk_class": "R2",
        }
        context = {
            "awu_id": "ENG-06.2-WU01",
            "scope_base_sha": "1" * 40,
            "required_t3": [],
            "required_t4": [],
        }
        binding1 = mod.build_input_binding(
            candidate1,
            ["input.txt", "policy.json"],
            context,
            policy,
            assurance,
            root=root,
        )
        binding1_repeat = mod.build_input_binding(
            candidate1,
            ["policy.json", "input.txt"],
            context,
            policy,
            assurance,
            root=root,
        )
        assert binding1["input_identity_sha256"] == binding1_repeat["input_identity_sha256"]

        runs = [
            {
                "run_id": 101,
                "workflow": "Engineering Bootstrap",
                "head_sha": head1,
                "conclusion": "success",
            },
            {
                "run_id": 102,
                "workflow": "Security Secrets",
                "head_sha": head1,
                "conclusion": "success",
            },
        ]
        bundle1 = mod.build_evidence_bundle(binding1, runs, policy)
        mod.validate_evidence_bundle(bundle1, binding1, policy)

        wrong_candidate = dict(candidate1)
        wrong_candidate["head_sha"] = "2" * 40
        _expect(
            mod.ExactHeadBindingError,
            lambda: mod.build_input_binding(
                wrong_candidate, ["input.txt"], context, policy, assurance, root=root
            ),
            "candidate head mismatch",
        )

        (root / "input.txt").write_text("dirty\n", encoding="utf-8")
        _expect(
            mod.ExactHeadBindingError,
            lambda: mod.build_input_binding(
                candidate1, ["input.txt"], context, policy, assurance, root=root
            ),
            "dirty bound path",
        )
        _run(root, "checkout", "--", "input.txt")

        bad_head_runs = copy.deepcopy(runs)
        bad_head_runs[0]["head_sha"] = "3" * 40
        _expect(
            mod.ExactHeadBindingError,
            lambda: mod.build_evidence_bundle(binding1, bad_head_runs, policy),
            "CI evidence wrong head",
        )

        failed_runs = copy.deepcopy(runs)
        failed_runs[0]["conclusion"] = "failure"
        _expect(
            mod.ExactHeadBindingError,
            lambda: mod.build_evidence_bundle(binding1, failed_runs, policy),
            "CI evidence failure",
        )

        duplicate_runs = [copy.deepcopy(runs[0]), copy.deepcopy(runs[0])]
        _expect(
            mod.ExactHeadBindingError,
            lambda: mod.build_evidence_bundle(binding1, duplicate_runs, policy),
            "duplicate run id",
        )

        _expect(
            mod.ExactHeadBindingError,
            lambda: mod.build_input_binding(
                candidate1, ["../escape"], context, policy, assurance, root=root
            ),
            "path traversal",
        )

        (root / "untracked.txt").write_text("not committed\n", encoding="utf-8")
        _expect(
            mod.ExactHeadBindingError,
            lambda: mod.build_input_binding(
                candidate1, ["untracked.txt"], context, policy, assurance, root=root
            ),
            "untracked path",
        )

        if hasattr(os, "symlink"):
            try:
                os.symlink("input.txt", root / "link.txt")
                head_link = _commit(root, "add symlink")
            except OSError:
                head_link = ""
            if head_link:
                symlink_candidate = dict(candidate1)
                symlink_candidate["candidate_id"] = "ENG06-EXACT-SYMLINK"
                symlink_candidate["head_sha"] = head_link
                _expect(
                    mod.ExactHeadBindingError,
                    lambda: mod.build_input_binding(
                        symlink_candidate,
                        ["link.txt"],
                        context,
                        policy,
                        assurance,
                        root=root,
                    ),
                    "symlink binding",
                )
                _run(root, "rm", "-q", "link.txt")
                _commit(root, "remove symlink")

        (root / "input.txt").write_text("beta\n", encoding="utf-8")
        head2 = _commit(root, "change input")
        candidate2 = {
            "candidate_id": "ENG06-EXACT-2",
            "head_sha": head2,
            "risk_class": "R2",
        }
        binding2 = mod.build_input_binding(
            candidate2,
            ["input.txt", "policy.json"],
            context,
            policy,
            assurance,
            root=root,
        )
        assert binding2["input_identity_sha256"] != binding1["input_identity_sha256"]

        changed_run = copy.deepcopy(runs)
        for item in changed_run:
            item["head_sha"] = head1
        changed_run[0]["run_id"] = 999
        bundle_changed_run = mod.build_evidence_bundle(binding1, changed_run, policy)
        assert bundle_changed_run["bundle_identity_sha256"] != bundle1["bundle_identity_sha256"]

        tampered = copy.deepcopy(bundle1)
        tampered["material"]["ci_runs"][0]["workflow"] = "Tampered"
        _expect(
            mod.ExactHeadBindingError,
            lambda: mod.validate_evidence_bundle(tampered, binding1, policy),
            "bundle tamper",
        )

        r3_candidate = dict(candidate2)
        r3_candidate["candidate_id"] = "ENG06-R3"
        r3_candidate["risk_class"] = "R3"
        _expect(
            mod.ExactHeadBindingError,
            lambda: mod.build_input_binding(
                r3_candidate,
                ["input.txt"],
                context,
                policy,
                assurance,
                root=root,
            ),
            "R3 requirement floor missing",
        )

    assert "T4" in proof["forbidden_tiers"]
    assert "EXACT_HEAD_CERTIFICATION" in proof["forbidden_subject_ids"]
    print("CERTIFICATION_EXACT_HEAD_SELFTEST_PASS probes=12")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
