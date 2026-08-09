# Crypto Quant Bot V3.6-Ops

Plateforme quantitative crypto défensive, déterministe, extensible et auditable.

## État courant

| Élément | État |
|---|---|
| Dernier lot implémenté et validé | **Lot 36 — Freshness, Gap, Outage Audit & V3 Closure** |
| Version | **0.36.0** |
| Baseline qualité | **P0 institutionnel fusionné** |
| Prochain lot planifié | **Lot 37 — V4 Microstructure scope/offline contracts**, `PLANNED_LOCKED` |
| Runtime maximal | `DATA_GOVERNANCE_ONLY` |
| Trading | **désactivé** |
| Connectivité exchange | **désactivée** |

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
execution_allowed = false
approved_size = 0
live_execution = DISABLED
leverage = FORBIDDEN
withdrawals = FORBIDDEN
```

Le Lot 29 prouve que les artefacts certifiés des Lots 21 à 28 forment une chaîne ordonnée,
déterministe et non exécutable. Le Lot 30 clôture V2 en revérifiant les huit artefacts,
les preuves Lot 29, deux replays identiques du validateur et cinq contrôles négatifs
fail-closed.

Le Lot 31 ouvre V3 avec un registre de sources strictement **metadata-only**. Il déclare une
source de vérité et deux sources de secours, versionne les responsabilités, licences,
cadences, révisions et capacités, mais n'effectue aucune requête réseau. Toutes les sources
restent `auth_mode=NONE`, `enabled=false` et `connection_status=DISABLED`.

Le Lot 32 ajoute une identité canonique d’instrument et des alias de venue strictement
offline. La référence certifiée est `BTC/EUR:SPOT`, reliée aux alias déclaratifs Bitstamp,
Coinbase et Kraken. Les contraintes utilisent des chaînes décimales exactes, les conversions
canonique ↔ venue sont bidirectionnelles et les champs dérivés non applicables restent
explicitement nuls. Aucun connecteur ou événement de marché n’est activé.

Le Lot 33 normalise les timestamps, horloges et timezones de façon déterministe. Les valeurs
canoniques sont en UTC, les offsets sont vérifiés contre les timezones IANA, les durées
critiques utilisent des microsecondes entières et l'ordre canonique est
`(event_time_utc, sequence_id, revision_id)`. La fixture certifiée reste `HEALTHY` et aucune
connectivité ou publication d'événement de marché n'est autorisée.

Le Lot 34 ajoute le **Market Data Quality Engine** offline : détection des intervalles
manquants, doublons, out-of-order, stale data, OHLC invalides, volumes négatifs, spreads
impossibles et schema drift. Il calcule coverage/freshness/completeness/consistency en points
de base, applique une quarantaine non destructive et un veto fail-closed. Les preuves
certifiées sont 98.80% lignes, 97.30% branches et 84.00% mutation. Le raw reste immuable,
le réseau reste désactivé et aucune capacité de trading n'est ouverte.

Le Lot 35 ajoute la **réconciliation Candle / Trade / Book** offline : deltas exacts en `Decimal`, écarts temporels en microsecondes entières, source de vérité explicite, classification `MATCH/TOLERATED_DIFF/MINOR_DIVERGENCE/CRITICAL_DIVERGENCE`, détection des orphelins et doublons, ordre canonique déterministe et veto fail-closed. La fixture certifiée contient 3 rapports (2 `MATCH`, 1 `TOLERATED_DIFF`) et conserve `ALLOW_ANALYSIS`; aucune connectivité, mutation raw ou capacité de trading/exécution n’est ouverte. Les preuves finales sont 96.43% lignes, 93.75% branches et 83.73% mutation.

Le Lot 36 clôture **V3 Market Data Governance** après audit post-merge indépendant. Il audite freshness/gaps/outages, rejoue exactement les Lots 34 et 35, vérifie la chaîne Lots 31–36 et conserve un manifest d’implémentation historiquement candidat. La certification post-merge porte la release à `0.36.0`, avec 100.00% lignes, 100.00% branches, 83.48% mutation et replay déterministe. Lot 37 reste verrouillé jusqu’à un gate V4 distinct.

## Vision temporelle

Le système cible un flux de marché canonique unique et continu, plusieurs représentations
temporelles et plusieurs horizons prédictifs. Il ne crée pas un robot indépendant par
timeframe.

Six notions restent séparées :

```text
data_resolution
feature_lookback
forecast_horizon
decision_clock
signal_ttl
holding_horizon
```

Le profil initial du Lot 26 est :

```text
flux continu amont
→ états confirmés de barres fermées
→ timebar-5m comme contexte local
→ timebar-15m comme contexte supérieur
→ ASOF_BACKWARD avec available_at <= decision_time
→ alignement descriptif et auditable
```

Le 5m/15m est une première configuration, pas une limitation du futur système. Le registre
temporel prévoit une interface extensible, tandis que les échelles supplémentaires restent
désactivées dans le Lot 26.

Le 15m n'oppose aucun veto automatique au 5m. Une divergence peut représenter un rebond
local dans une structure supérieure différente. Le vote majoritaire naïf entre timeframes
est interdit.

## Flux continu et données confirmées

Une barre ouverte peut être observée comme état provisoire, mais elle ne peut pas être
consommée comme état confirmé. Les Lots 31 à 36 constituent désormais la chaîne V3 Market Data Governance fermée et auditée : registre de sources, instruments canoniques, temps canonique, qualité, réconciliation et audit freshness/gap/outage. Les features de carnet, trades, liquidations et order flow appartiennent à V4 et restent verrouillées à partir du Lot 37.

## Prévision et modèles stochastiques

La roadmap prévoit des prévisions par horizons distincts — initialement 30s, 5m, 15m et
1h — avec distributions, quantiles, volatilité, target/stop hit, MAE/MFE, temps avant
événement et incertitude.

Ces contrats sont `PLANNED_LOCKED_NOT_IMPLEMENTED`. Les Lots 26 à 36 ne produisent aucune
prediction, probability, expected return ou direction BUY/SELL.

Les futurs modèles stochastiques devront être sélectionnés par preuve, comparés à des
baselines et validés hors échantillon. La sophistication d'un modèle n'est pas une preuve
d'alpha.

## Carnet, participants et Game Theory

V4 — Lots 37–52 possède :

- carnet L2/L3, deltas, santé et séquences ;
- spread, profondeur, imbalance, murs et vides ;
- résilience, replenishment, absorption et liquidité cachée proxy ;
- aggressor classification, order flow, delta et CVD ;
- volume clusters, time-at-level, sweeps, fakeouts et traps ;
- OI, funding, basis et liquidations ;
- Game Theory et scénarios concurrents.

Les zones futures sont explicitement typées :

```text
STOP_LOSS_CLUSTER
TAKE_PROFIT_CLUSTER
BREAK_EVEN_CLUSTER
LIQUIDATION_CLUSTER
ENTRY_CONGESTION_ZONE
TRAPPED_POSITION_ZONE
FORCED_EXIT_ZONE
PASSIVE_DEFENSE_ZONE
```

Elles restent des inférences probabilistes, jamais des ordres privés prétendument observés.

## Décision, risque et exécution future

```text
forecast
→ scenario
→ signal
→ TradeIntent
→ PortfolioDecisionSnapshotV1
→ RiskDecision
→ RiskReservationV1
→ OrderIntent
→ OMS/EMS
→ fill/reconciliation
```

Chaque future décision augmentant le risque doit consommer un snapshot portefeuille
cohérent incluant positions, ordres ouverts, intents en attente, capital réservé et risque
déjà engagé. Le sizing final est le minimum de tous les caps de risque, capital, heat,
concentration, corrélation, drawdown et liquidité. Une réservation atomique empêche
plusieurs décisions simultanées d'utiliser le même budget.

Toute augmentation de position exige un nouvel intent, une nouvelle décision et une
nouvelle réservation. La moyenne à la baisse implicite est interdite ; un ajout dans la
même direction est bloqué lorsque le PnL de liquidation net de coûts est négatif ou nul.

Les futurs ordres protecteurs — stop-loss, take-profit, break-even, trailing, partial exits,
bracket et OCO — sont spécifiés mais non implémentés. Ils appartiennent à V5/V7/V8/V15
selon leurs responsabilités.

## Environnement canonique

```text
Python 3.11.9
timezone UTC
locale indépendante
seed/config/horloge injectées
```

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.lock
```

