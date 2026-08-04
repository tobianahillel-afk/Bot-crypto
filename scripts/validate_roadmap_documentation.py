#!/usr/bin/env python3
"""Validate roadmap structure, quality gates, math, auditability and history."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REGISTRY = ROOT / "data/audit/product_scope_roadmap_lot21.jsonl"

class RoadmapValidationError(RuntimeError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise RoadmapValidationError(message)

def text(name: str) -> str:
    path = DOCS / name
    require(path.is_file(), f"Missing architecture document: docs/{name}")
    return path.read_text(encoding="utf-8")

def load_registry() -> list[dict[str, object]]:
    require(REGISTRY.is_file(), f"Missing registry: {REGISTRY}")
    rows = []
    for number, line in enumerate(REGISTRY.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise RoadmapValidationError(f"Invalid JSONL line {number}: {exc}") from exc
    return rows

def validate_registry(rows: list[dict[str, object]]) -> None:
    require(len(rows) == 178, f"Expected 178 lots, found {len(rows)}")
    require([row.get("lot_number") for row in rows] == list(range(178)), "Lots must be continuous 0-177")
    require(rows[25].get("status") == "IMPLEMENTED_VALIDATED", "Lot 25 must remain validated")
    require(rows[26].get("status") == "PLANNED_LOCKED", "Lot 26 must remain next locked lot")
    required = {"responsible_component","package_boundary","runtime_mode","responsibility","input_contracts","output_contracts","processing_sequence","domain_rules","failure_modes","observability","implementation_files","acceptance_tests","non_goals","definition_of_done","promotion_gate","safety_invariants"}
    for row in rows[26:]:
        lot = row["lot_number"]
        missing = required.difference(row)
        require(not missing, f"Lot {lot}: missing {sorted(missing)}")
        require(not str(row.get("objective", "")).startswith("Implémenter le lot"), f"Lot {lot}: generic objective")
        require(len(row.get("processing_sequence", [])) >= 4, f"Lot {lot}: insufficient processing sequence")
        require(len(row.get("failure_modes", [])) >= 3, f"Lot {lot}: insufficient failure modes")
        require(len(row.get("implementation_files", [])) >= 4, f"Lot {lot}: insufficient implementation files")
        require(len(row.get("acceptance_tests", [])) >= 6, f"Lot {lot}: insufficient acceptance tests")
        require(len(row.get("non_goals", [])) >= 2, f"Lot {lot}: insufficient non-goals")
    for row in rows[:26]:
        lot = row["lot_number"]
        require(row.get("historical_paths_must_not_be_renamed") is True, f"Lot {lot}: historical paths unlocked")
        require(str(row.get("historical_evidence_policy", "")).startswith("HISTORICAL_"), f"Lot {lot}: historical policy missing")
        require(isinstance(row.get("historical_evidence_files"), list), f"Lot {lot}: evidence list missing")
    for row in rows[166:172]:
        require("HFT_LIVE=FORBIDDEN" in " ".join(map(str, row.get("safety_invariants", []))), f"Lot {row['lot_number']}: HFT live prohibition missing")

def validate_versions() -> None:
    files = sorted((DOCS / "roadmap").glob("V*.md"))
    require(len(files) == 21, f"Expected 21 version docs, found {len(files)}")
    lots = []
    section = re.compile(r"^## Lot (\d+) —", re.MULTILINE)
    blocks = re.compile(r"(?ms)^## Lot (\d+) —.*?(?=^## Lot \d+ —|\Z)")
    for path in files:
        content = path.read_text(encoding="utf-8")
        lots.extend(map(int, section.findall(content)))
        for match in blocks.finditer(content):
            lot = int(match.group(1))
            if lot <= 25:
                block = match.group(0)
                require("### Preuves historiques et fichiers réels" in block, f"{path}: Lot {lot} lacks evidence")
                require("### Fichiers et artefacts d’implémentation attendus" not in block, f"{path}: Lot {lot} has synthetic paths")
    require(lots == list(range(178)), "Version docs must contain Lots 0-177 exactly once")

def require_terms(name: str, terms: list[str]) -> None:
    content = text(name).casefold()
    for term in terms:
        require(term.casefold() in content, f"{name} missing: {term}")

def validate_quality_standards() -> None:
    required_docs = [
        "ROADMAP_V1_TO_V21.md","MASTER_SYSTEM_SPECIFICATION.md","SYSTEM_EXECUTION_ARCHITECTURE.md","DOMAIN_BOUNDARIES_AND_OWNERSHIP.md","CANONICAL_DATA_AND_EVENT_CONTRACTS.md","RUNTIME_MODES_AND_STATE_MACHINES.md","STRATEGY_LIFECYCLE_AND_PROMOTION_GATES.md","VETO_CONSEQUENCE_MATRIX.md","CONFIGURATION_RELEASE_AND_ENVIRONMENT_GOVERNANCE.md","FAILURE_DEGRADED_AND_RECOVERY_POLICY.md","ROADMAP_TRACEABILITY_MATRIX.md","ROADMAP_DOCUMENTATION_VALIDATION_REPORT.md","HISTORICAL_IMPLEMENTATION_RECONCILIATION.md","LOT_SPECIFICATION_STANDARD.md","TEST_STRATEGY_COVERAGE_AND_QUALITY_GATES.md","MATHEMATICAL_MODELING_AND_NUMERICAL_VALIDATION_STANDARD.md","DEVELOPMENT_ENGINEERING_STANDARD.md","DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md","LOT_FINAL_AUDIT_AND_GO_NO_GO_GATE.md"
    ]
    for name in required_docs:
        text(name)
    require_terms("MASTER_SYSTEM_SPECIFICATION.md", ["trade_allowed = false","runtime_mode = LIVE_DISABLED","BTC/EUR","Kraken","Withdrawals","Risk Approval","Order Intent","Reconciliation","Pas de HFT live"])
    master = text("MASTER_SYSTEM_SPECIFICATION.md").casefold()
    require("levier" in master or "leverage" in master, "Master missing leverage prohibition")
    require_terms("SYSTEM_EXECUTION_ARCHITECTURE.md", ["Data governance","Market analysis","Microstructure","Strategy research","Backtest/TCA","RiskDecision","OrderIntent","OMS","EMS","Reconciliation","Portfolio/PnL","KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE"])
    require_terms("TEST_STRATEGY_COVERAGE_AND_QUALITY_GATES.md", ["line coverage global du code ajouté/modifié >= 90 %","branch coverage","mutation score","Non-Regression Test Suite","Mathematical Logic Test Suite","Property-Based Test Suite","Failure Injection","GO/NO-GO"])
    require_terms("MATHEMATICAL_MODELING_AND_NUMERICAL_VALIDATION_STANDARD.md", ["domaine et codomaine","cohérence dimensionnelle","calibrée","anti-lookahead","stabilité numérique","implémentation de référence","NO_GO_MATHEMATICAL_VALIDATION"])
    require_terms("DEVELOPMENT_ENGINEERING_STANDARD.md", ["fonction <= 50 lignes logiques","complexité cyclomatique","une seule source de vérité","aucune duplication","NO_GO_ENGINEERING_QUALITY"])
    require_terms("DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md", ["decision_id","input_checksums","output_checksum","journal append-only","Replay d'audit","NO_GO_AUDITABILITY"])
    require_terms("LOT_FINAL_AUDIT_AND_GO_NO_GO_GATE.md", ["BLOCKER","MAJOR","CONDITIONAL_GO","NO_GO_COVERAGE","NO_GO_REPLAY","Une CI verte seule ne donne jamais GO"])
    require_terms("LOT_SPECIFICATION_STANDARD.md", ["line coverage ajouté/modifié >= 90 %","mathematical_logic","non_regression","audit final et gate GO/NO-GO"])

def validate_historical_paths() -> None:
    path_re = re.compile(r"(?<![A-Za-z0-9_.-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:jsonl|json|py|md|sh|toml|txt|csv))")
    for lot in range(22, 26):
        acceptance = DOCS / f"ACCEPTANCE_CRITERIA_LOT_{lot}.md"
        require(acceptance.is_file(), f"Missing acceptance Lot {lot}")
        refs = sorted(set(path_re.findall(acceptance.read_text(encoding="utf-8"))))
        require(refs, f"Lot {lot}: no historical paths")
        missing = [path for path in refs if not (ROOT / path).is_file()]
        require(not missing, f"Lot {lot}: missing historical paths {missing}")

def validate_no_temporary_files() -> None:
    patterns = [".github/scripts/roadmap_payload_*.txt",".github/scripts/deep_roadmap_payload_*.txt",".github/scripts/enhance_roadmap.py",".github/workflows/generate-roadmap-v21.yml",".github/workflows/deep-audit-roadmap.yml",".github/workflows/reconcile-historical-roadmap.yml",".github/workflows/fix-reconcile-regex.yml"]
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
    print("lots=178 versions=21 coverage_gate=90 math=audit engineering=auditable final_gate=GO_NO_GO")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
