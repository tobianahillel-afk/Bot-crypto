# V20 — Options Context

Identifiant : `V20_OPTIONS_CONTEXT`

Plage canonique : **Lots 172 à 174**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Ajouter un contexte options avancé, optionnel et non exécutable.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 172 — Options Data & Contract Registry

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Options Data & Contract Registry » dans la phase Options Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Options data read-only/offline
- Underlying market context

### Exigences d’implémentation

- Normaliser contrats options, expiries, strikes et greeks.
- Calculer IV, skew, term structure et contextes d’expiration.
- Fusionner le contexte options sans générer de signal automatique.
- Documenter qualité, liquidité et limites des données.

### Artefacts attendus

- Options context state
- Volatility surface summaries
- Expiry risk reports

### Tests et critères d’acceptation

- Contract normalization
- No stale surface accepted
- No direct trade signal

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Options module optional and non-blocking for core roadmap

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 173 — Implied Volatility, Skew & Term Structure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Implied Volatility, Skew & Term Structure » dans la phase Options Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Options data read-only/offline
- Underlying market context

### Exigences d’implémentation

- Normaliser contrats options, expiries, strikes et greeks.
- Calculer IV, skew, term structure et contextes d’expiration.
- Fusionner le contexte options sans générer de signal automatique.
- Documenter qualité, liquidité et limites des données.

### Artefacts attendus

- Options context state
- Volatility surface summaries
- Expiry risk reports

### Tests et critères d’acceptation

- Contract normalization
- No stale surface accepted
- No direct trade signal

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Options module optional and non-blocking for core roadmap

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 174 — Expiry, Greeks, Context Fusion & V20 Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Expiry, Greeks, Context Fusion & V20 Closure » dans la phase Options Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Options data read-only/offline
- Underlying market context

### Exigences d’implémentation

- Normaliser contrats options, expiries, strikes et greeks.
- Calculer IV, skew, term structure et contextes d’expiration.
- Fusionner le contexte options sans générer de signal automatique.
- Documenter qualité, liquidité et limites des données.

### Artefacts attendus

- Options context state
- Volatility surface summaries
- Expiry risk reports
- Rapport de clôture V20_OPTIONS_CONTEXT

### Tests et critères d’acceptation

- Contract normalization
- No stale surface accepted
- No direct trade signal
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Options module optional and non-blocking for core roadmap

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