## Validation

```bash
python scripts/validate_lot30.py
python scripts/validate_lot31.py
python scripts/validate_lot31_no_connectivity.py
python scripts/validate_lot32.py
python scripts/validate_lot32_no_connectivity.py
python scripts/validate_lot33.py
python scripts/validate_lot33_no_connectivity.py
python scripts/validate_lot34.py
python scripts/validate_lot34_no_connectivity.py
python scripts/validate_lot34_post_merge.py
python scripts/validate_lot35.py
python scripts/validate_lot35_no_connectivity.py
python scripts/validate_lot35_post_merge.py
python scripts/validate_lot36.py
python scripts/validate_lot36_no_connectivity.py
python scripts/validate_lot36_post_merge.py
python scripts/validate_roadmap_documentation.py
python scripts/validate_architecture_boundaries.py
python scripts/check_no_silent_numeric_coercion.py
pytest -q
```

La CI ajoute Ruff, mypy, coverage lignes/branches, diff coverage, Bandit, `pip-audit`,
complexité, mutation testing et répétitions anti-flake.

## Sources de vérité

### Lot 26

- [Gate pré-Lot26](docs/PRE_LOT26_ENTRY_GATE.md)
- [Spécification Lot 26](docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md)
- [Critères d'acceptation](docs/ACCEPTANCE_CRITERIA_LOT_26.md)
- [Mathématiques](docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md)
- [ADR temporel](docs/adr/ADR_0001_TIME_SEMANTICS_AND_ASOF_JOIN.md)
- [Contrats temporels](docs/contracts/LOT26_TEMPORAL_CONTRACTS.md)

### Lot 28

- [Spécification](docs/LOT_28_EXPLANATION_CORE_AND_WHY_NOT_TRADE_LAYER.md)
- [Critères d’acceptation](docs/ACCEPTANCE_CRITERIA_LOT_28.md)
- [Worklog de validation](docs/LOT_28_IMPLEMENTATION_WORKLOG.md)
- [Rapport final](reports/lot_28_explanation_core_and_why_not_trade_layer_report.md)
- État certifié : `data/audit/explanation_core_and_why_not_trade_layer_lot28.json`
- Audit certifié : `data/audit/explanation_core_and_why_not_trade_layer_audit_lot28.json`

### Lot 29

- [Spécification](docs/LOT_29_V2_DETERMINISTIC_REPLAY_AND_AUDIT.md)
- [Critères d’acceptation](docs/ACCEPTANCE_CRITERIA_LOT_29.md)
- [Worklog certifié](docs/LOT_29_IMPLEMENTATION_WORKLOG.md)
- [Audit post-merge](docs/LOT_29_POST_MERGE_AUDIT.md)
- [Rapport final](reports/lot_29_v2_deterministic_replay_and_audit_report.md)
- État certifié : `data/audit/v2_deterministic_replay_and_audit_lot29.json`
- Audit certifié : `data/audit/v2_deterministic_replay_and_audit_audit_lot29.json`
- Manifest de clôture : `data/audit/v2_replay_closure_manifest_lot29.json`

### Lot 30

- [Spécification](docs/LOT_30_V2_MARKET_ANALYSIS_CLOSURE.md)
- [Critères d’acceptation](docs/ACCEPTANCE_CRITERIA_LOT_30.md)
- [Worklog certifié](docs/LOT_30_IMPLEMENTATION_WORKLOG.md)
- [Audit post-merge](docs/LOT_30_POST_MERGE_AUDIT.md)
- [Rapport final](reports/lot_30_v2_market_analysis_closure_report.md)
- État certifié : `data/audit/v2_market_analysis_closure_lot30.json`
- Audit certifié : `data/audit/v2_market_analysis_closure_audit_lot30.json`
- Manifest final V2 : `data/audit/closure_manifest_lot30.json`
- Lifecycle historique : `data/audit/roadmap_lifecycle_overlay_lot30.json`

### Lot 31

- [Gate d’entrée V3](docs/LOT_31_V3_ENTRY_GATE.md)
- [Spécification](docs/LOT_31_MARKET_DATA_GOVERNANCE_SCOPE_AND_SOURCE_REGISTRY.md)
- [Critères d’acceptation](docs/ACCEPTANCE_CRITERIA_LOT_31.md)
- [Worklog certifié](docs/LOT_31_IMPLEMENTATION_WORKLOG.md)
- [Audit post-merge](docs/LOT_31_POST_MERGE_AUDIT.md)
- [Rapport final](reports/lot_31_market_data_governance_scope_and_source_registry_report.md)
- État certifié : `data/audit/market_data_governance_scope_and_source_registry_lot31.json`
- Audit certifié : `data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json`
- Registre de sources : `data/audit/source_registry_lot31.json`
- Lifecycle historique : `data/audit/roadmap_lifecycle_overlay_lot31.json`

### Lot 32 — Instrument, Symbol & Contract Normalization

- [Gate d’entrée](docs/LOT_32_V3_ENTRY_GATE.md)
- [Spécification](docs/LOT_32_INSTRUMENT_SYMBOL_AND_CONTRACT_NORMALIZATION.md)
- [Critères d’acceptation](docs/ACCEPTANCE_CRITERIA_LOT_32.md)
- [Worklog certifié](docs/LOT_32_IMPLEMENTATION_WORKLOG.md)
- [Audit post-merge](docs/LOT_32_POST_MERGE_AUDIT.md)
- [Rapport final](reports/lot_32_instrument_symbol_and_contract_normalization_report.md)
- État certifié : `data/audit/instrument_symbol_and_contract_normalization_lot32.json`
- Audit certifié : `data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json`
- Registre d’instruments : `data/audit/instrument_registry_lot32.json`
- Lifecycle historique : `data/audit/roadmap_lifecycle_overlay_lot32.json`

### Lot 33

- [Gate d’entrée](docs/LOT_33_V3_ENTRY_GATE.md)
- [Spécification](docs/LOT_33_TIMESTAMP_CLOCK_AND_TIMEZONE_GOVERNANCE.md)
- [Critères d’acceptation](docs/ACCEPTANCE_CRITERIA_LOT_33.md)
- [Audit post-merge](docs/LOT_33_POST_MERGE_AUDIT.md)
- État certifié : `data/audit/timestamp_clock_and_timezone_governance_lot33.json`
- Audit certifié : `data/audit/timestamp_clock_and_timezone_governance_audit_lot33.json`
- Collection canonique : `data/audit/canonical_time_envelopes_lot33.json`
- Lifecycle historique : `data/audit/roadmap_lifecycle_overlay_lot33.json`

### Lot 34

- [Gate d’entrée](docs/LOT_34_V3_ENTRY_GATE.md)
- [Spécification](docs/LOT_34_MARKET_DATA_QUALITY_ENGINE.md)
- [Critères d’acceptation](docs/ACCEPTANCE_CRITERIA_LOT_34.md)
- [Audit post-merge](docs/LOT_34_POST_MERGE_AUDIT.md)
- [Rapport final](reports/lot_34_market_data_quality_engine_report.md)
- État certifié : `data/audit/market_data_quality_engine_lot34.json`
- Audit certifié : `data/audit/market_data_quality_engine_audit_lot34.json`
- États qualité : `data/audit/data_quality_states_lot34.json`
- Anomalies : `data/audit/data_anomalies_lot34.json`
- Veto qualité : `data/audit/data_quality_veto_lot34.json`
- Lifecycle courant : `data/audit/roadmap_lifecycle_overlay_lot34.json`

### Lot 35

- [Gate d’entrée](docs/LOT_35_V3_ENTRY_GATE.md)
- [Spécification](docs/LOT_35_CANDLE_TRADE_BOOK_RECONCILIATION.md)
- [Critères d’acceptation](docs/ACCEPTANCE_CRITERIA_LOT_35.md)
- [Audit post-merge](docs/LOT_35_POST_MERGE_AUDIT.md)
- [Rapport final](reports/lot_35_candle_trade_book_reconciliation_report.md)
- État certifié : `data/audit/candle_trade_book_reconciliation_lot35.json`
- Audit certifié : `data/audit/candle_trade_book_reconciliation_audit_lot35.json`
- Rapports de réconciliation : `data/audit/reconciliation_reports_lot35.json`
- Veto réconciliation : `data/audit/reconciliation_veto_lot35.json`
- Coverage : `reports/lot35/coverage_summary.json`
- Mutation : `reports/lot35/mutation_summary.json`
- Lifecycle historique : `data/audit/roadmap_lifecycle_overlay_lot35.json`

### Lot 36

- [Gate d’entrée](docs/LOT_36_V3_ENTRY_GATE.md)
- [Spécification](docs/LOT_36_FRESHNESS_GAP_OUTAGE_AUDIT_AND_V3_CLOSURE.md)
- [Critères d’acceptation](docs/ACCEPTANCE_CRITERIA_LOT_36.md)
- [Audit post-merge / fermeture V3](docs/LOT_36_POST_MERGE_AUDIT.md)
- [Matrice de validation](docs/LOT36_POST_MERGE_VALIDATION_MATRIX.md)
- [Rapport d’implémentation](reports/lot_36_freshness_gap_outage_audit_and_v3_closure_report.md)
- État certifié : `data/audit/freshness_gap_outage_audit_and_v3_closure_lot36.json`
- Audit certifié : `data/audit/freshness_gap_outage_audit_and_v3_closure_audit_lot36.json`
- Manifest historique : `data/audit/closure_manifest_lot36.json`
- Replay : `data/audit/replay_evidence_lot36.json`
- Coverage : `reports/lot36/coverage_summary.json`
- Mutation : `reports/lot36/mutation_summary.json`
- Lifecycle courant : `data/audit/roadmap_lifecycle_overlay_lot36.json`

### Architecture future verrouillée

- [Architecture multi-échelle et horloges](docs/TEMPORAL_MULTI_SCALE_AND_DECISION_CLOCK_ARCHITECTURE.md)
- [Standard stochastique et multi-horizon](docs/STOCHASTIC_CONTINUOUS_STATE_AND_MULTI_HORIZON_FORECASTING_STANDARD.md)
- [Participants et zones de sortie](docs/PARTICIPANT_BEHAVIOR_AND_LIQUIDITY_EXIT_ZONE_INFERENCE_STANDARD.md)
- [Ordres protecteurs](docs/PROTECTIVE_ORDERS_AND_EXIT_LIFECYCLE_STANDARD.md)
- [Risque portefeuille, sizing, réservations et sorties](docs/CANONICAL_PORTFOLIO_RISK_SIZING_AND_EXIT_STANDARD.md)
- [Addendum normatif V7/V9](docs/roadmap/V07_V09_PORTFOLIO_RISK_NORMATIVE_ADDENDUM.md)
- [Addendum de roadmap](docs/roadmap/MULTI_SCALE_STOCHASTIC_PREDICTION_AND_PARTICIPANT_INFERENCE_ADDENDUM.md)
- [Roadmap V1 → V21](docs/ROADMAP_V1_TO_V21.md)

## Contribution

Toute modification suit [CONTRIBUTING.md](CONTRIBUTING.md). Aucun lot ne commence sans
rapport `GO` sur le commit exact. Un contrat futur documenté ne devient pas une capability
implémentée.
