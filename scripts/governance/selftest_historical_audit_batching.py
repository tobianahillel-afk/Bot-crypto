#!/usr/bin/env python3
"""Adversarial qualification for ENG-07.1 historical audit batching."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "plan_historical_audit_batches.py"
    spec = importlib.util.spec_from_file_location("historical_batching_selftest", path)
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
    raise AssertionError(f"historical batching negative scenario passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._load(mod.POLICY_PATH)
    mod.validate_policy(policy)

    request = mod.synthetic_request()
    first = mod.plan_batches(request, policy)
    second = mod.plan_batches(copy.deepcopy(request), policy)
    assert mod._canonical(first) == mod._canonical(second)

    flattened = [
        item["lot"] for batch in first["batches"] for item in batch["lots"]
    ]
    assert flattened == list(range(45))
    assert 45 not in flattened and 46 not in flattened
    assert len(flattened) == len(set(flattened)) == 45

    assert all(batch["lot_count"] <= 6 for batch in first["batches"])
    assert all(
        batch["complexity_total"] <= 18
        for batch in first["batches"]
        if not batch["isolated_oversized"]
    )

    high = copy.deepcopy(request)
    for item in high["lots"]:
        item["complexity"] = 10
    high_plan = mod.plan_batches(high, policy)
    assert all(batch["lot_count"] <= 1 for batch in high_plan["batches"])

    oversized = copy.deepcopy(request)
    oversized["lots"][20]["complexity"] = 25
    over_plan = mod.plan_batches(oversized, policy)
    target = [
        batch
        for batch in over_plan["batches"]
        if any(x["lot"] == 20 for x in batch["lots"])
    ]
    assert len(target) == 1
    assert target[0]["isolated_oversized"] is True
    assert target[0]["lot_count"] == 1
    assert target[0]["split_reason"] == "OVERSIZED_SINGLE_LOT"

    changed = copy.deepcopy(request)
    changed["lots"][10]["complexity"] += 1
    changed_plan = mod.plan_batches(changed, policy)
    assert changed_plan["plan_identity_sha256"] != first["plan_identity_sha256"]
    assert changed_plan["request_identity_sha256"] != first["request_identity_sha256"]

    duplicate = copy.deepcopy(request)
    duplicate["lots"][1]["lot"] = 0
    _expect(
        mod.HistoricalAuditBatchingError,
        lambda: mod.plan_batches(duplicate, policy),
        "duplicate lot",
    )

    missing = copy.deepcopy(request)
    missing["lots"].pop()
    _expect(
        mod.HistoricalAuditBatchingError,
        lambda: mod.plan_batches(missing, policy),
        "missing lot",
    )

    candidate = copy.deepcopy(request)
    candidate["lots"][-1]["lot"] = 45
    _expect(
        mod.HistoricalAuditBatchingError,
        lambda: mod.plan_batches(candidate, policy),
        "Lot45 candidate inclusion",
    )

    unordered = copy.deepcopy(request)
    unordered["lots"][2], unordered["lots"][3] = (
        unordered["lots"][3],
        unordered["lots"][2],
    )
    _expect(
        mod.HistoricalAuditBatchingError,
        lambda: mod.plan_batches(unordered, policy),
        "non-ascending request",
    )

    malformed = copy.deepcopy(request)
    malformed["lots"][5]["complexity"] = True
    _expect(
        mod.HistoricalAuditBatchingError,
        lambda: mod.plan_batches(malformed, policy),
        "boolean complexity",
    )

    too_large = copy.deepcopy(request)
    too_large["lots"][5]["complexity"] = 51
    _expect(
        mod.HistoricalAuditBatchingError,
        lambda: mod.plan_batches(too_large, policy),
        "complexity over policy maximum",
    )

    bad_policy = copy.deepcopy(policy)
    bad_policy["eligible_lot_range"]["max"] = 45
    _expect(
        mod.HistoricalAuditBatchingError,
        lambda: mod.validate_policy(bad_policy),
        "eligible range widened to Lot45",
    )

    print("HISTORICAL_AUDIT_BATCHING_SELFTEST_PASS probes=12")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
