#!/usr/bin/env python3
"""Adversarial qualification for ENG-06.6 post-merge certification reuse."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_certification_post_merge.py"
    spec = importlib.util.spec_from_file_location("post_merge_selftest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _require_revalidation(
    mod: ModuleType,
    policy: dict[str, Any],
    fixture: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    result = mod.evaluate_post_merge(policy=policy, **fixture)
    assert result["decision"] == "REVALIDATION_REQUIRED", result
    assert result["reuse_prior_certification"] is False
    assert reason in result["reasons"], result
    assert result["full_regression_rerun"] is None
    assert result["t4_rerun"] is None
    return result


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)
    good = mod.synthetic_fixture()
    first = mod.evaluate_post_merge(policy=policy, **good)
    assert first["decision"] == "POST_MERGE_VERIFIED_REUSE"
    assert first["reuse_prior_certification"] is True
    assert first["full_regression_rerun"] is False
    assert first["t4_rerun"] is False
    assert not (set(policy["forbidden_output_fields"]) & set(first))

    x = copy.deepcopy(good)
    x["merge_record"]["merged_tree_sha"] = "d" * 40
    _require_revalidation(mod, policy, x, "MERGED_TREE_DIFFERS_FROM_CERTIFIED_TREE")

    x = copy.deepcopy(good)
    x["promotion_result"]["decision"] = "PROMOTION_DENIED"
    _require_revalidation(mod, policy, x, "INVALID_PRIOR_CERTIFICATION_RECORD")

    x = copy.deepcopy(good)
    x["merge_record"]["source_candidate_id"] = "OTHER-CANDIDATE"
    _require_revalidation(mod, policy, x, "SOURCE_CANDIDATE_ID_MISMATCH")

    x = copy.deepcopy(good)
    x["merge_record"]["source_candidate_head_sha"] = "d" * 40
    _require_revalidation(mod, policy, x, "SOURCE_CANDIDATE_HEAD_MISMATCH")

    x = copy.deepcopy(good)
    x["merge_record"]["target_branch"] = "release"
    _require_revalidation(mod, policy, x, "WRONG_TARGET_BRANCH")

    x = copy.deepcopy(good)
    x["merge_record"]["merge_method"] = "UNKNOWN"
    _require_revalidation(mod, policy, x, "UNSUPPORTED_MERGE_METHOD")

    x = copy.deepcopy(good)
    x["merge_record"]["pr_number"] = 0
    _require_revalidation(mod, policy, x, "INVALID_PR_NUMBER")

    x = copy.deepcopy(good)
    x["certified_candidate"]["promotion_result_sha256"] = "f" * 64
    _require_revalidation(mod, policy, x, "INVALID_PRIOR_CERTIFICATION_RECORD")

    x = copy.deepcopy(good)
    x["certified_candidate"]["provenance_identity_sha256"] = "f" * 64
    _require_revalidation(mod, policy, x, "INVALID_PRIOR_CERTIFICATION_RECORD")

    x = copy.deepcopy(good)
    x["certified_candidate"]["candidate_tree_sha"] = "BAD"
    _require_revalidation(mod, policy, x, "INVALID_PRIOR_CERTIFICATION_RECORD")

    second = copy.deepcopy(good)
    second["merge_record"]["merged_head_sha"] = "e" * 40
    second_result = mod.evaluate_post_merge(policy=policy, **second)
    assert second_result["decision"] == "POST_MERGE_VERIFIED_REUSE"
    assert second_result["post_merge_identity_sha256"] != first["post_merge_identity_sha256"]

    third = copy.deepcopy(good)
    third["merge_record"]["merge_method"] = "MERGE"
    third_result = mod.evaluate_post_merge(policy=policy, **third)
    assert third_result["decision"] == "POST_MERGE_VERIFIED_REUSE"
    assert third_result["post_merge_identity_sha256"] != first["post_merge_identity_sha256"]

    bad_policy = copy.deepcopy(policy)
    bad_policy["require_exact_tree_equivalence"] = False
    try:
        mod.validate_policy(bad_policy)
    except mod.CertificationPostMergeError:
        pass
    else:
        raise AssertionError("non-equivalent reuse policy unexpectedly accepted")

    print("CERTIFICATION_POST_MERGE_SELFTEST_PASS probes=14")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
