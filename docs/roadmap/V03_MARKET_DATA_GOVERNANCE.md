# V3 — Market Data Governance

Identifiant : `V3_MARKET_DATA_GOVERNANCE`

Plage canonique : **Lots 31 à 36**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Garantir qualité, normalisation, temporalité et provenance des données marché.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 31 — Market Data Governance Scope & Source Registry

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Market Data Governance Scope & Source Registry » dans la phase Market Data Governance avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Sources marché autorisées
- Métadonnées exchange
- Fixtures OHLCV/trades/book

### Exigences d’implémentation

- Définir des contrats canoniques pour sources, instruments, timestamps et qualité.
- Conserver event_time, receive_time, process_time et source_time lorsque disponibles.
- Détecter données manquantes, dupliquées, obsolètes, hors ordre ou incohérentes.
- Réconcilier candles, trades et books avec tolérances documentées.
- Produire un score de qualité, une liste d’anomalies et un veto data_quality.

### Artefacts attendus

- Source registry
- Instrument registry
- Data quality reports
- Gap/outage/freshness evidence

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING`
- Aucune connectivité externe avant gate dédié

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 32 — Instrument, Symbol & Contract Normalization

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Instrument, Symbol & Contract Normalization » dans la phase Market Data Governance avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Sources marché autorisées
- Métadonnées exchange
- Fixtures OHLCV/trades/book

### Exigences d’implémentation

- Définir des contrats canoniques pour sources, instruments, timestamps et qualité.
- Conserver event_time, receive_time, process_time et source_time lorsque disponibles.
- Détecter données manquantes, dupliquées, obsolètes, hors ordre ou incohérentes.
- Réconcilier candles, trades et books avec tolérances documentées.
- Produire un score de qualité, une liste d’anomalies et un veto data_quality.

### Artefacts attendus

- Source registry
- Instrument registry
- Data quality reports
- Gap/outage/freshness evidence

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING`
- Aucune connectivité externe avant gate dédié

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 33 — Timestamp, Clock & Timezone Governance

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Timestamp, Clock & Timezone Governance » dans la phase Market Data Governance avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Sources marché autorisées
- Métadonnées exchange
- Fixtures OHLCV/trades/book

### Exigences d’implémentation

- Définir des contrats canoniques pour sources, instruments, timestamps et qualité.
- Conserver event_time, receive_time, process_time et source_time lorsque disponibles.
- Détecter données manquantes, dupliquées, obsolètes, hors ordre ou incohérentes.
- Réconcilier candles, trades et books avec tolérances documentées.
- Produire un score de qualité, une liste d’anomalies et un veto data_quality.

### Artefacts attendus

- Source registry
- Instrument registry
- Data quality reports
- Gap/outage/freshness evidence

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING`
- Aucune connectivité externe avant gate dédié

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 34 — Market Data Quality Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Market Data Quality Engine » dans la phase Market Data Governance avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Sources marché autorisées
- Métadonnées exchange
- Fixtures OHLCV/trades/book

### Exigences d’implémentation

- Définir des contrats canoniques pour sources, instruments, timestamps et qualité.
- Conserver event_time, receive_time, process_time et source_time lorsque disponibles.
- Détecter données manquantes, dupliquées, obsolètes, hors ordre ou incohérentes.
- Réconcilier candles, trades et books avec tolérances documentées.
- Produire un score de qualité, une liste d’anomalies et un veto data_quality.

### Artefacts attendus

- Source registry
- Instrument registry
- Data quality reports
- Gap/outage/freshness evidence

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING`
- Aucune connectivité externe avant gate dédié

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 35 — Candle / Trade / Book Reconciliation

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Candle / Trade / Book Reconciliation » dans la phase Market Data Governance avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Sources marché autorisées
- Métadonnées exchange
- Fixtures OHLCV/trades/book

### Exigences d’implémentation

- Définir des contrats canoniques pour sources, instruments, timestamps et qualité.
- Conserver event_time, receive_time, process_time et source_time lorsque disponibles.
- Détecter données manquantes, dupliquées, obsolètes, hors ordre ou incohérentes.
- Réconcilier candles, trades et books avec tolérances documentées.
- Produire un score de qualité, une liste d’anomalies et un veto data_quality.

### Artefacts attendus

- Source registry
- Instrument registry
- Data quality reports
- Gap/outage/freshness evidence

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING`
- Aucune connectivité externe avant gate dédié

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 36 — Freshness, Gap, Outage Audit & V3 Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Freshness, Gap, Outage Audit & V3 Closure » dans la phase Market Data Governance avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Sources marché autorisées
- Métadonnées exchange
- Fixtures OHLCV/trades/book

### Exigences d’implémentation

- Définir des contrats canoniques pour sources, instruments, timestamps et qualité.
- Conserver event_time, receive_time, process_time et source_time lorsque disponibles.
- Détecter données manquantes, dupliquées, obsolètes, hors ordre ou incohérentes.
- Réconcilier candles, trades et books avec tolérances documentées.
- Produire un score de qualité, une liste d’anomalies et un veto data_quality.

### Artefacts attendus

- Source registry
- Instrument registry
- Data quality reports
- Gap/outage/freshness evidence
- Rapport de clôture V3_MARKET_DATA_GOVERNANCE

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING`
- Aucune connectivité externe avant gate dédié

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
