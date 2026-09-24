#!/usr/bin/env python3
"""Adversarial qualification for ENG-07 immutable-evidence protection."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _expect(
    exc_type: type[BaseException],
    fn: Callable[[], Any],
    label: str,
) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(
        f"audit evidence protection negative scenario unexpectedly passed: {label}"
    )


def main() -> int:
    mod = _module(
        "historical_audit_evidence_protection_adversarial",
        ROOT / "scripts" / "governance" /
        "validate_historical_audit_evidence_protection.py",
    )
    policy = mod._load(mod.POLICY_PATH)
    mod.validate_repository(policy)
    probes = 0

    def expect_policy(
        label: str,
        mutate: Callable[[dict[str, Any]], None],
    ) -> None:
        nonlocal probes
        candidate = copy.deepcopy(policy)
        mutate(candidate)
        _expect(
            mod.HistoricalAuditEvidenceProtectionError,
            lambda: mod.validate_policy(candidate),
            label,
        )
        probes += 1

    expect_policy(
        "remediation execution authority",
        lambda x: x["authority"].__setitem__(
            "remediation_execution_authority", True
        ),
    )
    expect_policy(
        "writable required mutation permission",
        lambda x: x["required_mutation_permissions"].__setitem__(
            "historical_evidence", True
        ),
    )
    expect_policy(
        "canonical protection path drift",
        lambda x: x["canonical_protection"].__setitem__(
            "policy_path", "engineering/OTHER.json"
        ),
    )
    expect_policy(
        "canonical comparison-base drift",
        lambda x: x["canonical_protection"].__setitem__(
            "comparison_base", "HEAD~1"
        ),
    )
    expect_policy(
        "validator coverage removal",
        lambda x: x.__setitem__(
            "audit_validator_paths", x["audit_validator_paths"][:-1]
        ),
    )
    expect_policy(
        "data-audit guard removal",
        lambda x: x.__setitem__(
            "forbidden_scope_prefixes",
            [p for p in x["forbidden_scope_prefixes"] if p != "data/audit/"],
        ),
    )
    expect_policy(
        "duplicated queue guard",
        lambda x: x["forbidden_queue_fields"].append(
            x["forbidden_queue_fields"][0]
        ),
    )

    canonical_mod = mod._module(
        "historical_audit_evidence_canonical_adversarial",
        ROOT / policy["canonical_protection"]["validator_path"],
    )
    canonical = mod._load(
        ROOT / policy["canonical_protection"]["policy_path"]
    )

    def expect_canonical(
        label: str,
        mutate: Callable[[dict[str, Any]], None],
    ) -> None:
        nonlocal probes
        candidate = copy.deepcopy(canonical)
        mutate(candidate)
        _expect(
            canonical_mod.EvidenceProtectionError,
            lambda: canonical_mod.validate(candidate),
            label,
        )
        probes += 1

    expect_canonical(
        "Lot44 verdict drift",
        lambda x: x["anchors"][0].__setitem__("verdict", "NOT_GO"),
    )
    expect_canonical(
        "Lot45 prerequisite drift",
        lambda x: x["anchors"][1].__setitem__(
            "prerequisite_merge", x["anchors"][1]["gate_merge"]
        ),
    )
    expect_canonical(
        "canonical anchor rewrite",
        lambda x: x["anchors"][1].__setitem__("gate_merge", "0" * 40),
    )
    expect_canonical(
        "required protected path removal",
        lambda x: x.__setitem__(
            "protected_current_tree_paths",
            [
                p for p in x["protected_current_tree_paths"]
                if p != "data/audit/lot45_v4_entry_gate.json"
            ],
        ),
    )
    expect_canonical(
        "protected mutable overlap",
        lambda x: x["intentionally_mutable_views"].append(
            x["protected_current_tree_paths"][0]
        ),
    )

    expected_permissions = policy["required_mutation_permissions"]
    mod.validate_permission_object(
        {"mutation_permissions": copy.deepcopy(expected_permissions)},
        expected_permissions,
        "synthetic-safe-policy",
    )
    writable_policy = {"mutation_permissions": copy.deepcopy(expected_permissions)}
    writable_policy["mutation_permissions"]["reports"] = True
    _expect(
        mod.HistoricalAuditEvidenceProtectionError,
        lambda: mod.validate_permission_object(
            writable_policy, expected_permissions, "synthetic-writable-policy"
        ),
        "writable findings/report policy",
    )
    probes += 1

    safe_source = "def validate():\n    return True\n"
    mod.validate_source_text_no_write("safe.py", safe_source, policy)

    external_client = "import " + "shutil" + "\n"
    _expect(
        mod.HistoricalAuditEvidenceProtectionError,
        lambda: mod.validate_source_text_no_write(
            "external_client.py", external_client, policy
        ),
        "mutation-capable client import",
    )
    probes += 1

    write_method = "write" + "_bytes"
    write_source = (
        "from pathlib import Path\n"
        "def validate():\n"
        f"    getattr(Path('x'), '{write_method}')(b'x')\n"
    )
    _expect(
        mod.HistoricalAuditEvidenceProtectionError,
        lambda: mod.validate_source_text_no_write(
            "write_primitive.py", write_source, policy
        ),
        "filesystem write primitive",
    )
    probes += 1

    direct_source = "def validate():\n    return " + "open" + "('x')\n"
    _expect(
        mod.HistoricalAuditEvidenceProtectionError,
        lambda: mod.validate_source_text_no_write(
            "direct_primitive.py", direct_source, policy
        ),
        "direct file primitive",
    )
    probes += 1

    safe_queue = {"queue_id": {}, "finding_id": {}, "owner": {}}
    mod.validate_queue_properties(safe_queue, policy)
    for forbidden_field in ("command", "target_path"):
        bad_queue = dict(safe_queue)
        bad_queue[forbidden_field] = {}
        _expect(
            mod.HistoricalAuditEvidenceProtectionError,
            lambda q=bad_queue: mod.validate_queue_properties(q, policy),
            f"queue field {forbidden_field}",
        )
        probes += 1

    protected = {"protected/frozen.json"}
    prefixes = policy["forbidden_scope_prefixes"]
    mod.validate_allowed_paths(
        "safe-awu", ["engineering/safe.json"], protected, prefixes
    )
    for label, candidate in (
        ("data audit AWU scope", "data/audit/forbidden.json"),
        ("canonical protected AWU scope", "protected/frozen.json"),
        ("contracts wildcard AWU scope", "contracts/**"),
    ):
        _expect(
            mod.HistoricalAuditEvidenceProtectionError,
            lambda value=candidate: mod.validate_allowed_paths(
                "unsafe-awu", [value], protected, prefixes
            ),
            label,
        )
        probes += 1

    if probes < 16:
        raise AssertionError(
            f"audit evidence protection adversarial suite too small: {probes}"
        )
    print(
        "HISTORICAL_AUDIT_EVIDENCE_PROTECTION_SELFTEST_PASS "
        f"positive_repository=1 negative_probes={probes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
