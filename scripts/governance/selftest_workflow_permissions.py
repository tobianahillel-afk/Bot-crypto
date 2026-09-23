#!/usr/bin/env python3
"""Adversarial qualification for incremental workflow permission enforcement."""

from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "audit_workflow_permissions.py"
    spec = importlib.util.spec_from_file_location("workflow_permission_selftest", path)
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
    raise AssertionError(f"workflow-permission negative scenario unexpectedly passed: {label}")


def _gate(mod: ModuleType, policy: dict[str, Any], text: str) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        path = root / ".github" / "workflows" / "probe.yml"
        path.parent.mkdir(parents=True)
        path.write_text(text, encoding="utf-8")
        return mod.changed_gate(mod.audit([path], policy, root=root), policy)


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)

    assert _gate(mod, policy, "name: Probe\npermissions:\n  contents: read\njobs:\n  test:\n    runs-on: ubuntu-latest\n") == []
    assert _gate(mod, policy, "name: Probe\npermissions: {}\njobs:\n  test:\n    runs-on: ubuntu-latest\n") == []

    missing = _gate(mod, policy, "name: Probe\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
    assert {x["reason"] for x in missing} == {"MISSING_TOP_LEVEL_PERMISSIONS"}

    write_all = _gate(mod, policy, "name: Probe\npermissions: write-all\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
    assert any(x["reason"] == "WRITE_ALL_FORBIDDEN" for x in write_all)

    read_all = _gate(mod, policy, "name: Probe\npermissions: read-all\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
    assert any(x["reason"] == "READ_ALL_FORBIDDEN" for x in read_all)

    contents_write = _gate(mod, policy, "name: Probe\npermissions:\n  contents: write\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
    assert any(x["reason"] == "UNAPPROVED_WRITE_SCOPE" for x in contents_write)

    dynamic = _gate(mod, policy, "name: Probe\npermissions: ${{ fromJSON('{}') }}\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
    assert any(x["reason"] == "DYNAMIC_PERMISSIONS" for x in dynamic)

    widened = _gate(
        mod, policy,
        "name: Probe\npermissions:\n  contents: read\njobs:\n  test:\n    permissions:\n      contents: read\n      pull-requests: read\n    runs-on: ubuntu-latest\n",
    )
    assert any(x["reason"] == "JOB_PERMISSION_WIDENS_TOP_LEVEL" for x in widened)

    narrowed = _gate(
        mod, policy,
        "name: Probe\npermissions:\n  contents: read\n  pull-requests: read\njobs:\n  test:\n    permissions:\n      contents: read\n      pull-requests: none\n    runs-on: ubuntu-latest\n",
    )
    assert narrowed == []

    approved = copy.deepcopy(policy)
    approved["approved_write_scopes"] = [{
        "workflow": ".github/workflows/probe.yml",
        "scope": "security-events",
        "rationale": "Required for a deliberately approved security result publication workflow.",
    }]
    assert _gate(mod, approved, "name: Probe\npermissions:\n  security-events: write\njobs:\n  test:\n    runs-on: ubuntu-latest\n") == []

    malformed_policy = copy.deepcopy(policy)
    malformed_policy["approved_write_scopes"] = [{
        "workflow": ".github/workflows/probe.yml",
        "scope": "contents",
        "rationale": "short",
    }]
    _expect(mod.WorkflowPermissionError, lambda: mod.validate_policy(malformed_policy), "weak write approval rationale")

    print("WORKFLOW_PERMISSION_SELFTEST_PASS probes=11")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
