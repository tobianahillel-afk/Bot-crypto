# V4 — Microstructure / Liquidity / Game Theory

Identifiant : `V4_MICROSTRUCTURE_LIQUIDITY`

Plage canonique : **Lots 37 à 52**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Analyser order book, order flow, liquidité, dérivés et scénarios comportementaux en offline.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 37 — Microstructure Scope & Offline Data Contracts

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Microstructure Scope & Offline Data Contracts » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 38 — Order Book L2 Snapshot Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Order Book L2 Snapshot Engine » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 39 — Order Book Delta & Sequence Reconstructor

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Order Book Delta & Sequence Reconstructor » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 40 — Book Integrity / Desynchronization Detector

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Book Integrity / Desynchronization Detector » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 41 — Spread, Depth & Imbalance Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Spread, Depth & Imbalance Engine » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 42 — Liquidity Zones, Walls & Voids Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Liquidity Zones, Walls & Voids Engine » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 43 — Book Resilience & Replenishment Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Book Resilience & Replenishment Engine » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 44 — Trades & Aggressor Classification Schema

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Trades & Aggressor Classification Schema » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 45 — Order Flow, Delta & CVD Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Order Flow, Delta & CVD Engine » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 46 — Trade Classification Confidence Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Trade Classification Confidence Engine » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 47 — Absorption, Defense & Hidden Liquidity Proxy

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Absorption, Defense & Hidden Liquidity Proxy » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 48 — Volume Clusters & Time-at-Level Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Volume Clusters & Time-at-Level Engine » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 49 — Stop Zones, Liquidity Pools & Breakout Attraction

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Stop Zones, Liquidity Pools & Breakout Attraction » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 50 — Sweep, Fakeout, Trap & Failed Auction Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Sweep, Fakeout, Trap & Failed Auction Engine » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 51 — Derivatives Context: OI, Funding, Basis & Liquidations

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Derivatives Context: OI, Funding, Basis & Liquidations » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 52 — Game Theory, Scenario Aggregation & V4 Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Game Theory, Scenario Aggregation & V4 Closure » dans la phase Microstructure / Liquidity / Game Theory avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order book L2/L3 offline
- Trades horodatés
- Contexte V2
- Données dérivés offline

### Exigences d’implémentation

- Travailler d’abord sur fixtures offline et replays déterministes.
- Séparer snapshot, delta, sequence_id, event_time et receive_time.
- Mesurer spread, depth, imbalance, resilience, order flow, CVD et absorption avec incertitude explicite.
- Détecter zones de liquidité, stops probables, sweeps, fakeouts et liquidations sans prétendre connaître les intentions réelles.
- Fusionner les observations en scénarios concurrents avec scores de confiance et conflits.

### Artefacts attendus

- États microstructure
- Zones et événements
- Scénarios explicables
- Replay et audit anti-lookahead
- Rapport de clôture V4_MICROSTRUCTURE_LIQUIDITY

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `participant_behavior = inference_explicitly_labeled`
- `scenario_score != signal`
- `execution_allowed=false`

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
