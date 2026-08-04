# V6 — Backtesting / Expected Value / TCA

Identifiant : `V6_BACKTEST_EV_TCA`  
Plage canonique : **Lots 60 à 71**  
Composant/domain owner : `BacktestDomain`  
Mode maximal autorisé : `BACKTEST_ONLY`

## Finalité de la version

Faire évoluer le système de **V5 promotion gate** vers **EV net de coûts et robustesse OOS prouvées**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- V5 promotion gate.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/backtesting`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 60 — Outcome Labeling & Event Definition

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Outcome Labeling & Event Definition » dans Backtesting / Expected Value / TCA, produire OutcomeLabelingEventDefinitionStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- OutcomeLabelingEventDefinitionStateV1
- OutcomeLabelingEventDefinitionAuditV1
- OutcomeEventV1
- OutcomeLabelV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 60, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Outcome Labeling & Event Definition » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir t0, horizon, barriers/targets configurables, censoring et observation window.
6. Calculer labels uniquement dans le moteur offline après séparation des données.
7. Tracer label_available_at et interdire son entrée dans les features à t0.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/outcome_labeling_and_event_definition.py
- src/crypto_quant_bot/backtesting/outcome_labeling_and_event_definition_models.py
- scripts/run_lot60_outcome_labeling_and_event_definition.py
- scripts/validate_lot60.py
- tests/test_lot60_outcome_labeling_and_event_definition.py
- data/audit/outcome_labeling_and_event_definition_lot60.json
- reports/lot_60_outcome_labeling_and_event_definition_report.md
- docs/LOT_60_OUTCOME_LABELING_AND_EVENT_DEFINITION.md
- docs/ACCEPTANCE_CRITERIA_LOT_60.md

### Observabilité minimale

- lot_60_records_processed_total
- lot_60_validation_failures_total
- lot_60_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Leakage test label_available_at > decision_time.
- Événements chevauchants traités selon policy.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 61 — Strategy Replay / Backtest Core

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Strategy Replay / Backtest Core » dans Backtesting / Expected Value / TCA, produire StrategyReplayBacktestCoreStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- StrategyReplayBacktestCoreStateV1
- StrategyReplayBacktestCoreAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- BacktestRunV1
- SimulatedExecutionLedgerV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 61, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Strategy Replay / Backtest Core » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Utiliser moteur event-driven et horloge simulée ; aucune lecture après simulated_now.
10. Rejouer data→features→scenario→signal→risk→simulated fill avec mêmes contrats que runtimes ultérieurs.
11. Versionner seed, dataset, config, code et models.
12. Séparer gross performance, costs, cashflows et rejected/no-trade events.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Checksum différent → NON_DETERMINISTIC_FAIL.
- Lot antérieur non PASS → closure refusée.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/strategy_replay_backtest_core.py
- src/crypto_quant_bot/backtesting/strategy_replay_backtest_core_models.py
- scripts/run_lot61_strategy_replay_backtest_core.py
- scripts/validate_lot61.py
- tests/test_lot61_strategy_replay_backtest_core.py
- data/audit/strategy_replay_backtest_core_lot61.json
- reports/lot_61_strategy_replay_backtest_core_report.md
- docs/LOT_61_STRATEGY_REPLAY_BACKTEST_CORE.md
- docs/ACCEPTANCE_CRITERIA_LOT_61.md

### Observabilité minimale

- lot_61_records_processed_total
- lot_61_validation_failures_total
- lot_61_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Same seed/config → checksum identique.
- Future access monkeypatch fait échouer le run.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 62 — Fees, Funding & Spread Cost Model

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Fees, Funding & Spread Cost Model » dans Backtesting / Expected Value / TCA, produire FeesFundingSpreadCostModelStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- BookFeatureStateV1 produit par V4
- DerivativesContextStateV1 produit par V4

### Contrats de sortie

- FeesFundingSpreadCostModelStateV1
- FeesFundingSpreadCostModelAuditV1
- TransactionCostStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 62, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Fees, Funding & Spread Cost Model » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Valider IDs, checksums, fraîcheur et compatibilité des états V4 consommés sans recalculer leur microstructure.
6. Modéliser maker/taker fee, fee tier, spread crossing, funding et settlement cashflows.
7. Aligner publication/effective_time du funding et gérer les révisions.
8. Appliquer devise de frais et conversion FX versionnée.
9. Refuser coût nul par défaut lorsque donnée absente ; utiliser un fallback conservateur explicite.
10. Publier chaque composante de coût, sa provenance, son incertitude et le coût total réconcilié.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/fees_funding_and_spread_cost_model.py
- src/crypto_quant_bot/backtesting/fees_funding_and_spread_cost_model_models.py
- scripts/run_lot62_fees_funding_and_spread_cost_model.py
- scripts/validate_lot62.py
- tests/test_lot62_fees_funding_and_spread_cost_model.py
- data/audit/fees_funding_and_spread_cost_model_lot62.json
- reports/lot_62_fees_funding_and_spread_cost_model_report.md
- docs/LOT_62_FEES_FUNDING_AND_SPREAD_COST_MODEL.md
- docs/ACCEPTANCE_CRITERIA_LOT_62.md

### Observabilité minimale

- lot_62_records_processed_total
- lot_62_validation_failures_total
- lot_62_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- États V4 absents, stale ou incompatibles bloquent le coût.
- Le Lot 62 ne produit aucun BookFeatureStateV1 ni DerivativesContextStateV1.
- Funding publication vs effective time.
- Maker/taker et devise de frais.
- Funding multi-périodes et signe long/short.
- Somme des composantes = coût total selon tolérance versionnée.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 63 — Slippage & Market Impact Simulator

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Slippage & Market Impact Simulator » dans Backtesting / Expected Value / TCA, produire SlippageMarketImpactSimulatorStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SlippageMarketImpactSimulatorStateV1
- SlippageMarketImpactSimulatorAuditV1
- SlippageImpactEstimateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 63, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Slippage & Market Impact Simulator » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Estimer slippage depuis spread, depth, participation, volatility et latency.
6. Séparer temporary impact, permanent proxy et adverse movement.
7. Calibrer par buckets instrument/régime/taille ; publier intervalle et fallback.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/slippage_and_market_impact_simulator.py
- src/crypto_quant_bot/backtesting/slippage_and_market_impact_simulator_models.py
- scripts/run_lot63_slippage_and_market_impact_simulator.py
- scripts/validate_lot63.py
- tests/test_lot63_slippage_and_market_impact_simulator.py
- data/audit/slippage_and_market_impact_simulator_lot63.json
- reports/lot_63_slippage_and_market_impact_simulator_report.md
- docs/LOT_63_SLIPPAGE_AND_MARKET_IMPACT_SIMULATOR.md
- docs/ACCEPTANCE_CRITERIA_LOT_63.md

### Observabilité minimale

- lot_63_records_processed_total
- lot_63_validation_failures_total
- lot_63_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Slippage monotone avec taille.
- Book insuffisant → no-fill/partial-fill, pas prix inventé.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 64 — Fill Probability, Queue Proxy & Capacity

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Fill Probability, Queue Proxy & Capacity » dans Backtesting / Expected Value / TCA, produire FillProbabilityQueueProxyCapacityStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- FillProbabilityQueueProxyCapacityStateV1
- FillProbabilityQueueProxyCapacityAuditV1
- FillProbabilityStateV1
- CapacityEstimateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 64, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Fill Probability, Queue Proxy & Capacity » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Estimer queue_ahead à partir de book observé et hypothèses documentées.
6. Simuler cancellations, trades at price, partial fills et expiry.
7. Calculer capacité maximale sous contraintes participation/slippage/impact.
8. Marquer proxy lorsque L3 indisponible.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/fill_probability_queue_proxy_and_capacity.py
- src/crypto_quant_bot/backtesting/fill_probability_queue_proxy_and_capacity_models.py
- scripts/run_lot64_fill_probability_queue_proxy_and_capacity.py
- scripts/validate_lot64.py
- tests/test_lot64_fill_probability_queue_proxy_and_capacity.py
- data/audit/fill_probability_queue_proxy_and_capacity_lot64.json
- reports/lot_64_fill_probability_queue_proxy_and_capacity_report.md
- docs/LOT_64_FILL_PROBABILITY_QUEUE_PROXY_AND_CAPACITY.md
- docs/ACCEPTANCE_CRITERIA_LOT_64.md

### Observabilité minimale

- lot_64_records_processed_total
- lot_64_validation_failures_total
- lot_64_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Aucun fill sans volume suffisant.
- Capacité diminue lorsque spread/volatility augmentent.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 65 — Expected Value Net of Costs

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Expected Value Net of Costs » dans Backtesting / Expected Value / TCA, produire ExpectedValueNetOfCostsStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ExpectedValueNetOfCostsStateV1
- ExpectedValueNetOfCostsAuditV1
- ExpectedValueStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 65, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Expected Value Net of Costs » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Calculer distribution de gross return puis soustraire chaque composant de coût.
6. Publier mean, median, quantiles, confidence interval, downside EV et stressed EV.
7. Segmenter par régime, horizon et taille.
8. EV positive seule ne crée ni signal ni promotion.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/expected_value_net_of_costs.py
- src/crypto_quant_bot/backtesting/expected_value_net_of_costs_models.py
- scripts/run_lot65_expected_value_net_of_costs.py
- scripts/validate_lot65.py
- tests/test_lot65_expected_value_net_of_costs.py
- data/audit/expected_value_net_of_costs_lot65.json
- reports/lot_65_expected_value_net_of_costs_report.md
- docs/LOT_65_EXPECTED_VALUE_NET_OF_COSTS.md
- docs/ACCEPTANCE_CRITERIA_LOT_65.md

### Observabilité minimale

- lot_65_records_processed_total
- lot_65_validation_failures_total
- lot_65_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Identité EV_net = EV_gross - coûts.
- Stress costs peut faire basculer le gate.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 66 — Walk-Forward Validation

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Walk-Forward Validation » dans Backtesting / Expected Value / TCA, produire WalkForwardValidationStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- WalkForwardValidationStateV1
- WalkForwardValidationAuditV1
- WalkForwardPlanV1
- WalkForwardResultV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 66, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Walk-Forward Validation » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir fenêtres train/validation/test chronologiques et cadence de refit.
6. Geler paramètres avant chaque test window.
7. Agrégater résultats sans réutiliser la test window.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/walk_forward_validation.py
- src/crypto_quant_bot/backtesting/walk_forward_validation_models.py
- scripts/run_lot66_walk_forward_validation.py
- scripts/validate_lot66.py
- tests/test_lot66_walk_forward_validation.py
- data/audit/walk_forward_validation_lot66.json
- reports/lot_66_walk_forward_validation_report.md
- docs/LOT_66_WALK_FORWARD_VALIDATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_66.md

### Observabilité minimale

- lot_66_records_processed_total
- lot_66_validation_failures_total
- lot_66_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Aucun overlap temporel.
- Paramètre modifié après ouverture test détecté.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 67 — Out-of-Sample, Purged CV & Embargo

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Out-of-Sample, Purged CV & Embargo » dans Backtesting / Expected Value / TCA, produire OutOfSamplePurgedCVEmbargoStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- OutOfSamplePurgedCVEmbargoStateV1
- OutOfSamplePurgedCVEmbargoAuditV1
- OOSValidationResultV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 67, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Out-of-Sample, Purged CV & Embargo » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Purgez observations dont labels/horizons chevauchent le fold test.
6. Appliquer embargo temporel configurable.
7. Conserver splits exacts et justification de chaque exclusion.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/out_of_sample_purged_cv_and_embargo.py
- src/crypto_quant_bot/backtesting/out_of_sample_purged_cv_and_embargo_models.py
- scripts/run_lot67_out_of_sample_purged_cv_and_embargo.py
- scripts/validate_lot67.py
- tests/test_lot67_out_of_sample_purged_cv_and_embargo.py
- data/audit/out_of_sample_purged_cv_and_embargo_lot67.json
- reports/lot_67_out_of_sample_purged_cv_and_embargo_report.md
- docs/LOT_67_OUT_OF_SAMPLE_PURGED_CV_AND_EMBARGO.md
- docs/ACCEPTANCE_CRITERIA_LOT_67.md

### Observabilité minimale

- lot_67_records_processed_total
- lot_67_validation_failures_total
- lot_67_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Synthetic overlap supprimé.
- Embargo boundary test.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 68 — Placebo, Randomization & Multiple-Testing Control

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Placebo, Randomization & Multiple-Testing Control » dans Backtesting / Expected Value / TCA, produire PlaceboRandomizationMultipleTestingControlStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- PlaceboRandomizationMultipleTestingControlStateV1
- PlaceboRandomizationMultipleTestingControlAuditV1
- PlaceboTestResultV1
- MultipleTestingReportV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 68, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Placebo, Randomization & Multiple-Testing Control » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Comparer à labels/permutations/signaux aléatoires compatibles avec la dépendance temporelle.
6. Enregistrer nombre total d’hypothèses testées et correction choisie.
7. Refuser promotion si performance n’excède pas baselines/placebos de façon robuste.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/placebo_randomization_and_multiple_testing_control.py
- src/crypto_quant_bot/backtesting/placebo_randomization_and_multiple_testing_control_models.py
- scripts/run_lot68_placebo_randomization_and_multiple_testing_control.py
- scripts/validate_lot68.py
- tests/test_lot68_placebo_randomization_and_multiple_testing_control.py
- data/audit/placebo_randomization_and_multiple_testing_control_lot68.json
- reports/lot_68_placebo_randomization_and_multiple_testing_control_report.md
- docs/LOT_68_PLACEBO_RANDOMIZATION_AND_MULTIPLE_TESTING_CONTROL.md
- docs/ACCEPTANCE_CRITERIA_LOT_68.md

### Observabilité minimale

- lot_68_records_processed_total
- lot_68_validation_failures_total
- lot_68_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Random baseline reproduite par seed.
- Correction multiple-testing appliquée au bon univers.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 69 — Monte Carlo, Bootstrap & Parameter Sensitivity

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Monte Carlo, Bootstrap & Parameter Sensitivity » dans Backtesting / Expected Value / TCA, produire MonteCarloBootstrapParameterSensitivityStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MonteCarloBootstrapParameterSensitivityStateV1
- MonteCarloBootstrapParameterSensitivityAuditV1
- LiquidityBehaviorEventV1
- RobustnessSimulationResultV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 69, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Monte Carlo, Bootstrap & Parameter Sensitivity » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Détecter breach de zone, excursion, volume/flow associé puis reclaim/acceptance dans fenêtre définie.
6. Classer SWEEP, BREAKOUT_ACCEPTED, FAKEOUT, LONG_TRAP, SHORT_TRAP ou FAILED_AUCTION.
7. Exiger séquence temporelle complète et publier evidence/invalidating_evidence.
8. Ne pas utiliser de barre future au-delà du temps de décision.
9. Bootstrap par blocs pour préserver dépendance temporelle.
10. Randomiser ordre des trades/cost shocks selon scénario.
11. Balayer paramètres autour du point choisi et détecter cliffs.
12. Publier risk-of-ruin et drawdown distribution.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/monte_carlo_bootstrap_and_parameter_sensitivity.py
- src/crypto_quant_bot/backtesting/monte_carlo_bootstrap_and_parameter_sensitivity_models.py
- scripts/run_lot69_monte_carlo_bootstrap_and_parameter_sensitivity.py
- scripts/validate_lot69.py
- tests/test_lot69_monte_carlo_bootstrap_and_parameter_sensitivity.py
- data/audit/monte_carlo_bootstrap_and_parameter_sensitivity_lot69.json
- reports/lot_69_monte_carlo_bootstrap_and_parameter_sensitivity_report.md
- docs/LOT_69_MONTE_CARLO_BOOTSTRAP_AND_PARAMETER_SENSITIVITY.md
- docs/ACCEPTANCE_CRITERIA_LOT_69.md

### Observabilité minimale

- lot_69_records_processed_total
- lot_69_validation_failures_total
- lot_69_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Breach sans reclaim ≠ fakeout.
- Late reclaim après expiration ≠ trap actif.
- Seed reproductible.
- Paramètre fragile marqué non promotable.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 70 — Performance Attribution & Regime Split

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Performance Attribution & Regime Split » dans Backtesting / Expected Value / TCA, produire PerformanceAttributionRegimeSplitStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- PerformanceAttributionRegimeSplitStateV1
- PerformanceAttributionRegimeSplitAuditV1
- PerformanceAttributionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 70, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Performance Attribution & Regime Split » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Attribuer PnL/EV à alpha, scénario, régime, instrument, période et composant de coût.
6. Conserver interaction et unexplained residual.
7. Éviter l’attribution causale lorsque seule corrélation observée.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/backtesting/performance_attribution_and_regime_split.py
- src/crypto_quant_bot/backtesting/performance_attribution_and_regime_split_models.py
- scripts/run_lot70_performance_attribution_and_regime_split.py
- scripts/validate_lot70.py
- tests/test_lot70_performance_attribution_and_regime_split.py
- data/audit/performance_attribution_and_regime_split_lot70.json
- reports/lot_70_performance_attribution_and_regime_split_report.md
- docs/LOT_70_PERFORMANCE_ATTRIBUTION_AND_REGIME_SPLIT.md
- docs/ACCEPTANCE_CRITERIA_LOT_70.md

### Observabilité minimale

- lot_70_records_processed_total
- lot_70_validation_failures_total
- lot_70_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Somme attributions + residual = total.
- Petits échantillons marqués insufficient.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 71 — Backtest Promotion Gate & V6 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `BACKTEST_ONLY`  
**Composant propriétaire :** `BacktestDomain`  
**Frontière de code :** `src/crypto_quant_bot/backtesting`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Backtest Promotion Gate & V6 Closure » dans Backtesting / Expected Value / TCA, produire BacktestPromotionGateV6ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- BacktestPromotionGateV6ClosureStateV1
- BacktestPromotionGateV6ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- PromotionDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 71, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Backtest Promotion Gate & V6 Closure » dans le composant BacktestDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Assembler preuves requises, seuils versionnés, exceptions et sign-offs.
10. Évaluer chaque critère PASS/FAIL/NOT_APPLICABLE avec justification.
11. Toute donnée manquante → FAIL ; aucun override silencieux.
12. Enregistrer approver, timestamp, expiry et scope exact de la promotion.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Checksum différent → NON_DETERMINISTIC_FAIL.
- Lot antérieur non PASS → closure refusée.

### Fichiers et artefacts d’implémentation attendus

- scripts/validate_all_until_lot71.py
- scripts/run_required_chain_until_lot71.sh
- scripts/diagnose_exact_chain_until_lot71.py
- tests/test_lot71_closure_contract.py
- data/audit/closure_manifest_lot71.json
- reports/lot_71_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_71.md
- src/crypto_quant_bot/backtesting/backtest_promotion_gate_and_v6_closure.py
- src/crypto_quant_bot/backtesting/backtest_promotion_gate_and_v6_closure_models.py
- scripts/run_lot71_backtest_promotion_gate_and_v6_closure.py
- scripts/validate_lot71.py
- tests/test_lot71_backtest_promotion_gate_and_v6_closure.py
- data/audit/backtest_promotion_gate_and_v6_closure_lot71.json
- reports/lot_71_backtest_promotion_gate_and_v6_closure_report.md
- docs/LOT_71_BACKTEST_PROMOTION_GATE_AND_V6_CLOSURE.md

### Observabilité minimale

- lot_71_records_processed_total
- lot_71_validation_failures_total
- lot_71_processing_latency_ms

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Preuve manquante bloque promotion.
- Promotion expirée ne peut être consommée.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 60–71 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
