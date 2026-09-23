#!/usr/bin/env python3
"""Adversarial qualification for ENG-04.3 SAST controls."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_sast_controls.py"
    spec = importlib.util.spec_from_file_location("sast_controls_selftest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"SAST-control negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    workflow = mod.WORKFLOW_PATH.read_text(encoding="utf-8")
    quality = mod.QUALITY_PATH.read_text(encoding="utf-8")
    mod.validate_policy(policy)
    mod.validate_existing_bandit(policy, quality)
    mod.validate_workflow(policy, workflow)

    floating = workflow.replace(
        policy["deep_sast"]["commit"],
        "v4",
    )
    _expect(mod.SastControlError, lambda: mod.validate_workflow(policy, floating), "floating CodeQL ref")

    upload = workflow.replace("upload: never", "upload: always")
    _expect(mod.SastControlError, lambda: mod.validate_workflow(policy, upload), "SARIF upload enabled")

    write_perm = workflow.replace("contents: read", "contents: write")
    _expect(mod.SastControlError, lambda: mod.validate_workflow(policy, write_perm), "write permission")

    no_queries = workflow.replace("queries: security-extended", "queries: default")
    _expect(mod.SastControlError, lambda: mod.validate_workflow(policy, no_queries), "security suite weakened")

    broad_root = workflow.replace("source-root: src/crypto_quant_bot", "source-root: .")
    _expect(mod.SastControlError, lambda: mod.validate_workflow(policy, broad_root), "source root broadened")

    no_gate = workflow.replace(
        'raise SystemExit("CODEQL_FINDINGS_DETECTED")',
        'print("CODEQL_FINDINGS_DETECTED")',
    )
    _expect(mod.SastControlError, lambda: mod.validate_workflow(policy, no_gate), "finding gate removed")

    no_src_path = workflow.replace('      - "src/**/*.py"\n', "", 2)
    _expect(mod.SastControlError, lambda: mod.validate_workflow(policy, no_src_path), "source path filter removed")

    weak_bandit = quality.replace("bandit -q -r src -ll", "bandit -q -r src -lll")
    _expect(mod.SastControlError, lambda: mod.validate_existing_bandit(policy, weak_bandit), "Bandit threshold weakened")

    paid = copy.deepcopy(policy)
    paid["cost_policy"]["paid_api_required"] = True
    _expect(mod.SastControlError, lambda: mod.validate_policy(paid), "paid API")

    bad_bundle = copy.deepcopy(policy)
    bad_bundle["deep_sast"]["default_bundle"] = "latest"
    _expect(mod.SastControlError, lambda: mod.validate_policy(bad_bundle), "floating CodeQL bundle")

    print("SAST_CONTROLS_SELFTEST_PASS probes=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
