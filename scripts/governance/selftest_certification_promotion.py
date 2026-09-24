#!/usr/bin/env python3
"""Adversarial qualification for ENG-06.5 fail-closed promotion rules."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts/governance/validate_certification_promotion.py"
    spec = importlib.util.spec_from_file_location("certification_promotion_selftest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _denied(mod: ModuleType, policy: dict[str, Any], fixture: dict[str, Any], reason: str) -> None:
    result = mod.evaluate_promotion(policy=policy, **fixture)
    assert result["decision"] == "PROMOTION_DENIED", result
    assert reason in result["reasons"], result


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)
    good = mod.synthetic_fixture(policy)
    allowed = mod.evaluate_promotion(policy=policy, **good)
    assert allowed["decision"] == "PROMOTION_ALLOWED"
    assert allowed["target_state"] == "CERTIFIED"
    assert not (set(policy["forbidden_output_fields"]) & set(allowed))

    x = copy.deepcopy(good)
    x["candidate"]["state"] = "VALIDATING"
    x["candidate"]["evidence_bindings"].pop("NO_OPEN_BLOCKER", None)
    _denied(mod, policy, x, "SOURCE_STATE_NOT_CERTIFICATION_READY")

    x = copy.deepcopy(good)
    x["candidate"]["satisfied_t4"] = ["EXACT_HEAD_CERTIFICATION"]
    _denied(mod, policy, x, "UNSATISFIED_T4_REQUIREMENTS")

    x = copy.deepcopy(good)
    x["blockers"] = ["BLOCKER-1"]
    _denied(mod, policy, x, "OPEN_BLOCKERS")

    x = copy.deepcopy(good)
    x["input_binding"]["material"]["candidate"]["head_sha"] = "e" * 40
    _denied(mod, policy, x, "INVALID_EXACT_HEAD_EVIDENCE")

    x = copy.deepcopy(good)
    x["exact_head_bundle"]["material"]["ci_runs"][0]["conclusion"] = "failure"
    _denied(mod, policy, x, "INVALID_EXACT_HEAD_EVIDENCE")

    x = copy.deepcopy(good)
    x["assurance_plan"]["material"]["candidate_head"] = "e" * 40
    _denied(mod, policy, x, "INVALID_DEEP_ASSURANCE")

    x = copy.deepcopy(good)
    x["provenance_envelope"]["material"]["candidate"]["candidate_id"] = "OTHER-CANDIDATE"
    _denied(mod, policy, x, "INVALID_CANONICAL_PROVENANCE")

    x = copy.deepcopy(good)
    x["native_attestation"]["subject_sha256"] = "f" * 64
    _denied(mod, policy, x, "INVALID_NATIVE_ATTESTATION")

    x = copy.deepcopy(good)
    x["native_attestation"]["attestation_id"] = ""
    _denied(mod, policy, x, "INVALID_NATIVE_ATTESTATION")

    x = copy.deepcopy(good)
    x["native_attestation"]["attestation_url"] = "https://example.com/attestations/7003"
    _denied(mod, policy, x, "INVALID_NATIVE_ATTESTATION")

    x = copy.deepcopy(good)
    x["certification_verdict"]["material"]["status"] = "FAIL"
    _denied(mod, policy, x, "INVALID_CERTIFICATION_VERDICT")

    x = copy.deepcopy(good)
    x["certification_verdict"]["material"]["head_sha"] = "e" * 40
    _denied(mod, policy, x, "INVALID_CERTIFICATION_VERDICT")

    x = copy.deepcopy(good)
    x["certification_verdict"]["material"]["provenance_identity_sha256"] = "f" * 64
    _denied(mod, policy, x, "INVALID_CERTIFICATION_VERDICT")

    x = copy.deepcopy(good)
    x["candidate"]["candidate_id"] = "ENG-06.4-ATTESTATION-PROBE"
    _denied(mod, policy, x, "FORBIDDEN_ENGINEERING_TRANSPORT_PROBE")

    x = copy.deepcopy(good)
    x["candidate"]["evidence_fresh"] = False
    _denied(mod, policy, x, "INVALID_LIFECYCLE_CANDIDATE")

    bad_policy = copy.deepcopy(policy)
    bad_policy["target_state"] = "VALIDATING"
    try:
        mod.validate_policy(bad_policy)
    except mod.CertificationPromotionError:
        pass
    else:
        raise AssertionError("unsafe target-state policy unexpectedly accepted")

    print("CERTIFICATION_PROMOTION_SELFTEST_PASS probes=17")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
