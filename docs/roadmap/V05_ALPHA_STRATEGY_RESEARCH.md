# V5 — Alpha / Strategy Research

Identifiant : `V5_ALPHA_STRATEGY_RESEARCH`

Plage canonique : **Lots 53 à 59**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Transformer des scénarios en hypothèses d’alpha et contrats de stratégie sans exécution.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 53 — Alpha Governance & Hypothesis Registry

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Alpha Governance & Hypothesis Registry » dans la phase Alpha / Strategy Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Scénarios V4
- Feature registry
- Hypothèses de recherche

### Exigences d’implémentation

- Enregistrer chaque hypothèse avec intuition, mécanisme, données, régime et falsification.
- Définir un StrategyCandidate immuable et versionné.
- Séparer Signal, TradeIntent et OrderIntent par contrats distincts.
- Définir expiration, invalidation, horizon et éligibilité par régime.
- Bloquer la promotion sans preuve statistique et revue humaine.

### Artefacts attendus

- Alpha registry
- Strategy candidate registry
- Signal/trade-intent schemas
- Promotion decisions

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `signal != order`
- `trade_intent != order_intent`
- LLM cannot create signal

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 54 — Strategy Candidate Contract

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Strategy Candidate Contract » dans la phase Alpha / Strategy Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Scénarios V4
- Feature registry
- Hypothèses de recherche

### Exigences d’implémentation

- Enregistrer chaque hypothèse avec intuition, mécanisme, données, régime et falsification.
- Définir un StrategyCandidate immuable et versionné.
- Séparer Signal, TradeIntent et OrderIntent par contrats distincts.
- Définir expiration, invalidation, horizon et éligibilité par régime.
- Bloquer la promotion sans preuve statistique et revue humaine.

### Artefacts attendus

- Alpha registry
- Strategy candidate registry
- Signal/trade-intent schemas
- Promotion decisions

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `signal != order`
- `trade_intent != order_intent`
- LLM cannot create signal

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 55 — Signal Schema, Calibration & Expiration

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Signal Schema, Calibration & Expiration » dans la phase Alpha / Strategy Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Scénarios V4
- Feature registry
- Hypothèses de recherche

### Exigences d’implémentation

- Enregistrer chaque hypothèse avec intuition, mécanisme, données, régime et falsification.
- Définir un StrategyCandidate immuable et versionné.
- Séparer Signal, TradeIntent et OrderIntent par contrats distincts.
- Définir expiration, invalidation, horizon et éligibilité par régime.
- Bloquer la promotion sans preuve statistique et revue humaine.

### Artefacts attendus

- Alpha registry
- Strategy candidate registry
- Signal/trade-intent schemas
- Promotion decisions

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `signal != order`
- `trade_intent != order_intent`
- LLM cannot create signal

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 56 — Trade Intent / Order Intent Boundary

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Trade Intent / Order Intent Boundary » dans la phase Alpha / Strategy Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Scénarios V4
- Feature registry
- Hypothèses de recherche

### Exigences d’implémentation

- Enregistrer chaque hypothèse avec intuition, mécanisme, données, régime et falsification.
- Définir un StrategyCandidate immuable et versionné.
- Séparer Signal, TradeIntent et OrderIntent par contrats distincts.
- Définir expiration, invalidation, horizon et éligibilité par régime.
- Bloquer la promotion sans preuve statistique et revue humaine.

### Artefacts attendus

- Alpha registry
- Strategy candidate registry
- Signal/trade-intent schemas
- Promotion decisions

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `signal != order`
- `trade_intent != order_intent`
- LLM cannot create signal

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 57 — Regime Eligibility, Holding Horizon & Invalidation

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Regime Eligibility, Holding Horizon & Invalidation » dans la phase Alpha / Strategy Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Scénarios V4
- Feature registry
- Hypothèses de recherche

### Exigences d’implémentation

- Enregistrer chaque hypothèse avec intuition, mécanisme, données, régime et falsification.
- Définir un StrategyCandidate immuable et versionné.
- Séparer Signal, TradeIntent et OrderIntent par contrats distincts.
- Définir expiration, invalidation, horizon et éligibilité par régime.
- Bloquer la promotion sans preuve statistique et revue humaine.

### Artefacts attendus

- Alpha registry
- Strategy candidate registry
- Signal/trade-intent schemas
- Promotion decisions

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `signal != order`
- `trade_intent != order_intent`
- LLM cannot create signal

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 58 — Alpha Decay, Stability & Retirement Rules

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Alpha Decay, Stability & Retirement Rules » dans la phase Alpha / Strategy Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Scénarios V4
- Feature registry
- Hypothèses de recherche

### Exigences d’implémentation

- Enregistrer chaque hypothèse avec intuition, mécanisme, données, régime et falsification.
- Définir un StrategyCandidate immuable et versionné.
- Séparer Signal, TradeIntent et OrderIntent par contrats distincts.
- Définir expiration, invalidation, horizon et éligibilité par régime.
- Bloquer la promotion sans preuve statistique et revue humaine.

### Artefacts attendus

- Alpha registry
- Strategy candidate registry
- Signal/trade-intent schemas
- Promotion decisions

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `signal != order`
- `trade_intent != order_intent`
- LLM cannot create signal

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 59 — Research-to-Backtest Promotion Gate & V5 Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Research-to-Backtest Promotion Gate & V5 Closure » dans la phase Alpha / Strategy Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Scénarios V4
- Feature registry
- Hypothèses de recherche

### Exigences d’implémentation

- Enregistrer chaque hypothèse avec intuition, mécanisme, données, régime et falsification.
- Définir un StrategyCandidate immuable et versionné.
- Séparer Signal, TradeIntent et OrderIntent par contrats distincts.
- Définir expiration, invalidation, horizon et éligibilité par régime.
- Bloquer la promotion sans preuve statistique et revue humaine.

### Artefacts attendus

- Alpha registry
- Strategy candidate registry
- Signal/trade-intent schemas
- Promotion decisions
- Rapport de clôture V5_ALPHA_STRATEGY_RESEARCH

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `signal != order`
- `trade_intent != order_intent`
- LLM cannot create signal

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
