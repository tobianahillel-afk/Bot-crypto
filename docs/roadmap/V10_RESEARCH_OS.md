# V10 — Research OS

Identifiant : `V10_RESEARCH_OS`

Plage canonique : **Lots 96 à 102**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Tracer expériences, versions, hypothèses, résultats et gouvernance de recherche.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 96 — Research OS Foundation

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Research OS Foundation » dans la phase Research OS avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- All research artifacts
- Registries
- Git commit/config checksums

### Exigences d’implémentation

- Versionner expériences, hypothèses, datasets, features, configs et résultats.
- Tracer lineage et statut de promotion des stratégies.
- Gérer ablations, placebos, OOS et résultats négatifs.
- Générer des rapports reproductibles et une base de connaissances.
- Interdire la suppression silencieuse des expériences défavorables.

### Artefacts attendus

- Experiment registry
- Knowledge base
- Research reports
- Governance audit

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Research metadata cannot alter runtime permissions

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 97 — Experiment Registry

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Experiment Registry » dans la phase Research OS avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- All research artifacts
- Registries
- Git commit/config checksums

### Exigences d’implémentation

- Versionner expériences, hypothèses, datasets, features, configs et résultats.
- Tracer lineage et statut de promotion des stratégies.
- Gérer ablations, placebos, OOS et résultats négatifs.
- Générer des rapports reproductibles et une base de connaissances.
- Interdire la suppression silencieuse des expériences défavorables.

### Artefacts attendus

- Experiment registry
- Knowledge base
- Research reports
- Governance audit

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Research metadata cannot alter runtime permissions

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 98 — Dataset, Feature & Configuration Versioning

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Dataset, Feature & Configuration Versioning » dans la phase Research OS avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- All research artifacts
- Registries
- Git commit/config checksums

### Exigences d’implémentation

- Versionner expériences, hypothèses, datasets, features, configs et résultats.
- Tracer lineage et statut de promotion des stratégies.
- Gérer ablations, placebos, OOS et résultats négatifs.
- Générer des rapports reproductibles et une base de connaissances.
- Interdire la suppression silencieuse des expériences défavorables.

### Artefacts attendus

- Experiment registry
- Knowledge base
- Research reports
- Governance audit

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Research metadata cannot alter runtime permissions

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 99 — Hypothesis & Strategy Lifecycle Governance

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Hypothesis & Strategy Lifecycle Governance » dans la phase Research OS avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- All research artifacts
- Registries
- Git commit/config checksums

### Exigences d’implémentation

- Versionner expériences, hypothèses, datasets, features, configs et résultats.
- Tracer lineage et statut de promotion des stratégies.
- Gérer ablations, placebos, OOS et résultats négatifs.
- Générer des rapports reproductibles et une base de connaissances.
- Interdire la suppression silencieuse des expériences défavorables.

### Artefacts attendus

- Experiment registry
- Knowledge base
- Research reports
- Governance audit

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Research metadata cannot alter runtime permissions

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 100 — Ablation, Placebo & OOS Tracking

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Ablation, Placebo & OOS Tracking » dans la phase Research OS avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- All research artifacts
- Registries
- Git commit/config checksums

### Exigences d’implémentation

- Versionner expériences, hypothèses, datasets, features, configs et résultats.
- Tracer lineage et statut de promotion des stratégies.
- Gérer ablations, placebos, OOS et résultats négatifs.
- Générer des rapports reproductibles et une base de connaissances.
- Interdire la suppression silencieuse des expériences défavorables.

### Artefacts attendus

- Experiment registry
- Knowledge base
- Research reports
- Governance audit

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Research metadata cannot alter runtime permissions

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 101 — Research Report Generator & Knowledge Base

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Research Report Generator & Knowledge Base » dans la phase Research OS avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- All research artifacts
- Registries
- Git commit/config checksums

### Exigences d’implémentation

- Versionner expériences, hypothèses, datasets, features, configs et résultats.
- Tracer lineage et statut de promotion des stratégies.
- Gérer ablations, placebos, OOS et résultats négatifs.
- Générer des rapports reproductibles et une base de connaissances.
- Interdire la suppression silencieuse des expériences défavorables.

### Artefacts attendus

- Experiment registry
- Knowledge base
- Research reports
- Governance audit

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Research metadata cannot alter runtime permissions

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 102 — V10 Research Governance & Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « V10 Research Governance & Closure » dans la phase Research OS avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- All research artifacts
- Registries
- Git commit/config checksums

### Exigences d’implémentation

- Versionner expériences, hypothèses, datasets, features, configs et résultats.
- Tracer lineage et statut de promotion des stratégies.
- Gérer ablations, placebos, OOS et résultats négatifs.
- Générer des rapports reproductibles et une base de connaissances.
- Interdire la suppression silencieuse des expériences défavorables.

### Artefacts attendus

- Experiment registry
- Knowledge base
- Research reports
- Governance audit
- Rapport de clôture V10_RESEARCH_OS

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Research metadata cannot alter runtime permissions

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
