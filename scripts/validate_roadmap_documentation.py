#!/usr/bin/env python3
"""Validate immutable roadmap history, current lifecycle and locked future standards."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ROADMAP_DIR = DOCS / "roadmap"
REGISTRY = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"
OVERLAY = ROOT / "data/audit/roadmap_lifecycle_overlay_lot30.json"

VERSION_DOCS = [
    f"V{number:02d}_{name}.md"
    for number, name in enumerate(
        (
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
        ),
        start=1,
    )
]

REQUIRED_LOT26_FILES = [
    "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_26.md",
    "docs/LOT_26_IMPLEMENTATION_WORKLOG.md",
    "docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md",
    "config/math/multi_timeframe_alignment_v1.json",
    "config/temporal/temporal_scale_registry_v1.json",
    "config/temporal/decision_clock_policy_v1.json",
    "contracts/schemas/timeframe_market_context_state_v1.schema.json",
    "contracts/schemas/closed_bar_availability_v1.schema.json",
    "contracts/schemas/multi_timeframe_alignment_state_v1.schema.json",
    "src/crypto_quant_bot/contracts/timeframe_alignment.py",
    "src/crypto_quant_bot/market_analysis/alignment_engine.py",
    "scripts/run_lot26_multi_timeframe_alignment_engine.py",
    "scripts/validate_lot26.py",
    "reports/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_FINAL_REPORT.md",
]

REQUIRED_LOT29_FILES = [
    "docs/LOT_29_V2_DETERMINISTIC_REPLAY_AND_AUDIT.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_29.md",
    "docs/LOT_29_IMPLEMENTATION_WORKLOG.md",
    "docs/LOT_29_POST_MERGE_AUDIT.md",
    "config/replay/v2_deterministic_replay_audit_v1.json",
    "contracts/schemas/v2_deterministic_replay_audit_state_v1.schema.json",
    "data/audit/v2_deterministic_replay_and_audit_lot29.json",
    "data/audit/v2_deterministic_replay_and_audit_audit_lot29.json",
    "data/audit/v2_replay_closure_manifest_lot29.json",
    "reports/lot_29_v2_deterministic_replay_and_audit_report.md",
    "src/crypto_quant_bot/market_analysis/v2_deterministic_replay_and_audit.py",
    "src/crypto_quant_bot/market_analysis/v2_replay_audit_models.py",
    "scripts/run_lot29_v2_deterministic_replay_and_audit.py",
    "scripts/validate_lot29.py",
]

REQUIRED_LOT30_FILES = [
    "docs/LOT_30_V2_MARKET_ANALYSIS_CLOSURE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_30.md",
    "docs/LOT_30_IMPLEMENTATION_WORKLOG.md",
    "docs/LOT_30_POST_MERGE_AUDIT.md",
    "config/closure/v2_market_analysis_closure_v1.json",
    "contracts/schemas/v2_market_analysis_closure_state_v1.schema.json",
    "data/audit/v2_market_analysis_closure_lot30.json",
    "data/audit/v2_market_analysis_closure_audit_lot30.json",
    "data/audit/closure_manifest_lot30.json",
    "data/audit/roadmap_lifecycle_overlay_lot30.json",
    "reports/lot_30_v2_market_analysis_closure_report.md",
    "reports/lot30/coverage_summary.json",
    "reports/lot30/mutation/score.json",
    "src/crypto_quant_bot/market_analysis/v2_market_analysis_closure.py",
    "src/crypto_quant_bot/market_analysis/v2_market_analysis_closure_models.py",
    "scripts/run_lot30_v2_market_analysis_closure.py",
    "scripts/validate_lot30.py",
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


def load_registry() -> list[dict[str, Any]]:
    require(REGISTRY.is_file(), "historical roadmap registry is missing")
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(REGISTRY.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        require(isinstance(value, dict), f"registry row {number} is not an object")
        rows.append(value)
    return rows


def validate_history(rows: list[dict[str, Any]]) -> None:
    require(len(rows) == 178, f"expected 178 historical lots, found {len(rows)}")
    require(
        [row.get("lot_number") for row in rows] == list(range(178)),
        "lots are not continuous 0-177",
    )
    require(rows[25].get("status") == "IMPLEMENTED_VALIDATED", "Lot 25 historical status changed")
    require(rows[26].get("status") == "PLANNED_LOCKED", "historical Lot 21 snapshot changed")
    fields = {
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
        missing = fields.difference(row)
        require(not missing, f"Lot {row['lot_number']}: missing {sorted(missing)}")
        require(
            len(row.get("processing_sequence", [])) >= 4,
            f"Lot {row['lot_number']}: sequence too short",
        )
        require(
            len(row.get("failure_modes", [])) >= 3,
            f"Lot {row['lot_number']}: failure modes too short",
        )
        require(
            len(row.get("acceptance_tests", [])) >= 6,
            f"Lot {row['lot_number']}: tests too short",
        )


def validate_lifecycle() -> None:
    overlay = load_object(OVERLAY)
    require(overlay.get("latest_implemented_lot") == 30, "lifecycle latest lot must be 30")
    require(
        overlay.get("previous_overlay") == "data/audit/roadmap_lifecycle_overlay_lot29.json",
        "Lot 30 lifecycle predecessor mismatch",
    )
    lots = overlay.get("lots")
    require(isinstance(lots, dict), "lifecycle lots are missing")

    for lot_number in (26, 27, 28):
        entry = lots.get(str(lot_number))
        require(isinstance(entry, dict), f"Lot {lot_number} lifecycle entry missing")
        require(
            entry.get("status") == "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY",
            f"Lot {lot_number} validated status changed",
        )
        require(entry.get("trade_allowed") is False, f"Lot {lot_number} trading enabled")
        require(entry.get("execution_allowed") is False, f"Lot {lot_number} execution enabled")

    lot29 = lots.get("29")
    lot30 = lots.get("30")
    lot31 = lots.get("31")
    require(isinstance(lot29, dict), "Lot 29 lifecycle entry missing")
    require(isinstance(lot30, dict), "Lot 30 lifecycle entry missing")
    require(isinstance(lot31, dict), "Lot 31 lifecycle entry missing")
    require(
        lot29.get("status") == "IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY",
        "Lot 29 validated status changed",
    )
    require(lot29.get("trade_allowed") is False, "Lot 29 trading must remain disabled")
    require(lot29.get("execution_allowed") is False, "Lot 29 execution must remain disabled")
    require(
        lot30.get("status") == "IMPLEMENTED_VALIDATED_OFFLINE_CLOSURE_ONLY",
        "Lot 30 must remain validated offline closure only",
    )
    require(
        lot30.get("merged_commit") == "4551f4973ce535a6f2733ea4d92833d84ae298f7",
        "Lot 30 merged commit mismatch",
    )
    require(lot30.get("trade_allowed") is False, "Lot 30 trading must remain disabled")
    require(lot30.get("execution_allowed") is False, "Lot 30 execution must remain disabled")
    require(lot31.get("status") == "PLANNED_LOCKED", "Lot 31 must remain locked")
    require(lot31.get("implementation_started") is False, "Lot 31 must not be started")


def validate_version_docs() -> None:
    paths = [ROADMAP_DIR / name for name in VERSION_DOCS]
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    require(not missing, f"missing version documents: {missing}")
    pattern = re.compile(r"^## Lot (\d+) —", re.MULTILINE)
    lots: list[int] = []
    for path in paths:
        lots.extend(map(int, pattern.findall(path.read_text(encoding="utf-8"))))
    require(lots == list(range(178)), "version documents must contain Lots 0-177 exactly once")


def validate_lot26_files_and_boundaries() -> None:
    missing = [relative for relative in REQUIRED_LOT26_FILES if not (ROOT / relative).is_file()]
    require(not missing, f"missing Lot 26 files: {missing}")
    text = (ROOT / "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "timebar-5m",
        "timebar-15m",
        "ASOF_BACKWARD",
        "forecast_generation_allowed=false",
        "probability_claims_allowed=false",
        "execution_allowed=false",
        "trade_allowed=false",
    ):
        require(token in text, f"Lot 26 contract missing boundary: {token}")
    status = (ROOT / "docs/LOT_26_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")
    require(
        "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY" in status,
        "Lot 26 status is not current",
    )


def validate_lot29_release() -> None:
    missing = [relative for relative in REQUIRED_LOT29_FILES if not (ROOT / relative).is_file()]
    require(not missing, f"missing Lot 29 release files: {missing}")

    state = load_object(ROOT / "data/audit/v2_deterministic_replay_and_audit_lot29.json")
    audit = load_object(ROOT / "data/audit/v2_deterministic_replay_and_audit_audit_lot29.json")
    closure = load_object(ROOT / "data/audit/v2_replay_closure_manifest_lot29.json")
    worklog = (ROOT / "docs/LOT_29_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")
    post_merge = (ROOT / "docs/LOT_29_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/ROADMAP_V1_TO_V21.md").read_text(encoding="utf-8")

    require(state.get("replay_status") == "MATCH", "Lot 29 replay status changed")
    require(state.get("analysis_only") is True, "Lot 29 analysis-only invariant changed")
    require(state.get("used_for_decision") is False, "Lot 29 decision permission enabled")
    require(state.get("trade_allowed") is False, "Lot 29 trading permission enabled")
    require(state.get("execution_allowed") is False, "Lot 29 execution permission enabled")
    require(state.get("approved_size") == 0, "Lot 29 approved size changed")
    require(state.get("closure_manifest") == closure, "Lot 29 closure differs from state")
    require(audit.get("output_checksum") == state.get("output_checksum"), "Lot 29 audit link mismatch")
    require(audit.get("chain_checksum") == closure.get("chain_checksum"), "Lot 29 chain link mismatch")
    require(closure.get("lot_sequence") == list(range(21, 29)), "Lot 29 lot sequence mismatch")
    require(closure.get("artifact_count") == 8, "Lot 29 artifact count mismatch")
    require(closure.get("validator_count") == 8, "Lot 29 validator count mismatch")
    require(
        "IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY" in worklog,
        "Lot 29 worklog status is not current",
    )
    require("GO_LOT29_POST_MERGE_AUDIT" in post_merge, "Lot 29 post-merge verdict missing")
    require("Lot 29 : `IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY`" in roadmap, "roadmap Lot 29 status missing")


def validate_lot30_release() -> None:
    missing = [relative for relative in REQUIRED_LOT30_FILES if not (ROOT / relative).is_file()]
    require(not missing, f"missing Lot 30 release files: {missing}")

    state = load_object(ROOT / "data/audit/v2_market_analysis_closure_lot30.json")
    audit = load_object(ROOT / "data/audit/v2_market_analysis_closure_audit_lot30.json")
    manifest = load_object(ROOT / "data/audit/closure_manifest_lot30.json")
    coverage = load_object(ROOT / "reports/lot30/coverage_summary.json")
    mutation = load_object(ROOT / "reports/lot30/mutation/score.json")
    worklog = (ROOT / "docs/LOT_30_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")
    post_merge = (ROOT / "docs/LOT_30_POST_MERGE_AUDIT.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/ROADMAP_V1_TO_V21.md").read_text(encoding="utf-8")

    expected_chain = "2a598990adaec7ebc1368f30295a0130d4d8bd8f89c9610772347f25ba6c17cf"
    require(state.get("closure_manifest") == manifest, "Lot 30 manifest differs from state")
    require(audit.get("output_checksum") == state.get("output_checksum"), "Lot 30 audit link mismatch")
    require(audit.get("final_chain_checksum") == expected_chain, "Lot 30 audit chain mismatch")
    require(manifest.get("final_chain_checksum") == expected_chain, "Lot 30 manifest chain mismatch")
    require(manifest.get("covered_lot_sequence") == list(range(21, 31)), "Lot 30 lot sequence mismatch")
    require(manifest.get("upstream_lot_sequence") == list(range(21, 29)), "Lot 30 upstream sequence mismatch")
    require(manifest.get("negative_control_count") == 5, "Lot 30 negative-control count mismatch")
    require(state.get("analysis_only") is True, "Lot 30 analysis-only invariant changed")
    require(state.get("used_for_decision") is False, "Lot 30 decision permission enabled")
    require(state.get("signal_generation_allowed") is False, "Lot 30 signal permission enabled")
    require(state.get("risk_approval_allowed") is False, "Lot 30 risk permission enabled")
    require(state.get("order_routing_allowed") is False, "Lot 30 order permission enabled")
    require(state.get("trade_allowed") is False, "Lot 30 trading permission enabled")
    require(state.get("execution_allowed") is False, "Lot 30 execution permission enabled")
    require(state.get("approved_size") == 0, "Lot 30 approved size changed")
    require(coverage.get("line_coverage_percent", 0) >= 95.0, "Lot 30 line coverage below gate")
    require(coverage.get("branch_coverage_percent", 0) >= 90.0, "Lot 30 branch coverage below gate")
    require(mutation.get("score_percent", 0) >= 80.0, "Lot 30 mutation score below gate")
    require(mutation.get("status") == "PASS", "Lot 30 mutation evidence is not PASS")
    require(
        "IMPLEMENTED_VALIDATED_OFFLINE_CLOSURE_ONLY" in worklog,
        "Lot 30 worklog status is not current",
    )
    require("GO_LOT30_POST_MERGE_AUDIT" in post_merge, "Lot 30 post-merge verdict missing")
    require("Lot 31 remains `PLANNED_LOCKED`" in post_merge, "Lot 31 lock statement missing")
    require("Dernier lot dont l'implémentation est terminée : **Lot 30**" in roadmap, "roadmap current Lot 30 status missing")


def validate_portfolio_risk_standard() -> None:
    missing = [
        relative for relative in REQUIRED_PORTFOLIO_RISK_FILES if not (ROOT / relative).is_file()
    ]
    require(not missing, f"missing canonical portfolio-risk files: {missing}")

    standard = (ROOT / REQUIRED_PORTFOLIO_RISK_FILES[0]).read_text(encoding="utf-8")
    addendum = (ROOT / REQUIRED_PORTFOLIO_RISK_FILES[1]).read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/ROADMAP_V1_TO_V21.md").read_text(encoding="utf-8")

    standard_tokens = (
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
        "SNAPSHOT_CONFLICT",
        "AVERAGING_DOWN_FORBIDDEN",
        "NetLiquidationPnL <= 0",
        "KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE",
    )
    for token in standard_tokens:
        require(token in standard, f"portfolio-risk standard missing token: {token}")

    addendum_tokens = (
        "Lot 74",
        "Lot 75",
        "Lot 76",
        "Lot 77",
        "Lot 78",
        "Lot 79",
        "Lot 80",
        "Lot 88",
        "Lot 89",
        "Lot 90",
        "Lot 93",
        "AVERAGING_DOWN_FORBIDDEN",
    )
    for token in addendum_tokens:
        require(token in addendum, f"V7/V9 addendum missing token: {token}")

    snapshot = load_object(ROOT / REQUIRED_PORTFOLIO_RISK_FILES[2])
    reservation = load_object(ROOT / REQUIRED_PORTFOLIO_RISK_FILES[3])
    require(snapshot.get("title") == "PortfolioDecisionSnapshotV1", "snapshot schema title mismatch")
    require(reservation.get("title") == "RiskReservationV1", "reservation schema title mismatch")
    require(snapshot.get("additionalProperties") is False, "snapshot schema must be strict")
    require(reservation.get("additionalProperties") is False, "reservation schema must be strict")

    snapshot_required = set(snapshot.get("required", []))
    require(
        {
            "snapshot_id",
            "snapshot_sequence",
            "ledger_watermark",
            "portfolio_state_id",
            "position_state_ids",
            "open_order_state_ids",
            "pending_intent_state_ids",
            "reservation_ids",
            "cash_reserved",
            "cash_available",
            "portfolio_risk",
            "reserved_risk",
            "portfolio_heat",
            "drawdown",
            "state_hash",
        }
        <= snapshot_required,
        "snapshot schema omits required portfolio state",
    )

    reservation_required = set(reservation.get("required", []))
    require(
        {
            "reservation_id",
            "intent_hash",
            "snapshot_id",
            "snapshot_sequence",
            "reserved_capital",
            "reserved_risk",
            "idempotency_key",
            "decision_hash",
            "status",
            "state_hash",
        }
        <= reservation_required,
        "reservation schema omits atomic binding fields",
    )

    for token in (
        "CANONICAL_PORTFOLIO_RISK_SIZING_AND_EXIT_STANDARD.md",
        "V07_V09_PORTFOLIO_RISK_NORMATIVE_ADDENDUM.md",
        "risk reservation ≠ order intent",
    ):
        require(token in roadmap, f"canonical roadmap missing portfolio-risk reference: {token}")


def validate_no_temporary_files() -> None:
    for pattern in FORBIDDEN_TEMPORARY_PATTERNS:
        require(not list(ROOT.glob(pattern)), f"temporary Lot 26 file remains: {pattern}")


def main() -> int:
    try:
        validate_history(load_registry())
        validate_lifecycle()
        validate_version_docs()
        validate_lot26_files_and_boundaries()
        validate_lot29_release()
        validate_lot30_release()
        validate_portfolio_risk_standard()
        validate_no_temporary_files()
    except (RoadmapValidationError, json.JSONDecodeError) as exc:
        print(f"ROADMAP DOCUMENTATION VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    print("ROADMAP DOCUMENTATION VALIDATION: PASS")
    print("historical_lots=178 lifecycle_latest=30 status=POST_MERGE_AUDITED next_locked=31")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
