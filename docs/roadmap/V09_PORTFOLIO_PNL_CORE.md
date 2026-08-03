# V9 — Portfolio / PnL Core

Identifiant : `V9_PORTFOLIO_PNL`

Plage canonique : **Lots 88 à 95**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Centraliser portefeuille, positions, expositions et PnL dans un cœur comptable unique.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 88 — Portfolio Core & State Model

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Portfolio Core & State Model » dans la phase Portfolio / PnL Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Paper/sandbox/live adapters
- Order/fill ledger
- Instrument registry

### Exigences d’implémentation

- Centraliser cash, collateral, buying power, positions et expositions.
- Conserver un PnL Core unique avec adapters paper/sandbox/live.
- Attribuer fees, funding, spread, slippage et impact.
- Calculer concentration, corrélation, portfolio heat et drawdown.
- Produire statements, reconciliation et exports auditables.

### Artefacts attendus

- Portfolio state
- Unified PnL ledger
- Exposure reports
- Statements and audit exports

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown balance/position => freeze portfolio`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 89 — Cash, Collateral, Margin & Buying Power

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Cash, Collateral, Margin & Buying Power » dans la phase Portfolio / PnL Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Paper/sandbox/live adapters
- Order/fill ledger
- Instrument registry

### Exigences d’implémentation

- Centraliser cash, collateral, buying power, positions et expositions.
- Conserver un PnL Core unique avec adapters paper/sandbox/live.
- Attribuer fees, funding, spread, slippage et impact.
- Calculer concentration, corrélation, portfolio heat et drawdown.
- Produire statements, reconciliation et exports auditables.

### Artefacts attendus

- Portfolio state
- Unified PnL ledger
- Exposure reports
- Statements and audit exports

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown balance/position => freeze portfolio`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 90 — Position Lifecycle & Corporate/Instrument Events

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Position Lifecycle & Corporate/Instrument Events » dans la phase Portfolio / PnL Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Paper/sandbox/live adapters
- Order/fill ledger
- Instrument registry

### Exigences d’implémentation

- Centraliser cash, collateral, buying power, positions et expositions.
- Conserver un PnL Core unique avec adapters paper/sandbox/live.
- Attribuer fees, funding, spread, slippage et impact.
- Calculer concentration, corrélation, portfolio heat et drawdown.
- Produire statements, reconciliation et exports auditables.

### Artefacts attendus

- Portfolio state
- Unified PnL ledger
- Exposure reports
- Statements and audit exports

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown balance/position => freeze portfolio`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 91 — Unified PnL Core

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Unified PnL Core » dans la phase Portfolio / PnL Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Paper/sandbox/live adapters
- Order/fill ledger
- Instrument registry

### Exigences d’implémentation

- Centraliser cash, collateral, buying power, positions et expositions.
- Conserver un PnL Core unique avec adapters paper/sandbox/live.
- Attribuer fees, funding, spread, slippage et impact.
- Calculer concentration, corrélation, portfolio heat et drawdown.
- Produire statements, reconciliation et exports auditables.

### Artefacts attendus

- Portfolio state
- Unified PnL ledger
- Exposure reports
- Statements and audit exports

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown balance/position => freeze portfolio`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 92 — Fee, Funding, Slippage & Attribution

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Fee, Funding, Slippage & Attribution » dans la phase Portfolio / PnL Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Paper/sandbox/live adapters
- Order/fill ledger
- Instrument registry

### Exigences d’implémentation

- Centraliser cash, collateral, buying power, positions et expositions.
- Conserver un PnL Core unique avec adapters paper/sandbox/live.
- Attribuer fees, funding, spread, slippage et impact.
- Calculer concentration, corrélation, portfolio heat et drawdown.
- Produire statements, reconciliation et exports auditables.

### Artefacts attendus

- Portfolio state
- Unified PnL ledger
- Exposure reports
- Statements and audit exports

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown balance/position => freeze portfolio`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 93 — Exposure, Correlation, Concentration & Portfolio Heat

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Exposure, Correlation, Concentration & Portfolio Heat » dans la phase Portfolio / PnL Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Paper/sandbox/live adapters
- Order/fill ledger
- Instrument registry

### Exigences d’implémentation

- Centraliser cash, collateral, buying power, positions et expositions.
- Conserver un PnL Core unique avec adapters paper/sandbox/live.
- Attribuer fees, funding, spread, slippage et impact.
- Calculer concentration, corrélation, portfolio heat et drawdown.
- Produire statements, reconciliation et exports auditables.

### Artefacts attendus

- Portfolio state
- Unified PnL ledger
- Exposure reports
- Statements and audit exports

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown balance/position => freeze portfolio`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 94 — Statements, Reconciliation & Audit Export

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Statements, Reconciliation & Audit Export » dans la phase Portfolio / PnL Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Paper/sandbox/live adapters
- Order/fill ledger
- Instrument registry

### Exigences d’implémentation

- Centraliser cash, collateral, buying power, positions et expositions.
- Conserver un PnL Core unique avec adapters paper/sandbox/live.
- Attribuer fees, funding, spread, slippage et impact.
- Calculer concentration, corrélation, portfolio heat et drawdown.
- Produire statements, reconciliation et exports auditables.

### Artefacts attendus

- Portfolio state
- Unified PnL ledger
- Exposure reports
- Statements and audit exports

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown balance/position => freeze portfolio`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 95 — V9 Portfolio / PnL Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « V9 Portfolio / PnL Closure » dans la phase Portfolio / PnL Core avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Paper/sandbox/live adapters
- Order/fill ledger
- Instrument registry

### Exigences d’implémentation

- Centraliser cash, collateral, buying power, positions et expositions.
- Conserver un PnL Core unique avec adapters paper/sandbox/live.
- Attribuer fees, funding, spread, slippage et impact.
- Calculer concentration, corrélation, portfolio heat et drawdown.
- Produire statements, reconciliation et exports auditables.

### Artefacts attendus

- Portfolio state
- Unified PnL ledger
- Exposure reports
- Statements and audit exports
- Rapport de clôture V9_PORTFOLIO_PNL

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Unknown balance/position => freeze portfolio`

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
