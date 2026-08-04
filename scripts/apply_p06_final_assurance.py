#!/usr/bin/env python3
"""Apply the reviewed P0.6 semantic and governance corrections.

This migration is intentionally deterministic and idempotent. It is used only
on the dedicated P0.6 branch and must be removed before final promotion.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_required(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    if new in text and old not in text:
        return
    if old not in text:
        raise RuntimeError(f"expected text not found in {relative}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_roadmap_index() -> None:
    replace_required(
        "docs/ROADMAP_V1_TO_V21.md",
        "- Préparation Lot 26 : contrats, architecture temporelle et gate en revue.",
        "- Préparation Lot 26 : architecture fusionnée ; le gate transversal P0.6 est actif avant démarrage.",
    )
    replace_required(
        "docs/ROADMAP_V1_TO_V21.md",
        "- [Lot Final Audit and GO / NO-GO Gate](LOT_FINAL_AUDIT_AND_GO_NO_GO_GATE.md)\n",
        "- [Lot Final Audit and GO / NO-GO Gate](LOT_FINAL_AUDIT_AND_GO_NO_GO_GATE.md)\n"
        "- [Capability and Contract Ownership Registry](CAPABILITY_AND_CONTRACT_OWNERSHIP_REGISTRY.md)\n"
        "- [Model Retraining and Promotion Policy](MODEL_RETRAINING_AND_PROMOTION_POLICY.md)\n"
        "- [Economic Objective and Risk Utility Policy](ECONOMIC_OBJECTIVE_AND_RISK_UTILITY_POLICY.md)\n",
    )
    replace_required(
        "docs/ROADMAP_V1_TO_V21.md",
        "- Forecast horizon registry: `config/research/forecast_horizon_registry_v1.json`\n",
        "- Forecast horizon registry: `config/research/forecast_horizon_registry_v1.json`\n"
        "- Domain ownership registry: `config/governance/domain_ownership_registry_v1.json`\n"
        "- Decision evidence schema: `contracts/schemas/decision_evidence_envelope_v1.schema.json`\n",
    )


def patch_v1_lot0() -> None:
    path = "docs/roadmap/V01_DEFENSIVE_AUDIT_NO_TRADING.md"
    replace_required(
        path,
        "- ProjectBootstrapSafetyBaselineStateV1\n"
        "- ProjectBootstrapSafetyBaselineAuditV1\n"
        "- LiquidityBehaviorEventV1\n"
        "- RobustnessSimulationResultV1",
        "- ProjectBootstrapSafetyBaselineStateV1\n"
        "- ProjectBootstrapSafetyBaselineAuditV1",
    )
    replace_required(
        path,
        "6. Détecter breach de zone, excursion, volume/flow associé puis reclaim/acceptance dans fenêtre définie.\n"
        "7. Classer SWEEP, BREAKOUT_ACCEPTED, FAKEOUT, LONG_TRAP, SHORT_TRAP ou FAILED_AUCTION.\n"
        "8. Exiger séquence temporelle complète et publier evidence/invalidating_evidence.\n"
        "9. Ne pas utiliser de barre future au-delà du temps de décision.\n"
        "10. Bootstrap par blocs pour préserver dépendance temporelle.\n"
        "11. Randomiser ordre des trades/cost shocks selon scénario.\n"
        "12. Balayer paramètres autour du point choisi et détecter cliffs.\n"
        "13. Publier risk-of-ruin et drawdown distribution.",
        "6. Enregistrer identité projet, runtime autorisé, version Python, toolchain et invariants de sécurité.\n"
        "7. Vérifier qu'aucun connecteur, moteur de prédiction, signal, sizing ou exécution n'est activé.\n"
        "8. Produire un manifest de bootstrap et un audit déterministes avec checksums.",
    )
    replace_required(
        path,
        "- Breach sans reclaim ≠ fakeout.\n"
        "- Late reclaim après expiration ≠ trap actif.\n"
        "- Seed reproductible.\n"
        "- Paramètre fragile marqué non promotable.",
        "- Manifest de bootstrap reconstructible.\n"
        "- Runtime hors `EDUCATIONAL_AUDIT_ONLY` rejeté.\n"
        "- Aucun contrat ou algorithme appartenant aux versions futures.",
    )


def patch_v6_lot62() -> None:
    path = "docs/roadmap/V06_BACKTESTING_EXPECTED_VALUE_TCA.md"
    replace_required(
        path,
        "- LineageEnvelopeV1 des artefacts produits par les lots préalables\n\n"
        "### Contrats de sortie\n\n"
        "- FeesFundingSpreadCostModelStateV1\n"
        "- FeesFundingSpreadCostModelAuditV1\n"
        "- BookFeatureStateV1\n"
        "- DerivativesContextStateV1\n"
        "- TransactionCostStateV1",
        "- LineageEnvelopeV1 des artefacts produits par les lots préalables\n"
        "- BookFeatureStateV1 produit par V4\n"
        "- DerivativesContextStateV1 produit par V4\n\n"
        "### Contrats de sortie\n\n"
        "- FeesFundingSpreadCostModelStateV1\n"
        "- FeesFundingSpreadCostModelAuditV1\n"
        "- TransactionCostStateV1",
    )
    replace_required(
        path,
        "5. Calculer spread absolu/bps, mid, microprice, depth par bande bps et cumulative depth.\n"
        "6. Calculer imbalance symétrique avec gestion du dénominateur nul.\n"
        "7. Publier valeurs par horizon/niveau et qualité du book.\n"
        "8. Ne pas extrapoler au-delà de la profondeur observée.\n"
        "9. Normaliser OI, funding, mark/index, basis et liquidations par venue/contrat.\n"
        "10. Aligner publication/effective_time et gérer révisions.\n"
        "11. Calculer crowding, leverage build-up, squeeze/liquidation risk comme contexte probabiliste.\n"
        "12. Interdire l’usage si spot/perp mapping ou notionals ne sont pas comparables.\n"
        "13. Modéliser maker/taker fee, fee tier, spread crossing, funding et settlement cashflows.\n"
        "14. Appliquer devise de frais et conversion FX versionnée.\n"
        "15. Refuser coût nul par défaut lorsque donnée absente ; utiliser conservative fallback explicite.",
        "5. Valider IDs, checksums, fraîcheur et compatibilité des états V4 consommés sans recalculer leur microstructure.\n"
        "6. Modéliser maker/taker fee, fee tier, spread crossing, funding et settlement cashflows.\n"
        "7. Aligner publication/effective_time du funding et gérer les révisions.\n"
        "8. Appliquer devise de frais et conversion FX versionnée.\n"
        "9. Refuser coût nul par défaut lorsque donnée absente ; utiliser un fallback conservateur explicite.\n"
        "10. Publier chaque composante de coût, sa provenance, son incertitude et le coût total réconcilié.",
    )
    replace_required(
        path,
        "- Book vide/unilatéral.\n"
        "- Invariance à l’unité de cotation et contrôle des bornes.\n"
        "- Funding publication vs effective time.\n"
        "- OI change sans prix/volume ne produit pas de scénario certain.\n"
        "- Maker/taker et devise de frais.\n"
        "- Funding multi-périodes et signe long/short.",
        "- États V4 absents, stale ou incompatibles bloquent le coût.\n"
        "- Le Lot 62 ne produit aucun BookFeatureStateV1 ni DerivativesContextStateV1.\n"
        "- Funding publication vs effective time.\n"
        "- Maker/taker et devise de frais.\n"
        "- Funding multi-périodes et signe long/short.\n"
        "- Somme des composantes = coût total selon tolérance versionnée.",
    )


def patch_v9_lot90() -> None:
    path = "docs/roadmap/V09_PORTFOLIO_PNL_CORE.md"
    replace_required(path, "- ExchangeInstrumentMetadataV1", "- InstrumentSpecificationV1 produit par V3")
    replace_required(
        path,
        "- PositionLifecycleCorporateInstrumentEventsStateV1\n"
        "- PositionLifecycleCorporateInstrumentEventsAuditV1\n"
        "- InstrumentRegistryV1\n"
        "- InstrumentSpecificationV1\n"
        "- PositionStateV1\n"
        "- PositionEventV1",
        "- PositionLifecycleCorporateInstrumentEventsStateV1\n"
        "- PositionLifecycleCorporateInstrumentEventsAuditV1\n"
        "- PositionStateV1\n"
        "- PositionEventV1",
    )
    replace_required(
        path,
        "5. Normaliser venue, base, quote, market_type, canonical_symbol et exchange_symbol.\n"
        "6. Modéliser spot, perpetual, dated future et option avec champs non applicables explicitement null/forbidden.\n"
        "7. Valider tick_size, lot_size, min_qty, min_notional, price/qty precision, fee tier, settlement, margin et leverage policy.\n"
        "8. Appliquer fills, fees, funding, transfers et instrument events dans ordre déterministe.\n"
        "9. Gérer increase/reduce/close/reopen et average cost selon méthode documentée.\n"
        "10. Distinguer position économique, venue position et strategy attribution.",
        "5. Consommer l'InstrumentSpecificationV1 de V3 et rejeter toute version inconnue ou stale sans la renormaliser.\n"
        "6. Appliquer fills, fees, funding, transfers et instrument events dans ordre déterministe.\n"
        "7. Gérer increase/reduce/close/reopen et average cost selon méthode documentée.\n"
        "8. Distinguer position économique, venue position et strategy attribution.\n"
        "9. Produire chaque transition de position comme événement idempotent et réconciliable.",
    )
    replace_required(
        path,
        "- Métadonnée instrument ambiguë ou révisée → INSTRUMENT_FROZEN.\n"
        "- Arrondi qui viole min_notional → order intent rejeté.",
        "- InstrumentSpecificationV1 ambiguë, stale ou révisée → POSITION_PROCESSING_FROZEN.\n"
        "- Fill ou instrument event invalide → événement rejeté et réconciliation requise.",
    )
    replace_required(
        path,
        "- Round-trip symbol canonical ↔ venue.\n"
        "- Tests de quantization aux frontières tick/lot/min_notional.\n"
        "- Long→flat→long ne mélange pas lots.\n"
        "- Out-of-order fill event réconcilié.",
        "- Le Lot 90 ne produit ni InstrumentRegistryV1 ni InstrumentSpecificationV1.\n"
        "- InstrumentSpecificationV1 stale ou incompatible gèle le traitement.\n"
        "- Long→flat→long ne mélange pas lots.\n"
        "- Out-of-order fill event réconcilié.",
    )


def patch_v11_lot105() -> None:
    path = "docs/roadmap/V11_NEWS_AI_EVENT_CONTEXT.md"
    replace_required(
        path,
        "- NewsIngestionReadOnlyStateV1\n"
        "- NewsIngestionReadOnlyAuditV1\n"
        "- EventContextV1\n"
        "- SourceReliabilityStateV1\n"
        "- ReadOnlyAccountSnapshotV1\n"
        "- PermissionAuditV1",
        "- NewsIngestionReadOnlyStateV1\n"
        "- NewsIngestionReadOnlyAuditV1\n"
        "- EventContextV1\n"
        "- SourceReliabilityStateV1",
    )
    replace_required(
        path,
        "9. Autoriser uniquement endpoints GET/read ; bloquer au code et à la permission toute écriture/trade/withdrawal.\n"
        "10. Paginer et dédupliquer histories via IDs venue.\n"
        "11. Conserver request_time, venue_time, cursor et completeness.\n"
        "12. Scanner permissions et faire échouer si trading/withdrawal présent.",
        "9. Utiliser uniquement des sources de news/événements enregistrées et des adapters contextuels read-only.\n"
        "10. Ne produire aucun snapshot de compte, permission audit ou historique exchange appartenant à V13.",
    )
    replace_required(
        path,
        "- Prompt injection ne modifie aucun state exécutable.\n"
        "- Mock POST/DELETE interdit.\n"
        "- Clé avec withdrawal fait échouer startup.\n"
        "- Pagination duplicate/missing page.",
        "- Prompt injection ne modifie aucun state exécutable.\n"
        "- Aucun ReadOnlyAccountSnapshotV1 ou PermissionAuditV1 produit.\n"
        "- Aucune dépendance vers les connecteurs compte/exchange de V13.",
    )


def patch_traceability_docs() -> None:
    replace_required(
        "docs/DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md",
        "## 2. Decision Evidence Envelope",
        "## 2. `DecisionEvidenceEnvelopeV1`",
    )
    replace_required(
        "docs/LOT_SPECIFICATION_STANDARD.md",
        "5. Contrats de sortie : schémas, états, reason codes, incertitude et lineage.",
        "5. Contrats de sortie : schémas, états, reason codes, incertitude, lineage et `DecisionEvidenceEnvelopeV1`.",
    )
    replace_required(
        "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md",
        "Le score peut être `null`. Une valeur absente n'est jamais transformée en zéro.",
        "Chaque état est accompagné d'un `DecisionEvidenceEnvelopeV1` fermé reliant inputs, checksums, règles, reason codes, incertitude et conséquence finale.\n\n"
        "Le score peut être `null`. Une valeur absente n'est jamais transformée en zéro.",
    )
    replace_required(
        "docs/LOT26_REQUIREMENT_TEST_MATRIX.md",
        "| AC-26-22 audit evidence | audit/replay | manifest, lineage, config/registry checksums |",
        "| AC-26-22 audit evidence | audit/replay | `DecisionEvidenceEnvelopeV1`, manifest, lineage, config/registry checksums |",
    )


def patch_coverage_standards() -> None:
    replace_required(
        "docs/TEST_STRATEGY_COVERAGE_AND_QUALITY_GATES.md",
        "Pour tout nouveau lot ou correctif :\n\n"
        "```text\n"
        "line coverage global du code ajouté/modifié >= 90 %\n"
        "branch coverage global du code ajouté/modifié >= 85 %\n"
        "line coverage des modules critiques >= 95 %\n"
        "branch coverage des modules critiques >= 90 %\n"
        "mutation score des modules mathématiques/risque/exécution >= 80 %\n"
        "```",
        "Pour tout nouveau lot ou correctif, la dette historique ne peut plus être masquée par une couverture différentielle seule :\n\n"
        "```text\n"
        "line coverage globale du package runtime >= 90 %\n"
        "branch coverage globale du package runtime >= 85 %\n"
        "line coverage du code ajouté/modifié >= 90 %\n"
        "branch coverage du code ajouté/modifié >= 85 %\n"
        "line coverage des modules critiques >= 95 %\n"
        "branch coverage des modules critiques >= 90 %\n"
        "mutation score des modules mathématiques/risque/exécution >= 80 %\n"
        "```",
    )
    replace_required(
        "docs/LOT_SPECIFICATION_STANDARD.md",
        "line coverage ajouté/modifié >= 90 %\n"
        "branch coverage ajouté/modifié >= 85 %",
        "line coverage globale runtime >= 90 %\n"
        "branch coverage globale runtime >= 85 %\n"
        "line coverage ajouté/modifié >= 90 %\n"
        "branch coverage ajouté/modifié >= 85 %",
    )
    replace_required(
        "CONTRIBUTING.md",
        "python scripts/validate_architecture_boundaries.py\n"
        "python scripts/check_no_silent_numeric_coercion.py\n"
        "python scripts/validate_roadmap_documentation.py\n"
        "python scripts/validate_pre_lot26_readiness.py\n"
        "pytest -q --cov --cov-branch",
        "python scripts/validate_architecture_boundaries.py\n"
        "python scripts/validate_domain_architecture.py\n"
        "python scripts/audit_roadmap_semantics.py\n"
        "python scripts/validate_traceability_contract.py\n"
        "python scripts/check_no_silent_numeric_coercion.py\n"
        "python scripts/validate_roadmap_documentation.py\n"
        "python scripts/validate_pre_lot26_readiness.py\n"
        "pytest -q --cov --cov-branch --cov-report=json:coverage.json\n"
        "python scripts/validate_global_coverage.py",
    )
    replace_required(
        "CONTRIBUTING.md",
        "Nouveau code :\n\n"
        "```text\n"
        "line coverage >= 90 %\n"
        "branch coverage >= 85 %",
        "Dépôt et nouveau code :\n\n"
        "```text\n"
        "line coverage globale runtime >= 90 %\n"
        "branch coverage globale runtime >= 85 %\n"
        "line coverage du code modifié >= 90 %\n"
        "branch coverage du code modifié >= 85 %",
    )


def patch_code_quality_workflow() -> None:
    path = ".github/workflows/code-quality.yml"
    replace_required(path, "python-version: '3.11'", "python-version: '3.11.9'")
    replace_required(path, "python -m pip install -r requirements-dev.txt", "python -m pip install -r requirements-dev.lock")
    replace_required(
        path,
        "      - name: Architecture boundary gate\n"
        "        run: python scripts/validate_architecture_boundaries.py\n",
        "      - name: Legacy market-analysis execution boundary\n"
        "        run: python scripts/validate_architecture_boundaries.py\n"
        "      - name: All-domain architecture and ownership gate\n"
        "        run: python scripts/validate_domain_architecture.py\n"
        "      - name: Semantic roadmap ownership gate\n"
        "        run: python scripts/audit_roadmap_semantics.py\n"
        "      - name: Mandatory decision traceability gate\n"
        "        run: python scripts/validate_traceability_contract.py\n",
    )
    replace_required(
        path,
        "      - name: Full tests with line and branch coverage\n"
        "        run: pytest -q --cov --cov-branch --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=json:coverage.json\n"
        "      - name: P0 numerical core coverage gate",
        "      - name: Full tests with line and branch coverage\n"
        "        run: pytest -q --cov --cov-branch --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=json:coverage.json\n"
        "      - name: Repository-wide coverage gate\n"
        "        run: python scripts/validate_global_coverage.py --line-minimum 90 --branch-minimum 85\n"
        "      - name: Flake detection — repeat full suite three times\n"
        "        shell: bash\n"
        "        run: |\n"
        "          for attempt in 1 2 3; do\n"
        "            echo \"Full regression repetition ${attempt}/3\"\n"
        "            pytest -q\n"
        "          done\n"
        "      - name: P0 numerical core coverage gate",
    )
    replace_required(path, "pip-audit -r requirements-dev.txt", "pip-audit -r requirements-dev.lock")
    replace_required(
        path,
        "            reports/quality/mutation_score.json\n",
        "            reports/quality/mutation_score.json\n"
        "            reports/quality/global_coverage_gate.json\n"
        "            reports/P0_6_ROADMAP_SEMANTIC_AUDIT.json\n",
    )


def patch_other_workflows() -> None:
    path = ".github/workflows/roadmap-documentation-validation.yml"
    replace_required(
        path,
        "      - uses: actions/checkout@v4\n"
        "      - name: Validate canonical roadmap\n"
        "        run: python scripts/validate_roadmap_documentation.py",
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@v5\n"
        "        with:\n"
        "          python-version: '3.11.9'\n"
        "          cache: pip\n"
        "      - name: Install locked toolchain\n"
        "        run: |\n"
        "          python -m pip install --upgrade pip\n"
        "          python -m pip install -r requirements-dev.lock\n"
        "      - name: Validate canonical roadmap\n"
        "        run: python scripts/validate_roadmap_documentation.py\n"
        "      - name: Validate semantic ownership\n"
        "        run: python scripts/audit_roadmap_semantics.py\n"
        "      - name: Validate domain architecture\n"
        "        run: python scripts/validate_domain_architecture.py\n"
        "      - name: Validate traceability contract\n"
        "        run: python scripts/validate_traceability_contract.py",
    )
    path = ".github/workflows/pre-lot26-readiness-validation.yml"
    replace_required(
        path,
        "      - name: Validate canonical roadmap\n"
        "        run: python scripts/validate_roadmap_documentation.py\n",
        "      - name: Validate canonical roadmap\n"
        "        run: python scripts/validate_roadmap_documentation.py\n"
        "      - name: Validate semantic roadmap ownership\n"
        "        run: python scripts/audit_roadmap_semantics.py\n"
        "      - name: Validate all domain boundaries\n"
        "        run: python scripts/validate_domain_architecture.py\n"
        "      - name: Validate mandatory decision traceability\n"
        "        run: python scripts/validate_traceability_contract.py\n",
    )


def patch_roadmap_validator() -> None:
    path = "scripts/validate_roadmap_documentation.py"
    replace_required(
        path,
        '    "DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md",\n'
        '    "LOT_FINAL_AUDIT_AND_GO_NO_GO_GATE.md",',
        '    "DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md",\n'
        '    "CAPABILITY_AND_CONTRACT_OWNERSHIP_REGISTRY.md",\n'
        '    "MODEL_RETRAINING_AND_PROMOTION_POLICY.md",\n'
        '    "ECONOMIC_OBJECTIVE_AND_RISK_UTILITY_POLICY.md",\n'
        '    "LOT_FINAL_AUDIT_AND_GO_NO_GO_GATE.md",',
    )
    replace_required(
        path,
        '            "line coverage global du code ajouté/modifié >= 90 %",',
        '            "line coverage globale du package runtime >= 90 %",\n'
        '            "branch coverage globale du package runtime >= 85 %",',
    )


def main() -> int:
    patch_roadmap_index()
    patch_v1_lot0()
    patch_v6_lot62()
    patch_v9_lot90()
    patch_v11_lot105()
    patch_traceability_docs()
    patch_coverage_standards()
    patch_code_quality_workflow()
    patch_other_workflows()
    patch_roadmap_validator()
    print("P0.6 assurance migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
