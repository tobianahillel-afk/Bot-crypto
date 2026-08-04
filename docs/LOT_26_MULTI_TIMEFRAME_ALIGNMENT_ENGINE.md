# Lot 26 — Multi-Timeframe Alignment Engine

Statut : `PLANNED_LOCKED`  
Version : V2 Market Analysis Offline  
Owner : `MarketAnalysisDomain`  
Runtime maximal : `LOCAL_OFFLINE_ANALYSIS_ONLY`  
Configuration mathématique : `config/math/multi_timeframe_alignment_v1.json`  
Registre des échelles : `config/temporal/temporal_scale_registry_v1.json`  
Politique d'horloge : `config/temporal/decision_clock_policy_v1.json`

## 1. Objectif falsifiable

Implémenter une interface générique de comparaison entre deux états confirmés appartenant à une relation temporelle ordonnée, puis activer pour la version v1 exactement :

```text
timebar-5m (contexte local) → timebar-15m (contexte supérieur)
```

Pour chaque nouvel état local 5m issu d'une barre fermée, le moteur sélectionne le dernier état supérieur 15m légalement disponible, compare six composantes de contexte et produit un état descriptif rejouable d'alignement, divergence et cohérence.

Le moteur est correct si les mêmes inputs, config, code, horloge et ordre canonique produisent les mêmes sorties/checksums, sans lire de barre ouverte ou future.

## 2. Intention d'architecture

Le profil 5m→15m est la première configuration, pas une limitation du futur robot. Le code du Lot 26 doit accepter une description de relation `local_scale_id/higher_scale_id` validée par registre, sans coder la logique métier sous la forme de fonctions dupliquées `compare_5m_15m`.

Une extension future pourra ajouter d'autres échelles ou arêtes après gate dédié, mais le Lot 26 v1 :

- n'active qu'une arête ;
- ne compare pas 1m, 1h, tick, volume bar ou event stream ;
- ne fusionne pas plusieurs arêtes ;
- interdit tout vote majoritaire naïf.

## 3. Périmètre inclus

- ingestion amont potentiellement continue ;
- états confirmés de barres fermées 5m/15m ;
- `ASOF_BACKWARD` ;
- validation du registre temporel ;
- compatibilité trend/range/momentum/volatility/regime/confluence ;
- couverture, agreement score, divergence, cohérence et incertitude descriptive ;
- reason codes, lineage et replay ;
- interface extensible d'arête temporelle ;
- séparation explicite entre résolution, horizon de prévision et horloge de décision.

## 4. Hors périmètre

- construction de `ContinuousMarketStateV1` ;
- consommation event-level du carnet ou des trades ;
- prévision de rendement ;
- modèle stochastique ;
- `MultiHorizonForecastV1` ;
- probability ou calibration ;
- alpha ou signal BUY/SELL ;
- sizing, ordre ou exécution ;
- veto automatique du 15m sur le 5m ;
- inférence des participants ;
- stop-loss, take-profit, break-even ou liquidation zones ;
- Game Theory ;
- protective orders, bracket ou OCO.

Ces capabilities sont enregistrées pour les versions propriétaires, mais restent `PLANNED_LOCKED_NOT_IMPLEMENTED`.

## 5. Dépendances

- Lots 22–25 validés ;
- artefacts 5m/15m du Lot 25 ;
- P0 institutionnel fusionné ;
- gate pré-Lot26 `GO` ;
- contrats temporels ;
- configuration mathématique versionnée ;
- `TemporalScaleRegistryV1` ;
- `DecisionClockPolicyV1`.

## 6. Contrats d'entrée

- `RunContextV1` ;
- relation temporelle enregistrée ;
- `TimeframeMarketContextStateV1` local 5m ;
- série de `TimeframeMarketContextStateV1` supérieure 15m ;
- `ClosedBarAvailabilityV1` pour chaque état ;
- `LineageEnvelopeV1`.

Chaque entrée déclare :

```text
data_resolution
feature_lookback si applicable
available_at
decision_time
```

Aucun `forecast_horizon`, `signal_ttl` ou `holding_horizon` n'est déduit du timeframe.

## 7. Contrat de sortie

`MultiTimeframeAlignmentStateV1` contient au minimum :

```text
alignment_id
local_scale_id
higher_scale_id
local_state_id
higher_state_id
decision_time
component_scores
weighted_coverage_ratio
overall_agreement_score
alignment_state
divergence_state
coherence_state
uncertainty_state
reason_codes
lineage_id
config_version
config_checksum
code_commit
```

Chaque état est accompagné d'un `DecisionEvidenceEnvelopeV1` fermé reliant inputs, checksums, règles, reason codes, incertitude et conséquence finale.

Le score peut être `null`. Une valeur absente n'est jamais transformée en zéro.

La sortie est conçue pour être consommable ultérieurement par V4/V5, mais elle n'est pas une prévision et ne porte aucun champ exécutable.

## 8. Séquence obligatoire

1. Valider runtime, schémas, registres, config et checksums.
2. Vérifier que la relation active est exactement `timebar-5m→timebar-15m` pour v1.
3. Valider UTC, durées de barres, ordre et disponibilité.
4. Rejeter états ouverts, futurs, stale, dupliqués ambigus ou incomplets.
5. Pour le 5m courant, faire `ASOF_BACKWARD` vers le 15m.
6. Normaliser les six enums sans inventer de valeur.
7. Calculer les compatibilités par formule/matrice normative.
8. Calculer couverture et score seulement si les minima sont atteints.
9. Classer alignement, divergence, cohérence et incertitude.
10. Ajouter reason codes, IDs, lineage et checksum.
11. Écrire atomiquement état et audit.
12. Rejouer et comparer run1/run2.
13. Vérifier l'absence de champs forecast/signal/order.
14. Conserver toutes les permissions d'exécution à `false`.

