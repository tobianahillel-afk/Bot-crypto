#!/usr/bin/env python3
"""Adversarial qualification for GitHub Actions supply-chain inventory."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "audit_action_supply_chain.py"
    spec = importlib.util.spec_from_file_location("action_supply_chain_selftest", path)
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
    raise AssertionError(f"supply-chain negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)

    pinned = mod.classify_uses(
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        policy,
    )
    assert pinned["classification"] == "REMOTE_PINNED_SHA"
    assert pinned["owner"] == "actions" and pinned["repo"] == "checkout"

    for floating in (
        "actions/checkout@v4",
        "owner/action@main",
        "owner/action@master",
        "owner/action@v1.2.3",
    ):
        assert mod.classify_uses(floating, policy)["classification"] == "REMOTE_FLOATING_REF"

    assert mod.classify_uses("./.github/actions/local", policy)["classification"] == "LOCAL_ACTION_OR_WORKFLOW"
    assert mod.classify_uses("docker://alpine:3.20", policy)["classification"] == "DOCKER_IMAGE"
    assert mod.classify_uses("owner/repo/path@${{ github.ref }}", policy)["classification"] == "DYNAMIC_EXPRESSION"
    assert mod.classify_uses("not-a-valid-action", policy)["classification"] == "MALFORMED_USES"

    quoted = mod.classify_uses(
        '"actions/checkout@11d5960a326750d5838078e36cf38b85af677262" # pinned',
        policy,
    )
    assert quoted["classification"] == "REMOTE_PINNED_SHA"

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        workflow = root / ".github" / "workflows" / "probe.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text(
            """name: Probe
jobs:
  reusable:
    uses: owner/reusable/.github/workflows/test.yml@v1
  test:
    steps:
      - uses: ./local
      - uses: docker://alpine:3.20
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
      # - uses: ignored/comment@main
""",
            encoding="utf-8",
        )
        records = mod.parse_file(workflow, policy, root=root)
        assert len(records) == 4
        assert [record.classification for record in records] == [
            "REMOTE_FLOATING_REF",
            "LOCAL_ACTION_OR_WORKFLOW",
            "DOCKER_IMAGE",
            "REMOTE_PINNED_SHA",
        ]
        result = mod.audit([workflow], policy, root=root)
        blocked = mod.changed_gate(result)
        assert len(blocked) == 1
        assert blocked[0]["classification"] == "REMOTE_FLOATING_REF"

        safe = root / ".github" / "workflows" / "safe.yml"
        safe.write_text(
            "steps:\n  - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065\n",
            encoding="utf-8",
        )
        assert mod.changed_gate(mod.audit([safe], policy, root=root)) == []

    broken = dict(policy)
    broken["immutable_remote_ref_regex"] = "^v\\d+$"
    _expect(
        mod.ActionSupplyChainError,
        lambda: mod.validate_policy(broken),
        "mutable immutable-ref policy",
    )

    print("ACTION_SUPPLY_CHAIN_SELFTEST_PASS probes=12")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
