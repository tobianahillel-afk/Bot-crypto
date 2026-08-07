#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    file_checksum,
    load_json_object,
)
from crypto_quant_bot.data_governance.market_data_quality_engine_validation import (  # noqa: E402
    MarketDataQualityError,
    lot34_safety,
)

MERGED_COMMIT = "27880f7e14f3d1c97cce9a73f9fe4b5498947068"
IMPLEMENTATION_COMMIT = "b1c6900bf19a32090ad1b2da0e59fccee0e90067"
QUALITY_EVIDENCE_COMMIT = "e1276409fab61a9b2f884435697145d38bd1c85c"
EXPECTED_STATE_CHECKSUM = "bc66816383ddf141016ad66796cc5dd4ad3442cd3594d96ad1f7db13d7c6bc01"
EXPECTED_AUDIT_CHECKSUM = "cd4410a2ea9ef6cdc061caf5115d908d03575e219eb9f4da402bff1712f6c7ce"
EXPECTED_CANONICAL_TIME_SHA256 = "bbcc809d5e32c724073273bbeb0e1d551a93b846094b21d904e1b5b923b5727d"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MarketDataQualityError(message)


def verified_payload(path: Path, checksum_field: str) -> tuple[dict[str, Any], str]:
    payload = load_json_object(path)
    content = dict(payload)
    checksum = content.pop(checksum_field, None)
    require(isinstance(checksum, str), f"{checksum_field} missing in {path.name}")
    require(canonical_checksum(content) == checksum, f"{checksum_field} mismatch in {path.name}")
    return payload, checksum


def validate_version() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    require(project["version"] == "0.34.0", "project version must be 0.34.0")
    require("Lot 34" in project["description"], "project description must identify Lot 34")


