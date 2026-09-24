#!/usr/bin/env python3
"""Adversarial tests for historical audit traceability mapping semantics."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_historical_audit_mapping.py"
    spec = importlib.util.spec_from_file_location("historical_mapping_selftest", path)
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
    raise AssertionError(f"historical mapping negative scenario unexpectedly passed: {label}")


def _rehash(mod: ModuleType, mapping: dict[str, Any]) -> None:
    mapping["mapping_identity_sha256"] = mod._sha256(mod.mapping_material(mapping))


def main() -> int:
    mod = _module()
    mapping, manifest, plan = mod._synthetic_bundle()
    mod.validate_mapping(mapping, manifest, plan)

    tampered = copy.deepcopy(mapping)
    tampered["requirements"][0]["category"] = "GOVERNANCE"
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(tampered, manifest, plan),
        "identity-bound semantic tamper",
    )

    outside = copy.deepcopy(mapping)
    candidate = next((lot for lot in range(45) if lot not in manifest["lots"]), None)
    if candidate is None:
        raise AssertionError("synthetic manifest unexpectedly covers all historical lots")
    outside["lot"] = candidate
    outside["mapping_id"] = f"HIST-MAP-B{manifest['batch_index']:03d}-L{candidate:03d}"
    _rehash(mod, outside)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(outside, manifest, plan),
        "lot outside bound batch",
    )

    lot45 = copy.deepcopy(mapping)
    lot45["lot"] = 45
    lot45["mapping_id"] = f"HIST-MAP-B{manifest['batch_index']:03d}-L045"
    _rehash(mod, lot45)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(lot45, manifest, plan),
        "Lot45 mapping",
    )

    forged_manifest = copy.deepcopy(manifest)
    forged_manifest["plan_identity_sha256"] = "0" * 64
    forged_manifest["manifest_identity_sha256"] = mod._module(
        "mapping_manifest_rehash",
        ROOT / "scripts" / "governance" / "validate_historical_audit_manifest.py",
    )._sha256(
        mod._module(
            "mapping_manifest_material",
            ROOT / "scripts" / "governance" / "validate_historical_audit_manifest.py",
        ).manifest_material(forged_manifest)
    )
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(mapping, forged_manifest, plan),
        "forged bound manifest plan",
    )

    missing_test = copy.deepcopy(mapping)
    missing_test["requirements"][0]["test_ids"] = []
    _rehash(mod, missing_test)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(missing_test, manifest, plan),
        "MAPPED without test",
    )

    justified = copy.deepcopy(mapping)
    req = justified["requirements"][0]
    req["coverage_status"] = "JUSTIFIED_NON_CODE"
    req["implementation_symbols"] = []
    req["test_ids"] = []
    req["justification"] = "Requirement is governance-only and has no executable implementation."
    _rehash(mod, justified)
    mod.validate_mapping(justified, manifest, plan)

    bad_justified = copy.deepcopy(justified)
    bad_justified["requirements"][0]["justification"] = None
    _rehash(mod, bad_justified)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(bad_justified, manifest, plan),
        "JUSTIFIED_NON_CODE without justification",
    )

    fake_code = copy.deepcopy(justified)
    fake_code["requirements"][0]["implementation_symbols"] = [
        {"path": "scripts/fake.py", "symbol": "fake"}
    ]
    _rehash(mod, fake_code)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(fake_code, manifest, plan),
        "JUSTIFIED_NON_CODE with fake code",
    )

    unresolved = copy.deepcopy(mapping)
    req = unresolved["requirements"][0]
    req["coverage_status"] = "UNRESOLVED"
    req["gap_reason"] = "No certified test evidence located yet."
    _rehash(mod, unresolved)
    mod.validate_mapping(unresolved, manifest, plan)

    hidden_gap = copy.deepcopy(unresolved)
    hidden_gap["requirements"][0]["gap_reason"] = None
    _rehash(mod, hidden_gap)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(hidden_gap, manifest, plan),
        "UNRESOLVED without gap reason",
    )

    traversal = copy.deepcopy(mapping)
    traversal["requirements"][0]["design_sections"][0]["path"] = "../docs/escape.md"
    _rehash(mod, traversal)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(traversal, manifest, plan),
        "path traversal",
    )

    wrong_prefix = copy.deepcopy(mapping)
    wrong_prefix["requirements"][0]["test_ids"][0]["path"] = "docs/not_a_test.md"
    _rehash(mod, wrong_prefix)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(wrong_prefix, manifest, plan),
        "typed reference prefix violation",
    )

    duplicate_ref = copy.deepcopy(mapping)
    ref = copy.deepcopy(duplicate_ref["requirements"][0]["evidence_artifacts"][0])
    duplicate_ref["requirements"][0]["evidence_artifacts"].append(ref)
    _rehash(mod, duplicate_ref)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(duplicate_ref, manifest, plan),
        "duplicate evidence reference",
    )

    duplicate_requirement = copy.deepcopy(mapping)
    duplicate_requirement["requirements"].append(
        copy.deepcopy(duplicate_requirement["requirements"][0])
    )
    _rehash(mod, duplicate_requirement)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(duplicate_requirement, manifest, plan),
        "duplicate requirement id",
    )

    unsorted = copy.deepcopy(mapping)
    second = copy.deepcopy(unsorted["requirements"][0])
    second["requirement_id"] = "AAA-REQ-SECOND"
    unsorted["requirements"].append(second)
    _rehash(mod, unsorted)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(unsorted, manifest, plan),
        "unsorted requirement ids",
    )

    writable = copy.deepcopy(mapping)
    writable["mutation_permissions"]["business_code"] = True
    _rehash(mod, writable)
    _expect(
        mod.HistoricalAuditMappingError,
        lambda: mod.validate_mapping(writable, manifest, plan),
        "writable mapping",
    )

    print("HISTORICAL_AUDIT_MAPPING_SELFTEST_PASS probes=15")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
