# V14 — Exchange Risk / API Health

Identifiant : `V14_EXCHANGE_RISK`  
Plage canonique : **Lots 126 à 132**  
Composant/domain owner : `ExchangeRiskDomain`  
Mode maximal autorisé : `EXCHANGE_HEALTH_ONLY`

## Finalité de la version

Faire évoluer le système de **Connecteur read-only stable** vers **Vetos exchange et disponibilité audités**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Connecteur read-only stable.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/exchange_risk`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 126 — Exchange Risk Registry

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `EXCHANGE_HEALTH_ONLY`  
**Composant propriétaire :** `ExchangeRiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/exchange_risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Exchange Risk Registry » dans Exchange Risk / API Health, produire ExchangeRiskRegistryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ExchangeRiskRegistryStateV1
- ExchangeRiskRegistryAuditV1
- ExchangeHealthStateV1
- ExchangeRiskVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 126, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Exchange Risk Registry » dans le composant ExchangeRiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Mesurer REST/WS availability, error rate, latency, reconnects, sequence gaps, maintenance et symbol status.
6. Appliquer circuit breakers et backoff avec budgets bornés.
7. Définir source de vérité pour maintenance/halts.
8. Unknown venue state interdit tout nouvel ordre.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/exchange_risk/exchange_risk_registry.py
- src/crypto_quant_bot/exchange_risk/exchange_risk_registry_models.py
- scripts/run_lot126_exchange_risk_registry.py
- scripts/validate_lot126.py
- tests/test_lot126_exchange_risk_registry.py
- data/audit/exchange_risk_registry_lot126.json
- reports/lot_126_exchange_risk_registry_report.md
- docs/LOT_126_EXCHANGE_RISK_REGISTRY.md
- docs/ACCEPTANCE_CRITERIA_LOT_126.md

### Observabilité minimale

- lot_126_records_processed_total
- lot_126_validation_failures_total
- lot_126_processing_latency_ms

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Disconnect/429/5xx/maintenance injectés.
- Failover ne duplique ni ordre ni event.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Unknown exchange state => no new orders

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 127 — REST / WebSocket Health Monitor

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `EXCHANGE_HEALTH_ONLY`  
**Composant propriétaire :** `ExchangeRiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/exchange_risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « REST / WebSocket Health Monitor » dans Exchange Risk / API Health, produire RESTWebSocketHealthMonitorStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- RESTWebSocketHealthMonitorStateV1
- RESTWebSocketHealthMonitorAuditV1
- ExchangeHealthStateV1
- ExchangeRiskVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 127, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « REST / WebSocket Health Monitor » dans le composant ExchangeRiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Mesurer REST/WS availability, error rate, latency, reconnects, sequence gaps, maintenance et symbol status.
6. Appliquer circuit breakers et backoff avec budgets bornés.
7. Définir source de vérité pour maintenance/halts.
8. Unknown venue state interdit tout nouvel ordre.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/exchange_risk/rest_websocket_health_monitor.py
- src/crypto_quant_bot/exchange_risk/rest_websocket_health_monitor_models.py
- scripts/run_lot127_rest_websocket_health_monitor.py
- scripts/validate_lot127.py
- tests/test_lot127_rest_websocket_health_monitor.py
- data/audit/rest_websocket_health_monitor_lot127.json
- reports/lot_127_rest_websocket_health_monitor_report.md
- docs/LOT_127_REST_WEBSOCKET_HEALTH_MONITOR.md
- docs/ACCEPTANCE_CRITERIA_LOT_127.md

### Observabilité minimale

- lot_127_records_processed_total
- lot_127_validation_failures_total
- lot_127_processing_latency_ms

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Disconnect/429/5xx/maintenance injectés.
- Failover ne duplique ni ordre ni event.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Unknown exchange state => no new orders

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 128 — Market, Symbol & Instrument Availability

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `EXCHANGE_HEALTH_ONLY`  
**Composant propriétaire :** `ExchangeRiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/exchange_risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Market, Symbol & Instrument Availability » dans Exchange Risk / API Health, produire MarketSymbolInstrumentAvailabilityStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ExchangeInstrumentMetadataV1

### Contrats de sortie

- MarketSymbolInstrumentAvailabilityStateV1
- MarketSymbolInstrumentAvailabilityAuditV1
- InstrumentRegistryV1
- InstrumentSpecificationV1
- ExchangeHealthStateV1
- ExchangeRiskVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 128, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Market, Symbol & Instrument Availability » dans le composant ExchangeRiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Normaliser venue, base, quote, market_type, canonical_symbol et exchange_symbol.
6. Modéliser spot, perpetual, dated future et option avec champs non applicables explicitement null/forbidden.
7. Valider tick_size, lot_size, min_qty, min_notional, price/qty precision, fee tier, settlement, margin et leverage policy.
8. Mesurer REST/WS availability, error rate, latency, reconnects, sequence gaps, maintenance et symbol status.
9. Appliquer circuit breakers et backoff avec budgets bornés.
10. Définir source de vérité pour maintenance/halts.
11. Unknown venue state interdit tout nouvel ordre.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Métadonnée instrument ambiguë ou révisée → INSTRUMENT_FROZEN.
- Arrondi qui viole min_notional → order intent rejeté.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/exchange_risk/market_symbol_and_instrument_availability.py
- src/crypto_quant_bot/exchange_risk/market_symbol_and_instrument_availability_models.py
- scripts/run_lot128_market_symbol_and_instrument_availability.py
- scripts/validate_lot128.py
- tests/test_lot128_market_symbol_and_instrument_availability.py
- data/audit/market_symbol_and_instrument_availability_lot128.json
- reports/lot_128_market_symbol_and_instrument_availability_report.md
- docs/LOT_128_MARKET_SYMBOL_AND_INSTRUMENT_AVAILABILITY.md
- docs/ACCEPTANCE_CRITERIA_LOT_128.md