## 9. Mathématiques

Spécification normative : `docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md`.

Pour l'arête active :

```text
A_e = Σ(w_i a_i I_i) / Σ(w_i I_i)
```

avec :

```text
Σ(I_i) >= 4
Σ(w_i I_i) >= 0.70
```

`A_e` est un agreement score descriptif :

```text
agreement score != probability
agreement score != expected return
agreement score != signal
agreement score != trade permission
```

## 10. Machine d'état

```text
INPUT_VALIDATION
→ SCALE_RELATION_VALIDATION
→ TIME_ELIGIBILITY
→ ASOF_JOIN
→ COMPONENT_COMPATIBILITY
→ COVERAGE_GATE
→ CLASSIFICATION
→ AUDIT_PERSISTENCE
→ REPLAY_VALIDATION
→ COMPLETE
```

Transitions d'échec :

```text
* → BLOCKED_SCHEMA
* → BLOCKED_SCALE_RELATION
* → BLOCKED_TIME_ALIGNMENT
* → BLOCKED_STALE_DATA
* → UNKNOWN_INSUFFICIENT_COVERAGE
* → NON_DETERMINISTIC_FAIL
```

Aucun état d'échec ne publie un score valide.

## 11. Decision clock

Lot 26 active seulement :

```text
CLOSED_LOCAL_BAR
```

Les déclencheurs `MARKET_EVENT`, `BOOK_IMBALANCE_CHANGE`, `LIQUIDITY_SWEEP`, `FORECAST_UPDATE` et `RISK_EVENT` sont enregistrés mais désactivés.

## 12. Reason codes

La liste fermée est définie dans la configuration. Ajouter notamment :

```text
MTF_SCALE_RELATION_NOT_ALLOWED
MTF_NAIVE_VOTING_FORBIDDEN
MTF_FORECAST_FIELD_FORBIDDEN
```

Tout code inconnu est rejeté.

## 13. Configuration

La config est immuable par run, versionnée, hashée et jointe à chaque sortie. Les paramètres sont `PROVISIONAL_UNCALIBRATED_OFFLINE_ONLY`.

Le registre temporel sépare les échelles disponibles de celles activées dans le Lot 26.

## 14. Observabilité

- `lot_26_records_processed_total`
- `lot_26_validation_failures_total`
- `lot_26_processing_latency_ms`
- `mtf_join_lag_seconds`
- `mtf_local_state_age_seconds`
- `mtf_higher_state_age_seconds`
- `mtf_weighted_coverage_ratio`
- `mtf_alignment_score`
- `mtf_hard_mismatch_total`
- `mtf_open_bar_rejection_total`
- `mtf_future_state_rejection_total`
- `mtf_invalid_scale_relation_total`
- `mtf_replay_divergence_total`

## 15. Auditabilité

Chaque sortie contient les IDs des deux états sources, leurs bar closes, `decision_time`, la relation d'échelle, les versions de registre/config, `code_commit`, `lineage_id`, scores par composante, reason codes et checksum final.

## 16. Tests obligatoires

- unitaires ;
- oracles mathématiques ;
- property-based ;
- JSON schemas ;
- intégration Lot25→Lot26 ;
- replay déterministe ;
- anti-lookahead ;
- stale/missing/out-of-order/duplicates ;
- dernière 15m ouverte ignorée ;
- 15m future ignorée ;
- égalité `available_at == decision_time` acceptée ;
- divergence 5m/15m sans veto automatique ;
- relation 1m→5m rejetée dans le profil v1 ;
- autres échelles conservées `disabled` ;
- distinction résolution/horizon/clock/TTL/holding ;
- absence de vote naïf ;
- absence de forecast/probability/BUY/SELL/size/order fields ;
- mutation des comparateurs, poids, seuils et dénominateur ;
- performance sur séries longues.

## 17. Seuils qualité

```text
line coverage ajouté/modifié >= 90 %
branch coverage ajouté/modifié >= 85 %
module critique line >= 95 %
module critique branch >= 90 %
mutation score >= 80 %
```

## 18. Performance

Objectif offline initial :

```text
O(n log n) maximum pour préparation triée
O(log n) ou O(1) amorti par jointure après indexation
mémoire bornée par fenêtre/config
```

## 19. Migration historique

Les Lots 22–25 ne sont pas réécrits. Un adaptateur Lot 26 construit les nouveaux contrats depuis leurs artefacts, conserve les références sources et refuse tout champ temporel non démontrable.

## 20. Rollback

Supprimer les nouveaux artefacts Lot 26 et revenir au commit readiness. Aucun état d'exécution n'existe à réconcilier.

## 21. Risques connus

- enums historiques incomplets ;
- fixtures courtes ;
- paramètres non calibrés ;
- score descriptif facilement surinterprété ;
- révisions de données futures ;
- risque de coder des timeframes en dur ;
- confusion possible entre alignement et prédiction.

Ces risques interdisent toute promotion paper/live.

## 22. Definition of Done

Tous les tests, coverage, mutation, replay, sécurité, documentation et rapports sont PASS ; zéro BLOCKER/MAJOR ; audit humain `GO`; Lot 27 reste verrouillé.

## 23. Invariants

```text
analysis_only=true
used_for_decision=false
forecast_generation_allowed=false
probability_claims_allowed=false
signal_generation_allowed=false
order_routing_allowed=false
execution_allowed=false
trade_allowed=false
approved_size=0
live_execution=DISABLED
```
