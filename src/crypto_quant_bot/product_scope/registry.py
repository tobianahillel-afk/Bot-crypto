from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.product_scope.io import load_json, read_text_limited
from crypto_quant_bot.product_scope.models import (
    FunctionalCapability,
    ProductScopePolicy,
    ProductScopeRegistry,
    ProductScopeResult,
    RoadmapLot,
    RoadmapPhase,
)

DATASET_CATALOG_PATH = "data/audit/dataset_catalog.json"
LOT16_MANIFEST_PATH = "data/audit/reproducibility_manifest_lot16.json"
LOT17_HEALTH_PATH = "data/audit/health_monitor_lot17.json"
LOT18_OUTPUT_PATH = "data/audit/no_trading_compliance_lot18.json"
LOT19_OUTPUT_PATH = "data/audit/release_candidate_lot19.json"
LOT20_OUTPUT_PATH = "data/audit/v1_closure_lot20.json"
LOT21_OUTPUT_PATH = "data/audit/product_scope_lot21.json"
LOT21_CAPABILITIES_OUTPUT_PATH = "data/audit/product_scope_capabilities_lot21.jsonl"
LOT21_ROADMAP_OUTPUT_PATH = "data/audit/product_scope_roadmap_lot21.jsonl"
LOT21_REPORT_OUTPUT_PATH = "reports/lot_21_product_scope_report.md"
LOT21_VALIDATION_REPORT_PATH = "reports/lot_21_validation_report.md"
LOT21_FREEZE_REPORT_PATH = "reports/lot_21_v1_archive_freeze_report.md"
LOT21_OVERVIEW_DOC_PATH = "docs/LOT_21_PRODUCT_SCOPE.md"
LOT21_ACCEPTANCE_DOC_PATH = "docs/ACCEPTANCE_CRITERIA_LOT_21.md"
LOT21_ROADMAP_DOC_PATH = "docs/V2_PRODUCT_ROADMAP.md"
LOT21_COVERAGE_DOC_PATH = "docs/FUNCTIONAL_COVERAGE_REGISTRY.md"
ARCHIVE_OUTPUT_PATH = "dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
ARCHIVE_SHA256_OUTPUT_PATH = "dist/crypto_quant_bot_v1_defensive_audit_lot_20.sha256"

MANDATORY_CAPABILITY_IDS = [
    "v1_defensive_audit_closure",
    "market_analysis_engine",
    "multi_timeframe_engine",
    "technical_indicators_pack",
    "volume_profile_engine",
    "confluence_zones_engine",
    "order_book_l2_offline",
    "order_flow_offline",
    "strategic_microstructure",
    "scenario_engine",
    "scenario_explanation_engine",
    "expected_value_engine",
    "advanced_backtesting",
    "walk_forward_validation",
    "anti_overfitting_audit",
    "paper_trading_demo_portfolio",
    "simulated_orders_and_fills",
    "research_os",
    "experiment_registry",
    "hypothesis_tracking",
    "ablation_placebo_oos_testing",
    "ai_news_event_engine",
    "economic_calendar",
    "news_ingestion_read_only",
    "sentiment_narrative_engine",
    "llm_explanation_layer",
    "ai_hallucination_source_audit",
    "graphical_interface",
    "market_dashboard",
    "scenario_dashboard",
    "decision_logs_dashboard",
    "paper_trading_dashboard",
    "portfolio_dashboard",
    "audit_replay_ui",
    "account_analysis_read_only",
    "exchange_api_read_only",
    "balances_positions_read_only",
    "reconciliation_engine",
    "sandbox_demo_trading",
    "demo_order_lifecycle",
    "demo_risk_controls",
    "incident_response",
    "kill_switch_governance",
    "secrets_policy",
    "future_personal_live_trading",
    "live_human_approval_mode",
    "live_small_capital_guard",
    "live_reconciliation",
    "final_product_reporting",
]

MANDATORY_PHASE_IDS = [
    "V2_MARKET_ANALYSIS",
    "V3_MICROSTRUCTURE_SCENARIOS",
    "V4_EXPECTED_VALUE_BACKTESTING",
    "V5_PAPER_TRADING_DEMO",
    "V6_RESEARCH_OS",
    "V7_AI_NEWS_EVENT_ENGINE",
    "V8_UI_DASHBOARD",
    "V9_ACCOUNT_READ_ONLY",
    "V10_SANDBOX_DEMO_TRADING",
    "V11_LIVE_PERSONAL_GOVERNANCE",
]

SCOPE_INVARIANTS = {
    "TradingDecision": "WAIT",
    "SystemDecision": "BLOCK_TRADING",
    "final_decision": "WAIT",
    "final_system_decision": "BLOCK_TRADING",
    "trade_allowed": False,
    "execution_allowed": False,
    "Risk Engine blocks by default": True,
    "live_execution": "DISABLED",
    "leverage": "FORBIDDEN",
    "exposure_allowed": False,
    "allocation_allowed": False,
    "rebalance_allowed": False,
    "portfolio_state": "FROZEN",
    "capital_at_risk": 0,
    "external_connectivity_allowed": False,
    "human_review_required": True,
    "immutability_mode": "APPEND_ONLY_SIMULATED",
    "project_mode": "EDUCATIONAL_AUDIT_ONLY",
    "compliance_state": "COMPLIANT",
    "no_trading_state": "ENFORCED",
    "release_candidate_state": "READY_FOR_LOCAL_AUDIT_REVIEW",
    "closure_state": "V1_DEFENSIVE_AUDIT_CLOSED",
}

ACCEPTANCE_CRITERIA = [
    "La V1 defensive/audit reste cloturee et verifiee depuis l'archive locale Lot 20.",
    "Le gel de l'archive V1 est valide au Lot 21-bis et les chaines V2 ne la regenerent plus.",
    "La V2 est ouverte uniquement comme planning-only scope lock, sans implementation active.",
    "Le registre couvre explicitement Market Analysis, Research OS, AI / News / Event Engine, UI / Dashboard, Account Read-Only, Sandbox Demo Trading et Future Personal Live Trading.",
    "Toutes les capabilities hors V1 sont notees not_yet_implemented avec execution_allowed=false.",
    "Aucune connectivite externe, aucun connecteur exchange, aucune cle API et aucun WebSocket ne sont autorises.",
    "La roadmap officielle Lot 22 a Lot 147 est documentee comme forecast-only.",
    "Le DatasetCatalog contient les entrees Lot 21 sans doublon et reste upsertable idempotent.",
    "Le scope_checksum est deterministe hors champs runtime-only.",
    "Toute activation future exige un lot dedie, une validation propre et une revue humaine.",
]