### Observabilité minimale

- lot_128_records_processed_total
- lot_128_validation_failures_total
- lot_128_processing_latency_ms

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Round-trip symbol canonical ↔ venue.
- Tests de quantization aux frontières tick/lot/min_notional.
- Disconnect/429/5xx/maintenance injectés.
- Failover ne duplique ni ordre ni event.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Unknown exchange state => no new orders

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 129 — Data Staleness, Clock Drift & Sequence Health

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `EXCHANGE_HEALTH_ONLY`  
**Composant propriétaire :** `ExchangeRiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/exchange_risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Data Staleness, Clock Drift & Sequence Health » dans Exchange Risk / API Health, produire DataStalenessClockDriftSequenceHealthStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- RawTimestampEnvelopeV1

### Contrats de sortie

- DataStalenessClockDriftSequenceHealthStateV1
- DataStalenessClockDriftSequenceHealthAuditV1
- CanonicalTimeEnvelopeV1
- ClockHealthStateV1
- StrategyHealthStateV1
- RetirementDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 129, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Data Staleness, Clock Drift & Sequence Health » dans le composant ExchangeRiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver source_time, exchange_time, event_time, receive_time, process_time et monotonic_time selon disponibilité.
6. Convertir en UTC sans perdre la valeur brute ni la précision.
7. Mesurer clock drift, out-of-order delay et latency components.
8. Définir available_at/usable_from pour empêcher l’usage avant disponibilité.
9. Comparer performance récente aux distributions backtest/paper approuvées.
10. Mesurer feature drift, prediction drift, calibration drift et cost drift.
11. Déclencher REVIEW, DE_RISK, PAUSE ou RETIRE selon politique ; jamais auto-scale-up.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Timezone naive → rejet.
- Clock drift au-delà du seuil versionné → DEGRADED/BLOCK_NEW_ACTIONS.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/exchange_risk/data_staleness_clock_drift_and_sequence_health.py
- src/crypto_quant_bot/exchange_risk/data_staleness_clock_drift_and_sequence_health_models.py
- scripts/run_lot129_data_staleness_clock_drift_and_sequence_health.py
- scripts/validate_lot129.py
- tests/test_lot129_data_staleness_clock_drift_and_sequence_health.py
- data/audit/data_staleness_clock_drift_and_sequence_health_lot129.json
- reports/lot_129_data_staleness_clock_drift_and_sequence_health_report.md
- docs/LOT_129_DATA_STALENESS_CLOCK_DRIFT_AND_SEQUENCE_HEALTH.md
- docs/ACCEPTANCE_CRITERIA_LOT_129.md

### Observabilité minimale

- lot_129_records_processed_total
- lot_129_validation_failures_total
- lot_129_processing_latency_ms

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- DST/timezone boundary tests.
- Events hors ordre et timestamps identiques avec sequence_id.
- Drift synthétique détecté.
- Retour à la normale ne réactive pas sans gate.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Unknown exchange state => no new orders

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 130 — Rate Limits, Maintenance & Failover

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `EXCHANGE_HEALTH_ONLY`  
**Composant propriétaire :** `ExchangeRiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/exchange_risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Rate Limits, Maintenance & Failover » dans Exchange Risk / API Health, produire RateLimitsMaintenanceFailoverStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- RateLimitsMaintenanceFailoverStateV1
- RateLimitsMaintenanceFailoverAuditV1
- ExchangeHealthStateV1
- ExchangeRiskVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 130, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Rate Limits, Maintenance & Failover » dans le composant ExchangeRiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Mesurer REST/WS availability, error rate, latency, reconnects, sequence gaps, maintenance et symbol status.
6. Appliquer circuit breakers et backoff avec budgets bornés.
7. Définir source de vérité pour maintenance/halts.
8. Unknown venue state interdit tout nouvel ordre.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/exchange_risk/rate_limits_maintenance_and_failover.py
- src/crypto_quant_bot/exchange_risk/rate_limits_maintenance_and_failover_models.py
- scripts/run_lot130_rate_limits_maintenance_and_failover.py
- scripts/validate_lot130.py
- tests/test_lot130_rate_limits_maintenance_and_failover.py
- data/audit/rate_limits_maintenance_and_failover_lot130.json
- reports/lot_130_rate_limits_maintenance_and_failover_report.md
- docs/LOT_130_RATE_LIMITS_MAINTENANCE_AND_FAILOVER.md
- docs/ACCEPTANCE_CRITERIA_LOT_130.md

