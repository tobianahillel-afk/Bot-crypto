#!/usr/bin/env python3
"""Adversarial qualification for ENG-07.2 historical audit manifests."""

from __future__ import annotations

import copy
import importlib.util
import sys
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


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"historical manifest negative scenario passed: {label}")


def main() -> int:
    mod = _module(
        "historical_manifest_selftest",
        ROOT / "scripts" / "governance" / "validate_historical_audit_manifest.py",
    )
    planner = _module(
        "historical_manifest_selftest_planner",
        ROOT / "scripts" / "governance" / "plan_historical_audit_batches.py",
    )
    plan = planner.plan_batches(planner.synthetic_request(), planner._load(planner.POLICY_PATH))
    batch = plan["batches"][0]
    manifest = mod.build_manifest(
        batch=batch,
        plan_identity_sha256=plan["plan_identity_sha256"],
        source_head_sha="b" * 40,
    )
    mod.validate_manifest(manifest, plan)
    replay = mod.build_manifest(
        batch=batch,
        plan_identity_sha256=plan["plan_identity_sha256"],
        source_head_sha="b" * 40,
    )
    assert mod._canonical(manifest) == mod._canonical(replay)

    tampered = copy.deepcopy(manifest)
    tampered["complexity_total"] += 1
    _expect(mod.HistoricalAuditManifestError, lambda: mod.validate_manifest(tampered, plan), "identity tamper")

    candidate = copy.deepcopy(manifest)
    candidate["lots"] = [45]
    candidate["manifest_identity_sha256"] = mod._sha256(mod.manifest_material(candidate))
    _expect(mod.HistoricalAuditManifestError, lambda: mod.validate_manifest(candidate, plan), "Lot45 inclusion")

    unordered = copy.deepcopy(manifest)
    unordered["lots"] = [2, 1]
    unordered["manifest_identity_sha256"] = mod._sha256(mod.manifest_material(unordered))
    _expect(mod.HistoricalAuditManifestError, lambda: mod.validate_manifest(unordered, plan), "unordered lots")

    writable = copy.deepcopy(manifest)
    writable["permissions"]["remediation_write"] = True
    writable["manifest_identity_sha256"] = mod._sha256(mod.manifest_material(writable))
    _expect(mod.HistoricalAuditManifestError, lambda: mod.validate_manifest(writable, plan), "remediation permission")

    bad_source = copy.deepcopy(manifest)
    bad_source["source_binding"]["source_head_sha"] = "not-a-sha"
    bad_source["manifest_identity_sha256"] = mod._sha256(mod.manifest_material(bad_source))
    _expect(mod.HistoricalAuditManifestError, lambda: mod.validate_manifest(bad_source, plan), "source sha")

    blocked = copy.deepcopy(manifest)
    blocked["status"] = "BLOCKED"
    blocked["manifest_identity_sha256"] = mod._sha256(mod.manifest_material(blocked))
    _expect(mod.HistoricalAuditManifestError, lambda: mod.validate_manifest(blocked, plan), "blocked without blocker")

    stray = copy.deepcopy(manifest)
    stray["blockers"] = ["unexpected"]
    stray["manifest_identity_sha256"] = mod._sha256(mod.manifest_material(stray))
    _expect(mod.HistoricalAuditManifestError, lambda: mod.validate_manifest(stray, plan), "nonblocked blocker")

    forged_plan = copy.deepcopy(plan)
    forged_plan["plan_identity_sha256"] = "0" * 64
    _expect(
        mod.HistoricalAuditManifestError,
        lambda: mod.validate_manifest(manifest, forged_plan),
        "forged plan identity",
    )

    wrong_batch = copy.deepcopy(manifest)
    wrong_batch["batch_identity_sha256"] = "0" * 64
    wrong_batch["manifest_identity_sha256"] = mod._sha256(mod.manifest_material(wrong_batch))
    _expect(
        mod.HistoricalAuditManifestError,
        lambda: mod.validate_manifest(wrong_batch, plan),
        "forged batch identity",
    )

    duplicate = copy.deepcopy(manifest)
    if len(duplicate["lots"]) >= 2:
        duplicate["lots"][1] = duplicate["lots"][0]
    else:
        duplicate["lots"] = [duplicate["lots"][0], duplicate["lots"][0]]
    duplicate["manifest_identity_sha256"] = mod._sha256(mod.manifest_material(duplicate))
    _expect(
        mod.HistoricalAuditManifestError,
        lambda: mod.validate_manifest(duplicate, plan),
        "duplicate lots",
    )

    lifecycle = mod._load(mod.LIFECYCLE_PATH)
    for source, target in (
        ("PLANNED","READY"),
        ("READY","IN_PROGRESS"),
        ("IN_PROGRESS","REVIEW_REQUIRED"),
        ("REVIEW_REQUIRED","COMPLETE"),
        ("PLANNED","BLOCKED"),
        ("BLOCKED","READY"),
    ):
        mod.validate_transition(source, target, lifecycle)

    _expect(
        mod.HistoricalAuditManifestError,
        lambda: mod.validate_transition("PLANNED", "COMPLETE", lifecycle),
        "skipped lifecycle",
    )
    _expect(
        mod.HistoricalAuditManifestError,
        lambda: mod.validate_transition("READY", "READY", lifecycle),
        "same-state lifecycle",
    )
    _expect(
        mod.HistoricalAuditManifestError,
        lambda: mod.validate_transition("UNKNOWN", "READY", lifecycle),
        "unknown lifecycle",
    )

    bad_lifecycle = copy.deepcopy(lifecycle)
    bad_lifecycle["allowed_transitions"]["PLANNED"].append("COMPLETE")
    _expect(
        mod.HistoricalAuditManifestError,
        lambda: mod.validate_lifecycle_policy(bad_lifecycle),
        "lifecycle policy drift",
    )

    schema = mod._load(mod.SCHEMA_PATH)
    bad_schema = copy.deepcopy(schema)
    bad_schema["properties"]["lots"]["items"]["maximum"] = 45
    _expect(
        mod.HistoricalAuditManifestError,
        lambda: mod.validate_schema_contract(bad_schema),
        "schema permits Lot45",
    )

    print("HISTORICAL_AUDIT_MANIFEST_SELFTEST_PASS probes=15")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
