# V21 — On-chain / Flow Intelligence

Identifiant : `V21_ONCHAIN_FLOW`

Plage canonique : **Lots 175 à 177**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Ajouter un contexte on-chain fiable, auxiliaire, puis fermer la roadmap documentaire.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 175 — On-Chain Source Registry & Reliability

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « On-Chain Source Registry & Reliability » dans la phase On-chain / Flow Intelligence avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- On-chain data read-only/offline
- Market context
- Source reliability registry

### Exigences d’implémentation

- Enregistrer sources on-chain, délais, révisions et fiabilité.
- Construire contextes exchange flows, stablecoins, miners et whales.
- Détecter doublons, attribution incertaine et lags.
- Fusionner avec contexte marché comme information auxiliaire uniquement.

### Artefacts attendus

- On-chain context
- Flow reports
- Reliability evidence
- Fusion summary

### Tests et critères d’acceptation

- Provenance complete
- Lag visible
- No wallet attribution presented as certainty
- No direct signal

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- On-chain context cannot authorize trading alone

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 176 — Exchange, Stablecoin, Miner & Whale Flow Context

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Exchange, Stablecoin, Miner & Whale Flow Context » dans la phase On-chain / Flow Intelligence avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- On-chain data read-only/offline
- Market context
- Source reliability registry

### Exigences d’implémentation

- Enregistrer sources on-chain, délais, révisions et fiabilité.
- Construire contextes exchange flows, stablecoins, miners et whales.
- Détecter doublons, attribution incertaine et lags.
- Fusionner avec contexte marché comme information auxiliaire uniquement.

### Artefacts attendus

- On-chain context
- Flow reports
- Reliability evidence
- Fusion summary

### Tests et critères d’acceptation

- Provenance complete
- Lag visible
- No wallet attribution presented as certainty
- No direct signal

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- On-chain context cannot authorize trading alone

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 177 — On-Chain / Market Fusion & Final Roadmap Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « On-Chain / Market Fusion & Final Roadmap Closure » dans la phase On-chain / Flow Intelligence avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- On-chain data read-only/offline
- Market context
- Source reliability registry

### Exigences d’implémentation

- Enregistrer sources on-chain, délais, révisions et fiabilité.
- Construire contextes exchange flows, stablecoins, miners et whales.
- Détecter doublons, attribution incertaine et lags.
- Fusionner avec contexte marché comme information auxiliaire uniquement.

### Artefacts attendus

- On-chain context
- Flow reports
- Reliability evidence
- Fusion summary
- Rapport de clôture V21_ONCHAIN_FLOW
- Matrice finale V1→V21
- Registre des lots 0→177
- Liste des extensions optionnelles

### Tests et critères d’acceptation

- Provenance complete
- Lag visible
- No wallet attribution presented as certainty
- No direct signal
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- On-chain context cannot authorize trading alone

### Gate de promotion

Clôture documentaire de la roadmap ; aucune activation live/HFT implicite.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
