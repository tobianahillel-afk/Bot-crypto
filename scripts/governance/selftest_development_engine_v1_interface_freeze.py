#!/usr/bin/env python3
"""Adversarial qualification for the Development Engine V1 interface freeze."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts/governance/validate_development_engine_v1_interface_freeze.py"
    spec = importlib.util.spec_from_file_location("engine_v1_interface_freeze_selftest", path)
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
    raise AssertionError(f"V1 interface freeze negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)
    repository = mod.validate_repository()
    assert repository["status"] == "PASS"
    assert repository["dynamic_payloads_frozen"] is False

    moved_state = copy.deepcopy(policy)
    moved_state["bootstrap"]["current_authority"] = "engineering/STATE.json"
    _expect(mod.EngineV1InterfaceFreezeError, lambda: mod.validate_policy(moved_state), "authority path move")

    reordered = copy.deepcopy(policy)
    reordered["bootstrap"]["read_order"] = list(reversed(reordered["bootstrap"]["read_order"]))
    _expect(mod.EngineV1InterfaceFreezeError, lambda: mod.validate_policy(reordered), "bootstrap order inversion")

    changed_cli = copy.deepcopy(policy)
    changed_cli["stable_cli_contracts"]["verify_external_git_state"] = [
        "python", "scripts/governance/verify_external_git_state.py"
    ]
    _expect(mod.EngineV1InterfaceFreezeError, lambda: mod.validate_policy(changed_cli), "CLI drift")

    paid = copy.deepcopy(policy)
    paid["compatibility"]["paid_dependency_required"] = True
    _expect(mod.EngineV1InterfaceFreezeError, lambda: mod.validate_policy(paid), "paid dependency")

    frozen_dynamic = copy.deepcopy(policy)
    frozen_dynamic["dynamic_not_frozen"] = [
        x for x in frozen_dynamic["dynamic_not_frozen"]
        if not x.startswith("config/governance/project_state.json#")
    ]
    _expect(mod.EngineV1InterfaceFreezeError, lambda: mod.validate_policy(frozen_dynamic), "dynamic state byte-freeze")

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "engineering").mkdir()
        context = {
            "schema_version": 1,
            "map_kind": "active_agent_context_map_v1",
            "authority": {
                "current_state": "engineering/STATE.json",
                "resume_hint_is_authoritative": True,
            },
            "active_work": {"awu_path": "engineering/wu.json"},
        }
        (root / "engineering/CONTEXT_MAP.json").write_text(json.dumps(context), encoding="utf-8")
        (root / "engineering/wu.json").write_text(
            json.dumps({"schema_version": 1, "kind": "agent_work_unit", "status": "IN_PROGRESS"}),
            encoding="utf-8",
        )
        _expect(
            mod.EngineV1InterfaceFreezeError,
            lambda: mod._validate_active_awu(policy, root),
            "context-map authority inversion",
        )

    bad_cert = copy.deepcopy(policy)
    bad_cert["certification_identity"]["bundle_identity_sha256"] = "0" * 64
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        path = root / "engineering"
        path.mkdir()
        evidence = {
            "qualified_head_sha": policy["certification_identity"]["qualified_head_sha"],
            "exact_identities": {
                "candidate_material_sha256": policy["certification_identity"]["candidate_material_sha256"],
                "input_identity_sha256": policy["certification_identity"]["input_identity_sha256"],
                "bundle_identity_sha256": policy["certification_identity"]["bundle_identity_sha256"],
            },
            "authority_separation": {
                "business_development_unlocked": False,
                "runtime_unlocked": False,
                "lot45_merge_allowed": False,
                "lot46_unlock_allowed": False,
                "trade_allowed": False,
                "execution_allowed": False,
            },
        }
        (path / "DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json").write_text(
            json.dumps(evidence), encoding="utf-8"
        )
        _expect(
            mod.EngineV1InterfaceFreezeError,
            lambda: mod._validate_certification(bad_cert, root),
            "certification identity drift",
        )

    assert policy["compatibility"]["incompatible_change_requires_new_interface_version"] is True
    assert policy["compatibility"]["v1_must_not_freeze_dynamic_payload_bytes"] is True
    print("DEVELOPMENT_ENGINE_V1_INTERFACE_FREEZE_SELFTEST_PASS probes=8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
