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
    registry = mod.load_pin_registry(policy)

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
        floating_record = next(
            record for record in result["records"]
            if record["classification"] == "REMOTE_FLOATING_REF"
        )
        changed = {floating_record["file"]: {floating_record["line"]}}
        blocked = mod.changed_gate(result, registry, changed)
        assert len(blocked) == 1
        assert blocked[0]["classification"] == "REMOTE_FLOATING_REF"

        conservative = mod.changed_gate(result, registry)
        assert len(conservative) == 2
        assert {item["blocked_reason"] for item in conservative} == {
            "REMOTE_FLOATING_REF",
            "UNAPPROVED_REMOTE_SHA",
        }

        assert mod.changed_gate(
            result,
            registry,
            {floating_record["file"]: {1}},
        ) == []

        safe = root / ".github" / "workflows" / "safe.yml"
        safe.write_text(
            "steps:\n  - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065\n",
            encoding="utf-8",
        )
        safe_result = mod.audit([safe], policy, root=root)
        safe_record = safe_result["records"][0]
        assert mod.changed_gate(
            safe_result,
            registry,
            {safe_record["file"]: {safe_record["line"]}},
        ) == []

        unknown = root / ".github" / "workflows" / "unknown.yml"
        unknown.write_text(
            "steps:\n  - uses: actions/checkout@0000000000000000000000000000000000000000\n",
            encoding="utf-8",
        )
        unknown_result = mod.audit([unknown], policy, root=root)
        unknown_record = unknown_result["records"][0]
        unknown_blocked = mod.changed_gate(
            unknown_result,
            registry,
            {unknown_record["file"]: {unknown_record["line"]}},
        )
        assert len(unknown_blocked) == 1
        assert unknown_blocked[0]["blocked_reason"] == "UNAPPROVED_REMOTE_SHA"


    diff_probe = """diff --git a/.github/workflows/probe.yml b/.github/workflows/probe.yml
--- a/.github/workflows/probe.yml
+++ b/.github/workflows/probe.yml
@@ -1,2 +1 @@
-on:
-  pull_request:
+on: workflow_dispatch
@@ -8,0 +8 @@
+      - uses: owner/action@v1
"""
    assert mod.parse_changed_head_lines(diff_probe) == {
        ".github/workflows/probe.yml": {1, 8}
    }

    new_file_probe = """diff --git a/.github/workflows/new.yml b/.github/workflows/new.yml
new file mode 100644
--- /dev/null
+++ b/.github/workflows/new.yml
@@ -0,0 +1,2 @@
+name: New
+on: push
"""
    assert mod.parse_changed_head_lines(new_file_probe) == {
        ".github/workflows/new.yml": {1, 2}
    }

    broken = dict(policy)
    broken["immutable_remote_ref_regex"] = "^v\\d+$"
    _expect(
        mod.ActionSupplyChainError,
        lambda: mod.validate_policy(broken),
        "mutable immutable-ref policy",
    )

    print("ACTION_SUPPLY_CHAIN_SELFTEST_PASS probes=18")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
