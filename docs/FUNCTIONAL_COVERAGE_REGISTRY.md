# Functional Coverage Registry

Registre complet du scope fonctionnel V2+ fige au Lot 21-bis.

Le registre documente les modules attendus sans activer trading, connectivite externe ou interface operative.

source_v1_archive_path = dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz

source_v1_archive_frozen = true

source_v1_archive_sha256 = ef5b5998cd5f75b6d97acc4afc10aeaf4833b565d2c11e9f3278bace06c78667

source_v1_archive_size_bytes = 366985

Le Lot 21-bis confirme aussi que la V2 reference seulement l'archive V1 figee et n'a plus le droit de la regenerer.

## v1_defensive_audit_closure

Title: V1 Defensive Audit Closure

Status: DONE_V1_DEFENSIVE

Phase: V1_DEFENSIVE_AUDIT_CLOSED

Description: Confirme la fermeture defensive/audit/no-trading de la V1 et l'existence d'une archive locale verifiee.

Risk level: LOW

Not yet implemented: false

Dependencies:
- None

Activation gate:
- Already validated by the Lot 20 V1 closure and archive verification.
- Any later change requires a separate lot and fresh audit.

## market_analysis_engine

Title: Market Analysis Engine

Status: PLANNED_V2

Phase: V2_MARKET_ANALYSIS

Description: Cadre analytique de marche pour consolider contexte, tendance, range et structure descriptive.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `v1_defensive_audit_closure`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## multi_timeframe_engine

Title: Multi-Timeframe Engine

Status: PLANNED_V2

Phase: V2_MARKET_ANALYSIS

Description: Moteur de synchronisation des horizons de temps pour analyses descriptives sans decision executable.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `market_analysis_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## technical_indicators_pack

Title: Technical Indicators

Status: PLANNED_V2

Phase: V2_MARKET_ANALYSIS

Description: Pack d'indicateurs techniques formalise pour usage analytique et comparaison de scenarios.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `market_analysis_engine`
- `multi_timeframe_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## volume_profile_engine

Title: Volume Profile / Confluence Zones

Status: PLANNED_V2

Phase: V2_MARKET_ANALYSIS

Description: Formalisation du volume profile candle-based et des zones descriptives de structure.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `market_analysis_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## confluence_zones_engine

Title: Confluence Zones Engine

Status: PLANNED_V2

Phase: V2_MARKET_ANALYSIS

Description: Cadrage des zones de confluence et des syntheses de contexte multi-sources.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `market_analysis_engine`
- `volume_profile_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## order_book_l2_offline

Title: Order Book L2 Offline

Status: PLANNED_V3

Phase: V3_MICROSTRUCTURE_SCENARIOS

Description: Bloc offline de reconstruction analytique L2, sans connectivite externe et sans execution.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `market_analysis_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## order_flow_offline

Title: Order Flow Offline

Status: PLANNED_V3

Phase: V3_MICROSTRUCTURE_SCENARIOS

Description: Moteur de lecture offline du flux et de la pression de marche pour recherche uniquement.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `order_book_l2_offline`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## strategic_microstructure

Title: Strategic Microstructure

Status: PLANNED_V3

Phase: V3_MICROSTRUCTURE_SCENARIOS

Description: Brique de recherche microstructurelle pour hypotheses tactiques et lectures contextuelles.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `order_book_l2_offline`
- `order_flow_offline`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## scenario_engine

Title: Scenario Engine

Status: PLANNED_V3

Phase: V3_MICROSTRUCTURE_SCENARIOS

Description: Moteur de structuration des scenarios de marche, documente sans decision active.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `market_analysis_engine`
- `strategic_microstructure`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## scenario_explanation_engine

Title: Decision Explanation Engine

Status: PLANNED_V3

Phase: V3_MICROSTRUCTURE_SCENARIOS

Description: Couche d'explication de scenarios et de raisonnement, sans sortie executable.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `scenario_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## expected_value_engine

Title: Expected Value Engine

Status: PLANNED_V4

Phase: V4_EXPECTED_VALUE_BACKTESTING

