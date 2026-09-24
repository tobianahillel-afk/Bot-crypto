#!/usr/bin/env python3
"""Plan deterministic read-only historical-audit batches from explicit lot complexities."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "historical_audit_batching_v1.json"


class HistoricalAuditBatchingError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalAuditBatchingError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HistoricalAuditBatchingError(f"{path} must contain an object")
    return value


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise HistoricalAuditBatchingError(
            f"value is not canonical-JSON encodable: {exc}"
        ) from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise HistoricalAuditBatchingError("unsupported batching policy schema_version")
    if policy.get("policy_kind") != "historical_audit_batching_v1":
        raise HistoricalAuditBatchingError("invalid batching policy kind")
    if policy.get("semantics") != "EXPLICIT_COMPLEXITY_GREEDY_ASCENDING_READ_ONLY":
        raise HistoricalAuditBatchingError("batching semantics drift")
    if policy.get("eligible_lot_range") != {"min": 0, "max": 44}:
        raise HistoricalAuditBatchingError("eligible historical lot range drift")
    if policy.get("suspended_candidate_lot") != 45:
        raise HistoricalAuditBatchingError("Lot45 exclusion drift")
    if policy.get("next_locked_lot") != 46:
        raise HistoricalAuditBatchingError("Lot46 lock drift")
    complexity = policy.get("complexity")
    if complexity != {"min": 1, "max": 50, "normal_batch_budget": 18}:
        raise HistoricalAuditBatchingError("complexity bounds/budget drift")
    if policy.get("max_lots_per_batch") != 6:
        raise HistoricalAuditBatchingError("batch lot-count budget drift")
    if policy.get("oversized_lot_policy") != "ISOLATE_SINGLE_LOT":
        raise HistoricalAuditBatchingError("oversized lot policy drift")
    if policy.get("ordering") != "ASCENDING_LOT_ID":
        raise HistoricalAuditBatchingError("historical ordering drift")
    if policy.get("mutation_policy") != "READ_ONLY_NO_HISTORICAL_EVIDENCE_MUTATION":
        raise HistoricalAuditBatchingError("read-only mutation policy drift")
    if policy.get("identity_algorithm") != "SHA256_CANONICAL_JSON":
        raise HistoricalAuditBatchingError("identity algorithm drift")


def validate_request(request: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, int]]:
    if request.get("schema_version") != 1:
        raise HistoricalAuditBatchingError("unsupported request schema_version")
    if request.get("request_kind") != "historical_audit_batch_request_v1":
        raise HistoricalAuditBatchingError("invalid request kind")
    if set(request) != {"schema_version", "request_kind", "lots"}:
        raise HistoricalAuditBatchingError("request contains unsupported fields")
    lots = request.get("lots")
    if not isinstance(lots, list):
        raise HistoricalAuditBatchingError("request lots must be a list")

    expected = list(
        range(
            policy["eligible_lot_range"]["min"],
            policy["eligible_lot_range"]["max"] + 1,
        )
    )
    if len(lots) != len(expected):
        raise HistoricalAuditBatchingError(
            f"request must contain exactly {len(expected)} historical lots"
        )

    normalized: list[dict[str, int]] = []
    observed: list[int] = []
    for index, item in enumerate(lots):
        if not isinstance(item, dict) or set(item) != {"lot", "complexity"}:
            raise HistoricalAuditBatchingError(
                f"lot descriptor at index {index} has invalid shape"
            )
        lot = item["lot"]
        complexity = item["complexity"]
        if not isinstance(lot, int) or isinstance(lot, bool):
            raise HistoricalAuditBatchingError("lot id must be integer")
        if not isinstance(complexity, int) or isinstance(complexity, bool):
            raise HistoricalAuditBatchingError(
                f"Lot {lot} complexity must be integer"
            )
        if not policy["complexity"]["min"] <= complexity <= policy["complexity"]["max"]:
            raise HistoricalAuditBatchingError(
                f"Lot {lot} complexity out of bounds: {complexity}"
            )
        observed.append(lot)
        normalized.append({"lot": lot, "complexity": complexity})

    if observed != expected:
        if len(observed) != len(set(observed)):
            raise HistoricalAuditBatchingError("duplicate historical lot descriptor")
        missing = sorted(set(expected) - set(observed))
        out_of_range = sorted(set(observed) - set(expected))
        if out_of_range:
            raise HistoricalAuditBatchingError(
                f"out-of-range lot descriptors forbidden: {out_of_range}"
            )
        if missing:
            raise HistoricalAuditBatchingError(
                f"historical lots missing from request: {missing}"
            )
        raise HistoricalAuditBatchingError(
            "historical lot descriptors must be in ascending order"
        )
    return normalized


def _finalize_batch(
    index: int,
    descriptors: list[dict[str, int]],
    *,
    oversized: bool,
    split_reason: str,
) -> dict[str, Any]:
    if not descriptors:
        raise HistoricalAuditBatchingError("cannot finalize empty batch")
    material = {
        "batch_index": index,
        "lot_start": descriptors[0]["lot"],
        "lot_end": descriptors[-1]["lot"],
        "lot_count": len(descriptors),
        "complexity_total": sum(x["complexity"] for x in descriptors),
        "lots": descriptors,
        "isolated_oversized": oversized,
        "split_reason": split_reason,
        "read_only": True,
    }
    return {**material, "batch_identity_sha256": _sha256(material)}


def plan_batches(
    request: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    validate_policy(policy)
    lots = validate_request(request, policy)
    budget = policy["complexity"]["normal_batch_budget"]
    max_count = policy["max_lots_per_batch"]

    batches: list[dict[str, Any]] = []
    current: list[dict[str, int]] = []
    current_complexity = 0

    def flush(reason: str) -> None:
        nonlocal current, current_complexity
        if current:
            batches.append(
                _finalize_batch(
                    len(batches) + 1,
                    current,
                    oversized=False,
                    split_reason=reason,
                )
            )
            current = []
            current_complexity = 0

    for descriptor in lots:
        complexity = descriptor["complexity"]
        if complexity > budget:
            flush("BEFORE_OVERSIZED_LOT")
            batches.append(
                _finalize_batch(
                    len(batches) + 1,
                    [descriptor],
                    oversized=True,
                    split_reason="OVERSIZED_SINGLE_LOT",
                )
            )
            continue

        count_exceeded = len(current) + 1 > max_count
        complexity_exceeded = current_complexity + complexity > budget
        if current and (count_exceeded or complexity_exceeded):
            reason = (
                "MAX_LOT_COUNT"
                if count_exceeded and not complexity_exceeded
                else "COMPLEXITY_BUDGET"
                if complexity_exceeded and not count_exceeded
                else "COUNT_AND_COMPLEXITY_BUDGET"
            )
            flush(reason)

        current.append(descriptor)
        current_complexity += complexity

    flush("END_OF_PLAN")

    flattened = [item["lot"] for batch in batches for item in batch["lots"]]
    expected = list(range(0, 45))
    if flattened != expected:
        raise HistoricalAuditBatchingError(
            "internal plan invariant failed: coverage/order drift"
        )
    if any(batch["lot_count"] > max_count for batch in batches):
        raise HistoricalAuditBatchingError(
            "internal plan invariant failed: lot-count budget exceeded"
        )
    for batch in batches:
        if (
            not batch["isolated_oversized"]
            and batch["complexity_total"] > budget
        ):
            raise HistoricalAuditBatchingError(
                "internal plan invariant failed: complexity budget exceeded"
            )
        if batch["isolated_oversized"] and (
            batch["lot_count"] != 1 or batch["complexity_total"] <= budget
        ):
            raise HistoricalAuditBatchingError(
                "internal plan invariant failed: malformed oversized batch"
            )

    policy_identity = _sha256(policy)
    request_identity = _sha256(request)
    plan_material = {
        "plan_version": 1,
        "eligible_lot_range": policy["eligible_lot_range"],
        "excluded_lots": {
            "suspended_candidate": policy["suspended_candidate_lot"],
            "next_locked": policy["next_locked_lot"],
        },
        "policy_identity_sha256": policy_identity,
        "request_identity_sha256": request_identity,
        "batch_count": len(batches),
        "batches": batches,
        "read_only": True,
        "historical_evidence_mutation_allowed": False,
    }
    return {
        **plan_material,
        "plan_identity_sha256": _sha256(plan_material),
    }


def synthetic_request() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "request_kind": "historical_audit_batch_request_v1",
        "lots": [
            {"lot": lot, "complexity": 1 + (lot % 5)}
            for lot in range(45)
        ],
    }


def self_check(policy: dict[str, Any]) -> None:
    validate_policy(policy)
    request = synthetic_request()
    first = plan_batches(request, policy)
    second = plan_batches(json.loads(json.dumps(request)), policy)
    if _canonical(first) != _canonical(second):
        raise HistoricalAuditBatchingError("deterministic replay mismatch")
    flattened = [
        item["lot"] for batch in first["batches"] for item in batch["lots"]
    ]
    if flattened != list(range(45)):
        raise HistoricalAuditBatchingError("self-check historical coverage mismatch")
    if any(lot >= 45 for lot in flattened):
        raise HistoricalAuditBatchingError("self-check included non-historical lot")
    print(
        "HISTORICAL_AUDIT_BATCHING_SELF_CHECK_PASS "
        f"batches={first['batch_count']} plan={first['plan_identity_sha256']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-check", action="store_true")
    group.add_argument("--request", type=Path)
    args = parser.parse_args()
    try:
        policy = _load(POLICY_PATH)
        if args.self_check:
            self_check(policy)
            return 0
        request = _load(args.request)
        result = plan_batches(request, policy)
    except (HistoricalAuditBatchingError, KeyError, TypeError) as exc:
        print(f"HISTORICAL_AUDIT_BATCHING_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
