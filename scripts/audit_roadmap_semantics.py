#!/usr/bin/env python3
"""Audit semantic ownership across the 178-lot roadmap.

The structural validator proves that all sections exist. This audit proves that
critical output contracts are produced only by their canonical domain owner and
that known cross-domain template contamination is absent.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROADMAP_DIR = ROOT / "docs" / "roadmap"
REPORT_PATH = ROOT / "reports" / "P0_6_ROADMAP_SEMANTIC_AUDIT.json"

VERSION_FILES = {
    f"V{number:02d}": path
    for number, path in enumerate(
        [
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
        ],
        start=1,
    )
}

# Only contracts with an unambiguous producer are included. Generic audit,
# replay, lineage and closure contracts are deliberately excluded.
CONTRACT_OWNERS = {
    "SourceRegistryV1": "V03",
    "InstrumentRegistryV1": "V03",
    "InstrumentSpecificationV1": "V03",
    "CanonicalTimeEnvelopeV1": "V03",
    "ClockHealthStateV1": "V03",
    "DataQualityStateV1": "V03",
    "DataAnomalyV1": "V03",
    "DataQualityVetoV1": "V03",
    "ContinuousMarketStateV1": "V03",
    "OrderBookSnapshotV1": "V04",
    "ReconstructedOrderBookV1": "V04",
    "BookHealthStateV1": "V04",
    "BookFeatureStateV1": "V04",
    "DerivativesContextStateV1": "V04",
    "ParticipantBehaviorScenarioV1": "V04",
    "LiquidityExitZoneV1": "V04",
    "MultiHorizonForecastV1": "V05",
    "SignalV1": "V05",
    "TradeIntentV1": "V05",
    "StrategyCandidateV1": "V05",
    "TransactionCostStateV1": "V06",
    "BacktestRunV1": "V06",
    "SimulatedExecutionLedgerV1": "V06",
    "ExpectedValueStateV1": "V06",
    "RiskLimitSetV1": "V07",
    "RiskDecisionV1": "V07",
    "PaperOrderV1": "V08",
    "PaperFillV1": "V08",
    "PaperPositionV1": "V08",
    "PortfolioStateV1": "V09",
    "CapitalStateV1": "V09",
    "PositionStateV1": "V09",
    "PositionEventV1": "V09",
    "PnLLedgerV1": "V09",
    "PnLStateV1": "V09",
    "ExperimentRecordV1": "V10",
    "ResearchArtifactManifestV1": "V10",
    "EventContextV1": "V11",
    "SourceReliabilityStateV1": "V11",
    "UIReadModelV1": "V12",
    "OperatorActionAuditV1": "V12",
    "ReadOnlyAccountSnapshotV1": "V13",
    "PermissionAuditV1": "V13",
    "ExchangeHealthStateV1": "V14",
    "ExchangeRiskVetoV1": "V14",
    "OMSOrderStateV1": "V15",
    "OrderTransitionEventV1": "V15",
    "IdempotencyRecordV1": "V15",
    "ProtectiveOrderPlanV1": "V15",
    "SandboxExecutionStateV1": "V16",
    "FailureInjectionEvidenceV1": "V16",
    "RuntimeModeStateV1": "V17",
    "HumanApprovalV1": "V17",
    "LiveEligibilityStateV1": "V17",
    "TelemetryEnvelopeV1": "V18",
    "IncidentRecordV1": "V18",
    "RecoveryEvidenceV1": "V18",
    "HFTResearchResultV1": "V19",
    "QueueSimulationStateV1": "V19",
    "OptionsContextStateV1": "V20",
    "OnChainContextStateV1": "V21",
}

KNOWN_CONTAMINATION = {
    ("V01", 0): [
        "LiquidityBehaviorEventV1",
        "RobustnessSimulationResultV1",
        "Classer SWEEP",
        "Publier risk-of-ruin",
    ],
    ("V06", 62): [
        "- BookFeatureStateV1",
        "- DerivativesContextStateV1",
        "Calculer imbalance symétrique",
        "Calculer crowding, leverage build-up",
    ],
    ("V09", 90): [
        "- InstrumentRegistryV1",
        "- InstrumentSpecificationV1",
        "Normaliser venue, base, quote",
        "Valider tick_size, lot_size",
    ],
    ("V11", 105): [
        "- ReadOnlyAccountSnapshotV1",
        "- PermissionAuditV1",
        "Paginer et dédupliquer histories",
        "Scanner permissions et faire échouer",
    ],
}

LOT_RE = re.compile(r"(?ms)^## Lot (?P<lot>\d+) —.*?(?=^## Lot \d+ —|\Z)")
OUTPUT_RE = re.compile(
    r"(?ms)^### Contrats de sortie\s+(?P<body>.*?)(?=^### )"
)
CONTRACT_RE = re.compile(r"^-\s+`?([A-Za-z][A-Za-z0-9_]*V\d+)`?\s*$", re.MULTILINE)


def audit() -> dict[str, object]:
    violations: list[dict[str, object]] = []
    checked_lots = 0
    output_contracts = 0

    for version, filename in VERSION_FILES.items():
        path = ROADMAP_DIR / filename
        content = path.read_text(encoding="utf-8")
        for match in LOT_RE.finditer(content):
            checked_lots += 1
            lot = int(match.group("lot"))
            block = match.group(0)
            output_match = OUTPUT_RE.search(block)
            if output_match:
                contracts = CONTRACT_RE.findall(output_match.group("body"))
                output_contracts += len(contracts)
                for contract in contracts:
                    owner = CONTRACT_OWNERS.get(contract)
                    if owner and owner != version:
                        violations.append(
                            {
                                "type": "CONTRACT_OWNER_MISMATCH",
                                "version": version,
                                "lot": lot,
                                "contract": contract,
                                "expected_owner": owner,
                                "file": f"docs/roadmap/{filename}",
                            }
                        )
            for needle in KNOWN_CONTAMINATION.get((version, lot), []):
                if needle in block:
                    violations.append(
                        {
                            "type": "KNOWN_TEMPLATE_CONTAMINATION",
                            "version": version,
                            "lot": lot,
                            "needle": needle,
                            "file": f"docs/roadmap/{filename}",
                        }
                    )

    payload: dict[str, object] = {
        "schema_version": "p0-6-roadmap-semantic-audit-v1",
        "checked_versions": len(VERSION_FILES),
        "checked_lots": checked_lots,
        "checked_output_contracts": output_contracts,
        "critical_contract_owner_rules": len(CONTRACT_OWNERS),
        "violations": violations,
        "status": "PASS" if not violations and checked_lots == 178 else "FAIL",
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    payload = audit()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    if payload["status"] != "PASS" and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