Description: Bloc de calcul d'esperance pour recherche et comparaison de scenarios, sans activation.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `scenario_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## advanced_backtesting

Title: Backtesting Advanced

Status: PLANNED_V4

Phase: V4_EXPECTED_VALUE_BACKTESTING

Description: Roadmap d'un backtesting avance strictement separe du mode live et du mode demo actif.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `expected_value_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## walk_forward_validation

Title: Walk Forward Validation

Status: PLANNED_V4

Phase: V4_EXPECTED_VALUE_BACKTESTING

Description: Validation walk-forward documentee pour les futurs audits de robustesse.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `advanced_backtesting`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## anti_overfitting_audit

Title: Anti Overfitting Audit

Status: PLANNED_V4

Phase: V4_EXPECTED_VALUE_BACKTESTING

Description: Audit anti-overfitting, placebo et hors echantillon reserve a des lots dedies.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `advanced_backtesting`
- `walk_forward_validation`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## paper_trading_demo_portfolio

Title: Paper Trading / Demo Portfolio

Status: FUTURE_DEMO_ONLY

Phase: V5_PAPER_TRADING_DEMO

Description: Portefeuille demo futur strictement bloque au Lot 21 et reserve a un cadre non live.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `advanced_backtesting`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Demo-only guardrails must be validated without enabling active execution.

## simulated_orders_and_fills

Title: Simulated Order Lifecycle

Status: FUTURE_DEMO_ONLY

Phase: V5_PAPER_TRADING_DEMO

Description: Cycle de simulation purement futur pour demo, sans activation ni usage exploitable au Lot 21.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `paper_trading_demo_portfolio`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Demo-only guardrails must be validated without enabling active execution.

## research_os

Title: Research OS

Status: RESEARCH_ONLY

Phase: V6_RESEARCH_OS

Description: Socle de recherche pour hypotheses, experiences et gouvernance methodologique.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `v1_defensive_audit_closure`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## experiment_registry

Title: Experiment Registry

Status: RESEARCH_ONLY

Phase: V6_RESEARCH_OS

Description: Registre d'experiences futur pour tracer hypotheses, variantes et evidences.

Risk level: LOW

Not yet implemented: true

Dependencies:
- `research_os`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## hypothesis_tracking

Title: Hypothesis Tracking

Status: RESEARCH_ONLY

Phase: V6_RESEARCH_OS

Description: Suivi explicite des hypotheses de recherche et de leur statut de validation.

Risk level: LOW

Not yet implemented: true

Dependencies:
- `research_os`
- `experiment_registry`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## ablation_placebo_oos_testing

Title: Ablation / Placebo / OOS Testing

Status: RESEARCH_ONLY

Phase: V6_RESEARCH_OS

Description: Briques de verification de robustesse reservees a la recherche et aux audits futurs.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `experiment_registry`
- `anti_overfitting_audit`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.

## ai_news_event_engine

Title: AI / News / Event Engine

Status: PLANNED_LATER

Phase: V7_AI_NEWS_EVENT_ENGINE

Description: Bloc futur d'analyse AI/news/events, documente sans connectivite ni inference active.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `research_os`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.

## economic_calendar

Title: Economic Calendar

Status: PLANNED_LATER

Phase: V7_AI_NEWS_EVENT_ENGINE

Description: Couche de calendrier economique future, strictement inactive au Lot 21.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `ai_news_event_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.

## news_ingestion_read_only

Title: News Ingestion Read-Only

Status: PLANNED_LATER

Phase: V7_AI_NEWS_EVENT_ENGINE

Description: Ingestion news read-only future, sans appel externe actif au Lot 21.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `ai_news_event_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.

## sentiment_narrative_engine

Title: Sentiment Narrative Engine

Status: RESEARCH_ONLY

Phase: V7_AI_NEWS_EVENT_ENGINE

