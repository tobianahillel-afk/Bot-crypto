#!/usr/bin/env python3
"""Validate canonical roadmap, quality standards, addenda and historical evidence."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ROADMAP_DIR = DOCS / "roadmap"
REGISTRY = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"

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

REQUIRED_ROADMAP_ADDENDA = [
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
]


class RoadmapValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RoadmapValidationError(message)


def read_doc(name: str) -> str:
    path = DOCS / name
    require(path.is_file(), f"Missing architecture document: docs/{name}")
    return path.read_text(encoding="utf-8")


def require_terms(name: str, terms: list[str]) -> None:
    content = read_doc(name).casefold()
    for term in terms:
        require(term.casefold() in content, f"{name} missing: {term}")


def load_registry() -> list[dict[str, object]]:
    require(REGISTRY.is_file(), f"Missing registry: {REGISTRY}")
    rows: list[dict[str, object]] = []
    for number, line in enumerate(REGISTRY.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RoadmapValidationError(f"Invalid JSONL line {number}: {exc}") from exc
        require(isinstance(value, dict), f"Registry line {number} is not an object")
        rows.append(value)
    return rows


def validate_registry(rows: list[dict[str, object]]) -> None:
    require(len(rows) == 178, f"Expected 178 lots, found {len(rows)}")
    require([row.get("lot_number") for row in rows] == list(range(178)), "Lots must be continuous 0-177")
    require(rows[25].get("status") == "IMPLEMENTED_VALIDATED", "Lot 25 must remain validated")
    require(rows[26].get("status") == "PLANNED_LOCKED", "Lot 26 must remain next locked lot")

    required = {
        "responsible_component",
        "package_boundary",
        "runtime_mode",
        "responsibility",
        "input_contracts",
        "output_contracts",
        "processing_sequence",
        "domain_rules",
        "failure_modes",
        "observability",
        "implementation_files",
        "acceptance_tests",
        "non_goals",
        "definition_of_done",
        "promotion_gate",
        "safety_invariants",
    }
    for row in rows[26:]:
        lot = row["lot_number"]
        missing = required.difference(row)
        require(not missing, f"Lot {lot}: missing {sorted(missing)}")
        require(not str(row.get("objective", "")).startswith("Implémenter le lot"), f"Lot {lot}: generic objective")
        require(len(row.get("processing_sequence", [])) >= 4, f"Lot {lot}: insufficient sequence")
        require(len(row.get("failure_modes", [])) >= 3, f"Lot {lot}: insufficient failure modes")
        require(len(row.get("implementation_files", [])) >= 4, f"Lot {lot}: insufficient files")
        require(len(row.get("acceptance_tests", [])) >= 6, f"Lot {lot}: insufficient tests")
        require(len(row.get("non_goals", [])) >= 2, f"Lot {lot}: insufficient non-goals")

    for row in rows[:26]:
        lot = row["lot_number"]
        require(row.get("historical_paths_must_not_be_renamed") is True, f"Lot {lot}: historical paths unlocked")
        policy = str(row.get("historical_evidence_policy", ""))
        require(policy.startswith("HISTORICAL_"), f"Lot {lot}: historical policy missing")
        require(isinstance(row.get("historical_evidence_files"), list), f"Lot {lot}: evidence list missing")

    for row in rows[166:172]:
        safety = " ".join(map(str, row.get("safety_invariants", [])))
        require("HFT_LIVE=FORBIDDEN" in safety, f"Lot {row['lot_number']}: HFT live prohibition missing")


def validate_versions() -> None:
    paths = [ROADMAP_DIR / name for name in CANONICAL_VERSION_DOCS]
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    require(not missing, f"Missing canonical version docs: {missing}")
    require(len(paths) == 21, "Canonical version list must contain exactly 21 files")

    lots: list[int] = []
    section = re.compile(r"^## Lot (\d+) —", re.MULTILINE)
    blocks = re.compile(r"(?ms)^## Lot (\d+) —.*?(?=^## Lot \d+ —|\Z)")
    for path in paths:
        content = path.read_text(encoding="utf-8")
        lots.extend(map(int, section.findall(content)))
        for match in blocks.finditer(content):
            lot = int(match.group(1))
            if lot <= 25:
                block = match.group(0)
                require("### Preuves historiques et fichiers réels" in block, f"{path}: Lot {lot} lacks evidence")
                require("### Fichiers et artefacts d’implémentation attendus" not in block, f"{path}: Lot {lot} has synthetic paths")
    require(lots == list(range(178)), "Version docs must contain Lots 0-177 exactly once")

    addenda_missing = [name for name in REQUIRED_ROADMAP_ADDENDA if not (ROADMAP_DIR / name).is_file()]
    require(not addenda_missing, f"Missing roadmap addenda: {addenda_missing}")


def validate_quality_standards() -> None:
    for name in REQUIRED_ARCHITECTURE_DOCS:
        read_doc(name)

    require_terms(
        "MASTER_SYSTEM_SPECIFICATION.md",
        [
            "trade_allowed = false",
            "runtime_mode = LIVE_DISABLED",
            "BTC/EUR",
            "Kraken",
            "Withdrawals",
            "Risk Approval",
            "Order Intent",
            "Reconciliation",
            "Pas de HFT live",
        ],
    )
    master = read_doc("MASTER_SYSTEM_SPECIFICATION.md").casefold()
    require("levier" in master or "leverage" in master, "Master missing leverage prohibition")
    require_terms(
        "SYSTEM_EXECUTION_ARCHITECTURE.md",
        [
            "Data governance",
            "Market analysis",
            "Microstructure",
            "Strategy research",
            "Backtest/TCA",
            "RiskDecision",
            "OrderIntent",
            "OMS",
            "EMS",
            "Reconciliation",
            "Portfolio/PnL",
            "KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE",
            "MultiHorizonForecastV1",
            "ProtectiveOrderPlan",
        ],
    )
    require_terms(
        "TEST_STRATEGY_COVERAGE_AND_QUALITY_GATES.md",
        [
            "line coverage globale du package runtime >= 90 %",
            "branch coverage globale du package runtime >= 85 %",
            "branch coverage",
            "mutation score",
            "Non-Regression Test Suite",
            "Mathematical Logic Test Suite",
            "Property-Based Test Suite",
            "Failure Injection",
            "GO/NO-GO",
        ],
    )
    require_terms(
        "MATHEMATICAL_MODELING_AND_NUMERICAL_VALIDATION_STANDARD.md",
        [
            "domaine et codomaine",
            "cohérence dimensionnelle",
            "calibrée",
            "anti-lookahead",
            "stabilité numérique",
            "implémentation de référence",
            "NO_GO_MATHEMATICAL_VALIDATION",
        ],
    )
    require_terms(
        "DEVELOPMENT_ENGINEERING_STANDARD.md",
        [
            "fonction <= 50 lignes logiques",
            "complexité cyclomatique",
            "une seule source de vérité",
            "aucune duplication",
            "NO_GO_ENGINEERING_QUALITY",
        ],
    )
    require_terms(
        "DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md",
        [
            "decision_id",
            "input_checksums",
            "output_checksum",
            "journal append-only",
            "Replay d'audit",
            "NO_GO_AUDITABILITY",
        ],
    )
    require_terms(
        "LOT_FINAL_AUDIT_AND_GO_NO_GO_GATE.md",
        [
            "BLOCKER",
            "MAJOR",
            "CONDITIONAL_GO",
            "NO_GO_COVERAGE",
            "NO_GO_REPLAY",
            "Une CI verte seule ne donne jamais GO",
        ],
    )
    require_terms(
        "LOT_SPECIFICATION_STANDARD.md",
        [
            "line coverage ajouté/modifié >= 90 %",
            "mathematical_logic",
            "non_regression",
            "audit final et gate GO/NO-GO",
        ],
    )
    require_terms(
        "TEMPORAL_MULTI_SCALE_AND_DECISION_CLOCK_ARCHITECTURE.md",
        ["data_resolution", "forecast_horizon", "decision_clock", "signal_ttl", "holding_horizon"],
    )
    require_terms(
        "PARTICIPANT_BEHAVIOR_AND_LIQUIDITY_EXIT_ZONE_INFERENCE_STANDARD.md",
        ["TAKE_PROFIT_CLUSTER", "BREAK_EVEN_CLUSTER", "payoff_proxy", "inference_explicitly_labeled"],
    )


def validate_historical_paths() -> None:
    path_re = re.compile(
        r"(?<![A-Za-z0-9_.-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:jsonl|json|py|md|sh|toml|txt|csv))"
    )
    for lot in range(22, 26):
        acceptance = DOCS / f"ACCEPTANCE_CRITERIA_LOT_{lot}.md"
        require(acceptance.is_file(), f"Missing acceptance Lot {lot}")
        refs = sorted(set(path_re.findall(acceptance.read_text(encoding="utf-8"))))
        require(refs, f"Lot {lot}: no historical paths")
        missing = [path for path in refs if not (ROOT / path).is_file()]
        require(not missing, f"Lot {lot}: missing historical paths {missing}")


def validate_no_temporary_files() -> None:
    patterns = [
        ".github/scripts/roadmap_payload_*.txt",
        ".github/scripts/deep_roadmap_payload_*.txt",
        ".github/scripts/enhance_roadmap.py",
        ".github/workflows/generate-roadmap-v21.yml",
        ".github/workflows/deep-audit-roadmap.yml",
        ".github/workflows/reconcile-historical-roadmap.yml",
        ".github/workflows/fix-reconcile-regex.yml",
        ".github/workflows/apply-pre-lot26-readiness.yml",
        "scripts/pre_lot26_payload_*.txt",
        "scripts/apply_pre_lot26_readiness.py",
    ]
    for pattern in patterns:
        require(not list(ROOT.glob(pattern)), f"Temporary generation file remains: {pattern}")


def main() -> int:
    try:
        rows = load_registry()
        validate_registry(rows)
        validate_versions()
        validate_quality_standards()
        validate_historical_paths()
        validate_no_temporary_files()
    except RoadmapValidationError as exc:
        print(f"ROADMAP DOCUMENTATION VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    print("ROADMAP DOCUMENTATION VALIDATION: PASS")
    print("lots=178 versions=21 addenda=6 coverage_gate=90 math=audit engineering=auditable final_gate=GO_NO_GO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
