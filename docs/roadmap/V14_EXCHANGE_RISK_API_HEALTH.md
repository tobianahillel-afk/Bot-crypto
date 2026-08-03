# V14 — Exchange Risk / API Health

Identifiant : `V14_EXCHANGE_RISK`

Plage canonique : **Lots 126 à 132**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Surveiller santé exchange, APIs, données et risques opérationnels.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 126 — Exchange Risk Registry

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Exchange Risk Registry » dans la phase Exchange Risk / API Health avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Connector health
- Exchange status
- Market metadata

### Exigences d’implémentation

- Enregistrer risques techniques, opérationnels et de contrepartie par exchange.
- Surveiller REST, WebSocket, latence, gaps, maintenance et symbol halts.
- Détecter staleness, clock drift, sequence gaps et conditions anormales.
- Définir failover/degraded modes sans exécution implicite.
- Afficher et auditer les vetos exchange/data.

### Artefacts attendus

- Exchange risk state
- Health metrics
- Availability reports
- Veto evidence

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown exchange state => no new orders`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 127 — REST / WebSocket Health Monitor

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « REST / WebSocket Health Monitor » dans la phase Exchange Risk / API Health avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Connector health
- Exchange status
- Market metadata

### Exigences d’implémentation

- Enregistrer risques techniques, opérationnels et de contrepartie par exchange.
- Surveiller REST, WebSocket, latence, gaps, maintenance et symbol halts.
- Détecter staleness, clock drift, sequence gaps et conditions anormales.
- Définir failover/degraded modes sans exécution implicite.
- Afficher et auditer les vetos exchange/data.

### Artefacts attendus

- Exchange risk state
- Health metrics
- Availability reports
- Veto evidence

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown exchange state => no new orders`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 128 — Market, Symbol & Instrument Availability

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Market, Symbol & Instrument Availability » dans la phase Exchange Risk / API Health avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Connector health
- Exchange status
- Market metadata

### Exigences d’implémentation

- Enregistrer risques techniques, opérationnels et de contrepartie par exchange.
- Surveiller REST, WebSocket, latence, gaps, maintenance et symbol halts.
- Détecter staleness, clock drift, sequence gaps et conditions anormales.
- Définir failover/degraded modes sans exécution implicite.
- Afficher et auditer les vetos exchange/data.

### Artefacts attendus

- Exchange risk state
- Health metrics
- Availability reports
- Veto evidence

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown exchange state => no new orders`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 129 — Data Staleness, Clock Drift & Sequence Health

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Data Staleness, Clock Drift & Sequence Health » dans la phase Exchange Risk / API Health avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Connector health
- Exchange status
- Market metadata

### Exigences d’implémentation

- Enregistrer risques techniques, opérationnels et de contrepartie par exchange.
- Surveiller REST, WebSocket, latence, gaps, maintenance et symbol halts.
- Détecter staleness, clock drift, sequence gaps et conditions anormales.
- Définir failover/degraded modes sans exécution implicite.
- Afficher et auditer les vetos exchange/data.

### Artefacts attendus

- Exchange risk state
- Health metrics
- Availability reports
- Veto evidence

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown exchange state => no new orders`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 130 — Rate Limits, Maintenance & Failover

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Rate Limits, Maintenance & Failover » dans la phase Exchange Risk / API Health avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Connector health
- Exchange status
- Market metadata

### Exigences d’implémentation

- Enregistrer risques techniques, opérationnels et de contrepartie par exchange.
- Surveiller REST, WebSocket, latence, gaps, maintenance et symbol halts.
- Détecter staleness, clock drift, sequence gaps et conditions anormales.
- Définir failover/degraded modes sans exécution implicite.
- Afficher et auditer les vetos exchange/data.

### Artefacts attendus

- Exchange risk state
- Health metrics
- Availability reports
- Veto evidence

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown exchange state => no new orders`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 131 — Counterparty / Operational Risk Dashboard

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Counterparty / Operational Risk Dashboard » dans la phase Exchange Risk / API Health avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Connector health
- Exchange status
- Market metadata

### Exigences d’implémentation

- Enregistrer risques techniques, opérationnels et de contrepartie par exchange.
- Surveiller REST, WebSocket, latence, gaps, maintenance et symbol halts.
- Détecter staleness, clock drift, sequence gaps et conditions anormales.
- Définir failover/degraded modes sans exécution implicite.
- Afficher et auditer les vetos exchange/data.

### Artefacts attendus

- Exchange risk state
- Health metrics
- Availability reports
- Veto evidence

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown exchange state => no new orders`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 132 — V14 Exchange Risk Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « V14 Exchange Risk Closure » dans la phase Exchange Risk / API Health avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Connector health
- Exchange status
- Market metadata

### Exigences d’implémentation

- Enregistrer risques techniques, opérationnels et de contrepartie par exchange.
- Surveiller REST, WebSocket, latence, gaps, maintenance et symbol halts.
- Détecter staleness, clock drift, sequence gaps et conditions anormales.
- Définir failover/degraded modes sans exécution implicite.
- Afficher et auditer les vetos exchange/data.

### Artefacts attendus

- Exchange risk state
- Health metrics
- Availability reports
- Veto evidence
- Rapport de clôture V14_EXCHANGE_RISK

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown exchange state => no new orders`

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