Description: Moteur futur de lecture narrative et de sentiment reserve a la recherche.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `ai_news_event_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Connectivity and secrets review required before any external access is considered.

## llm_explanation_layer

Title: LLM Explanation Layer

Status: RESEARCH_ONLY

Phase: V7_AI_NEWS_EVENT_ENGINE

Description: Couche d'explication LLM strictement research-only et non exec au Lot 21.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `scenario_explanation_engine`
- `research_os`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Connectivity and secrets review required before any external access is considered.

## ai_hallucination_source_audit

Title: AI Hallucination Source Audit

Status: RESEARCH_ONLY

Phase: V7_AI_NEWS_EVENT_ENGINE

Description: Audit futur des sources et des risques d'hallucination pour tout usage IA.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `llm_explanation_layer`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Connectivity and secrets review required before any external access is considered.

## graphical_interface

Title: Graphical Interface / Dashboard

Status: PLANNED_LATER

Phase: V8_UI_DASHBOARD

Description: Interface graphique reservee a une phase documentaire ulterieure, sans activation serveur.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `market_analysis_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.

## market_dashboard

Title: Market Dashboard

Status: PLANNED_LATER

Phase: V8_UI_DASHBOARD

Description: Dashboard marche futur, strictement passif tant qu'un lot UI dedie n'est pas valide.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `graphical_interface`
- `market_analysis_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.

## scenario_dashboard

Title: Scenario Dashboard

Status: PLANNED_LATER

Phase: V8_UI_DASHBOARD

Description: Dashboard futur de scenarios et d'explications, sans interface active au Lot 21.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `graphical_interface`
- `scenario_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.

## decision_logs_dashboard

Title: Decision Logs Dashboard

Status: PLANNED_LATER

Phase: V8_UI_DASHBOARD

