#!/usr/bin/env python3
"""Validate the canonical V1→V21 roadmap and its historical traceability."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REGISTRY = ROOT / "data" / "audit" / "product_scope_roadmap_lot21.jsonl"


class RoadmapValidationError(RuntimeError):
    """Raised when the roadmap contract is inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RoadmapValidationError(message)


def load_registry() -> list[dict[str, object]]:
    require(REGISTRY.is_file(), f"Missing registry: {REGISTRY}")
    rows: list[dict[str, object]] = []
    for line_number, line in enumerate(REGISTRY.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise RoadmapValidationError(f"Invalid JSONL at line {line_number}: {exc}") from exc
    return rows


def validate_registry(rows: list[dict[str, object]]) -> None:
    require(len(rows) == 178, f"Expected 178 lots, found {len(rows)}")
    numbers = [row.get("lot_number") for row in rows]
    require(numbers == list(range(178)), "Lot numbers must be continuous from 0 to 177")
    require(rows[25].get("status") == "IMPLEMENTED_VALIDATED", "Lot 25 must remain validated")
    require(rows[26].get("status") == "PLANNED_LOCKED", "Lot 26 must remain the next locked lot")

    future_required = {
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
        missing = future_required.difference(row)
        require(not missing, f"Lot {lot}: missing fields {sorted(missing)}")
        objective = str(row.get("objective", ""))
        require(not objective.startswith("Implémenter le lot"), f"Lot {lot}: generic objective remains")
        require(len(row.get("processing_sequence", [])) >= 4, f"Lot {lot}: insufficient processing steps")
        require(len(row.get("failure_modes", [])) >= 3, f"Lot {lot}: insufficient failure modes")
        require(len(row.get("implementation_files", [])) >= 4, f"Lot {lot}: insufficient implementation files")
        require(len(row.get("acceptance_tests", [])) >= 6, f"Lot {lot}: insufficient acceptance tests")
        require(len(row.get("non_goals", [])) >= 2, f"Lot {lot}: insufficient non-goals")

    for row in rows[:26]:
        lot = row["lot_number"]
        require(row.get("historical_paths_must_not_be_renamed") is True, f"Lot {lot}: historical paths not locked")
        policy = str(row.get("historical_evidence_policy", ""))
        require(policy.startswith("HISTORICAL_"), f"Lot {lot}: missing historical evidence policy")
        require(isinstance(row.get("historical_evidence_files"), list), f"Lot {lot}: evidence list missing")

    for row in rows[166:172]:
        invariants = " ".join(str(value) for value in row.get("safety_invariants", []))
        require("HFT_LIVE=FORBIDDEN" in invariants, f"Lot {row['lot_number']}: HFT live prohibition missing")


def validate_version_documents() -> None:
    version_files = sorted((DOCS / "roadmap").glob("V*.md"))
    require(len(version_files) == 21, f"Expected 21 version documents, found {len(version_files)}")

    lot_sections: list[int] = []
    section_re = re.compile(r"^## Lot (\d+) —", flags=re.MULTILINE)
    historical_block_re = re.compile(r"(?ms)^## Lot (\d+) —.*?(?=^## Lot \d+ —|\Z)")

    for path in version_files:
        text = path.read_text(encoding="utf-8")
        lot_sections.extend(int(value) for value in section_re.findall(text))
        for match in historical_block_re.finditer(text):
            lot = int(match.group(1))
            if lot <= 25:
                block = match.group(0)
                require("### Preuves historiques et fichiers réels" in block, f"{path}: Lot {lot} lacks historical evidence section")
                require(
                    "### Fichiers et artefacts d’implémentation attendus" not in block,
                    f"{path}: Lot {lot} still contains synthetic implementation paths",
                )

    require(lot_sections == list(range(178)), "Version documents must contain every Lot 0→177 exactly once")


def validate_architecture_documents() -> None:
    required = [
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
    ]
    for name in required:
        require((DOCS / name).is_file(), f"Missing architecture document: docs/{name}")

    master = (DOCS / "MASTER_SYSTEM_SPECIFICATION.md").read_text(encoding="utf-8").casefold()
    for term in [
        "trade_allowed = false",
        "runtime_mode = live_disabled",
        "btc/eur",
        "kraken",
        "leverage",
        "withdrawals",
        "risk approval",
        "order intent",
        "reconciliation",
        "pas de hft live",
    ]:
        require(term in master, f"Master specification missing: {term}")

    execution = (DOCS / "SYSTEM_EXECUTION_ARCHITECTURE.md").read_text(encoding="utf-8").casefold()
    for term in [
        "data governance",
        "market analysis",
        "microstructure",
        "strategy research",
        "backtest/tca",
        "riskdecision",
        "orderintent",
        "oms",
        "ems",
        "reconciliation",
        "portfolio/pnl",
        "kill_switch > pause > block_trading > wait > approve",
    ]:
        require(term in execution, f"Execution architecture missing: {term}")

    runtime = (DOCS / "RUNTIME_MODES_AND_STATE_MACHINES.md").read_text(encoding="utf-8").casefold()
    for term in ["live_disabled", "shadow_live", "live_manual_approval", "emergency_stop"]:
        require(term in runtime, f"Runtime state machine missing: {term}")


def validate_historical_acceptance_paths() -> None:
    path_re = re.compile(
        r"(?<![A-Za-z0-9_.-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:jsonl|json|py|md|sh|toml|txt|csv))"
    )
    for lot in range(22, 26):
        acceptance = DOCS / f"ACCEPTANCE_CRITERIA_LOT_{lot}.md"
        require(acceptance.is_file(), f"Missing historical acceptance criteria for Lot {lot}")
        references = sorted(set(path_re.findall(acceptance.read_text(encoding="utf-8"))))
        require(references, f"Lot {lot}: no historical paths found in acceptance criteria")
        missing = [path for path in references if not (ROOT / path).is_file()]
        require(not missing, f"Lot {lot}: missing historical paths: {missing}")


def validate_no_temporary_generation_files() -> None:
    temporary_patterns = [
        ".github/scripts/roadmap_payload_*.txt",
        ".github/scripts/deep_roadmap_payload_*.txt",
        ".github/scripts/enhance_roadmap.py",
        ".github/workflows/generate-roadmap-v21.yml",
        ".github/workflows/deep-audit-roadmap.yml",
        ".github/workflows/reconcile-historical-roadmap.yml",
        ".github/workflows/fix-reconcile-regex.yml",
    ]
    for pattern in temporary_patterns:
        require(not list(ROOT.glob(pattern)), f"Temporary generation file remains: {pattern}")


def main() -> int:
    try:
        rows = load_registry()
        validate_registry(rows)
        validate_version_documents()
        validate_architecture_documents()
        validate_historical_acceptance_paths()
        validate_no_temporary_generation_files()
    except RoadmapValidationError as exc:
        print(f"ROADMAP DOCUMENTATION VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1

    print("ROADMAP DOCUMENTATION VALIDATION: PASS")
    print("lots=178 versions=21 implemented=0-25 next=26 final=177")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
