#!/usr/bin/env python3
"""Adversarial tests for the offline approved action pin registry."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_action_pin_registry.py"
    spec = importlib.util.spec_from_file_location("action_pin_registry_selftest", path)
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
    raise AssertionError(f"action-pin negative scenario unexpectedly passed: {label}")


def _entry(registry: dict[str, Any], repository: str) -> dict[str, Any]:
    return next(item for item in registry["entries"] if item["repository"] == repository)


def main() -> int:
    mod = _module()
    registry = mod._json(mod.REGISTRY_PATH)
    mod.validate_registry_only(registry)

    bad_sha = copy.deepcopy(registry)
    _entry(bad_sha, "actions/checkout")["approved_commit_sha"] = "0" * 40
    _expect(mod.ActionPinRegistryError, lambda: mod.validate_registry_only(bad_sha), "checkout SHA")

    bad_license = copy.deepcopy(registry)
    _entry(bad_license, "actions/setup-python")["license"] = "UNKNOWN"
    _expect(mod.ActionPinRegistryError, lambda: mod.validate_registry_only(bad_license), "license")

    bad_owner = copy.deepcopy(registry)
    _entry(bad_owner, "actions/upload-artifact")["owner"] = "other"
    _expect(mod.ActionPinRegistryError, lambda: mod.validate_registry_only(bad_owner), "owner")

    bad_ref = copy.deepcopy(registry)
    _entry(bad_ref, "actions/setup-go")["source_ref"] = "main"
    _expect(mod.ActionPinRegistryError, lambda: mod.validate_registry_only(bad_ref), "source ref")

    bad_tag = copy.deepcopy(registry)
    _entry(bad_tag, "github/codeql-action")["dereferenced_commit_sha"] = "1" * 40
    _expect(mod.ActionPinRegistryError, lambda: mod.validate_registry_only(bad_tag), "annotated tag")

    missing = copy.deepcopy(registry)
    missing["entries"] = missing["entries"][:-1]
    _expect(mod.ActionPinRegistryError, lambda: mod.validate_registry_only(missing), "missing repo")

    duplicate = copy.deepcopy(registry)
    duplicate["entries"][-1]["repository"] = "actions/checkout"
    _expect(mod.ActionPinRegistryError, lambda: mod.validate_registry_only(duplicate), "duplicate repo")

    bad_legacy = copy.deepcopy(registry)
    _entry(bad_legacy, "actions/checkout")["legacy_floating_refs"] = []
    _expect(mod.ActionPinRegistryError, lambda: mod.validate_registry_only(bad_legacy), "legacy map")

    bad_state = copy.deepcopy(registry)
    _entry(bad_state, "actions/setup-python")["archived"] = True
    _expect(mod.ActionPinRegistryError, lambda: mod.validate_registry_only(bad_state), "repo state")

    print("ACTION_PIN_REGISTRY_SELFTEST_PASS probes=9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