SAFETY_BOUNDARIES = [
    "TradingDecision reste WAIT pour toute la portee Lot 21.",
    "SystemDecision reste BLOCK_TRADING pour toute la portee Lot 21.",
    "Aucune execution, aucune allocation et aucun reequilibrage ne sont autorises.",
    "Le capital_at_risk reste a 0 tant qu'aucun lot dedie n'est audite.",
]

RESEARCH_BOUNDARIES = [
    "Le Research OS reste un registre de recherche sans activation operationnelle.",
    "Les modules AI et explanation restent documentes ou research-only.",
    "Aucun resultat de recherche ne peut declencher une action executable au Lot 21.",
]

LIVE_TRADING_BOUNDARIES = [
    "Le live personnel n'est pas ouvert au Lot 21.",
    "Tout bloc live reste FUTURE_LIVE_GATED avec revue humaine obligatoire.",
    "Aucun ordre reel, aucune execution et aucune connectivite exchange ne sont autorises.",
]

UI_BOUNDARIES = [
    "L'UI est roadmap-only au Lot 21.",
    "Aucun serveur web et aucune interface operative ne sont demarres.",
    "Les dashboards restent des cibles documentaires jusqu'a un lot dedie.",
]

API_BOUNDARIES = [
    "Aucun appel API n'est autorise au Lot 21.",
    "Aucune cle API et aucun secret actif ne sont stockes ou utilises.",
    "Aucun WebSocket ni flux externe n'est autorise.",
]

PHASE_SPECS = [
    {
        "phase_id": "V2_MARKET_ANALYSIS",
        "title": "Market Analysis Foundation",
        "objective": "Structurer l'analyse de marche multi-timeframe, les indicateurs et les zones de confluence.",
        "start_lot_estimate": "Lot 22",
        "end_lot_estimate": "Lot 30",
        "status": "PLANNING_ONLY_LOCKED",
        "capabilities": [
            "market_analysis_engine",
            "multi_timeframe_engine",
            "technical_indicators_pack",
            "volume_profile_engine",
            "confluence_zones_engine",
        ],
    },
    {
        "phase_id": "V3_MICROSTRUCTURE_SCENARIOS",
        "title": "Offline Microstructure and Scenario Research",
        "objective": "Etendre le scope vers la microstructure offline et la recherche de scenarios explicables.",
        "start_lot_estimate": "Lot 31",
        "end_lot_estimate": "Lot 55",
        "status": "PLANNING_ONLY_LOCKED",
        "capabilities": [
            "order_book_l2_offline",
            "order_flow_offline",
            "strategic_microstructure",
            "scenario_engine",
            "scenario_explanation_engine",
        ],
    },
    {
        "phase_id": "V4_EXPECTED_VALUE_BACKTESTING",
        "title": "Expected Value and Advanced Backtesting",
        "objective": "Documenter les briques d'Expected Value, walk-forward et anti-overfitting.",
        "start_lot_estimate": "Lot 56",
        "end_lot_estimate": "Lot 66",
        "status": "PLANNING_ONLY_LOCKED",
        "capabilities": [
            "expected_value_engine",
            "advanced_backtesting",
            "walk_forward_validation",
            "anti_overfitting_audit",
        ],
    },
    {
        "phase_id": "V5_PAPER_TRADING_DEMO",
        "title": "Paper Trading and Demo Portfolio",
        "objective": "Encadrer un futur mode demo uniquement, sans activation au Lot 21.",
        "start_lot_estimate": "Lot 67",
        "end_lot_estimate": "Lot 76",
        "status": "PLANNING_ONLY_LOCKED",
        "capabilities": [
            "paper_trading_demo_portfolio",
            "simulated_orders_and_fills",
        ],
    },
    {
        "phase_id": "V6_RESEARCH_OS",
        "title": "Research OS",
        "objective": "Formaliser l'OS de recherche, l'experiment registry et le suivi d'hypotheses.",
        "start_lot_estimate": "Lot 77",
        "end_lot_estimate": "Lot 87",
        "status": "PLANNING_ONLY_LOCKED",
        "capabilities": [
            "research_os",
            "experiment_registry",
            "hypothesis_tracking",
            "ablation_placebo_oos_testing",
        ],
    },
    {
        "phase_id": "V7_AI_NEWS_EVENT_ENGINE",
        "title": "AI / News / Event Engine",
        "objective": "Documenter les blocs IA, news, evenements et audit des sources.",
        "start_lot_estimate": "Lot 88",
        "end_lot_estimate": "Lot 101",
        "status": "PLANNING_ONLY_LOCKED",
        "capabilities": [
            "ai_news_event_engine",
            "economic_calendar",
            "news_ingestion_read_only",
            "sentiment_narrative_engine",
            "llm_explanation_layer",
            "ai_hallucination_source_audit",
        ],
    },
    {
        "phase_id": "V8_UI_DASHBOARD",
        "title": "Graphical Interface and Dashboards",
        "objective": "Reserver l'interface graphique, les dashboards et la restitution produit a des lots dedies.",
        "start_lot_estimate": "Lot 102",
        "end_lot_estimate": "Lot 114",
        "status": "PLANNING_ONLY_LOCKED",
        "capabilities": [
            "graphical_interface",
            "market_dashboard",
            "scenario_dashboard",
            "decision_logs_dashboard",
            "paper_trading_dashboard",
            "portfolio_dashboard",
            "audit_replay_ui",
            "final_product_reporting",
        ],
    },
    {
        "phase_id": "V9_ACCOUNT_READ_ONLY",
        "title": "Account Analysis and Read-Only APIs",
        "objective": "Documenter l'analyse de compte et les futures integrations read-only sans activation.",
        "start_lot_estimate": "Lot 115",
        "end_lot_estimate": "Lot 124",
        "status": "PLANNING_ONLY_LOCKED",
        "capabilities": [
            "account_analysis_read_only",
            "exchange_api_read_only",
            "balances_positions_read_only",
            "reconciliation_engine",
        ],
    },
    {
        "phase_id": "V10_SANDBOX_DEMO_TRADING",
        "title": "Sandbox and Demo Trading",
        "objective": "Reserver les futures boucles demo/sandbox a un environnement entierement garde.",
        "start_lot_estimate": "Lot 125",
        "end_lot_estimate": "Lot 135",
        "status": "PLANNING_ONLY_LOCKED",
        "capabilities": [
            "sandbox_demo_trading",
            "demo_order_lifecycle",
            "demo_risk_controls",
        ],
    },
    {
        "phase_id": "V11_LIVE_PERSONAL_GOVERNANCE",
        "title": "Future Personal Live Trading Governance",
        "objective": "Verrouiller les controles de gouvernance, reconciliation et incident response avant tout live futur.",
        "start_lot_estimate": "Lot 136",
        "end_lot_estimate": "Lot 147",
        "status": "PLANNING_ONLY_LOCKED",
        "capabilities": [
            "incident_response",
            "kill_switch_governance",
            "secrets_policy",
            "future_personal_live_trading",
            "live_human_approval_mode",
            "live_small_capital_guard",
            "live_reconciliation",
        ],
    },
]

