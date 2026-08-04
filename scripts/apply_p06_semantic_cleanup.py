#!/usr/bin/env python3
"""Remove remaining cross-domain contract ownership contamination from the roadmap."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "roadmap"
LOT_PATTERN = re.compile(r"(?ms)^## Lot (?P<number>\d+) —.*?(?=^## Lot \d+ —|\Z)")
SECTION_PATTERN = r"(?ms)(^### {title}\s*\n)(?P<body>.*?)(?=^### |\Z)"


def _contract_line(contract: str) -> str:
    return f"- {contract}"


def _edit_contract_section(
    block: str,
    title: str,
    *,
    remove: tuple[str, ...] = (),
    add: tuple[str, ...] = (),
) -> str:
    pattern = re.compile(SECTION_PATTERN.format(title=re.escape(title)))
    match = pattern.search(block)
    if match is None:
        raise RuntimeError(f"missing section {title}")
    body = match.group("body")
    lines = body.rstrip().splitlines()
    remove_lines = {_contract_line(item) for item in remove}
    lines = [line for line in lines if line.strip() not in remove_lines]
    existing = {line.strip() for line in lines}
    for contract in add:
        line = _contract_line(contract)
        if line not in existing:
            lines.append(line)
            existing.add(line)
    new_body = "\n".join(lines).rstrip() + "\n\n"
    return block[: match.start("body")] + new_body + block[match.end("body") :]


def _edit_lot(
    filename: str,
    lot: int,
    *,
    remove_outputs: tuple[str, ...],
    add_inputs: tuple[str, ...] = (),
    add_outputs: tuple[str, ...] = (),
) -> None:
    path = ROADMAP / filename
    content = path.read_text(encoding="utf-8")
    matches = list(LOT_PATTERN.finditer(content))
    target = next((match for match in matches if int(match.group("number")) == lot), None)
    if target is None:
        raise RuntimeError(f"Lot {lot} not found in {filename}")
    block = target.group(0)
    block = _edit_contract_section(block, "Contrats d’entrée", add=add_inputs)
    block = _edit_contract_section(
        block,
        "Contrats de sortie",
        remove=remove_outputs,
        add=add_outputs,
    )
    path.write_text(content[: target.start()] + block + content[target.end() :], encoding="utf-8")


def _patch_audit_rules() -> None:
    path = ROOT / "scripts" / "audit_roadmap_semantics.py"
    content = path.read_text(encoding="utf-8")
    content = content.replace(
        '    ("V06", 62): [\n'
        '        "- BookFeatureStateV1",\n'
        '        "- DerivativesContextStateV1",\n'
        '        "Calculer imbalance symétrique",\n'
        '        "Calculer crowding, leverage build-up",\n'
        "    ],",
        '    ("V06", 62): [\n'
        '        "Calculer imbalance symétrique",\n'
        '        "Calculer crowding, leverage build-up",\n'
        "    ],",
    )
    content = content.replace(
        '    ("V09", 90): [\n'
        '        "- InstrumentRegistryV1",\n'
        '        "- InstrumentSpecificationV1",\n'
        '        "Normaliser venue, base, quote",\n'
        '        "Valider tick_size, lot_size",\n'
        "    ],",
        '    ("V09", 90): [\n'
        '        "Normaliser venue, base, quote",\n'
        '        "Valider tick_size, lot_size",\n'
        "    ],",
    )
    path.write_text(content, encoding="utf-8")


def main() -> int:
    _patch_audit_rules()
    _edit_lot(
        "V01_DEFENSIVE_AUDIT_NO_TRADING.md",
        17,
        remove_outputs=("ExchangeHealthStateV1", "ExchangeRiskVetoV1"),
    )
    _edit_lot(
        "V08_PAPER_TRADING.md",
        83,
        remove_outputs=("TradeIntentV1", "OrderIntentV1"),
        add_inputs=(
            "SignalV1 produit par V5",
            "TradeIntentV1 produit par V5",
            "RiskDecisionV1 produit par V7",
        ),
        add_outputs=("PaperOrderIntentV1",),
    )
    _edit_lot(
        "V08_PAPER_TRADING.md",
        85,
        remove_outputs=("TelemetryEnvelopeV1", "IncidentRecordV1", "RecoveryEvidenceV1"),
        add_outputs=("PaperIncidentEventV1", "PaperRiskActionV1"),
    )
    _edit_lot(
        "V08_PAPER_TRADING.md",
        86,
        remove_outputs=("SandboxExecutionStateV1", "FailureInjectionEvidenceV1"),
        add_outputs=("SandboxPromotionDecisionV1",),
    )
    _edit_lot(
        "V09_PORTFOLIO_PNL_CORE.md",
        92,
        remove_outputs=("DerivativesContextStateV1",),
        add_inputs=("DerivativesContextStateV1 produit par V4",),
    )
    _edit_lot(
        "V11_NEWS_AI_EVENT_CONTEXT.md",
        103,
        remove_outputs=("SourceRegistryV1",),
        add_inputs=("SourceRegistryV1 produit par V3",),
        add_outputs=("IntelligenceSourcePolicyV1",),
    )
    _edit_lot(
        "V13_API_READ_ONLY_ACCOUNT_READ_ONLY.md",
        122,
        remove_outputs=("DerivativesContextStateV1",),
        add_inputs=("DerivativesContextStateV1 produit par V4",),
    )
    _edit_lot(
        "V14_EXCHANGE_RISK_API_HEALTH.md",
        128,
        remove_outputs=("InstrumentRegistryV1", "InstrumentSpecificationV1"),
        add_inputs=(
            "InstrumentRegistryV1 produit par V3",
            "InstrumentSpecificationV1 produit par V3",
        ),
    )
    _edit_lot(
        "V14_EXCHANGE_RISK_API_HEALTH.md",
        129,
        remove_outputs=("CanonicalTimeEnvelopeV1", "ClockHealthStateV1"),
        add_inputs=(
            "CanonicalTimeEnvelopeV1 produit par V3",
            "ClockHealthStateV1 produit par V3",
        ),
    )
    _edit_lot(
        "V14_EXCHANGE_RISK_API_HEALTH.md",
        131,
        remove_outputs=("UIReadModelV1", "OperatorActionAuditV1"),
        add_outputs=("ExchangeRiskDashboardProjectionV1",),
    )
    _edit_lot(
        "V15_OMS_EMS_CORE.md",
        136,
        remove_outputs=("InstrumentRegistryV1", "InstrumentSpecificationV1"),
        add_inputs=(
            "InstrumentRegistryV1 produit par V3",
            "InstrumentSpecificationV1 produit par V3",
        ),
    )
    _edit_lot(
        "V16_SANDBOX_DEMO_EXECUTION.md",
        146,
        remove_outputs=("RiskDecisionV1",),
        add_inputs=("RiskDecisionV1 produit par V7",),
    )
    _edit_lot(
        "V16_SANDBOX_DEMO_EXECUTION.md",
        147,
        remove_outputs=("TelemetryEnvelopeV1", "IncidentRecordV1", "RecoveryEvidenceV1"),
        add_outputs=("SandboxIncidentEventV1",),
    )
    _edit_lot(
        "V18_OBSERVABILITY_INCIDENT_RESPONSE.md",
        160,
        remove_outputs=("DataQualityStateV1", "DataAnomalyV1", "DataQualityVetoV1"),
        add_inputs=(
            "DataQualityStateV1 produit par V3",
            "DataAnomalyV1 produit par V3",
            "DataQualityVetoV1 produit par V3",
        ),
        add_outputs=("RuntimeFreshnessMonitoringStateV1",),
    )
    _edit_lot(
        "V19_HFT_RESEARCH.md",
        167,
        remove_outputs=("CanonicalTimeEnvelopeV1", "ClockHealthStateV1"),
        add_inputs=(
            "CanonicalTimeEnvelopeV1 produit par V3",
            "ClockHealthStateV1 produit par V3",
        ),
        add_outputs=("HighResolutionTimePolicyV1",),
    )
    _edit_lot(
        "V21_ON_CHAIN_FLOW_INTELLIGENCE.md",
        175,
        remove_outputs=("SourceRegistryV1",),
        add_inputs=("SourceRegistryV1 produit par V3",),
        add_outputs=("OnChainSourcePolicyV1",),
    )
    print("P0.6 semantic cleanup applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
