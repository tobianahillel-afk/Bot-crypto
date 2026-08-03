# V2 Product Roadmap

Roadmap officielle V2+ du meme projet Crypto Quant Bot V3.1-Ops.

Le Lot 21-bis existe parce que les premieres chaines V2 rejouaient encore la cloture V1 et pouvaient ecraser l'archive finale validee au Lot 20-bis.

La V1 defensive/audit est fermee et reference uniquement une archive figee.

source_v1_archive_path = dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz

source_v1_archive_frozen = true

source_v1_archive_sha256 = ef5b5998cd5f75b6d97acc4afc10aeaf4833b565d2c11e9f3278bace06c78667

source_v1_archive_size_bytes = 366985

La V2 est ouverte uniquement comme cadrage fonctionnel et verrouillage de portefeuille de fonctionnalites.

Le Lot 22 pourra demarrer la Market Analysis Foundation en mode local/offline sans modifier l'archive V1 figee et sans activer le trading.

Le Lot 23 pourra ajouter un premier pack d'indicateurs techniques strictement descriptifs, toujours sans execution et sans connectivite externe.

Aucune phase ci-dessous n'est active au Lot 21. Chaque phase reste forecast-only jusqu'a validation d'un lot dedie.

## V2_MARKET_ANALYSIS — Market Analysis Foundation

Objective: Structurer l'analyse de marche multi-timeframe, les indicateurs et les zones de confluence.

Estimated lot span: Lot 22 to Lot 30

Status: PLANNING_ONLY_LOCKED

Activation constraints:
- Lot 21 scope lock remains accepted.
- No-trading invariants remain enforced before any implementation.
- A dedicated implementation lot is required before activation.
- Human review sign-off is mandatory before activation.

Capabilities:
- `market_analysis_engine`
- `multi_timeframe_engine`
- `technical_indicators_pack`
- `volume_profile_engine`
- `confluence_zones_engine`

## V3_MICROSTRUCTURE_SCENARIOS — Offline Microstructure and Scenario Research

Objective: Etendre le scope vers la microstructure offline et la recherche de scenarios explicables.

Estimated lot span: Lot 31 to Lot 55

Status: PLANNING_ONLY_LOCKED

Activation constraints:
- Lot 21 scope lock remains accepted.
- No-trading invariants remain enforced before any implementation.
- A dedicated implementation lot is required before activation.
- Human review sign-off is mandatory before activation.

Capabilities:
- `order_book_l2_offline`
- `order_flow_offline`
- `strategic_microstructure`
- `scenario_engine`
- `scenario_explanation_engine`

## V4_EXPECTED_VALUE_BACKTESTING — Expected Value and Advanced Backtesting

Objective: Documenter les briques d'Expected Value, walk-forward et anti-overfitting.

Estimated lot span: Lot 56 to Lot 66

Status: PLANNING_ONLY_LOCKED

Activation constraints:
- Lot 21 scope lock remains accepted.
- No-trading invariants remain enforced before any implementation.
- A dedicated implementation lot is required before activation.
- Human review sign-off is mandatory before activation.

Capabilities:
- `expected_value_engine`
- `advanced_backtesting`
- `walk_forward_validation`
- `anti_overfitting_audit`

## V5_PAPER_TRADING_DEMO — Paper Trading and Demo Portfolio

Objective: Encadrer un futur mode demo uniquement, sans activation au Lot 21.

Estimated lot span: Lot 67 to Lot 76

Status: PLANNING_ONLY_LOCKED

Activation constraints:
- Lot 21 scope lock remains accepted.
- No-trading invariants remain enforced before any implementation.
- A dedicated implementation lot is required before activation.
- Human review sign-off is mandatory before activation.

Capabilities:
- `paper_trading_demo_portfolio`
- `simulated_orders_and_fills`

## V6_RESEARCH_OS — Research OS

Objective: Formaliser l'OS de recherche, l'experiment registry et le suivi d'hypotheses.

Estimated lot span: Lot 77 to Lot 87

Status: PLANNING_ONLY_LOCKED