### Observabilité minimale

- lot_130_records_processed_total
- lot_130_validation_failures_total
- lot_130_processing_latency_ms

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Disconnect/429/5xx/maintenance injectés.
- Failover ne duplique ni ordre ni event.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Unknown exchange state => no new orders

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 131 — Counterparty / Operational Risk Dashboard

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `EXCHANGE_HEALTH_ONLY`  
**Composant propriétaire :** `ExchangeRiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/exchange_risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Counterparty / Operational Risk Dashboard » dans Exchange Risk / API Health, produire CounterpartyOperationalRiskDashboardStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- CounterpartyOperationalRiskDashboardStateV1
- CounterpartyOperationalRiskDashboardAuditV1
- UIReadModelV1
- OperatorActionAuditV1
- ExchangeHealthStateV1
- ExchangeRiskVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 131, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Counterparty / Operational Risk Dashboard » dans le composant ExchangeRiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Consommer uniquement read models backend ; aucune logique de gate n’est réimplémentée côté UI.
6. Afficher freshness, uncertainty, veto, lineage et state version.
7. Contrôler RBAC et confirmation renforcée pour pause/kill/approval lorsque ces actions existent.
8. Conserver audit de chaque action opérateur et résultat backend.
9. Mesurer REST/WS availability, error rate, latency, reconnects, sequence gaps, maintenance et symbol status.
10. Appliquer circuit breakers et backoff avec budgets bornés.
11. Définir source de vérité pour maintenance/halts.
12. Unknown venue state interdit tout nouvel ordre.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/exchange_risk/counterparty_operational_risk_dashboard.py
- src/crypto_quant_bot/exchange_risk/counterparty_operational_risk_dashboard_models.py
- scripts/run_lot131_counterparty_operational_risk_dashboard.py
- scripts/validate_lot131.py
- tests/test_lot131_counterparty_operational_risk_dashboard.py
- data/audit/counterparty_operational_risk_dashboard_lot131.json
- reports/lot_131_counterparty_operational_risk_dashboard_report.md
- docs/LOT_131_COUNTERPARTY_OPERATIONAL_RISK_DASHBOARD.md
- docs/ACCEPTANCE_CRITERIA_LOT_131.md

### Observabilité minimale

- lot_131_records_processed_total
- lot_131_validation_failures_total
- lot_131_processing_latency_ms

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- UI ne peut appeler endpoint non autorisé.
- Stale state clairement visible.
- Keyboard/accessibility et permission matrix.
- Disconnect/429/5xx/maintenance injectés.
- Failover ne duplique ni ordre ni event.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Unknown exchange state => no new orders

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 132 — V14 Exchange Risk Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `EXCHANGE_HEALTH_ONLY`  
**Composant propriétaire :** `ExchangeRiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/exchange_risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « V14 Exchange Risk Closure » dans Exchange Risk / API Health, produire V14ExchangeRiskClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- V14ExchangeRiskClosureStateV1
- V14ExchangeRiskClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- ExchangeHealthStateV1
- ExchangeRiskVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 132, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « V14 Exchange Risk Closure » dans le composant ExchangeRiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Mesurer REST/WS availability, error rate, latency, reconnects, sequence gaps, maintenance et symbol status.
10. Appliquer circuit breakers et backoff avec budgets bornés.
11. Définir source de vérité pour maintenance/halts.
12. Unknown venue state interdit tout nouvel ordre.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Checksum différent → NON_DETERMINISTIC_FAIL.
- Lot antérieur non PASS → closure refusée.

### Fichiers et artefacts d’implémentation attendus

- scripts/validate_all_until_lot132.py
- scripts/run_required_chain_until_lot132.sh
- scripts/diagnose_exact_chain_until_lot132.py
- tests/test_lot132_closure_contract.py
- data/audit/closure_manifest_lot132.json
- reports/lot_132_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_132.md
- src/crypto_quant_bot/exchange_risk/v14_exchange_risk_closure.py
- src/crypto_quant_bot/exchange_risk/v14_exchange_risk_closure_models.py
- scripts/run_lot132_v14_exchange_risk_closure.py
- scripts/validate_lot132.py
- tests/test_lot132_v14_exchange_risk_closure.py
- data/audit/v14_exchange_risk_closure_lot132.json
- reports/lot_132_v14_exchange_risk_closure_report.md
- docs/LOT_132_V14_EXCHANGE_RISK_CLOSURE.md

### Observabilité minimale

- lot_132_records_processed_total
- lot_132_validation_failures_total
- lot_132_processing_latency_ms

### Tests et critères d’acceptation

- Disconnect injecté détecté
- Maintenance bloque intents
- Clock drift détecté
- Failover ne duplique pas
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Disconnect/429/5xx/maintenance injectés.
- Failover ne duplique ni ordre ni event.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Unknown exchange state => no new orders

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 126–132 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