def validate_lifecycle() -> dict[str, Any]:
    previous = load_json_object(ROOT / "data/audit/roadmap_lifecycle_overlay_lot33.json")
    current = load_json_object(ROOT / "data/audit/roadmap_lifecycle_overlay_lot34.json")
    require(current["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot33.json", "Lot 34 lifecycle previous overlay mismatch")
    require(current["latest_implemented_lot"] == 34, "latest implemented lot must be 34")
    for lot in range(26, 34):
        require(current["lots"][str(lot)] == previous["lots"][str(lot)], f"Lot {lot} lifecycle was rewritten")
    lot34 = current["lots"]["34"]
    require(lot34["status"] == "IMPLEMENTED_VALIDATED_DATA_QUALITY_ONLY", "Lot 34 lifecycle status mismatch")
    require(lot34["implementation_commit"] == IMPLEMENTATION_COMMIT, "Lot 34 implementation commit mismatch")
    require(lot34["merged_commit"] == MERGED_COMMIT, "Lot 34 merged commit mismatch")
    require(lot34["pull_request"] == 28, "Lot 34 PR mismatch")
    require(lot34["runtime_mode"] == "DATA_GOVERNANCE_ONLY", "Lot 34 runtime mismatch")
    require(lot34["trade_allowed"] is False, "Lot 34 trade boundary changed")
    require(lot34["execution_allowed"] is False, "Lot 34 execution boundary changed")
    require(lot34["external_connectivity_allowed"] is False, "Lot 34 connectivity boundary changed")
    require(lot34["network_ingestion_allowed"] is False, "Lot 34 ingestion boundary changed")
    require(lot34["raw_data_mutation_allowed"] is False, "Lot 34 raw mutation boundary changed")
    require(current["lots"]["35"] == {"implementation_started": False, "status": "PLANNED_LOCKED"}, "Lot 35 must remain locked")
    require("ContinuousMarketStateV1" in current["future_capabilities_locked"], "Lot 35 capability must remain locked")
    return current


def validate_lot34_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    state, state_checksum = verified_payload(
        ROOT / "data/audit/market_data_quality_engine_lot34.json", "output_checksum"
    )
    audit, audit_checksum = verified_payload(
        ROOT / "data/audit/market_data_quality_engine_audit_lot34.json", "audit_checksum"
    )
    require(state_checksum == EXPECTED_STATE_CHECKSUM, "Lot 34 state checksum changed after merge")
    require(audit_checksum == EXPECTED_AUDIT_CHECKSUM, "Lot 34 audit checksum changed after merge")
    require(audit["state_output_checksum"] == state_checksum, "Lot 34 state/audit mismatch")
    require(state["lineage"]["canonical_time_collection_checksum"] == EXPECTED_CANONICAL_TIME_SHA256, "Lot 34 canonical-time lineage changed")
    require(file_checksum(ROOT / "data/audit/canonical_time_envelopes_lot33.json") == EXPECTED_CANONICAL_TIME_SHA256, "Lot 33 canonical-time file changed")
    require(state["anomalies"] == [], "certified Lot 34 reference fixture must remain anomaly-free")
    require(state["quarantine_record_ids"] == [], "certified Lot 34 reference fixture must remain unquarantined")
    require(state["quality_states"][0]["quality_score_bps"] == 10_000, "certified Lot 34 reference quality changed")
    require(state["veto"]["action"] == "ALLOW_ANALYSIS", "certified Lot 34 reference analysis veto changed")
    require(state["veto"]["quality_known"] is True, "certified Lot 34 reference quality became unknown")
    for field, expected in lot34_safety().items():
        require(state[field] == expected, f"Lot 34 state safety mismatch: {field}")
        require(audit[field] == expected, f"Lot 34 audit safety mismatch: {field}")
    require(load_json_object(ROOT / "data/audit/data_quality_states_lot34.json")["records"] == state["quality_states"], "Lot 34 quality-state collection mismatch")
    require(load_json_object(ROOT / "data/audit/data_anomalies_lot34.json")["records"] == state["anomalies"], "Lot 34 anomaly collection mismatch")
    require(load_json_object(ROOT / "data/audit/data_quality_veto_lot34.json") == state["veto"], "Lot 34 veto artifact mismatch")
    return state, audit


def validate_quality_proofs() -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = load_json_object(ROOT / "reports/lot34/coverage_summary.json")
    mutation = load_json_object(ROOT / "reports/lot34/mutation_summary.json")
    require(coverage["status"] == "PASS", "Lot 34 coverage evidence is not PASS")
    require(coverage["evidence_commit"] == QUALITY_EVIDENCE_COMMIT, "Lot 34 coverage evidence commit mismatch")
    require(float(coverage["line_coverage_percent"]) >= 95.0, "Lot 34 line coverage below 95%")
    require(float(coverage["branch_coverage_percent"]) >= 90.0, "Lot 34 branch coverage below 90%")
    require(coverage["anti_flake_repetitions"] >= 3, "Lot 34 anti-flake repetitions below 3")
    require(mutation["status"] == "PASS", "Lot 34 mutation evidence is not PASS")
    require(mutation["evidence_commit"] == QUALITY_EVIDENCE_COMMIT, "Lot 34 mutation evidence commit mismatch")
    require(float(mutation["mutation_score_percent"]) >= 80.0, "Lot 34 mutation score below 80%")
    require(mutation["killed_mutants"] == 1370, "Lot 34 killed-mutant evidence changed")
    require(mutation["evaluated_mutants"] == 1631, "Lot 34 evaluated-mutant evidence changed")
    return coverage, mutation


def validate_audit_documents() -> None:
    audit_doc = (ROOT / "docs/LOT_34_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    matrix_doc = (ROOT / "docs/LOT34_POST_MERGE_VALIDATION_MATRIX.md").read_text(encoding="utf-8")
    for text in (audit_doc, matrix_doc):
        require(MERGED_COMMIT in text, "post-merge document missing exact merge commit")
        require("0.34.0" in text, "post-merge document missing version 0.34.0")
        require("Lot 35" in text, "post-merge document missing Lot 35 lock")
    require("GO_LOT34_POST_MERGE" in audit_doc, "post-merge audit verdict missing")


def validate() -> dict[str, Any]:
    validate_version()
    lifecycle = validate_lifecycle()
    state, audit = validate_lot34_evidence()
    coverage, mutation = validate_quality_proofs()
    validate_audit_documents()
    result = {
        "schema_version": "lot34-post-merge-validation-v1",
        "status": "PASS",
        "verdict": "GO_LOT34_POST_MERGE",
        "project_version": "0.34.0",
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "merged_commit": MERGED_COMMIT,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "latest_implemented_lot": lifecycle["latest_implemented_lot"],
        "next_lot": 35,
        "next_lot_status": lifecycle["lots"]["35"]["status"],
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    result["validation_checksum"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return result


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (OSError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT34 POST-MERGE VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