Description: Vue future des logs et des justifications, sans action operative associee.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `graphical_interface`
- `scenario_explanation_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.

## paper_trading_dashboard

Title: Paper Trading Dashboard

Status: PLANNED_LATER

Phase: V8_UI_DASHBOARD

Description: Surface future de visualisation demo uniquement, bloquee au Lot 21.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `graphical_interface`
- `paper_trading_demo_portfolio`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.

## portfolio_dashboard

Title: Portfolio Dashboard

Status: PLANNED_LATER

Phase: V8_UI_DASHBOARD

Description: Dashboard futur de portefeuille pour lecture et audit, sans operation active.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `graphical_interface`
- `account_analysis_read_only`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.

## audit_replay_ui

Title: Logs / Audit Replay UI

Status: PLANNED_LATER

Phase: V8_UI_DASHBOARD

Description: UI future de replay d'audit et de parcours des traces, non active au Lot 21.

Risk level: LOW

Not yet implemented: true

Dependencies:
- `graphical_interface`
- `research_os`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.

## account_analysis_read_only

Title: Account Analysis Read-Only

Status: PLANNED_LATER

Phase: V9_ACCOUNT_READ_ONLY

Description: Analyse de compte future en lecture seule, sans connectivite ni appel externe au Lot 21.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `v1_defensive_audit_closure`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.

## exchange_api_read_only

Title: Exchange API Read-Only

Status: PLANNED_LATER

Phase: V9_ACCOUNT_READ_ONLY

Description: Integration exchange read-only future, documentee mais strictement inactive au Lot 21.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `account_analysis_read_only`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.

## balances_positions_read_only

Title: Balances and Positions Read-Only

Status: PLANNED_LATER

Phase: V9_ACCOUNT_READ_ONLY

Description: Lecture future des soldes et de l'etat compte, reservee a une couche read-only.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `exchange_api_read_only`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.

## reconciliation_engine

Title: Reconciliation Engine

Status: PLANNED_LATER

Phase: V9_ACCOUNT_READ_ONLY

Description: Moteur de rapprochement futur entre etats analytiques et etats read-only.

Risk level: HIGH

Not yet implemented: true

Dependencies:
- `balances_positions_read_only`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.

## sandbox_demo_trading

Title: Demo / Sandbox Trading

Status: FUTURE_DEMO_ONLY

Phase: V10_SANDBOX_DEMO_TRADING

Description: Mode sandbox/demo futur, integralement bloque et reserve a des garde-fous dedies.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `paper_trading_demo_portfolio`
- `demo_risk_controls`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.
- Demo-only guardrails must be validated without enabling active execution.

## demo_order_lifecycle

Title: Demo Order Lifecycle

Status: FUTURE_DEMO_ONLY

Phase: V10_SANDBOX_DEMO_TRADING

Description: Cycle demo futur pour environnement sandbox uniquement, non active au Lot 21.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `sandbox_demo_trading`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.
- Demo-only guardrails must be validated without enabling active execution.

## demo_risk_controls

Title: Demo Risk Controls

Status: FUTURE_DEMO_ONLY

Phase: V10_SANDBOX_DEMO_TRADING

Description: Controles de risque demo futurs avant toute ouverture d'un mode sandbox.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `paper_trading_demo_portfolio`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.
- Demo-only guardrails must be validated without enabling active execution.

## incident_response

Title: Incident Response

Status: FUTURE_LIVE_GATED

Phase: V11_LIVE_PERSONAL_GOVERNANCE

Description: Gouvernance future de reponse incident avant tout live personnel.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `reconciliation_engine`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.
- Future live activation requires kill switch, reconciliation and governance readiness.

## kill_switch_governance

Title: Incident Response / Kill Switch

Status: FUTURE_LIVE_GATED

Phase: V11_LIVE_PERSONAL_GOVERNANCE

Description: Bloc futur de kill switch et de gouvernance d'arret immediat, strictement gated.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `incident_response`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.
- Future live activation requires kill switch, reconciliation and governance readiness.

## secrets_policy

Title: Security / Secrets Policy

Status: FUTURE_LIVE_GATED

Phase: V11_LIVE_PERSONAL_GOVERNANCE

Description: Politique future de secrets et de securite prealable a toute connectivite externe.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `incident_response`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.
- Future live activation requires kill switch, reconciliation and governance readiness.

## future_personal_live_trading

Title: Future Personal Live Trading Governance

Status: FUTURE_LIVE_GATED

Phase: V11_LIVE_PERSONAL_GOVERNANCE

Description: Gouvernance future du live personnel, verrouillee et non ouverte au Lot 21.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `kill_switch_governance`
- `secrets_policy`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.
- Future live activation requires kill switch, reconciliation and governance readiness.

## live_human_approval_mode

Title: Live Human Approval Mode

Status: FUTURE_LIVE_GATED

Phase: V11_LIVE_PERSONAL_GOVERNANCE

Description: Mode futur d'approbation humaine obligatoire avant toute activation live.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `future_personal_live_trading`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.
- Future live activation requires kill switch, reconciliation and governance readiness.

## live_small_capital_guard

Title: Live Small Capital Guard

Status: FUTURE_LIVE_GATED

Phase: V11_LIVE_PERSONAL_GOVERNANCE

Description: Garde-fou futur de petit capital avant tout pilote live personnel.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `future_personal_live_trading`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.
- Future live activation requires kill switch, reconciliation and governance readiness.

## live_reconciliation

Title: Live Reconciliation

Status: FUTURE_LIVE_GATED

Phase: V11_LIVE_PERSONAL_GOVERNANCE

Description: Rapprochement futur specifique au live personnel, soumis a gate de gouvernance.

Risk level: VERY_HIGH

Not yet implemented: true

Dependencies:
- `reconciliation_engine`
- `future_personal_live_trading`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.
- Connectivity and secrets review required before any external access is considered.
- Future live activation requires kill switch, reconciliation and governance readiness.

## final_product_reporting

Title: Reporting / Client Reports

Status: PLANNED_LATER

Phase: V8_UI_DASHBOARD

Description: Reporting produit futur et restitution finale, sans diffusion active au Lot 21.

Risk level: MEDIUM

Not yet implemented: true

Dependencies:
- `graphical_interface`
- `research_os`

Activation gate:
- Dedicated implementation lot approved by project governance.
- No-trading invariants preserved through implementation and validation.
- Validation script and acceptance report added before activation.
- Human review sign-off recorded before activation.
- Capability remains planning-only until its dedicated lot is validated.

