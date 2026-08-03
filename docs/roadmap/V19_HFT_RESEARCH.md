# V19 — HFT Research

Identifiant : `V19_HFT_RESEARCH`

Plage canonique : **Lots 166 à 171**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Étudier la faisabilité HFT uniquement en recherche/simulation.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 166 — HFT Scope & Feasibility Reality Check

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « HFT Scope & Feasibility Reality Check » dans la phase HFT Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Tick/L2/L3 historical data
- Contract specs
- Latency assumptions

### Exigences d’implémentation

- Rester strictement research/simulation.
- Utiliser timestamps haute résolution et politiques clock explicites.
- Simuler matching engine, queue position, latency et message budget.
- Étudier market making, inventory risk, toxicity et adverse selection.
- Auditer réalisme des fills et conclure par un feasibility report.

### Artefacts attendus

- HFT simulator
- Queue/fill models
- Risk reports
- Feasibility conclusion

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `HFT_LIVE=FORBIDDEN`
- `research_only=true`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 167 — Tick / L2 / L3 Data & High-Resolution Time Policy

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Tick / L2 / L3 Data & High-Resolution Time Policy » dans la phase HFT Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Tick/L2/L3 historical data
- Contract specs
- Latency assumptions

### Exigences d’implémentation

- Rester strictement research/simulation.
- Utiliser timestamps haute résolution et politiques clock explicites.
- Simuler matching engine, queue position, latency et message budget.
- Étudier market making, inventory risk, toxicity et adverse selection.
- Auditer réalisme des fills et conclure par un feasibility report.

### Artefacts attendus

- HFT simulator
- Queue/fill models
- Risk reports
- Feasibility conclusion

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `HFT_LIVE=FORBIDDEN`
- `research_only=true`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 168 — Matching Engine & Queue-Position Simulator

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Matching Engine & Queue-Position Simulator » dans la phase HFT Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Tick/L2/L3 historical data
- Contract specs
- Latency assumptions

### Exigences d’implémentation

- Rester strictement research/simulation.
- Utiliser timestamps haute résolution et politiques clock explicites.
- Simuler matching engine, queue position, latency et message budget.
- Étudier market making, inventory risk, toxicity et adverse selection.
- Auditer réalisme des fills et conclure par un feasibility report.

### Artefacts attendus

- HFT simulator
- Queue/fill models
- Risk reports
- Feasibility conclusion

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `HFT_LIVE=FORBIDDEN`
- `research_only=true`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 169 — Low-Latency, Cancel/Replace & Message Budget

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Low-Latency, Cancel/Replace & Message Budget » dans la phase HFT Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Tick/L2/L3 historical data
- Contract specs
- Latency assumptions

### Exigences d’implémentation

- Rester strictement research/simulation.
- Utiliser timestamps haute résolution et politiques clock explicites.
- Simuler matching engine, queue position, latency et message budget.
- Étudier market making, inventory risk, toxicity et adverse selection.
- Auditer réalisme des fills et conclure par un feasibility report.

### Artefacts attendus

- HFT simulator
- Queue/fill models
- Risk reports
- Feasibility conclusion

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `HFT_LIVE=FORBIDDEN`
- `research_only=true`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 170 — Market Making, Inventory Risk & Adverse Selection

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Market Making, Inventory Risk & Adverse Selection » dans la phase HFT Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Tick/L2/L3 historical data
- Contract specs
- Latency assumptions

### Exigences d’implémentation

- Rester strictement research/simulation.
- Utiliser timestamps haute résolution et politiques clock explicites.
- Simuler matching engine, queue position, latency et message budget.
- Étudier market making, inventory risk, toxicity et adverse selection.
- Auditer réalisme des fills et conclure par un feasibility report.

### Artefacts attendus

- HFT simulator
- Queue/fill models
- Risk reports
- Feasibility conclusion

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `HFT_LIVE=FORBIDDEN`
- `research_only=true`

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 171 — HFT Replay, Risk Audit & Research Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « HFT Replay, Risk Audit & Research Closure » dans la phase HFT Research avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Tick/L2/L3 historical data
- Contract specs
- Latency assumptions

### Exigences d’implémentation

- Rester strictement research/simulation.
- Utiliser timestamps haute résolution et politiques clock explicites.
- Simuler matching engine, queue position, latency et message budget.
- Étudier market making, inventory risk, toxicity et adverse selection.
- Auditer réalisme des fills et conclure par un feasibility report.

### Artefacts attendus

- HFT simulator
- Queue/fill models
- Risk reports
- Feasibility conclusion
- Rapport de clôture V19_HFT_RESEARCH

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `HFT_LIVE=FORBIDDEN`
- `research_only=true`

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
