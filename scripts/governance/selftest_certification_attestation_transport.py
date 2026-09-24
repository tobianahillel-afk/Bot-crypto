#!/usr/bin/env python3
"""Adversarial qualification for ENG-06.4 native attestation transport."""

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
    path = ROOT / "scripts" / "governance" / "validate_certification_attestation_transport.py"
    spec = importlib.util.spec_from_file_location("attestation_transport_selftest", path)
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
    raise AssertionError(f"attestation-transport negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_documents(policy)
    envelope = mod.build_probe(
        head_sha="a" * 40,
        tree_sha="b" * 40,
        workflow_ref=policy["allowed_ref"],
        run_id=101,
        run_attempt=1,
        domain_digest="c" * 64,
        policy=policy,
    )
    assert envelope["material"]["candidate"]["candidate_id"] == "ENG-06.4-ATTESTATION-PROBE"
    assert envelope["material"]["deep_assurance"]["status"] == "NOT_REQUIRED"
    assert envelope["material"]["domain_integrity_refs"] == [{
        "path":"config/governance/certification_provenance_v1.json",
        "algorithm":"sha256",
        "digest":"c" * 64,
    }]
    assert envelope["attestation_subject"]["digest"]["sha256"] == envelope["provenance_identity_sha256"]

    wrong_ref = copy.deepcopy(policy)
    wrong_ref["allowed_ref"] = "refs/heads/main"
    _expect(mod.AttestationTransportError, lambda: mod.validate_policy(wrong_ref), "main ref")

    workflow = (ROOT / policy["workflow_path"]).read_text(encoding="utf-8")
    floating = workflow.replace(
        "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2",
        "actions/attest@v4",
    )
    _expect(mod.AttestationTransportError, lambda: mod.validate_workflow(policy, floating), "floating action")

    widened = workflow.replace(
        "  attestations: write\n",
        "  attestations: write\n  artifact-metadata: write\n",
    )
    _expect(mod.AttestationTransportError, lambda: mod.validate_workflow(policy, widened), "extra write")

    pushed = copy.deepcopy(policy)
    pushed["transport"]["push_to_registry"] = True
    _expect(mod.AttestationTransportError, lambda: mod.validate_policy(pushed), "registry push")

    business_probe = copy.deepcopy(policy)
    business_probe["probe"]["candidate_id"] = "LOT45-CERTIFIED"
    _expect(mod.AttestationTransportError, lambda: mod.validate_policy(business_probe), "business probe")

    bad_registry = mod._json(ROOT / policy["action_pin_registry_source"])
    next(x for x in bad_registry["entries"] if x["repository"] == "actions/attest")[
        "approved_pins"
    ][0]["approved_commit_sha"] = "0" * 40
    original_json = mod._json
    try:
        mod._json = lambda path: (
            bad_registry if path == ROOT / policy["action_pin_registry_source"] else original_json(path)
        )
        _expect(mod.AttestationTransportError, lambda: mod.validate_action_registry(policy), "pin drift")
    finally:
        mod._json = original_json

    bad_permissions = mod._json(ROOT / policy["workflow_permission_policy_source"])
    bad_permissions["approved_write_scopes"] = [
        x for x in bad_permissions["approved_write_scopes"] if x["scope"] != "id-token"
    ]
    try:
        mod._json = lambda path: (
            bad_permissions if path == ROOT / policy["workflow_permission_policy_source"] else original_json(path)
        )
        _expect(mod.AttestationTransportError, lambda: mod.validate_permission_policy(policy), "missing OIDC approval")
    finally:
        mod._json = original_json

    _expect(
        mod.AttestationTransportError,
        lambda: mod.build_probe(
            head_sha="a" * 40,
            tree_sha="b" * 40,
            workflow_ref="refs/heads/main",
            run_id=1,
            run_attempt=1,
            domain_digest="c" * 64,
            policy=policy,
        ),
        "probe on main",
    )

    provenance = mod._provenance()
    tampered = copy.deepcopy(envelope)
    tampered["material"]["workflow"]["run_id"] = 999
    _expect(
        provenance.CertificationProvenanceError,
        lambda: provenance.validate_provenance(tampered, provenance._load_policies()[0]),
        "predicate tamper",
    )

    with tempfile.TemporaryDirectory() as raw:
        bundle = Path(raw) / "bundle.json"
        bundle.write_text('{"mediaType":"application/vnd.dev.sigstore.bundle.v0.3+json"}\n', encoding="utf-8")
        mod.verify_action_outputs(
            "123",
            "https://github.com/tobianahillel-afk/Bot-crypto/attestations/123",
            bundle,
        )
        _expect(
            mod.AttestationTransportError,
            lambda: mod.verify_action_outputs("123", "https://example.com/attestations/123", bundle),
            "noncanonical attestation URL",
        )
        empty = Path(raw) / "empty.json"
        empty.write_text("{}\n", encoding="utf-8")
        _expect(
            mod.AttestationTransportError,
            lambda: mod.verify_action_outputs(
                "123",
                "https://github.com/tobianahillel-afk/Bot-crypto/attestations/123",
                empty,
            ),
            "empty bundle",
        )

    print("CERTIFICATION_ATTESTATION_TRANSPORT_SELFTEST_PASS probes=12")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
