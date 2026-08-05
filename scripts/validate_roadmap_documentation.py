#!/usr/bin/env python3
"""Validate the immutable roadmap history and current Lot 26 lifecycle."""
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
    require([row.get("lot_number") for row in rows] == list(range(178)), "lots are not continuous 0-177")
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
        require(len(row.get("processing_sequence", [])) >= 4, f"Lot {row['lot_number']}: sequence too short")
        require(len(row.get("failure_modes", [])) >= 3, f"Lot {row['lot_number']}: failure modes too short")
        require(len(row.get("acceptance_tests", [])) >= 6, f"Lot {row['lot_number']}: tests too short")


def validate_lifecycle() -> None:
    overlay = load_object(OVERLAY)
    require(overlay.get("latest_implemented_lot") == 26, "lifecycle latest lot must be 26")
    lots = overlay.get("lots")
    require(isinstance(lots, dict), "lifecycle lots are missing")
    lot26 = lots.get("26")
    lot27 = lots.get("27")
    require(isinstance(lot26, dict), "Lot 26 lifecycle entry missing")
    require(isinstance(lot27, dict), "Lot 27 lifecycle entry missing")
    require(
        lot26.get("status") == "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY",
        "Lot 26 must remain validated after exact-commit CI passes",
    )
    require(lot26.get("trade_allowed") is False, "Lot 26 trading must remain disabled")
    require(lot26.get("execution_allowed") is False, "Lot 26 execution must remain disabled")
    require(lot27.get("status") == "PLANNED_LOCKED", "Lot 27 must remain locked")
    require(lot27.get("implementation_started") is False, "Lot 27 must not be started")


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
    text = (ROOT / "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md").read_text(encoding="utf-8")
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
    require("IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY" in status, "Lot 26 status is not current")


def validate_no_temporary_files() -> None:
    for pattern in FORBIDDEN_TEMPORARY_PATTERNS:
        require(not list(ROOT.glob(pattern)), f"temporary Lot 26 file remains: {pattern}")


def main() -> int:
    try:
        validate_history(load_registry())
        validate_lifecycle()
        validate_version_docs()
        validate_lot26_files_and_boundaries()
        validate_no_temporary_files()
    except (RoadmapValidationError, json.JSONDecodeError) as exc:
        print(f"ROADMAP DOCUMENTATION VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    print("ROADMAP DOCUMENTATION VALIDATION: PASS")
    print("historical_lots=178 lifecycle_latest=26 status=AWAITING_EXACT_COMMIT_CI next_locked=27")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