Activation constraints:
- Lot 21 scope lock remains accepted.
- No-trading invariants remain enforced before any implementation.
- A dedicated implementation lot is required before activation.
- Human review sign-off is mandatory before activation.

Capabilities:
- `research_os`
- `experiment_registry`
- `hypothesis_tracking`
- `ablation_placebo_oos_testing`

## V7_AI_NEWS_EVENT_ENGINE — AI / News / Event Engine

Objective: Documenter les blocs IA, news, evenements et audit des sources.

Estimated lot span: Lot 88 to Lot 101

Status: PLANNING_ONLY_LOCKED

Activation constraints:
- Lot 21 scope lock remains accepted.
- No-trading invariants remain enforced before any implementation.
- A dedicated implementation lot is required before activation.
- Human review sign-off is mandatory before activation.
- External connectivity remains disabled until a dedicated gate review passes.

Capabilities:
- `ai_news_event_engine`
- `economic_calendar`
- `news_ingestion_read_only`
- `sentiment_narrative_engine`
- `llm_explanation_layer`
- `ai_hallucination_source_audit`

## V8_UI_DASHBOARD — Graphical Interface and Dashboards

Objective: Reserver l'interface graphique, les dashboards et la restitution produit a des lots dedies.

Estimated lot span: Lot 102 to Lot 114

Status: PLANNING_ONLY_LOCKED

Activation constraints:
- Lot 21 scope lock remains accepted.
- No-trading invariants remain enforced before any implementation.
- A dedicated implementation lot is required before activation.
- Human review sign-off is mandatory before activation.
- No server, no websocket and no active interface may be started before a dedicated UI lot.

Capabilities:
- `graphical_interface`
- `market_dashboard`
- `scenario_dashboard`
- `decision_logs_dashboard`
- `paper_trading_dashboard`
- `portfolio_dashboard`
- `audit_replay_ui`
- `final_product_reporting`

## V9_ACCOUNT_READ_ONLY — Account Analysis and Read-Only APIs

Objective: Documenter l'analyse de compte et les futures integrations read-only sans activation.

Estimated lot span: Lot 115 to Lot 124

Status: PLANNING_ONLY_LOCKED

Activation constraints:
- Lot 21 scope lock remains accepted.
- No-trading invariants remain enforced before any implementation.
- A dedicated implementation lot is required before activation.
- Human review sign-off is mandatory before activation.
- External connectivity remains disabled until a dedicated gate review passes.

Capabilities:
- `account_analysis_read_only`
- `exchange_api_read_only`
- `balances_positions_read_only`
- `reconciliation_engine`

## V10_SANDBOX_DEMO_TRADING — Sandbox and Demo Trading

Objective: Reserver les futures boucles demo/sandbox a un environnement entierement garde.

Estimated lot span: Lot 125 to Lot 135

Status: PLANNING_ONLY_LOCKED

Activation constraints:
- Lot 21 scope lock remains accepted.
- No-trading invariants remain enforced before any implementation.
- A dedicated implementation lot is required before activation.
- Human review sign-off is mandatory before activation.
- External connectivity remains disabled until a dedicated gate review passes.

Capabilities:
- `sandbox_demo_trading`
- `demo_order_lifecycle`
- `demo_risk_controls`

## V11_LIVE_PERSONAL_GOVERNANCE — Future Personal Live Trading Governance

Objective: Verrouiller les controles de gouvernance, reconciliation et incident response avant tout live futur.

Estimated lot span: Lot 136 to Lot 147

Status: PLANNING_ONLY_LOCKED

Activation constraints:
- Lot 21 scope lock remains accepted.
- No-trading invariants remain enforced before any implementation.
- A dedicated implementation lot is required before activation.
- Human review sign-off is mandatory before activation.
- External connectivity remains disabled until a dedicated gate review passes.
- Any live-oriented work remains FUTURE_LIVE_GATED until governance, reconciliation and kill switch controls are validated.

Capabilities:
- `incident_response`
- `kill_switch_governance`
- `secrets_policy`
- `future_personal_live_trading`
- `live_human_approval_mode`
- `live_small_capital_guard`
- `live_reconciliation`

