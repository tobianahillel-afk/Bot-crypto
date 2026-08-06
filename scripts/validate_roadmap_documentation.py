#!/usr/bin/env python3
"""Validate immutable roadmap history, current lifecycle and certified releases."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ROADMAP_DIR = DOCS / "roadmap"
REGISTRY = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
OVERLAY = ROOT / "data/audit/roadmap_lifecycle_overlay_lot32.json"

VERSION_NAMES = (
    "DEFENSIVE_AUDIT_NO_TRADING",
    "MARKET_ANALYSIS_OFFLINE",
    "MARKET_DATA_GOVERNANCE",
    "MICROSTRUCTURE_LIQUIDITY_GAME_THEORY",
    "ALPHA_STRATEGY_RESEARCH",
    "BACKTESTING_EXPECTED_VALUE_TCA",
    "MODEL_RISK_SIZING_RISK",
    "PAPER_TRADING",
    "PORTFOLIO_PNL_CORE",
    "RESEARCH_OS",
    "NEWS_AI_EVENT_CONTEXT",
    "UI_OPERATOR_CONSOLE",
    "API_READ_ONLY_ACCOUNT_READ_ONLY",
    "EXCHANGE_RISK_API_HEALTH",
    "OMS_EMS_CORE",
    "SANDBOX_DEMO_EXECUTION",
    "LIVE_GOVERNANCE_HUMAN_APPROVAL",
    "OBSERVABILITY_INCIDENT_RESPONSE",
    "HFT_RESEARCH",
    "OPTIONS_CONTEXT",
    "ON_CHAIN_FLOW_INTELLIGENCE",
)
VERSION_DOCS = [f"V{number:02d}_{name}.md" for number, name in enumerate(VERSION_NAMES, 1)]

REQUIRED_LOT26_FILES = [
    "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_26.md",
    "docs/LOT_26_IMPLEMENTATION_WORKLOG.md",
    "docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md",
    "config/math/multi_timeframe_alignment_v1.json",
    "config/temporal/temporal_scale_registry_v1.json",
    "config/temporal/decision_clock_policy_v1.json",
    "scripts/run_lot26_multi_timeframe_alignment_engine.py",
    "scripts/validate_lot26.py",
]
REQUIRED_LOT29_FILES = [
    "docs/LOT_29_V2_DETERMINISTIC_REPLAY_AND_AUDIT.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_29.md",
    "docs/LOT_29_IMPLEMENTATION_WORKLOG.md",
    "docs/LOT_29_POST_MERGE_AUDIT.md",
    "data/audit/v2_deterministic_replay_and_audit_lot29.json",
    "data/audit/v2_deterministic_replay_and_audit_audit_lot29.json",
    "data/audit/v2_replay_closure_manifest_lot29.json",
    "scripts/validate_lot29.py",
]
REQUIRED_LOT30_FILES = [
    "docs/LOT_30_V2_MARKET_ANALYSIS_CLOSURE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_30.md",
    "docs/LOT_30_IMPLEMENTATION_WORKLOG.md",
    "docs/LOT_30_POST_MERGE_AUDIT.md",
    "data/audit/v2_market_analysis_closure_lot30.json",
    "data/audit/v2_market_analysis_closure_audit_lot30.json",
    "data/audit/closure_manifest_lot30.json",
    "data/audit/roadmap_lifecycle_overlay_lot30.json",
    "reports/lot30/coverage_summary.json",
    "reports/lot30/mutation/score.json",
    "scripts/validate_lot30.py",
]
REQUIRED_LOT31_FILES = [
    "docs/LOT_31_MARKET_DATA_GOVERNANCE_SCOPE_AND_SOURCE_REGISTRY.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_31.md",
    "docs/LOT_31_IMPLEMENTATION_WORKLOG.md",
    "docs/LOT_31_POST_MERGE_AUDIT.md",
    "data/audit/market_data_governance_scope_and_source_registry_lot31.json",
    "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json",
    "data/audit/source_registry_lot31.json",
    "data/audit/roadmap_lifecycle_overlay_lot31.json",
    "reports/lot31/coverage_summary.json",
    "reports/lot31/mutation_summary.json",
    "scripts/validate_lot31.py",
    "scripts/validate_lot31_no_connectivity.py",
]
REQUIRED_LOT32_FILES = [
    "docs/LOT_32_V3_ENTRY_GATE.md",
    "docs/LOT_32_INSTRUMENT_SYMBOL_AND_CONTRACT_NORMALIZATION.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_32.md",
    "docs/LOT_32_IMPLEMENTATION_WORKLOG.md",
    "docs/LOT_32_POST_MERGE_AUDIT.md",
    "docs/LOT32_POST_MERGE_VALIDATION_MATRIX.md",
    "config/data_governance/instrument_symbol_contract_normalization_v1.json",
    "contracts/schemas/instrument_specification_v1.schema.json",
    "contracts/schemas/instrument_registry_v1.schema.json",
    "contracts/schemas/instrument_symbol_contract_normalization_state_v1.schema.json",
    "contracts/schemas/instrument_symbol_contract_normalization_audit_v1.schema.json",
    "data/audit/instrument_symbol_and_contract_normalization_lot32.json",
    "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json",
    "data/audit/instrument_registry_lot32.json",
    "data/audit/roadmap_lifecycle_overlay_lot32.json",
    "reports/lot32/coverage_summary.json",
    "reports/lot32/mutation_summary.json",
    "scripts/validate_lot32.py",
    "scripts/validate_lot32_no_connectivity.py",
]
REQUIRED_PORTFOLIO_RISK_FILES = [
    "docs/CANONICAL_PORTFOLIO_RISK_SIZING_AND_EXIT_STANDARD.md",
    "docs/roadmap/V07_V09_PORTFOLIO_RISK_NORMATIVE_ADDENDUM.md",
    "contracts/schemas/portfolio_decision_snapshot_v1.schema.json",
    "contracts/schemas/risk_reservation_v1.schema.json",
]
FORBIDDEN_TEMPORARY_PATTERNS = [
    ".github/workflows/apply-lot26-migration.yml",
    "scripts/apply_lot26_migration.py",
    "scripts/lot26_payload_*.txt",
]
FAIL_CLOSED_FIELDS = (
    "used_for_decision",
    "external_connectivity_allowed",
    "network_ingestion_allowed",
    "real_credentials_allowed",
    "signal_generation_allowed",
    "risk_approval_allowed",
    "order_routing_allowed",
    "trade_allowed",
    "execution_allowed",
)


class RoadmapValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RoadmapValidationError(message)


def load_object(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"expected JSON object: {path.relative_to(ROOT)}")
    return payload


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_files(paths: list[str], label: str) -> None:
    missing = [path for path in paths if not (ROOT / path).is_file()]
    require(not missing, f"missing {label} files: {missing}")


def load_registry() -> list[dict[str, Any]]:
    require(REGISTRY.is_file(), "historical roadmap registry is missing")
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(REGISTRY.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        require(isinstance(value, dict), f"registry row {number} is not an object")
        rows.append(value)
    return rows


def validate_history(rows: list[dict[str, Any]]) -> None:
    require(len(rows) == 178, f"expected 178 historical lots, found {len(rows)}")
    require([row.get("lot_number") for row in rows] == list(range(178)), "lots are not continuous")
    require(rows[25].get("status") == "IMPLEMENTED_VALIDATED", "Lot 25 status changed")
    require(rows[26].get("status") == "PLANNED_LOCKED", "historical snapshot changed")
    required = {
        "responsible_component",
        "package_boundary",
        "runtime_mode",
        "responsibility",
        "input_contracts",
        "output_contracts",
        "processing_sequence",
        "failure_modes",
        "implementation_files",
        "acceptance_tests",
        "non_goals",
        "definition_of_done",
        "promotion_gate",
        "safety_invariants",
    }
    for row in rows[26:]:
        missing = required.difference(row)
        require(not missing, f"Lot {row['lot_number']}: missing {sorted(missing)}")
        require(len(row.get("processing_sequence", [])) >= 4, "processing sequence too short")
        require(len(row.get("failure_modes", [])) >= 3, "failure modes too short")
        require(len(row.get("acceptance_tests", [])) >= 6, "acceptance tests too short")


def validate_version_docs() -> None:
    paths = [ROADMAP_DIR / name for name in VERSION_DOCS]
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    require(not missing, f"missing version documents: {missing}")
    pattern = re.compile(r"^## Lot (\d+) —", re.MULTILINE)
    lots: list[int] = []
    for path in paths:
        lots.extend(map(int, pattern.findall(path.read_text(encoding="utf-8"))))
    require(lots == list(range(178)), "version documents must contain Lots 0-177 exactly once")


def validate_descriptive_lots(lots: dict[str, Any]) -> None:
    for lot_number in (26, 27, 28):
        entry = lots.get(str(lot_number))
        require(isinstance(entry, dict), f"Lot {lot_number} lifecycle entry missing")
        require(
            entry.get("status") == "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY",
            f"Lot {lot_number} validated status changed",
        )
        require(entry.get("trade_allowed") is False, f"Lot {lot_number} trading enabled")
        require(entry.get("execution_allowed") is False, f"Lot {lot_number} execution enabled")


def validate_lifecycle() -> None:
    overlay = load_object(OVERLAY)
    require(overlay.get("latest_implemented_lot") == 32, "lifecycle latest lot must be 32")
    require(
        overlay.get("previous_overlay") == "data/audit/roadmap_lifecycle_overlay_lot31.json",
        "Lot 32 lifecycle predecessor mismatch",
    )
    lots = overlay.get("lots")
    require(isinstance(lots, dict), "lifecycle lots are missing")
    validate_descriptive_lots(lots)
    expected = {
        "29": "IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY",
        "30": "IMPLEMENTED_VALIDATED_OFFLINE_CLOSURE_ONLY",
        "31": "IMPLEMENTED_VALIDATED_METADATA_ONLY",
        "32": "IMPLEMENTED_VALIDATED_NORMALIZATION_ONLY",
    }
    for number, status in expected.items():
        entry = lots.get(number)
        require(isinstance(entry, dict), f"Lot {number} lifecycle entry missing")
        require(entry.get("status") == status, f"Lot {number} validated status changed")
        require(entry.get("trade_allowed") is False, f"Lot {number} trading enabled")
        require(entry.get("execution_allowed") is False, f"Lot {number} execution enabled")
    lot32 = lots["32"]
    require(
        lot32.get("merged_commit") == "7187f2ebfebeb67292c8a521e7e8bdbc653c3086",
        "Lot 32 merged commit mismatch",
    )
    require(lot32.get("external_connectivity_allowed") is False, "Lot 32 connectivity enabled")
    require(lot32.get("network_ingestion_allowed") is False, "Lot 32 ingestion enabled")
    require(
        lots.get("33") == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 33 must remain locked",
    )


def validate_lot26_release() -> None:
    require_files(REQUIRED_LOT26_FILES, "Lot 26")
    text = (ROOT / "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "timebar-5m",
        "timebar-15m",
        "ASOF_BACKWARD",
        "forecast_generation_allowed=false",
        "execution_allowed=false",
        "trade_allowed=false",
    ):
        require(token in text, f"Lot 26 contract missing boundary: {token}")


def validate_lot29_release() -> None:
    require_files(REQUIRED_LOT29_FILES, "Lot 29")
    state = load_object(ROOT / "data/audit/v2_deterministic_replay_and_audit_lot29.json")
    audit = load_object(ROOT / "data/audit/v2_deterministic_replay_and_audit_audit_lot29.json")
    closure = load_object(ROOT / "data/audit/v2_replay_closure_manifest_lot29.json")
    require(state.get("replay_status") == "MATCH", "Lot 29 replay status changed")
    require(state.get("closure_manifest") == closure, "Lot 29 closure differs from state")
    require(audit.get("output_checksum") == state.get("output_checksum"), "Lot 29 audit mismatch")
    require(audit.get("chain_checksum") == closure.get("chain_checksum"), "Lot 29 chain mismatch")
    require(closure.get("lot_sequence") == list(range(21, 29)), "Lot 29 sequence mismatch")
    require(closure.get("artifact_count") == 8, "Lot 29 artifact count mismatch")
    require(closure.get("validator_count") == 8, "Lot 29 validator count mismatch")


def validate_lot30_release() -> None:
    require_files(REQUIRED_LOT30_FILES, "Lot 30")
    state = load_object(ROOT / "data/audit/v2_market_analysis_closure_lot30.json")
    audit = load_object(ROOT / "data/audit/v2_market_analysis_closure_audit_lot30.json")
    manifest = load_object(ROOT / "data/audit/closure_manifest_lot30.json")
    coverage = load_object(ROOT / "reports/lot30/coverage_summary.json")
    mutation = load_object(ROOT / "reports/lot30/mutation/score.json")
    chain = "2a598990adaec7ebc1368f30295a0130d4d8bd8f89c9610772347f25ba6c17cf"
    require(state.get("closure_manifest") == manifest, "Lot 30 manifest differs from state")
    require(audit.get("output_checksum") == state.get("output_checksum"), "Lot 30 audit mismatch")
    require(audit.get("final_chain_checksum") == chain, "Lot 30 audit chain mismatch")
    require(manifest.get("final_chain_checksum") == chain, "Lot 30 manifest chain mismatch")
    require(manifest.get("covered_lot_sequence") == list(range(21, 31)), "Lot 30 sequence mismatch")
    require(manifest.get("negative_control_count") == 5, "Lot 30 controls mismatch")
    require(coverage.get("line_coverage_percent", 0) >= 95.0, "Lot 30 line coverage below gate")
    require(coverage.get("branch_coverage_percent", 0) >= 90.0, "Lot 30 branch coverage below gate")
    require(mutation.get("score_percent", 0) >= 80.0, "Lot 30 mutation below gate")


def validate_payload_checksum(
    payload: dict[str, Any],
    field: str,
    expected: str,
    label: str,
) -> str:
    content = dict(payload)
    checksum = content.pop(field, None)
    require(isinstance(checksum, str), f"{label} checksum missing")
    require(canonical_checksum(content) == checksum, f"{label} checksum mismatch")
    require(checksum == expected, f"{label} certified checksum changed")
    return checksum


def validate_fail_closed(payloads: tuple[dict[str, Any], ...], label: str) -> None:
    for payload in payloads:
        require(payload.get("analysis_only") is True, f"{label} analysis-only changed")
        require(payload.get("approved_size") == 0, f"{label} approved size changed")
        for field in FAIL_CLOSED_FIELDS:
            require(payload.get(field) is False, f"{label} permission enabled: {field}")


def validate_lot31_release() -> None:
    require_files(REQUIRED_LOT31_FILES, "Lot 31")
    state = load_object(ROOT / "data/audit/market_data_governance_scope_and_source_registry_lot31.json")
    audit = load_object(
        ROOT / "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
    )
    registry = load_object(ROOT / "data/audit/source_registry_lot31.json")
    coverage = load_object(ROOT / "reports/lot31/coverage_summary.json")
    mutation = load_object(ROOT / "reports/lot31/mutation_summary.json")
    state_checksum = validate_payload_checksum(
        state,
        "output_checksum",
        "c25c159fa3857eba9d08c7a8ddbd15a5c61e2b1d5b2aa78eae6cbf7e13dcdf05",
        "Lot 31 state",
    )
    validate_payload_checksum(
        audit,
        "audit_checksum",
        "e06ac07872ba51a1ca21af88f5298d08a362608bc7fe69b15e4d71afbbd60b6f",
        "Lot 31 audit",
    )
    require(state.get("source_registry") == registry, "Lot 31 registry differs from state")
    require(audit.get("state_output_checksum") == state_checksum, "Lot 31 audit link mismatch")
    sources = registry.get("sources")
    require(isinstance(sources, list) and len(sources) == 3, "Lot 31 source count mismatch")
    require(sum(item.get("source_of_truth") is True for item in sources) == 1, "truth count mismatch")
    require(all(item.get("auth_mode") == "NONE" for item in sources), "Lot 31 auth enabled")
    require(all(item.get("enabled") is False for item in sources), "Lot 31 source enabled")
    require(all(item.get("connection_status") == "DISABLED" for item in sources), "connection enabled")
    validate_fail_closed((state, audit), "Lot 31")
    require(coverage.get("line_coverage_percent", 0) >= 95.0, "Lot 31 line coverage below gate")
    require(coverage.get("branch_coverage_percent", 0) >= 90.0, "Lot 31 branch coverage below gate")
    require(mutation.get("score_percent", 0) >= 80.0, "Lot 31 mutation below gate")


def validate_lot32_lineage(state: dict[str, Any], audit: dict[str, Any]) -> None:
    lineage = state.get("lineage")
    require(isinstance(lineage, dict), "Lot 32 lineage missing")
    expected = {
        "source_registry_checksum": file_checksum(ROOT / "data/audit/source_registry_lot31.json"),
        "lot31_state_checksum": file_checksum(
            ROOT / "data/audit/market_data_governance_scope_and_source_registry_lot31.json"
        ),
        "lot31_audit_checksum": file_checksum(
            ROOT / "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
        ),
    }
    for field, value in expected.items():
        require(lineage.get(field) == value, f"Lot 32 lineage mismatch: {field}")
    require(audit.get("source_registry_checksum") == expected["source_registry_checksum"], "audit lineage mismatch")


def validate_lot32_release() -> None:
    require_files(REQUIRED_LOT32_FILES, "Lot 32")
    state = load_object(ROOT / "data/audit/instrument_symbol_and_contract_normalization_lot32.json")
    audit = load_object(ROOT / "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json")
    registry = load_object(ROOT / "data/audit/instrument_registry_lot32.json")
    coverage = load_object(ROOT / "reports/lot32/coverage_summary.json")
    mutation = load_object(ROOT / "reports/lot32/mutation_summary.json")
    state_checksum = validate_payload_checksum(
        state,
        "output_checksum",
        "da269de9a3a94f83b3dd437362ae565bd38a098cbe0dc81190887347c7fce240",
        "Lot 32 state",
    )
    validate_payload_checksum(
        audit,
        "audit_checksum",
        "b69aa85d72851470f9f807d05ae27127651e6ac8d12623aed8d3f5d96f94659a",
        "Lot 32 audit",
    )
    require(state.get("instrument_registry") == registry, "Lot 32 registry differs from state")
    require(audit.get("state_output_checksum") == state_checksum, "Lot 32 audit link mismatch")
    validate_lot32_lineage(state, audit)
    require(audit.get("instrument_count") == 1, "Lot 32 instrument count mismatch")
    require(audit.get("venue_alias_count") == 3, "Lot 32 alias count mismatch")
    require(audit.get("round_trip_count") == 6, "Lot 32 round-trip count mismatch")
    require(audit.get("frozen_instrument_count") == 0, "Lot 32 frozen count mismatch")
    validate_fail_closed((state, audit), "Lot 32")
    require(coverage.get("test_count") == 57, "Lot 32 test count mismatch")
    require(coverage.get("line_coverage_percent", 0) >= 95.0, "Lot 32 line coverage below gate")
    require(coverage.get("branch_coverage_percent", 0) >= 90.0, "Lot 32 branch coverage below gate")
    require(mutation.get("mutation_score_percent", 0) >= 80.0, "Lot 32 mutation below gate")
    require(mutation.get("killed_mutants") == 175, "Lot 32 killed-mutant count changed")
    document = (ROOT / "docs/LOT_32_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    require("GO_LOT32_POST_MERGE_AUDIT" in document, "Lot 32 post-merge verdict missing")


def validate_portfolio_risk_standard() -> None:
    require_files(REQUIRED_PORTFOLIO_RISK_FILES, "portfolio-risk")
    standard = (ROOT / REQUIRED_PORTFOLIO_RISK_FILES[0]).read_text(encoding="utf-8")
    addendum = (ROOT / REQUIRED_PORTFOLIO_RISK_FILES[1]).read_text(encoding="utf-8")
    for token in (
        "PortfolioDecisionSnapshotV1",
        "RiskReservationV1",
        "R_trade(q)",
        "PortfolioHeat(P)",
        "DeltaR(q)",
        "MaxWeight",
        "HHI",
        "Drawdown_t",
        "q_liquidity",
        "q_approved",
        "AVERAGING_DOWN_FORBIDDEN",
    ):
        require(token in standard, f"portfolio-risk standard missing token: {token}")
    for token in ("Lot 74", "Lot 75", "Lot 76", "Lot 77", "Lot 78", "Lot 79", "Lot 93"):
        require(token in addendum, f"V7/V9 addendum missing token: {token}")
    snapshot = load_object(ROOT / REQUIRED_PORTFOLIO_RISK_FILES[2])
    reservation = load_object(ROOT / REQUIRED_PORTFOLIO_RISK_FILES[3])
    require(snapshot.get("title") == "PortfolioDecisionSnapshotV1", "snapshot title mismatch")
    require(reservation.get("title") == "RiskReservationV1", "reservation title mismatch")
    require(snapshot.get("additionalProperties") is False, "snapshot schema must be strict")
    require(reservation.get("additionalProperties") is False, "reservation schema must be strict")


def validate_no_temporary_files() -> None:
    for pattern in FORBIDDEN_TEMPORARY_PATTERNS:
        require(not list(ROOT.glob(pattern)), f"temporary file remains: {pattern}")


def main() -> int:
    try:
        validate_history(load_registry())
        validate_lifecycle()
        validate_version_docs()
        validate_lot26_release()
        validate_lot29_release()
        validate_lot30_release()
        validate_lot31_release()
        validate_lot32_release()
        validate_portfolio_risk_standard()
        validate_no_temporary_files()
    except (RoadmapValidationError, json.JSONDecodeError) as exc:
        print(f"ROADMAP DOCUMENTATION VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    print("ROADMAP DOCUMENTATION VALIDATION: PASS")
    print("historical_lots=178 lifecycle_latest=32 status=POST_MERGE_AUDITED next_locked=33")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
