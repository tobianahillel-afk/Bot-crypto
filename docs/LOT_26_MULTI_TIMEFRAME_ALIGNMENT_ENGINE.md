# Lot 26 — Multi-Timeframe Alignment Engine

Statut : `PLANNED_LOCKED`  
Version : V2 Market Analysis Offline  
Owner : `MarketAnalysisDomain`  
Runtime maximal : `LOCAL_OFFLINE_ANALYSIS_ONLY`  
Configuration normative : `config/math/multi_timeframe_alignment_v1.json`  
Checksum de configuration : `cb6ac1d3c392df67b5eb15d4c07a8fc818772025ec05e142190b0b667308bd76`

## 1. Objectif falsifiable

Pour chaque nouvel état local 5m issu d’une barre fermée, sélectionner le dernier état supérieur 15m
légalement disponible, comparer six composantes de contexte et produire un état descriptif
rejouable d’alignement/divergence/cohérence.

Le moteur est correct si, pour les mêmes inputs, config, code, horloge et ordre canonique, il produit
les mêmes sorties et checksums, sans lire de barre ouverte ou future.

## 2. Périmètre

Inclus :

- ingestion déjà existante potentiellement continue ;
- snapshots fermés 5m/15m ;
- jointure as-of backward ;
- compatibilité de trend/range/momentum/volatility/regime/confluence ;
- couverture, accord, divergence, cohérence, incertitude descriptive ;
- reason codes, lineage et replay.

Exclus :

- prédiction de rendement ;
- probabilité ;
- alpha ;
- signal BUY/SELL ;
- sizing, ordre ou exécution ;
- veto automatique du 15m sur le 5m ;
- inférence de participants, stops, take-profit ou théorie des jeux.

## 3. Dépendances

- Lots 22–25 validés ;
- artifacts 5m/15m du Lot 25 ;
- P0 institutionnel ;
- gate pré-Lot26 `GO` ;
- contrats temporels et config versionnée.

## 4. Contrats d’entrée

- `RunContextV1` ;
- `TimeframeMarketContextStateV1` local 5m ;
- série de `TimeframeMarketContextStateV1` supérieure 15m ;
- `ClosedBarAvailabilityV1` pour chaque état ;
- `LineageEnvelopeV1`.

Les schémas JSON sont dans `contracts/schemas/`.

## 5. Contrat de sortie

`MultiTimeframeAlignmentStateV1`, défini dans
`contracts/schemas/multi_timeframe_alignment_state_v1.schema.json`.

Le score peut être `null`. Aucune valeur manquante n’est transformée en zéro.

## 6. Séquence obligatoire

1. Valider runtime, schémas, config et checksum.
2. Valider UTC, durées de barres, ordre et disponibilité.
3. Rejeter états ouverts, futurs, stale ou incomplets.
4. Pour le 5m courant, faire la jointure as-of backward vers le 15m.
5. Normaliser les six enums sans inventer de valeur.
6. Calculer les compatibilités par formule/matrice normative.
7. Calculer couverture et score seulement si les minima sont atteints.
8. Classer alignement, divergence, cohérence et incertitude.
9. Ajouter reason codes, IDs, lineage et checksum.
10. Écrire atomiquement état et audit.
11. Rejouer et comparer run1/run2.
12. Conserver toutes les permissions d’exécution à `false`.

## 7. Mathématiques

La spécification normative est
`docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md`.

Formule centrale :

```text
A = Σ(w_i a_i I_i) / Σ(w_i I_i)
```

sous condition :

```text
Σ(I_i) >= 4
Σ(w_i I_i) >= 0.70
```

Le score `A` n’est ni une probabilité ni une estimation de rendement.

## 8. Machine d’état

```text
INPUT_VALIDATION
→ TIME_ELIGIBILITY
→ ASOF_JOIN
→ COMPONENT_COMPATIBILITY
→ COVERAGE_GATE
→ CLASSIFICATION
→ AUDIT_PERSISTENCE
→ REPLAY_VALIDATION
→ COMPLETE
```

Transitions d’échec :

```text
* → BLOCKED_SCHEMA
* → BLOCKED_TIME_ALIGNMENT
* → BLOCKED_STALE_DATA
* → UNKNOWN_INSUFFICIENT_COVERAGE
* → NON_DETERMINISTIC_FAIL
```

Aucun état d’échec ne publie un score valide.

## 9. Reason codes

La liste fermée est définie dans la configuration. Tout code inconnu est rejeté.

## 10. Configuration

La config est immutable par run, versionnée, hashée et jointe à chaque sortie.
Les paramètres sont `PROVISIONAL_UNCALIBRATED_OFFLINE_ONLY`.

## 11. Observabilité

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
- `mtf_replay_divergence_total`

## 12. Auditabilité

Chaque sortie contient les IDs des deux états sources, leurs bar closes, `decision_time`,
`config_version`, `config_checksum`, `code_commit`, `lineage_id`, scores par composante,
reason codes et checksum final.

## 13. Tests obligatoires

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
- mutation des comparateurs, poids, seuils et dénominateur ;
- performance sur séries longues ;
- interdiction de BUY/SELL/size/order fields.

## 14. Seuils qualité

```text
line coverage ajouté/modifié >= 90 %
branch coverage ajouté/modifié >= 85 %
module critique line >= 95 %
module critique branch >= 90 %
mutation score >= 80 %
```

## 15. Performance

Objectif offline initial :

```text
O(n log n) maximum pour préparation triée
O(log n) ou O(1) amorti par jointure après indexation
mémoire bornée par fenêtre/config
```

Le rapport devra publier les mesures, pas seulement l’objectif.

## 16. Migration historique

Les Lots 22–25 ne sont pas réécrits. Un adaptateur Lot 26 construit les nouveaux contrats depuis
leurs artifacts, conserve les références sources et refuse tout champ temporel non démontrable.

## 17. Rollback

Supprimer les nouveaux artifacts Lot 26 et revenir au commit P0/readiness. Aucun état d’exécution
n’existe à réconcilier.

## 18. Risques connus

- enums historiques incomplets ;
- fixtures courtes ;
- paramètres non calibrés ;
- score descriptif facilement surinterprété ;
- révisions de données futures.

Ces risques interdisent toute promotion paper/live.

## 19. Definition of Done

Tous les tests, coverage, mutation, replay, sécurité, documentation et rapports sont PASS ; zéro
BLOCKER/MAJOR ; audit humain `GO`; Lot 27 reste verrouillé.

## 20. Invariants

```text
analysis_only=true
used_for_decision=false
signal_generation_allowed=false
order_routing_allowed=false
execution_allowed=false
trade_allowed=false
approved_size=0
live_execution=DISABLED
```