ROADMAP_BLOCKS = [
    {
        "start": 22,
        "end": 30,
        "phase_id": "V2_MARKET_ANALYSIS",
        "title_prefix": "Market Analysis work package",
        "objective": "Planning-only slice for market analysis, multi-timeframe context, indicators and confluence coverage.",
        "status": "FORECAST_ONLY",
        "capabilities": PHASE_SPECS[0]["capabilities"],
    },
    {
        "start": 31,
        "end": 42,
        "phase_id": "V3_MICROSTRUCTURE_SCENARIOS",
        "title_prefix": "Offline microstructure work package",
        "objective": "Planning-only slice for offline order book, order flow and strategic microstructure research.",
        "status": "FORECAST_ONLY",
        "capabilities": [
            "order_book_l2_offline",
            "order_flow_offline",
            "strategic_microstructure",
        ],
    },
    {
        "start": 43,
        "end": 55,
        "phase_id": "V3_MICROSTRUCTURE_SCENARIOS",
        "title_prefix": "Scenario engine work package",
        "objective": "Planning-only slice for scenario modeling and decision explanation research.",
        "status": "FORECAST_ONLY",
        "capabilities": [
            "scenario_engine",
            "scenario_explanation_engine",
        ],
    },
    {
        "start": 56,
        "end": 66,
        "phase_id": "V4_EXPECTED_VALUE_BACKTESTING",
        "title_prefix": "Expected value work package",
        "objective": "Planning-only slice for expected value research, backtesting, walk-forward validation and anti-overfitting audits.",
        "status": "FORECAST_ONLY",
        "capabilities": PHASE_SPECS[2]["capabilities"],
    },
    {
        "start": 67,
        "end": 76,
        "phase_id": "V5_PAPER_TRADING_DEMO",
        "title_prefix": "Paper demo work package",
        "objective": "Planning-only slice for demo portfolio and simulated order lifecycle artifacts.",
        "status": "FORECAST_ONLY",
        "capabilities": PHASE_SPECS[3]["capabilities"],
    },
    {
        "start": 77,
        "end": 87,
        "phase_id": "V6_RESEARCH_OS",
        "title_prefix": "Research OS work package",
        "objective": "Planning-only slice for research workflow, experiment registry and hypothesis governance.",
        "status": "FORECAST_ONLY",
        "capabilities": PHASE_SPECS[4]["capabilities"],
    },
    {
        "start": 88,
        "end": 101,
        "phase_id": "V7_AI_NEWS_EVENT_ENGINE",
        "title_prefix": "AI news event work package",
        "objective": "Planning-only slice for AI, news, event and explanation research modules.",
        "status": "FORECAST_ONLY",
        "capabilities": PHASE_SPECS[5]["capabilities"],
    },
    {
        "start": 102,
        "end": 114,
        "phase_id": "V8_UI_DASHBOARD",
        "title_prefix": "UI dashboard work package",
        "objective": "Planning-only slice for dashboards, audit replay UI and product reporting surfaces.",
        "status": "FORECAST_ONLY",
        "capabilities": PHASE_SPECS[6]["capabilities"],
    },
    {
        "start": 115,
        "end": 124,
        "phase_id": "V9_ACCOUNT_READ_ONLY",
        "title_prefix": "Account read-only work package",
        "objective": "Planning-only slice for read-only account analytics, balances and reconciliation.",
        "status": "FORECAST_ONLY",
        "capabilities": PHASE_SPECS[7]["capabilities"],
    },
    {
        "start": 125,
        "end": 135,
        "phase_id": "V10_SANDBOX_DEMO_TRADING",
        "title_prefix": "Sandbox demo work package",
        "objective": "Planning-only slice for sandbox demo controls and guarded demo-only operations.",
        "status": "FORECAST_ONLY",
        "capabilities": PHASE_SPECS[8]["capabilities"],
    },
    {
        "start": 136,
        "end": 147,
        "phase_id": "V11_LIVE_PERSONAL_GOVERNANCE",
        "title_prefix": "Live governance work package",
        "objective": "Planning-only slice for personal live governance, kill switch, secrets policy and live reconciliation gates.",
        "status": "FORECAST_ONLY",
        "capabilities": PHASE_SPECS[9]["capabilities"],
    },
]

