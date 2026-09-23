#!/usr/bin/env python3
"""Adversarial qualification for ENG-04.1 secret-control configuration."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_secret_controls.py"
    spec = importlib.util.spec_from_file_location("secret_controls_selftest", path)
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
    raise AssertionError(f"secret-control negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    workflow = (ROOT / policy["workflow_path"]).read_text(encoding="utf-8")
    config = (ROOT / ".gitleaks.toml").read_text(encoding="utf-8")
    mod.validate_documents(policy, workflow, config)

    floating_checkout = workflow.replace(
        "actions/checkout@" + policy["toolchain"]["checkout_action_sha"],
        "actions/checkout@v7",
    )
    _expect(
        mod.SecretControlError,
        lambda: mod.validate_workflow(policy, floating_checkout),
        "floating checkout action",
    )

    floating_go = workflow.replace(
        "actions/setup-go@" + policy["toolchain"]["setup_go_action_sha"],
        "actions/setup-go@v7",
    )
    _expect(
        mod.SecretControlError,
        lambda: mod.validate_workflow(policy, floating_go),
        "floating setup-go action",
    )

    no_redact = workflow.replace("--redact=100", "--redact=0")
    _expect(mod.SecretControlError, lambda: mod.validate_workflow(policy, no_redact), "redaction off")

    paid = workflow + "\n# GITLEAKS_LICENSE\n"
    _expect(mod.SecretControlError, lambda: mod.validate_workflow(policy, paid), "license dependency")

    writable = workflow.replace("contents: read", "contents: write")
    _expect(
        mod.SecretControlError,
        lambda: mod.validate_workflow(policy, writable),
        "write permission",
    )

    no_history = workflow.replace('"${GITLEAKS_BIN}" git', '"${GITLEAKS_BIN}" noop')
    _expect(
        mod.SecretControlError,
        lambda: mod.validate_workflow(policy, no_history),
        "history scan removed",
    )

    literal = workflow.replace('"gh" + "p_"', '"ghp_" + ""')
    _expect(
        mod.SecretControlError,
        lambda: mod.validate_workflow(policy, literal),
        "committed synthetic secret literal",
    )

    allowlisted = config + '\n[[allowlists]]\npaths = ["""tests/.*"""]\n'
    _expect(mod.SecretControlError, lambda: mod.validate_config(allowlisted), "broad allowlist")

    bad_pin = copy.deepcopy(policy)
    bad_pin["gitleaks"]["commit"] = "0" * 40
    _expect(mod.SecretControlError, lambda: mod.validate_policy(bad_pin), "Gitleaks commit drift")

    paid_policy = copy.deepcopy(policy)
    paid_policy["cost_policy"]["paid_saas_required"] = True
    _expect(mod.SecretControlError, lambda: mod.validate_policy(paid_policy), "paid SaaS")

    print("SECRET_CONTROLS_SELFTEST_PASS probes=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
