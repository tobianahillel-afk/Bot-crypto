# V7 — Model Risk / Sizing / Risk

Identifiant : `V7_MODEL_RISK_SIZING`

Plage canonique : **Lots 72 à 80**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Encadrer model risk, sizing, limites et risk approval avant toute simulation opérationnelle.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 72 — Model Inventory, Model Cards & Assumption Registry

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Model Inventory, Model Cards & Assumption Registry » dans la phase Model Risk / Sizing / Risk avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Backtest validé
- Market data quality
- Portfolio constraints

### Exigences d’implémentation

- Créer model cards, assumptions, limitations et ownership.
- Détecter drift, performance decay et invalidation de modèle.
- Définir limites globales, par stratégie, par instrument et par période.
- Calculer sizing ajusté volatilité, confiance, liquidité et slippage.
- Appliquer drawdown de-risking, risk of ruin et kill-switch policy.

### Artefacts attendus

- Model risk registry
- Sizing decisions simulées
- Risk approval evidence
- Kill-switch tests

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- No position without risk approval
- `Default sizing=0`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 73 — Model Risk, Drift & Performance Decay

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Model Risk, Drift & Performance Decay » dans la phase Model Risk / Sizing / Risk avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Backtest validé
- Market data quality
- Portfolio constraints

### Exigences d’implémentation

- Créer model cards, assumptions, limitations et ownership.
- Détecter drift, performance decay et invalidation de modèle.
- Définir limites globales, par stratégie, par instrument et par période.
- Calculer sizing ajusté volatilité, confiance, liquidité et slippage.
- Appliquer drawdown de-risking, risk of ruin et kill-switch policy.

### Artefacts attendus

- Model risk registry
- Sizing decisions simulées
- Risk approval evidence
- Kill-switch tests

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- No position without risk approval
- `Default sizing=0`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 74 — Risk Limits Framework

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Risk Limits Framework » dans la phase Model Risk / Sizing / Risk avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Backtest validé
- Market data quality
- Portfolio constraints

### Exigences d’implémentation

- Créer model cards, assumptions, limitations et ownership.
- Détecter drift, performance decay et invalidation de modèle.
- Définir limites globales, par stratégie, par instrument et par période.
- Calculer sizing ajusté volatilité, confiance, liquidité et slippage.
- Appliquer drawdown de-risking, risk of ruin et kill-switch policy.

### Artefacts attendus

- Model risk registry
- Sizing decisions simulées
- Risk approval evidence
- Kill-switch tests

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- No position without risk approval
- `Default sizing=0`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 75 — Volatility- and Confidence-Adjusted Sizing

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Volatility- and Confidence-Adjusted Sizing » dans la phase Model Risk / Sizing / Risk avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Backtest validé
- Market data quality
- Portfolio constraints

### Exigences d’implémentation

- Créer model cards, assumptions, limitations et ownership.
- Détecter drift, performance decay et invalidation de modèle.
- Définir limites globales, par stratégie, par instrument et par période.
- Calculer sizing ajusté volatilité, confiance, liquidité et slippage.
- Appliquer drawdown de-risking, risk of ruin et kill-switch policy.

### Artefacts attendus

- Model risk registry
- Sizing decisions simulées
- Risk approval evidence
- Kill-switch tests

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- No position without risk approval
- `Default sizing=0`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 76 — Liquidity- and Slippage-Adjusted Sizing

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Liquidity- and Slippage-Adjusted Sizing » dans la phase Model Risk / Sizing / Risk avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Backtest validé
- Market data quality
- Portfolio constraints

### Exigences d’implémentation

- Créer model cards, assumptions, limitations et ownership.
- Détecter drift, performance decay et invalidation de modèle.
- Définir limites globales, par stratégie, par instrument et par période.
- Calculer sizing ajusté volatilité, confiance, liquidité et slippage.
- Appliquer drawdown de-risking, risk of ruin et kill-switch policy.

### Artefacts attendus

- Model risk registry
- Sizing decisions simulées
- Risk approval evidence
- Kill-switch tests

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- No position without risk approval
- `Default sizing=0`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 77 — Drawdown De-Risking, Tail Risk & Risk of Ruin

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Drawdown De-Risking, Tail Risk & Risk of Ruin » dans la phase Model Risk / Sizing / Risk avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Backtest validé
- Market data quality
- Portfolio constraints

### Exigences d’implémentation

- Créer model cards, assumptions, limitations et ownership.
- Détecter drift, performance decay et invalidation de modèle.
- Définir limites globales, par stratégie, par instrument et par période.
- Calculer sizing ajusté volatilité, confiance, liquidité et slippage.
- Appliquer drawdown de-risking, risk of ruin et kill-switch policy.

### Artefacts attendus

- Model risk registry
- Sizing decisions simulées
- Risk approval evidence
- Kill-switch tests

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- No position without risk approval
- `Default sizing=0`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 78 — Correlation, Concentration & Portfolio Pre-Checks

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Correlation, Concentration & Portfolio Pre-Checks » dans la phase Model Risk / Sizing / Risk avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Backtest validé
- Market data quality
- Portfolio constraints

### Exigences d’implémentation

- Créer model cards, assumptions, limitations et ownership.
- Détecter drift, performance decay et invalidation de modèle.
- Définir limites globales, par stratégie, par instrument et par période.
- Calculer sizing ajusté volatilité, confiance, liquidité et slippage.
- Appliquer drawdown de-risking, risk of ruin et kill-switch policy.

### Artefacts attendus

- Model risk registry
- Sizing decisions simulées
- Risk approval evidence
- Kill-switch tests

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- No position without risk approval
- `Default sizing=0`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 79 — Risk Approval Gate & Kill-Switch Policy

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Risk Approval Gate & Kill-Switch Policy » dans la phase Model Risk / Sizing / Risk avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Backtest validé
- Market data quality
- Portfolio constraints

### Exigences d’implémentation

- Créer model cards, assumptions, limitations et ownership.
- Détecter drift, performance decay et invalidation de modèle.
- Définir limites globales, par stratégie, par instrument et par période.
- Calculer sizing ajusté volatilité, confiance, liquidité et slippage.
- Appliquer drawdown de-risking, risk of ruin et kill-switch policy.

### Artefacts attendus

- Model risk registry
- Sizing decisions simulées
- Risk approval evidence
- Kill-switch tests

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- No position without risk approval
- `Default sizing=0`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 80 — V7 Model Risk / Sizing Audit & Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « V7 Model Risk / Sizing Audit & Closure » dans la phase Model Risk / Sizing / Risk avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Backtest validé
- Market data quality
- Portfolio constraints

### Exigences d’implémentation

- Créer model cards, assumptions, limitations et ownership.
- Détecter drift, performance decay et invalidation de modèle.
- Définir limites globales, par stratégie, par instrument et par période.
- Calculer sizing ajusté volatilité, confiance, liquidité et slippage.
- Appliquer drawdown de-risking, risk of ruin et kill-switch policy.

### Artefacts attendus

- Model risk registry
- Sizing decisions simulées
- Risk approval evidence
- Kill-switch tests
- Rapport de clôture V7_MODEL_RISK_SIZING

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- No position without risk approval
- `Default sizing=0`

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
