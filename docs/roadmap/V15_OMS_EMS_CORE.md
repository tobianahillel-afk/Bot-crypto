# V15 — OMS / EMS Core

Identifiant : `V15_OMS_EMS`

Plage canonique : **Lots 133 à 141**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Construire un OMS/EMS robuste, idempotent, réconciliable et rejouable.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 133 — OMS / EMS Architecture & Contracts

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « OMS / EMS Architecture & Contracts » dans la phase OMS / EMS Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order intents risk-approved
- Instrument specs
- Exchange/sandbox adapters

### Exigences d’implémentation

- Définir OMS et EMS comme composants distincts avec contrats stables.
- Implémenter machine d’état d’ordre et transitions autorisées.
- Garantir idempotency, client_order_id et prévention des doublons.
- Gérer validation instrument, rejects, retries, partial fills et cancel/replace.
- Réconcilier ordres orphelins et restaurer l’état après crash.

### Artefacts attendus

- Order state ledger
- Execution events
- Reconciliation state
- Replay evidence

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- OMS cannot accept unapproved intent
- Retry bounded

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 134 — Order State Machine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Order State Machine » dans la phase OMS / EMS Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order intents risk-approved
- Instrument specs
- Exchange/sandbox adapters

### Exigences d’implémentation

- Définir OMS et EMS comme composants distincts avec contrats stables.
- Implémenter machine d’état d’ordre et transitions autorisées.
- Garantir idempotency, client_order_id et prévention des doublons.
- Gérer validation instrument, rejects, retries, partial fills et cancel/replace.
- Réconcilier ordres orphelins et restaurer l’état après crash.

### Artefacts attendus

- Order state ledger
- Execution events
- Reconciliation state
- Replay evidence

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- OMS cannot accept unapproved intent
- Retry bounded

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 135 — Client Order IDs, Idempotency & Duplicate Prevention

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Client Order IDs, Idempotency & Duplicate Prevention » dans la phase OMS / EMS Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order intents risk-approved
- Instrument specs
- Exchange/sandbox adapters

### Exigences d’implémentation

- Définir OMS et EMS comme composants distincts avec contrats stables.
- Implémenter machine d’état d’ordre et transitions autorisées.
- Garantir idempotency, client_order_id et prévention des doublons.
- Gérer validation instrument, rejects, retries, partial fills et cancel/replace.
- Réconcilier ordres orphelins et restaurer l’état après crash.

### Artefacts attendus

- Order state ledger
- Execution events
- Reconciliation state
- Replay evidence

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- OMS cannot accept unapproved intent
- Retry bounded

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 136 — Order Validation & Contract Specification Rules

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Order Validation & Contract Specification Rules » dans la phase OMS / EMS Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order intents risk-approved
- Instrument specs
- Exchange/sandbox adapters

### Exigences d’implémentation

- Définir OMS et EMS comme composants distincts avec contrats stables.
- Implémenter machine d’état d’ordre et transitions autorisées.
- Garantir idempotency, client_order_id et prévention des doublons.
- Gérer validation instrument, rejects, retries, partial fills et cancel/replace.
- Réconcilier ordres orphelins et restaurer l’état après crash.

### Artefacts attendus

- Order state ledger
- Execution events
- Reconciliation state
- Replay evidence

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- OMS cannot accept unapproved intent
- Retry bounded

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 137 — Reject, Retry, Rate-Limit & Backoff Handling

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Reject, Retry, Rate-Limit & Backoff Handling » dans la phase OMS / EMS Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order intents risk-approved
- Instrument specs
- Exchange/sandbox adapters

### Exigences d’implémentation

- Définir OMS et EMS comme composants distincts avec contrats stables.
- Implémenter machine d’état d’ordre et transitions autorisées.
- Garantir idempotency, client_order_id et prévention des doublons.
- Gérer validation instrument, rejects, retries, partial fills et cancel/replace.
- Réconcilier ordres orphelins et restaurer l’état après crash.

### Artefacts attendus

- Order state ledger
- Execution events
- Reconciliation state
- Replay evidence

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- OMS cannot accept unapproved intent
- Retry bounded

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 138 — Partial Fills, Average Price & Residual Quantity

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Partial Fills, Average Price & Residual Quantity » dans la phase OMS / EMS Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order intents risk-approved
- Instrument specs
- Exchange/sandbox adapters

### Exigences d’implémentation

- Définir OMS et EMS comme composants distincts avec contrats stables.
- Implémenter machine d’état d’ordre et transitions autorisées.
- Garantir idempotency, client_order_id et prévention des doublons.
- Gérer validation instrument, rejects, retries, partial fills et cancel/replace.
- Réconcilier ordres orphelins et restaurer l’état après crash.

### Artefacts attendus

- Order state ledger
- Execution events
- Reconciliation state
- Replay evidence

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- OMS cannot accept unapproved intent
- Retry bounded

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 139 — Cancel / Replace & Race-Condition Handling

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Cancel / Replace & Race-Condition Handling » dans la phase OMS / EMS Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order intents risk-approved
- Instrument specs
- Exchange/sandbox adapters

### Exigences d’implémentation

- Définir OMS et EMS comme composants distincts avec contrats stables.
- Implémenter machine d’état d’ordre et transitions autorisées.
- Garantir idempotency, client_order_id et prévention des doublons.
- Gérer validation instrument, rejects, retries, partial fills et cancel/replace.
- Réconcilier ordres orphelins et restaurer l’état après crash.

### Artefacts attendus

- Order state ledger
- Execution events
- Reconciliation state
- Replay evidence

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- OMS cannot accept unapproved intent
- Retry bounded

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 140 — Orphan Order Reconciliation & Crash Recovery

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Orphan Order Reconciliation & Crash Recovery » dans la phase OMS / EMS Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order intents risk-approved
- Instrument specs
- Exchange/sandbox adapters

### Exigences d’implémentation

- Définir OMS et EMS comme composants distincts avec contrats stables.
- Implémenter machine d’état d’ordre et transitions autorisées.
- Garantir idempotency, client_order_id et prévention des doublons.
- Gérer validation instrument, rejects, retries, partial fills et cancel/replace.
- Réconcilier ordres orphelins et restaurer l’état après crash.

### Artefacts attendus

- Order state ledger
- Execution events
- Reconciliation state
- Replay evidence

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- OMS cannot accept unapproved intent
- Retry bounded

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 141 — OMS / EMS Replay, Audit & V15 Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « OMS / EMS Replay, Audit & V15 Closure » dans la phase OMS / EMS Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Order intents risk-approved
- Instrument specs
- Exchange/sandbox adapters

### Exigences d’implémentation

- Définir OMS et EMS comme composants distincts avec contrats stables.
- Implémenter machine d’état d’ordre et transitions autorisées.
- Garantir idempotency, client_order_id et prévention des doublons.
- Gérer validation instrument, rejects, retries, partial fills et cancel/replace.
- Réconcilier ordres orphelins et restaurer l’état après crash.

### Artefacts attendus

- Order state ledger
- Execution events
- Reconciliation state
- Replay evidence
- Rapport de clôture V15_OMS_EMS

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- OMS cannot accept unapproved intent
- Retry bounded

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