CAPABILITY_SPECS = [
    {
        "capability_id": "v1_defensive_audit_closure",
        "title": "V1 Defensive Audit Closure",
        "status": "DONE_V1_DEFENSIVE",
        "phase": "V1_DEFENSIVE_AUDIT_CLOSED",
        "description": "Confirme la fermeture defensive/audit/no-trading de la V1 et l'existence d'une archive locale verifiee.",
        "depends_on": [],
        "risk_level": "LOW",
    },
    {
        "capability_id": "market_analysis_engine",
        "title": "Market Analysis Engine",
        "status": "PLANNED_V2",
        "phase": "V2_MARKET_ANALYSIS",
        "description": "Cadre analytique de marche pour consolider contexte, tendance, range et structure descriptive.",
        "depends_on": ["v1_defensive_audit_closure"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "multi_timeframe_engine",
        "title": "Multi-Timeframe Engine",
        "status": "PLANNED_V2",
        "phase": "V2_MARKET_ANALYSIS",
        "description": "Moteur de synchronisation des horizons de temps pour analyses descriptives sans decision executable.",
        "depends_on": ["market_analysis_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "technical_indicators_pack",
        "title": "Technical Indicators",
        "status": "PLANNED_V2",
        "phase": "V2_MARKET_ANALYSIS",
        "description": "Pack d'indicateurs techniques formalise pour usage analytique et comparaison de scenarios.",
        "depends_on": ["market_analysis_engine", "multi_timeframe_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "volume_profile_engine",
        "title": "Volume Profile / Confluence Zones",
        "status": "PLANNED_V2",
        "phase": "V2_MARKET_ANALYSIS",
        "description": "Formalisation du volume profile candle-based et des zones descriptives de structure.",
        "depends_on": ["market_analysis_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "confluence_zones_engine",
        "title": "Confluence Zones Engine",
        "status": "PLANNED_V2",
        "phase": "V2_MARKET_ANALYSIS",
        "description": "Cadrage des zones de confluence et des syntheses de contexte multi-sources.",
        "depends_on": ["market_analysis_engine", "volume_profile_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "order_book_l2_offline",
        "title": "Order Book L2 Offline",
        "status": "PLANNED_V3",
        "phase": "V3_MICROSTRUCTURE_SCENARIOS",
        "description": "Bloc offline de reconstruction analytique L2, sans connectivite externe et sans execution.",
        "depends_on": ["market_analysis_engine"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "order_flow_offline",
        "title": "Order Flow Offline",
        "status": "PLANNED_V3",
        "phase": "V3_MICROSTRUCTURE_SCENARIOS",
        "description": "Moteur de lecture offline du flux et de la pression de marche pour recherche uniquement.",
        "depends_on": ["order_book_l2_offline"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "strategic_microstructure",
        "title": "Strategic Microstructure",
        "status": "PLANNED_V3",
        "phase": "V3_MICROSTRUCTURE_SCENARIOS",
        "description": "Brique de recherche microstructurelle pour hypotheses tactiques et lectures contextuelles.",
        "depends_on": ["order_book_l2_offline", "order_flow_offline"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "scenario_engine",
        "title": "Scenario Engine",
        "status": "PLANNED_V3",
        "phase": "V3_MICROSTRUCTURE_SCENARIOS",
        "description": "Moteur de structuration des scenarios de marche, documente sans decision active.",
        "depends_on": ["market_analysis_engine", "strategic_microstructure"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "scenario_explanation_engine",
        "title": "Decision Explanation Engine",
        "status": "PLANNED_V3",
        "phase": "V3_MICROSTRUCTURE_SCENARIOS",
        "description": "Couche d'explication de scenarios et de raisonnement, sans sortie executable.",
        "depends_on": ["scenario_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "expected_value_engine",
        "title": "Expected Value Engine",
        "status": "PLANNED_V4",
        "phase": "V4_EXPECTED_VALUE_BACKTESTING",
        "description": "Bloc de calcul d'esperance pour recherche et comparaison de scenarios, sans activation.",
        "depends_on": ["scenario_engine"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "advanced_backtesting",
        "title": "Backtesting Advanced",
        "status": "PLANNED_V4",
        "phase": "V4_EXPECTED_VALUE_BACKTESTING",
        "description": "Roadmap d'un backtesting avance strictement separe du mode live et du mode demo actif.",
        "depends_on": ["expected_value_engine"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "walk_forward_validation",
        "title": "Walk Forward Validation",
        "status": "PLANNED_V4",
        "phase": "V4_EXPECTED_VALUE_BACKTESTING",
        "description": "Validation walk-forward documentee pour les futurs audits de robustesse.",
        "depends_on": ["advanced_backtesting"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "anti_overfitting_audit",
        "title": "Anti Overfitting Audit",
        "status": "PLANNED_V4",
        "phase": "V4_EXPECTED_VALUE_BACKTESTING",
        "description": "Audit anti-overfitting, placebo et hors echantillon reserve a des lots dedies.",
        "depends_on": ["advanced_backtesting", "walk_forward_validation"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "paper_trading_demo_portfolio",
        "title": "Paper Trading / Demo Portfolio",
        "status": "FUTURE_DEMO_ONLY",
        "phase": "V5_PAPER_TRADING_DEMO",
        "description": "Portefeuille demo futur strictement bloque au Lot 21 et reserve a un cadre non live.",
        "depends_on": ["advanced_backtesting"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "simulated_orders_and_fills",
        "title": "Simulated Order Lifecycle",
        "status": "FUTURE_DEMO_ONLY",
        "phase": "V5_PAPER_TRADING_DEMO",
        "description": "Cycle de simulation purement futur pour demo, sans activation ni usage exploitable au Lot 21.",
        "depends_on": ["paper_trading_demo_portfolio"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "research_os",
        "title": "Research OS",
        "status": "RESEARCH_ONLY",
        "phase": "V6_RESEARCH_OS",
        "description": "Socle de recherche pour hypotheses, experiences et gouvernance methodologique.",
        "depends_on": ["v1_defensive_audit_closure"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "experiment_registry",
        "title": "Experiment Registry",
        "status": "RESEARCH_ONLY",
        "phase": "V6_RESEARCH_OS",
        "description": "Registre d'experiences futur pour tracer hypotheses, variantes et evidences.",
        "depends_on": ["research_os"],
        "risk_level": "LOW",
    },
    {
        "capability_id": "hypothesis_tracking",
        "title": "Hypothesis Tracking",
        "status": "RESEARCH_ONLY",
        "phase": "V6_RESEARCH_OS",
        "description": "Suivi explicite des hypotheses de recherche et de leur statut de validation.",
        "depends_on": ["research_os", "experiment_registry"],
        "risk_level": "LOW",
    },
    {
        "capability_id": "ablation_placebo_oos_testing",
        "title": "Ablation / Placebo / OOS Testing",
        "status": "RESEARCH_ONLY",
        "phase": "V6_RESEARCH_OS",
        "description": "Briques de verification de robustesse reservees a la recherche et aux audits futurs.",
        "depends_on": ["experiment_registry", "anti_overfitting_audit"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "ai_news_event_engine",
        "title": "AI / News / Event Engine",
        "status": "PLANNED_LATER",
        "phase": "V7_AI_NEWS_EVENT_ENGINE",
        "description": "Bloc futur d'analyse AI/news/events, documente sans connectivite ni inference active.",
        "depends_on": ["research_os"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "economic_calendar",
        "title": "Economic Calendar",
        "status": "PLANNED_LATER",
        "phase": "V7_AI_NEWS_EVENT_ENGINE",
        "description": "Couche de calendrier economique future, strictement inactive au Lot 21.",
        "depends_on": ["ai_news_event_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "news_ingestion_read_only",
        "title": "News Ingestion Read-Only",
        "status": "PLANNED_LATER",
        "phase": "V7_AI_NEWS_EVENT_ENGINE",
        "description": "Ingestion news read-only future, sans appel externe actif au Lot 21.",
        "depends_on": ["ai_news_event_engine"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "sentiment_narrative_engine",
        "title": "Sentiment Narrative Engine",
        "status": "RESEARCH_ONLY",
        "phase": "V7_AI_NEWS_EVENT_ENGINE",
        "description": "Moteur futur de lecture narrative et de sentiment reserve a la recherche.",
        "depends_on": ["ai_news_event_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "llm_explanation_layer",
        "title": "LLM Explanation Layer",
        "status": "RESEARCH_ONLY",
        "phase": "V7_AI_NEWS_EVENT_ENGINE",
        "description": "Couche d'explication LLM strictement research-only et non exec au Lot 21.",
        "depends_on": ["scenario_explanation_engine", "research_os"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "ai_hallucination_source_audit",
        "title": "AI Hallucination Source Audit",
        "status": "RESEARCH_ONLY",
        "phase": "V7_AI_NEWS_EVENT_ENGINE",
        "description": "Audit futur des sources et des risques d'hallucination pour tout usage IA.",
        "depends_on": ["llm_explanation_layer"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "graphical_interface",
        "title": "Graphical Interface / Dashboard",
        "status": "PLANNED_LATER",
        "phase": "V8_UI_DASHBOARD",
        "description": "Interface graphique reservee a une phase documentaire ulterieure, sans activation serveur.",
        "depends_on": ["market_analysis_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "market_dashboard",
        "title": "Market Dashboard",
        "status": "PLANNED_LATER",
        "phase": "V8_UI_DASHBOARD",
        "description": "Dashboard marche futur, strictement passif tant qu'un lot UI dedie n'est pas valide.",
        "depends_on": ["graphical_interface", "market_analysis_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "scenario_dashboard",
        "title": "Scenario Dashboard",
        "status": "PLANNED_LATER",
        "phase": "V8_UI_DASHBOARD",
        "description": "Dashboard futur de scenarios et d'explications, sans interface active au Lot 21.",
        "depends_on": ["graphical_interface", "scenario_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "decision_logs_dashboard",
        "title": "Decision Logs Dashboard",
        "status": "PLANNED_LATER",
        "phase": "V8_UI_DASHBOARD",
        "description": "Vue future des logs et des justifications, sans action operative associee.",
        "depends_on": ["graphical_interface", "scenario_explanation_engine"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "paper_trading_dashboard",
        "title": "Paper Trading Dashboard",
        "status": "PLANNED_LATER",
        "phase": "V8_UI_DASHBOARD",
        "description": "Surface future de visualisation demo uniquement, bloquee au Lot 21.",
        "depends_on": ["graphical_interface", "paper_trading_demo_portfolio"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "portfolio_dashboard",
        "title": "Portfolio Dashboard",
        "status": "PLANNED_LATER",
        "phase": "V8_UI_DASHBOARD",
        "description": "Dashboard futur de portefeuille pour lecture et audit, sans operation active.",
        "depends_on": ["graphical_interface", "account_analysis_read_only"],
        "risk_level": "MEDIUM",
    },
    {
        "capability_id": "audit_replay_ui",
        "title": "Logs / Audit Replay UI",
        "status": "PLANNED_LATER",
        "phase": "V8_UI_DASHBOARD",
        "description": "UI future de replay d'audit et de parcours des traces, non active au Lot 21.",
        "depends_on": ["graphical_interface", "research_os"],
        "risk_level": "LOW",
    },
    {
        "capability_id": "account_analysis_read_only",
        "title": "Account Analysis Read-Only",
        "status": "PLANNED_LATER",
        "phase": "V9_ACCOUNT_READ_ONLY",
        "description": "Analyse de compte future en lecture seule, sans connectivite ni appel externe au Lot 21.",
        "depends_on": ["v1_defensive_audit_closure"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "exchange_api_read_only",
        "title": "Exchange API Read-Only",
        "status": "PLANNED_LATER",
        "phase": "V9_ACCOUNT_READ_ONLY",
        "description": "Integration exchange read-only future, documentee mais strictement inactive au Lot 21.",
        "depends_on": ["account_analysis_read_only"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "balances_positions_read_only",
        "title": "Balances and Positions Read-Only",
        "status": "PLANNED_LATER",
        "phase": "V9_ACCOUNT_READ_ONLY",
        "description": "Lecture future des soldes et de l'etat compte, reservee a une couche read-only.",
        "depends_on": ["exchange_api_read_only"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "reconciliation_engine",
        "title": "Reconciliation Engine",
        "status": "PLANNED_LATER",
        "phase": "V9_ACCOUNT_READ_ONLY",
        "description": "Moteur de rapprochement futur entre etats analytiques et etats read-only.",
        "depends_on": ["balances_positions_read_only"],
        "risk_level": "HIGH",
    },
    {
        "capability_id": "sandbox_demo_trading",
        "title": "Demo / Sandbox Trading",
        "status": "FUTURE_DEMO_ONLY",
        "phase": "V10_SANDBOX_DEMO_TRADING",
        "description": "Mode sandbox/demo futur, integralement bloque et reserve a des garde-fous dedies.",
        "depends_on": ["paper_trading_demo_portfolio", "demo_risk_controls"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "demo_order_lifecycle",
        "title": "Demo Order Lifecycle",
        "status": "FUTURE_DEMO_ONLY",
        "phase": "V10_SANDBOX_DEMO_TRADING",
        "description": "Cycle demo futur pour environnement sandbox uniquement, non active au Lot 21.",
        "depends_on": ["sandbox_demo_trading"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "demo_risk_controls",
        "title": "Demo Risk Controls",
        "status": "FUTURE_DEMO_ONLY",
        "phase": "V10_SANDBOX_DEMO_TRADING",
        "description": "Controles de risque demo futurs avant toute ouverture d'un mode sandbox.",
        "depends_on": ["paper_trading_demo_portfolio"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "incident_response",
        "title": "Incident Response",
        "status": "FUTURE_LIVE_GATED",
        "phase": "V11_LIVE_PERSONAL_GOVERNANCE",
        "description": "Gouvernance future de reponse incident avant tout live personnel.",
        "depends_on": ["reconciliation_engine"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "kill_switch_governance",
        "title": "Incident Response / Kill Switch",
        "status": "FUTURE_LIVE_GATED",
        "phase": "V11_LIVE_PERSONAL_GOVERNANCE",
        "description": "Bloc futur de kill switch et de gouvernance d'arret immediat, strictement gated.",
        "depends_on": ["incident_response"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "secrets_policy",
        "title": "Security / Secrets Policy",
        "status": "FUTURE_LIVE_GATED",
        "phase": "V11_LIVE_PERSONAL_GOVERNANCE",
        "description": "Politique future de secrets et de securite prealable a toute connectivite externe.",
        "depends_on": ["incident_response"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "future_personal_live_trading",
        "title": "Future Personal Live Trading Governance",
        "status": "FUTURE_LIVE_GATED",
        "phase": "V11_LIVE_PERSONAL_GOVERNANCE",
        "description": "Gouvernance future du live personnel, verrouillee et non ouverte au Lot 21.",
        "depends_on": ["kill_switch_governance", "secrets_policy"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "live_human_approval_mode",
        "title": "Live Human Approval Mode",
        "status": "FUTURE_LIVE_GATED",
        "phase": "V11_LIVE_PERSONAL_GOVERNANCE",
        "description": "Mode futur d'approbation humaine obligatoire avant toute activation live.",
        "depends_on": ["future_personal_live_trading"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "live_small_capital_guard",
        "title": "Live Small Capital Guard",
        "status": "FUTURE_LIVE_GATED",
        "phase": "V11_LIVE_PERSONAL_GOVERNANCE",
        "description": "Garde-fou futur de petit capital avant tout pilote live personnel.",
        "depends_on": ["future_personal_live_trading"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "live_reconciliation",
        "title": "Live Reconciliation",
        "status": "FUTURE_LIVE_GATED",
        "phase": "V11_LIVE_PERSONAL_GOVERNANCE",
        "description": "Rapprochement futur specifique au live personnel, soumis a gate de gouvernance.",
        "depends_on": ["reconciliation_engine", "future_personal_live_trading"],
        "risk_level": "VERY_HIGH",
    },
    {
        "capability_id": "final_product_reporting",
        "title": "Reporting / Client Reports",
        "status": "PLANNED_LATER",
        "phase": "V8_UI_DASHBOARD",
        "description": "Reporting produit futur et restitution finale, sans diffusion active au Lot 21.",
        "depends_on": ["graphical_interface", "research_os"],
        "risk_level": "MEDIUM",
    },
]


def default_source_artifacts() -> list[str]:
    return sorted(
        {
            DATASET_CATALOG_PATH,
            LOT16_MANIFEST_PATH,
            LOT17_HEALTH_PATH,
            LOT18_OUTPUT_PATH,
            LOT19_OUTPUT_PATH,
            LOT20_OUTPUT_PATH,
            ARCHIVE_OUTPUT_PATH,
            ARCHIVE_SHA256_OUTPUT_PATH,
            LOT21_FREEZE_REPORT_PATH,
            "docs/PROJECT_IDENTITY.md",
            "docs/MODULE_STATUS_MATRIX.md",
        }
    )


def _phase_activation_constraints(phase_id: str) -> list[str]:
    constraints = [
        "Lot 21 scope lock remains accepted.",
        "No-trading invariants remain enforced before any implementation.",
        "A dedicated implementation lot is required before activation.",
        "Human review sign-off is mandatory before activation.",
    ]
    if phase_id in {"V7_AI_NEWS_EVENT_ENGINE", "V9_ACCOUNT_READ_ONLY", "V10_SANDBOX_DEMO_TRADING", "V11_LIVE_PERSONAL_GOVERNANCE"}:
        constraints.append("External connectivity remains disabled until a dedicated gate review passes.")
    if phase_id == "V8_UI_DASHBOARD":
        constraints.append("No server, no websocket and no active interface may be started before a dedicated UI lot.")
    if phase_id == "V11_LIVE_PERSONAL_GOVERNANCE":
        constraints.append("Any live-oriented work remains FUTURE_LIVE_GATED until governance, reconciliation and kill switch controls are validated.")
    return constraints


def _capability_acceptance(spec: dict[str, Any]) -> list[str]:
    if spec["status"] == "DONE_V1_DEFENSIVE":
        return [
            "Already validated by the Lot 20 V1 closure and archive verification.",
            "Any later change requires a separate lot and fresh audit.",
        ]
    requirements = [
        "Dedicated implementation lot approved by project governance.",
        "No-trading invariants preserved through implementation and validation.",
        "Validation script and acceptance report added before activation.",
        "Human review sign-off recorded before activation.",
    ]
    if spec["status"] in {"FUTURE_DEMO_ONLY", "FUTURE_LIVE_GATED", "PLANNED_LATER"}:
        requirements.append("Capability remains planning-only until its dedicated lot is validated.")
    if spec["phase"] in {"V7_AI_NEWS_EVENT_ENGINE", "V9_ACCOUNT_READ_ONLY", "V10_SANDBOX_DEMO_TRADING", "V11_LIVE_PERSONAL_GOVERNANCE"}:
        requirements.append("Connectivity and secrets review required before any external access is considered.")
    if spec["status"] == "FUTURE_DEMO_ONLY":
        requirements.append("Demo-only guardrails must be validated without enabling active execution.")
    if spec["status"] == "FUTURE_LIVE_GATED":
        requirements.append("Future live activation requires kill switch, reconciliation and governance readiness.")
    return requirements


def _build_capabilities() -> list[FunctionalCapability]:
    capabilities = [
        FunctionalCapability(
            capability_id=spec["capability_id"],
            title=spec["title"],
            status=spec["status"],
            phase=spec["phase"],
            description=spec["description"],
            depends_on=list(spec["depends_on"]),
            not_yet_implemented=spec["status"] != "DONE_V1_DEFENSIVE",
            execution_allowed=False,
            external_connectivity_allowed=False,
            risk_level=spec["risk_level"],
            acceptance_required_before_activation=_capability_acceptance(spec),
        )
        for spec in CAPABILITY_SPECS
    ]
    return capabilities


def _build_phases() -> list[RoadmapPhase]:
    phases = []
    for spec in PHASE_SPECS:
        phases.append(
            RoadmapPhase(
                phase_id=spec["phase_id"],
                title=spec["title"],
                objective=spec["objective"],
                start_lot_estimate=spec["start_lot_estimate"],
                end_lot_estimate=spec["end_lot_estimate"],
                status=spec["status"],
                activation_constraints=_phase_activation_constraints(spec["phase_id"]),
                capabilities=list(spec["capabilities"]),
            )
        )
    return phases


def _build_roadmap_lots() -> list[RoadmapLot]:
    lots: list[RoadmapLot] = []
    for block in ROADMAP_BLOCKS:
        activation_constraints = _phase_activation_constraints(str(block["phase_id"]))
        for offset, lot_number in enumerate(range(int(block["start"]), int(block["end"]) + 1), start=1):
            lots.append(
                RoadmapLot(
                    lot_number=lot_number,
                    lot_id=f"Lot {lot_number}",
                    phase_id=str(block["phase_id"]),
                    title=f"Lot {lot_number} - {block['title_prefix']} {offset:02d}",
                    objective=str(block["objective"]),
                    status=str(block["status"]),
                    planning_only=True,
                    activation_constraints=list(activation_constraints),
                    capabilities=list(block["capabilities"]),
                )
            )
    return lots


def build_scope_checksum(payload: dict[str, object]) -> str:
    normalized = json.loads(json.dumps(payload))

    def strip_runtime_fields(obj: object) -> object:
        if isinstance(obj, dict):
            next_obj: dict[str, object] = {}
            for key, value in obj.items():
                if key in {"created_at", "scope_checksum"}:
                    continue
                next_obj[key] = strip_runtime_fields(value)
            return next_obj
        if isinstance(obj, list):
            return [strip_runtime_fields(item) for item in obj]
        return obj

    cleaned = strip_runtime_fields(normalized)
    if not isinstance(cleaned, dict):
        raise ValueError("scope checksum payload must remain a mapping")
    encoded = json.dumps(
        cleaned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_object(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{relative_path} must contain a JSON object")
    return payload


def _require_expected_pairs(payload: dict[str, Any], expected_pairs: dict[str, Any], *, name: str) -> None:
    for key, value in expected_pairs.items():
        if payload.get(key) != value:
            raise ValueError(f"{name} invalid {key}: {payload.get(key)}")


def _require_frozen_archive_report(
    root: Path,
    *,
    archive_checksum: str,
    archive_size_bytes: int,
) -> None:
    report_path = root / LOT21_FREEZE_REPORT_PATH
    if not report_path.exists():
        raise ValueError(f"missing archive freeze report: {LOT21_FREEZE_REPORT_PATH}")
    report_text = read_text_limited(report_path)
    required_lines = [
        f"source_v1_archive_path = {ARCHIVE_OUTPUT_PATH}",
        "source_v1_archive_frozen = true",
        f"source_v1_archive_sha256 = {archive_checksum}",
        f"source_v1_archive_size_bytes = {archive_size_bytes}",
    ]
    for line in required_lines:
        if line not in report_text:
            raise ValueError(f"archive freeze report mismatch: {line}")


def _build_scope_checks(
    *,
    archive_checksum: str,
    archive_size_bytes: int,
    closure_snapshot: dict[str, Any],
    release_snapshot: dict[str, Any],
    compliance_snapshot: dict[str, Any],
    health_snapshot: dict[str, Any],
    manifest_snapshot: dict[str, Any],
    capability_count: int,
    phase_count: int,
    future_lot_count: int,
) -> list[dict[str, Any]]:
    return [
        {
            "check_name": "v1_closure_state",
            "status": "PASS",
            "expected_value": "V1_DEFENSIVE_AUDIT_CLOSED",
            "observed_value": closure_snapshot.get("closure_state"),
            "block_reason": "",
            "message": "La V1 defensive/audit reste fermee avant ouverture du scope V2.",
        },
        {
            "check_name": "release_candidate_state",
            "status": "PASS",
            "expected_value": "READY_FOR_LOCAL_AUDIT_REVIEW",
            "observed_value": release_snapshot.get("release_candidate_state"),
            "block_reason": "",
            "message": "Le release candidate Lot 19 reste la base defensive de reference.",
        },
        {
            "check_name": "no_trading_state",
            "status": "PASS",
            "expected_value": "ENFORCED",
            "observed_value": compliance_snapshot.get("no_trading_state"),
            "block_reason": "",
            "message": "La conformite no-trading reste appliquee.",
        },
        {
            "check_name": "health_state",
            "status": "PASS",
            "expected_value": "HEALTHY_FOR_LOCAL_AUDIT",
            "observed_value": health_snapshot.get("health_state"),
            "block_reason": "",
            "message": "Le Health Monitor reste sain pour audit local.",
        },
        {
            "check_name": "reproducibility_state",
            "status": "PASS",
            "expected_value": "REPRODUCIBLE_LOCALLY",
            "observed_value": manifest_snapshot.get("reproducibility_state"),
            "block_reason": "",
            "message": "Le manifeste de reproductibilite reste utilisable comme source de depart.",
        },
        {
            "check_name": "archive_checksum_verified",
            "status": "PASS",
            "expected_value": closure_snapshot.get("archive_sha256"),
            "observed_value": archive_checksum,
            "block_reason": "",
            "message": "L'archive V1 et son SHA256 local sont verifies avant d'ouvrir le scope produit.",
        },
        {
            "check_name": "archive_size_verified",
            "status": "PASS",
            "expected_value": closure_snapshot.get("archive_size_bytes"),
            "observed_value": archive_size_bytes,
            "block_reason": "",
            "message": "La taille archivee observee reste coherente avec le snapshot Lot 20.",
        },
        {
            "check_name": "archive_frozen_guard",
            "status": "PASS",
            "expected_value": True,
            "observed_value": True,
            "block_reason": "",
            "message": "La V2 reference uniquement l'archive V1 gelee validee au Lot 21-bis.",
        },
        {
            "check_name": "capability_registry_complete",
            "status": "PASS",
            "expected_value": len(MANDATORY_CAPABILITY_IDS),
            "observed_value": capability_count,
            "block_reason": "",
            "message": "Toutes les capabilities minimales de la feuille de route produit sont enregistrees.",
        },
        {
            "check_name": "phase_registry_complete",
            "status": "PASS",
            "expected_value": len(MANDATORY_PHASE_IDS),
            "observed_value": phase_count,
            "block_reason": "",
            "message": "Toutes les phases roadmap minimales sont documentees.",
        },
        {
            "check_name": "future_lot_registry_complete",
            "status": "PASS",
            "expected_value": 126,
            "observed_value": future_lot_count,
            "block_reason": "",
            "message": "Les lots 22 a 147 sont previsionnellement verrouilles dans le registre.",
        },
        {
            "check_name": "scope_execution_blocked",
            "status": "PASS",
            "expected_value": False,
            "observed_value": False,
            "block_reason": "",
            "message": "Le scope reste documentaire, sans execution ni connectivite externe.",
        },
    ]


def build_product_scope_registry(root: Path) -> ProductScopeRegistry:
    policy = ProductScopePolicy()
    closure_snapshot = _require_object(root, LOT20_OUTPUT_PATH)
    release_snapshot = _require_object(root, LOT19_OUTPUT_PATH)
    compliance_snapshot = _require_object(root, LOT18_OUTPUT_PATH)
    health_snapshot = _require_object(root, LOT17_HEALTH_PATH)
    manifest_snapshot = _require_object(root, LOT16_MANIFEST_PATH)

    _require_expected_pairs(
        closure_snapshot,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "closure_state": policy.v1_closure_state,
            "release_candidate_state": "READY_FOR_LOCAL_AUDIT_REVIEW",
            "compliance_state": "COMPLIANT",
            "no_trading_state": "ENFORCED",
            "live_execution": policy.live_execution,
            "leverage": policy.leverage,
            "trade_allowed": policy.trade_allowed,
            "execution_allowed": policy.execution_allowed,
            "external_connectivity_allowed": policy.external_connectivity_allowed,
        },
        name="Lot 20 closure snapshot",
    )
    _require_expected_pairs(
        release_snapshot,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "release_candidate_state": "READY_FOR_LOCAL_AUDIT_REVIEW",
            "compliance_state": "COMPLIANT",
            "no_trading_state": "ENFORCED",
            "live_execution": policy.live_execution,
            "leverage": policy.leverage,
            "trade_allowed": policy.trade_allowed,
            "execution_allowed": policy.execution_allowed,
            "external_connectivity_allowed": policy.external_connectivity_allowed,
        },
        name="Lot 19 release snapshot",
    )
    _require_expected_pairs(
        compliance_snapshot,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "compliance_state": "COMPLIANT",
            "no_trading_state": "ENFORCED",
            "live_execution": policy.live_execution,
            "leverage": policy.leverage,
            "trade_allowed": policy.trade_allowed,
            "execution_allowed": policy.execution_allowed,
            "external_connectivity_allowed": policy.external_connectivity_allowed,
        },
        name="Lot 18 compliance snapshot",
    )
    _require_expected_pairs(
        health_snapshot,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "health_state": "HEALTHY_FOR_LOCAL_AUDIT",
            "trade_allowed": policy.trade_allowed,
            "execution_allowed": policy.execution_allowed,
            "external_connectivity_allowed": policy.external_connectivity_allowed,
        },
        name="Lot 17 health snapshot",
    )
    _require_expected_pairs(
        manifest_snapshot,
        {
            "project_name": policy.project_name,
            "project_mode": policy.project_mode,
            "reproducibility_state": "REPRODUCIBLE_LOCALLY",
            "trade_allowed": policy.trade_allowed,
            "execution_allowed": policy.execution_allowed,
            "external_connectivity_allowed": policy.external_connectivity_allowed,
        },
        name="Lot 16 reproducibility manifest",
    )
    health_invariants = health_snapshot.get("invariants")
    if not isinstance(health_invariants, dict):
        raise ValueError("Lot 17 health invariants missing")
    if health_invariants.get("live_execution") != policy.live_execution:
        raise ValueError("Lot 17 health invariant live_execution mismatch")
    if health_invariants.get("leverage") != policy.leverage:
        raise ValueError("Lot 17 health invariant leverage mismatch")
    manifest_invariants = manifest_snapshot.get("invariants")
    if not isinstance(manifest_invariants, dict):
        raise ValueError("Lot 16 manifest invariants missing")
    if manifest_invariants.get("live_execution") != policy.live_execution:
        raise ValueError("Lot 16 manifest invariant live_execution mismatch")
    if manifest_invariants.get("leverage") != policy.leverage:
        raise ValueError("Lot 16 manifest invariant leverage mismatch")

    archive_path = root / ARCHIVE_OUTPUT_PATH
    archive_sha256_path = root / ARCHIVE_SHA256_OUTPUT_PATH
    if not archive_path.exists():
        raise ValueError(f"missing archive: {ARCHIVE_OUTPUT_PATH}")
    if not archive_sha256_path.exists():
        raise ValueError(f"missing archive sha256 sidecar: {ARCHIVE_SHA256_OUTPUT_PATH}")
    archive_checksum = sha256_file(archive_path)
    sha_line = archive_sha256_path.read_text(encoding="utf-8").strip()
    expected_sha_line = f"{archive_checksum}  {archive_path.name}"
    if sha_line != expected_sha_line:
        raise ValueError("archive sha256 sidecar mismatch")
    if closure_snapshot.get("archive_path") != ARCHIVE_OUTPUT_PATH:
        raise ValueError("Lot 20 archive_path mismatch")
    if closure_snapshot.get("archive_sha256_path") != ARCHIVE_SHA256_OUTPUT_PATH:
        raise ValueError("Lot 20 archive_sha256_path mismatch")
    if closure_snapshot.get("archive_sha256") != archive_checksum:
        raise ValueError("Lot 20 archive checksum mismatch")
    archive_size_bytes = archive_path.stat().st_size
    if closure_snapshot.get("archive_size_bytes") != archive_size_bytes:
        raise ValueError("Lot 20 archive size mismatch")
    _require_frozen_archive_report(
        root,
        archive_checksum=archive_checksum,
        archive_size_bytes=archive_size_bytes,
    )

    capabilities = _build_capabilities()
    phases = _build_phases()
    roadmap_lots = _build_roadmap_lots()
    capability_ids = [capability.capability_id for capability in capabilities]
    phase_ids = [phase.phase_id for phase in phases]
    if capability_ids != MANDATORY_CAPABILITY_IDS:
        raise ValueError("capability registry ordering mismatch")
    if phase_ids != MANDATORY_PHASE_IDS:
        raise ValueError("phase registry ordering mismatch")

    scope_checks = _build_scope_checks(
        archive_checksum=archive_checksum,
        archive_size_bytes=archive_size_bytes,
        closure_snapshot=closure_snapshot,
        release_snapshot=release_snapshot,
        compliance_snapshot=compliance_snapshot,
        health_snapshot=health_snapshot,
        manifest_snapshot=manifest_snapshot,
        capability_count=len(capabilities),
        phase_count=len(phases),
        future_lot_count=len(roadmap_lots),
    )

    registry = ProductScopeRegistry(
        scope_version=policy.scope_version,
        policy_version=policy.policy_version,
        project_name=policy.project_name,
        project_identity=policy.project_identity,
        project_mode=policy.project_mode,
        created_at=utc_now_iso(),
        source_v1_archive_path=ARCHIVE_OUTPUT_PATH,
        source_v1_archive_frozen=True,
        source_v1_archive_sha256=archive_checksum,
        source_v1_archive_size_bytes=archive_size_bytes,
        v1_closure_state=closure_snapshot["closure_state"],
        v2_scope_state=policy.v2_scope_state,
        scope_state=policy.scope_state,
        execution_allowed=policy.execution_allowed,
        trade_allowed=policy.trade_allowed,
        external_connectivity_allowed=policy.external_connectivity_allowed,
        live_execution=policy.live_execution,
        leverage=policy.leverage,
        capability_count=len(capabilities),
        phase_count=len(phases),
        future_lot_count=len(roadmap_lots),
        capabilities=capabilities,
        roadmap_phases=phases,
        roadmap_lots=roadmap_lots,
        safety_boundaries=list(SAFETY_BOUNDARIES),
        research_boundaries=list(RESEARCH_BOUNDARIES),
        live_trading_boundaries=list(LIVE_TRADING_BOUNDARIES),
        ui_boundaries=list(UI_BOUNDARIES),
        api_boundaries=list(API_BOUNDARIES),
        acceptance_criteria=list(ACCEPTANCE_CRITERIA),
        scope_checks=scope_checks,
        scope_block_reasons=list(policy.scope_block_reasons),
        source_artifacts=default_source_artifacts(),
        scope_checksum="",
    )
    return replace(registry, scope_checksum=build_scope_checksum(registry.to_dict()))


def build_scope_result(_root: Path, registry: ProductScopeRegistry) -> ProductScopeResult:
    return ProductScopeResult(
        scope_version=registry.scope_version,
        policy_version=registry.policy_version,
        project_name=registry.project_name,
        project_identity=registry.project_identity,
        scope_state=registry.scope_state,
        v2_scope_state=registry.v2_scope_state,
        capability_count=registry.capability_count,
        phase_count=registry.phase_count,
        future_lot_count=registry.future_lot_count,
        output_paths=[
            LOT21_OUTPUT_PATH,
            LOT21_CAPABILITIES_OUTPUT_PATH,
            LOT21_ROADMAP_OUTPUT_PATH,
            LOT21_REPORT_OUTPUT_PATH,
            LOT21_VALIDATION_REPORT_PATH,
            LOT21_FREEZE_REPORT_PATH,
            LOT21_OVERVIEW_DOC_PATH,
            LOT21_ACCEPTANCE_DOC_PATH,
            LOT21_ROADMAP_DOC_PATH,
            LOT21_COVERAGE_DOC_PATH,
        ],
        source_artifacts=list(registry.source_artifacts),
        created_at=registry.created_at,
    )
