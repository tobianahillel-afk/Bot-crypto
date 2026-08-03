# V13 — API Read-Only / Account Read-Only

Identifiant : `V13_API_READ_ONLY`

Plage canonique : **Lots 119 à 125**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Lire comptes et historiques exchange avec permissions strictement read-only.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 119 — API Read-Only Scope & Secrets Policy

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « API Read-Only Scope & Secrets Policy » dans la phase API Read-Only / Account Read-Only avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Read-only credentials
- Exchange metadata
- Account snapshots

### Exigences d’implémentation

- Définir connecteurs strictement read-only.
- Scanner permissions API et appliquer least privilege.
- Lire balances, positions, historiques d’ordres/trades/funding.
- Réconcilier états locaux et exchange sans écrire sur le compte.
- Stocker les secrets hors dépôt avec rotation et révocation documentées.

### Artefacts attendus

- Read-only snapshots
- Permission audit
- Reconciliation reports
- Secrets runbooks

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `withdrawal_permission=FORBIDDEN`
- `trading_permission=FORBIDDEN`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 120 — Exchange Connector Read-Only

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Exchange Connector Read-Only » dans la phase API Read-Only / Account Read-Only avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Read-only credentials
- Exchange metadata
- Account snapshots

### Exigences d’implémentation

- Définir connecteurs strictement read-only.
- Scanner permissions API et appliquer least privilege.
- Lire balances, positions, historiques d’ordres/trades/funding.
- Réconcilier états locaux et exchange sans écrire sur le compte.
- Stocker les secrets hors dépôt avec rotation et révocation documentées.

### Artefacts attendus

- Read-only snapshots
- Permission audit
- Reconciliation reports
- Secrets runbooks

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `withdrawal_permission=FORBIDDEN`
- `trading_permission=FORBIDDEN`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 121 — Balances, Positions & Account Snapshot

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Balances, Positions & Account Snapshot » dans la phase API Read-Only / Account Read-Only avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Read-only credentials
- Exchange metadata
- Account snapshots

### Exigences d’implémentation

- Définir connecteurs strictement read-only.
- Scanner permissions API et appliquer least privilege.
- Lire balances, positions, historiques d’ordres/trades/funding.
- Réconcilier états locaux et exchange sans écrire sur le compte.
- Stocker les secrets hors dépôt avec rotation et révocation documentées.

### Artefacts attendus

- Read-only snapshots
- Permission audit
- Reconciliation reports
- Secrets runbooks

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `withdrawal_permission=FORBIDDEN`
- `trading_permission=FORBIDDEN`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 122 — Order, Trade & Funding History

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Order, Trade & Funding History » dans la phase API Read-Only / Account Read-Only avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Read-only credentials
- Exchange metadata
- Account snapshots

### Exigences d’implémentation

- Définir connecteurs strictement read-only.
- Scanner permissions API et appliquer least privilege.
- Lire balances, positions, historiques d’ordres/trades/funding.
- Réconcilier états locaux et exchange sans écrire sur le compte.
- Stocker les secrets hors dépôt avec rotation et révocation documentées.

### Artefacts attendus

- Read-only snapshots
- Permission audit
- Reconciliation reports
- Secrets runbooks

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `withdrawal_permission=FORBIDDEN`
- `trading_permission=FORBIDDEN`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 123 — Read-Only Reconciliation Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Read-Only Reconciliation Engine » dans la phase API Read-Only / Account Read-Only avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Read-only credentials
- Exchange metadata
- Account snapshots

### Exigences d’implémentation

- Définir connecteurs strictement read-only.
- Scanner permissions API et appliquer least privilege.
- Lire balances, positions, historiques d’ordres/trades/funding.
- Réconcilier états locaux et exchange sans écrire sur le compte.
- Stocker les secrets hors dépôt avec rotation et révocation documentées.

### Artefacts attendus

- Read-only snapshots
- Permission audit
- Reconciliation reports
- Secrets runbooks

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `withdrawal_permission=FORBIDDEN`
- `trading_permission=FORBIDDEN`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 124 — Permission Scanner & Least-Privilege Audit

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Permission Scanner & Least-Privilege Audit » dans la phase API Read-Only / Account Read-Only avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Read-only credentials
- Exchange metadata
- Account snapshots

### Exigences d’implémentation

- Définir connecteurs strictement read-only.
- Scanner permissions API et appliquer least privilege.
- Lire balances, positions, historiques d’ordres/trades/funding.
- Réconcilier états locaux et exchange sans écrire sur le compte.
- Stocker les secrets hors dépôt avec rotation et révocation documentées.

### Artefacts attendus

- Read-only snapshots
- Permission audit
- Reconciliation reports
- Secrets runbooks

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `withdrawal_permission=FORBIDDEN`
- `trading_permission=FORBIDDEN`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 125 — V13 API Read-Only Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « V13 API Read-Only Closure » dans la phase API Read-Only / Account Read-Only avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Read-only credentials
- Exchange metadata
- Account snapshots

### Exigences d’implémentation

- Définir connecteurs strictement read-only.
- Scanner permissions API et appliquer least privilege.
- Lire balances, positions, historiques d’ordres/trades/funding.
- Réconcilier états locaux et exchange sans écrire sur le compte.
- Stocker les secrets hors dépôt avec rotation et révocation documentées.

### Artefacts attendus

- Read-only snapshots
- Permission audit
- Reconciliation reports
- Secrets runbooks
- Rapport de clôture V13_API_READ_ONLY

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `withdrawal_permission=FORBIDDEN`
- `trading_permission=FORBIDDEN`

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
