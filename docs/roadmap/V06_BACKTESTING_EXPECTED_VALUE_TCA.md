# V6 — Backtesting / Expected Value / TCA

Identifiant : `V6_BACKTEST_EV_TCA`

Plage canonique : **Lots 60 à 71**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Évaluer les stratégies nettes de coûts avec validation temporelle et anti-overfitting.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 60 — Outcome Labeling & Event Definition

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Outcome Labeling & Event Definition » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 61 — Strategy Replay / Backtest Core

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Strategy Replay / Backtest Core » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 62 — Fees, Funding & Spread Cost Model

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Fees, Funding & Spread Cost Model » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 63 — Slippage & Market Impact Simulator

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Slippage & Market Impact Simulator » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 64 — Fill Probability, Queue Proxy & Capacity

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Fill Probability, Queue Proxy & Capacity » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 65 — Expected Value Net of Costs

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Expected Value Net of Costs » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 66 — Walk-Forward Validation

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Walk-Forward Validation » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 67 — Out-of-Sample, Purged CV & Embargo

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Out-of-Sample, Purged CV & Embargo » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 68 — Placebo, Randomization & Multiple-Testing Control

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Placebo, Randomization & Multiple-Testing Control » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 69 — Monte Carlo, Bootstrap & Parameter Sensitivity

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Monte Carlo, Bootstrap & Parameter Sensitivity » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 70 — Performance Attribution & Regime Split

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Performance Attribution & Regime Split » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 71 — Backtest Promotion Gate & V6 Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Backtest Promotion Gate & V6 Closure » dans la phase Backtesting / Expected Value / TCA avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Strategy candidates
- Datasets versionnés
- Cost models
- Instrument specifications

### Exigences d’implémentation

- Définir labels uniquement dans le contexte offline/backtest.
- Simuler fees, funding, spread, slippage, impact, fills et capacité.
- Calculer EV brut puis EV net de coûts.
- Appliquer walk-forward, OOS, purged CV, embargo, placebo et corrections multiple-testing.
- Produire attribution par régime, période et composant de coût.

### Artefacts attendus

- Backtest runs
- TCA reports
- Robustness reports
- Promotion gate evidence
- Rapport de clôture V6_BACKTEST_EV_TCA

### Tests et critères d’acceptation

- Aucun overlap train/test
- Fills réalistes
- Coûts non nuls
- Résultats reproductibles
- Baseline aléatoire comparée
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Backtest performance cannot authorize live
- Labels interdits hors offline

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
