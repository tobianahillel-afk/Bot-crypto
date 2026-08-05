#!/usr/bin/env python3
"""Validate the immutable 0-177 roadmap and the current lifecycle overlay."""
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
OVERLAY = ROOT / "data/audit/roadmap_lifecycle_overlay_lot26.json"

CANONICAL_VERSION_DOCS = [
    "V01_DEFENSIVE_AUDIT_NO_TRADING.md",
    "V02_MARKET_ANALYSIS_OFFLINE.md",
    "V03_MARKET_DATA_GOVERNANCE.md",
    "V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md",
    "V05_ALPHA_STRATEGY_RESEARCH.md",
    "V06_BACKTESTING_EXPECTED_VALUE_TCA.md",
    "V07_MODEL_RISK_SIZING_RISK.md",
    "V08_PAPER_TRADING.md",
    "V09_PORTFOLIO_PNL_CORE.md",
    "V10_RESEARCH_OS.md",
    "V11_NEWS_AI_EVENT_CONTEXT.md",
    "V12_UI_OPERATOR_CONSOLE.md",
    "V13_API_READ_ONLY_ACCOUNT_READ_ONLY.md",
    "V14_EXCHANGE_RISK_API_HEALTH.md",
    "V15_OMS_EMS_CORE.md",
    "V16_SANDBOX_DEMO_EXECUTION.md",
    "V17_LIVE_GOVERNANCE_HUMAN_APPROVAL.md",
    "V18_OBSERVABILITY_INCIDENT_RESPONSE.md",
    "V19_HFT_RESEARCH.md",
    "V20_OPTIONS_CONTEXT.md",
    "V21_ON_CHAIN_FLOW_INTELLIGENCE.md",
]

REQUIRED_ADDENDA = [
    "V02_LOT26_NORMATIVE_ADDENDUM.md",
    "V03_CONTINUOUS_MARKET_DATA_NORMATIVE_ADDENDUM.md",
    "V04_PARTICIPANT_GAME_THEORY_NORMATIVE_ADDENDUM.md",
    "V05_MULTI_HORIZON_FORECASTING_NORMATIVE_ADDENDUM.md",
    "V15_PROTECTIVE_ORDER_LIFECYCLE_NORMATIVE_ADDENDUM.md",
    "MULTI_SCALE_STOCHASTIC_PREDICTION_AND_PARTICIPANT_INFERENCE_ADDENDUM.md",
]

REQUIRED_ARCHITECTURE_DOCS = [
    "ROADMAP_V1_TO_V21.md",
    "MASTER_SYSTEM_SPECIFICATION.md",
    "SYSTEM_EXECUTION_ARCHITECTURE.md",
    "DOMAIN_BOUNDARIES_AND_OWNERSHIP.md",
    "CANONICAL_DATA_AND_EVENT_CONTRACTS.md",
    "RUNTIME_MODES_AND_STATE_MACHINES.md",
    "STRATEGY_LIFECYCLE_AND_PROMOTION_GATES.md",
    "VETO_CONSEQUENCE_MATRIX.md",
    "CONFIGURATION_RELEASE_AND_ENVIRONMENT_GOVERNANCE.md",
    "FAILURE_DEGRADED_AND_RECOVERY_POLICY.md",
    "ROADMAP_TRACEABILITY_MATRIX.md",
    "ROADMAP_DOCUMENTATION_VALIDATION_REPORT.md",
    "HISTORICAL_IMPLEMENTATION_RECONCILIATION.md",
    "LOT_SPECIFICATION_STANDARD.md",
    "TEST_STRATEGY_COVERAGE_AND_QUALITY_GATES.md",
    "MATHEMATICAL_MODELING_AND_NUMERICAL_VALIDATION_STANDARD.md",
    "DEVELOPMENT_ENGINEERING_STANDARD.md",
    "DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md",
    "CAPABILITY_AND_CONTRACT_OWNERSHIP_REGISTRY.md",
    "MODEL_RETRAINING_AND_PROMOTION_POLICY.md",
    "ECONOMIC_OBJECTIVE_AND_RISK_UTILITY_POLICY.md",
    "LOT_FINAL_AUDIT_AND_GO_NO_GO_GATE.md",
    "TEMPORAL_MULTI_SCALE_AND_DECISION_CLOCK_ARCHITECTURE.md",
    "STOCHASTIC_CONTINUOUS_STATE_AND_MULTI_HORIZON_FORECASTING_STANDARD.md",
    "PARTICIPANT_BEHAVIOR_AND_LIQUIDITY_EXIT_ZONE_INFERENCE_STANDARD.md",
    "PROTECTIVE_ORDERS_AND_EXIT_LIFECYCLE_STANDARD.md",
    "LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md",
    "ACCEPTANCE_CRITERIA_LOT_26.md",
]


class RoadmapValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RoadmapValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"Missing JSON document: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"Expected object: {path.relative_to(ROOT)}")
    return payload


def load_registry() -> list[dict[str, Any]]:
    require(REGISTRY.is_file(), "Missing historical roadmap registry")
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(REGISTRY.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RoadmapValidationError(f"Invalid registry JSONL line {number}: {exc}") from exc
        require(isinstance(value, dict), f"Registry line {number} is not an object")
        rows.append(value)
    return rows


def validate_registry_and_overlay(rows: list[dict[str, Any]]) -> None:
    require(len(rows) == 178, f"Expected 178 lots, found {len(rows)}")
    require([row.get("lot_number") for row in rows] == list(range(178)), "Lots must remain continuous 0-177")
    require(rows[25].get("status") == "IMPLEMENTED_VALIDATED", "Lot 25 historical status changed")
    require(rows[26].get("status") == "PLANNED_LOCKED", "Lot 21 historical snapshot for Lot 26 changed")
    overlay = load_json(OVERLAY)
    require(overlay.get("latest_implemented_lot") == 26, "Lifecycle overlay must identify Lot 26")
    lots = overlay.get("lots")
    require(isinstance(lots, dict), "Lifecycle overlay lots missing")
    lot26 = lots.get("26")
    lot27 = lots.get("27")
    require(isinstance(lot26, dict), "Lot 26 lifecycle entry missing")
    require(isinstance(lot27, dict), "Lot 27 lifecycle entry missing")
    require(lot26.get("status") == "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY", "Lot 26 lifecycle status invalid")
    require(lot26.get("trade_allowed") is False, "Lot 26 trading must remain disabled")
    require(lot26.get("execution_allowed") is False, "Lot 26 execution must remain disabled")
    require(lot27.get("status") == "PLANNED_LOCKED", "Lot 27 must remain locked")
    require(lot27.get("implementation_started") is False, "Lot 27 must not be started")
    required = {
        "responsible_component", "package_boundary", "runtime_mode", "responsibility",
        "input_contracts", "output_contracts", "processing_sequence", "domain_rules",
        "failure_modes", "observability", "implementation_files", "acceptance_tests",
        "non_goals", "definition_of_done", "promotion_gate", "safety_invariants",
    }
    for row in rows[26:]:
        lot = row["lot_number"]
        missing = required.difference(row)
        require(not missing, f"Lot {lot}: missing {sorted(missing)}")
        require(len(row.get("processing_sequence", [])) >= 4, f"Lot {lot}: insufficient sequence")
        require(len(row.get("failure_modes", [])) >= 3, f"Lot {lot}: insufficient failures")
        require(len(row.get("implementation_files", [])) >= 4, f"Lot {lot}: insufficient files")
        require(len(row.get("acceptance_tests", [])) >= 6, f"Lot {lot}: insufficient tests")
        require(len(row.get("non_goals", [])) >= 2, f"Lot {lot}: insufficient non-goals")
    for row in rows[:26]:
        lot = row["lot_number"]
        require(row.get("historical_paths_must_not_be_renamed") is True, f"Lot {lot}: historical paths unlocked")
        require(str(row.get("historical_evidence_policy", "")).startswith("HISTORICAL_"), f"Lot {lot}: historical policy missing")


def validate_versions() -> None:
    paths = [ROADMAP_DIR / name for name in CANONICAL_VERSION_DOCS]
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    require(not missing, f"Missing canonical version docs: {missing}")
    section = re.compile(r"^## Lot (\d+) —", re.MULTILINE)
    lots: list[int] = []
    for path in paths:
        content = path.read_text(encoding="utf-8")
        lots.extend(map(int, section.findall(content)))
    require(lots == list(range(178)), "Version docs must contain Lots 0-177 exactly once")
    missing_addenda = [name for name in REQUIRED_ADDENDA if not (ROADMAP_DIR / name).is_file()]
    require(not missing_addenda, f"Missing roadmap addenda: {missing_addenda}")


def require_terms(name: str, terms: tuple[str, ...]) -> None:
    path = DOCS / name
    require(path.is_file(), f"Missing architecture document: docs/{name}")
    content = path.read_text(encoding="utf-8").casefold()
    for term in terms:
        require(term.casefold() in content, f"{name} missing: {term}")


def validate_standards() -> None:
    for name in REQUIRED_ARCHITECTURE_DOCS:
        require((DOCS / name).is_file(), f"Missing architecture document: docs/{name}")
    require_terms("ROADMAP_V1_TO_V21.md", ("Lot 26", "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY", "Lot 27", "PLANNED_LOCKED"))
    require_terms("TEST_STRATEGY_COVERAGE_AND_QUALITY_GATES.md", ("line coverage globale du package runtime >= 90 %", "branch coverage globale du package runtime >= 85 %", "mutation score", "GO/NO-GO"))
    require_terms("MATHEMATICAL_MODELING_AND_NUMERICAL_VALIDATION_STANDARD.md", ("anti-lookahead", "stabilité numérique", "implémentation de référence", "NO_GO_MATHEMATICAL_VALIDATION"))
    require_terms("DEVELOPMENT_ENGINEERING_STANDARD.md", ("fonction <= 50 lignes logiques", "complexité cyclomatique", "aucune duplication", "NO_GO_ENGINEERING_QUALITY"))
    require_terms("DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md", ("decision_id", "input_checksums", "output_checksum", "Replay d'audit", "NO_GO_AUDITABILITY"))
    require_terms("LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md", ("timebar-5m", "timebar-15m", "ASOF_BACKWARD", "forecast_generation_allowed=false", "trade_allowed=false"))


def validate_historical_paths() -> None:
    path_re = re.compile(r"(?<![A-Za-z0-9_.-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:jsonl|json|py|md|sh|toml|txt|csv))")
    for lot in range(22, 27):
        acceptance = DOCS / f"ACCEPTANCE_CRITERIA_LOT_{lot}.md"
        require(acceptance.is_file(), f"Missing acceptance Lot {lot}")
        refs = sorted(set(path_re.findall(acceptance.read_text(encoding="utf-8"))))
        require(refs, f"Lot {lot}: no referenced paths")
        missing = [path for path in refs if not (ROOT / path).is_file()]
        require(not missing, f"Lot {lot}: missing referenced paths {missing}")


def validate_no_temporary_files() -> None:
    patterns = [
        ".github/scripts/roadmap_payload_*.txt", ".github/scripts/deep_roadmap_payload_*.txt",
        ".github/workflows/apply-pre-lot26-readiness.yml", ".github/workflows/apply-lot26-migration.yml",
        "scripts/pre_lot26_payload_*.txt", "scripts/lot26_payload_*.txt",
        "scripts/apply_pre_lot26_readiness.py", "scripts/apply_lot26_migration.py",
    ]
    for pattern in patterns:
        require(not list(ROOT.glob(pattern)), f"Temporary generation file remains: {pattern}")


def main() -> int:
    try:
        rows = load_registry()
        validate_registry_and_overlay(rows)
        validate_versions()
        validate_standards()
        validate_historical_paths()
        validate_no_temporary_files()
    except RoadmapValidationError as exc:
        print(f"ROADMAP DOCUMENTATION VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    print("ROADMAP DOCUMENTATION VALIDATION: PASS")
    print("historical_lots=178 lifecycle_latest=26 next_locked=27 versions=21")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
