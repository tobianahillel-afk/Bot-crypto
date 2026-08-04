# V3 — Market Data Governance

Identifiant : `V3_MARKET_DATA_GOVERNANCE`  
Plage canonique : **Lots 31 à 36**  
Composant/domain owner : `MarketDataGovernanceDomain`  
Mode maximal autorisé : `DATA_GOVERNANCE_ONLY`

## Finalité de la version

Faire évoluer le système de **V2 fermée** vers **Data quality gate, instruments et temps canoniques**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- V2 fermée.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/data_governance`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 31 — Market Data Governance Scope & Source Registry

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `DATA_GOVERNANCE_ONLY`  
**Composant propriétaire :** `MarketDataGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/data_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Market Data Governance Scope & Source Registry » dans Market Data Governance, produire MarketDataGovernanceScopeSourceRegistryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MarketDataGovernanceScopeSourceRegistryStateV1
- MarketDataGovernanceScopeSourceRegistryAuditV1
- MarketDataGovernanceScopeSourceRegistryContractRegistryV1
- MarketDataGovernanceScopeSourceRegistryCapabilityMatrixV1
- SourceRegistryV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 31, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Market Data Governance Scope & Source Registry » dans le composant MarketDataGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir frontières, responsabilités, dépendances autorisées, modes runtime et API publiques du domaine.
6. Classer chaque capability en REQUIRED, OPTIONAL_RESEARCH, DISABLED ou FORBIDDEN.
7. Enregistrer source_id, provider, venue, endpoint/type, champs, cadence, timezone, licence, auth_mode, retention et criticité.
8. Définir source of truth, sources de secours et politique de révision.
9. Interdire toute source inconnue ou non approuvée dans une décision.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/data_governance/market_data_governance_scope_and_source_registry.py
- src/crypto_quant_bot/data_governance/market_data_governance_scope_and_source_registry_models.py
- scripts/run_lot31_market_data_governance_scope_and_source_registry.py
- scripts/validate_lot31.py
- tests/test_lot31_market_data_governance_scope_and_source_registry.py
- data/audit/market_data_governance_scope_and_source_registry_lot31.json
- reports/lot_31_market_data_governance_scope_and_source_registry_report.md
- docs/LOT_31_MARKET_DATA_GOVERNANCE_SCOPE_AND_SOURCE_REGISTRY.md
- docs/ACCEPTANCE_CRITERIA_LOT_31.md

### Observabilité minimale

- lot_31_records_processed_total
- lot_31_validation_failures_total
- lot_31_processing_latency_ms

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test de dépendances interdites entre domaines.
- Test de couverture : chaque capability a owner, contrat et gate.
- Source inconnue rejetée.
- Révision de source incrémente schema/config version.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas implémenter prématurément les algorithmes métier décrits par l’architecture.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING
- Aucune connectivité externe avant gate dédié

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 32 — Instrument, Symbol & Contract Normalization

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `DATA_GOVERNANCE_ONLY`  
**Composant propriétaire :** `MarketDataGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/data_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Instrument, Symbol & Contract Normalization » dans Market Data Governance, produire InstrumentSymbolContractNormalizationStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ExchangeInstrumentMetadataV1

### Contrats de sortie

- InstrumentSymbolContractNormalizationStateV1
- InstrumentSymbolContractNormalizationAuditV1
- InstrumentRegistryV1
- InstrumentSpecificationV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 32, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Instrument, Symbol & Contract Normalization » dans le composant MarketDataGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Normaliser venue, base, quote, market_type, canonical_symbol et exchange_symbol.
6. Modéliser spot, perpetual, dated future et option avec champs non applicables explicitement null/forbidden.
7. Valider tick_size, lot_size, min_qty, min_notional, price/qty precision, fee tier, settlement, margin et leverage policy.

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

- src/crypto_quant_bot/data_governance/instrument_symbol_and_contract_normalization.py
- src/crypto_quant_bot/data_governance/instrument_symbol_and_contract_normalization_models.py
- scripts/run_lot32_instrument_symbol_and_contract_normalization.py
- scripts/validate_lot32.py
- tests/test_lot32_instrument_symbol_and_contract_normalization.py
- data/audit/instrument_symbol_and_contract_normalization_lot32.json
- reports/lot_32_instrument_symbol_and_contract_normalization_report.md
- docs/LOT_32_INSTRUMENT_SYMBOL_AND_CONTRACT_NORMALIZATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_32.md

### Observabilité minimale

- lot_32_records_processed_total
- lot_32_validation_failures_total
- lot_32_processing_latency_ms

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Round-trip symbol canonical ↔ venue.
- Tests de quantization aux frontières tick/lot/min_notional.

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
- Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING
- Aucune connectivité externe avant gate dédié

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 33 — Timestamp, Clock & Timezone Governance

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `DATA_GOVERNANCE_ONLY`  
**Composant propriétaire :** `MarketDataGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/data_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Timestamp, Clock & Timezone Governance » dans Market Data Governance, produire TimestampClockTimezoneGovernanceStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- RawTimestampEnvelopeV1

### Contrats de sortie

- TimestampClockTimezoneGovernanceStateV1
- TimestampClockTimezoneGovernanceAuditV1
- CanonicalTimeEnvelopeV1
- ClockHealthStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 33, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Timestamp, Clock & Timezone Governance » dans le composant MarketDataGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver source_time, exchange_time, event_time, receive_time, process_time et monotonic_time selon disponibilité.
6. Convertir en UTC sans perdre la valeur brute ni la précision.
7. Mesurer clock drift, out-of-order delay et latency components.
8. Définir available_at/usable_from pour empêcher l’usage avant disponibilité.

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

- src/crypto_quant_bot/data_governance/timestamp_clock_and_timezone_governance.py
- src/crypto_quant_bot/data_governance/timestamp_clock_and_timezone_governance_models.py
- scripts/run_lot33_timestamp_clock_and_timezone_governance.py
- scripts/validate_lot33.py
- tests/test_lot33_timestamp_clock_and_timezone_governance.py
- data/audit/timestamp_clock_and_timezone_governance_lot33.json
- reports/lot_33_timestamp_clock_and_timezone_governance_report.md
- docs/LOT_33_TIMESTAMP_CLOCK_AND_TIMEZONE_GOVERNANCE.md
- docs/ACCEPTANCE_CRITERIA_LOT_33.md

### Observabilité minimale

- lot_33_records_processed_total
- lot_33_validation_failures_total
- lot_33_processing_latency_ms

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- DST/timezone boundary tests.
- Events hors ordre et timestamps identiques avec sequence_id.

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
- Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING
- Aucune connectivité externe avant gate dédié

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 34 — Market Data Quality Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `DATA_GOVERNANCE_ONLY`  
**Composant propriétaire :** `MarketDataGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/data_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Market Data Quality Engine » dans Market Data Governance, produire MarketDataQualityEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MarketDataQualityEngineStateV1
- MarketDataQualityEngineAuditV1
- DataQualityStateV1
- DataAnomalyV1
- DataQualityVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 34, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Market Data Quality Engine » dans le composant MarketDataGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Détecter missing intervals, duplicates, out-of-order, stale, invalid OHLC, negative volume, impossible spread et schema drift.
6. Calculer coverage, freshness, completeness, consistency et quality_score par source/instrument/timeframe.
7. Associer sévérité, intervalle affecté, correction permise et statut quarantined.
8. Appliquer data_quality_veto avant analyse, signal et ordre.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Qualité inconnue → BLOCK_ANALYSIS_OR_TRADING.
- Correction destructive de raw data → interdite.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/data_governance/market_data_quality_engine.py
- src/crypto_quant_bot/data_governance/market_data_quality_engine_models.py
- scripts/run_lot34_market_data_quality_engine.py
- scripts/validate_lot34.py
- tests/test_lot34_market_data_quality_engine.py
- data/audit/market_data_quality_engine_lot34.json
- reports/lot_34_market_data_quality_engine_report.md
- docs/LOT_34_MARKET_DATA_QUALITY_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_34.md

### Observabilité minimale

- lot_34_records_processed_total
- lot_34_validation_failures_total
- lot_34_processing_latency_ms

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Injection de chaque anomalie.
- Quarantaine sans modification des données raw.

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
- Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING
- Aucune connectivité externe avant gate dédié

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 35 — Candle / Trade / Book Reconciliation

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `DATA_GOVERNANCE_ONLY`  
**Composant propriétaire :** `MarketDataGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/data_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Candle / Trade / Book Reconciliation » dans Market Data Governance, produire CandleTradeBookReconciliationStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- CandleTradeBookReconciliationStateV1
- CandleTradeBookReconciliationAuditV1
- ReconciliationReportV1
- ReconciliationVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 35, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Candle / Trade / Book Reconciliation » dans le composant MarketDataGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Comparer identifiants, quantités, prix, frais, balances, positions et timestamps entre les deux sources concernées.
6. Classer MATCH, TOLERATED_DIFF, MINOR_DIVERGENCE, CRITICAL_DIVERGENCE.
7. Produire delta exact, tolérance versionnée, source de vérité et action corrective.
8. MINOR → PAUSE ; CRITICAL/unknown ownership → KILL_SWITCH ou BLOCK_TRADING selon matrice.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Élément orphelin ou duplicate → RECONCILIATION_REQUIRED.
- Différence de frais non expliquée → PAUSE.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/data_governance/candle_trade_book_reconciliation.py
- src/crypto_quant_bot/data_governance/candle_trade_book_reconciliation_models.py
- scripts/run_lot35_candle_trade_book_reconciliation.py
- scripts/validate_lot35.py
- tests/test_lot35_candle_trade_book_reconciliation.py
- data/audit/candle_trade_book_reconciliation_lot35.json
- reports/lot_35_candle_trade_book_reconciliation_report.md
- docs/LOT_35_CANDLE_TRADE_BOOK_RECONCILIATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_35.md

### Observabilité minimale

- lot_35_records_processed_total
- lot_35_validation_failures_total
- lot_35_processing_latency_ms

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Ordre/fill/balance/frais divergents injectés.
- Reconciliation idempotente après restart.

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
- Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING
- Aucune connectivité externe avant gate dédié

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 36 — Freshness, Gap, Outage Audit & V3 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `DATA_GOVERNANCE_ONLY`  
**Composant propriétaire :** `MarketDataGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/data_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Freshness, Gap, Outage Audit & V3 Closure » dans Market Data Governance, produire FreshnessGapOutageAuditV3ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- FreshnessGapOutageAuditV3ClosureStateV1
- FreshnessGapOutageAuditV3ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- DataQualityStateV1
- DataAnomalyV1
- DataQualityVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 36, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Freshness, Gap, Outage Audit & V3 Closure » dans le composant MarketDataGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Détecter missing intervals, duplicates, out-of-order, stale, invalid OHLC, negative volume, impossible spread et schema drift.
10. Calculer coverage, freshness, completeness, consistency et quality_score par source/instrument/timeframe.
11. Associer sévérité, intervalle affecté, correction permise et statut quarantined.
12. Appliquer data_quality_veto avant analyse, signal et ordre.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Checksum différent → NON_DETERMINISTIC_FAIL.
- Lot antérieur non PASS → closure refusée.
- Qualité inconnue → BLOCK_ANALYSIS_OR_TRADING.
- Correction destructive de raw data → interdite.

### Fichiers et artefacts d’implémentation attendus

- scripts/validate_all_until_lot36.py
- scripts/run_required_chain_until_lot36.sh
- scripts/diagnose_exact_chain_until_lot36.py
- tests/test_lot36_closure_contract.py
- data/audit/closure_manifest_lot36.json
- reports/lot_36_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_36.md
- src/crypto_quant_bot/data_governance/freshness_gap_outage_audit_and_v3_closure.py
- src/crypto_quant_bot/data_governance/freshness_gap_outage_audit_and_v3_closure_models.py
- scripts/run_lot36_freshness_gap_outage_audit_and_v3_closure.py
- scripts/validate_lot36.py
- tests/test_lot36_freshness_gap_outage_audit_and_v3_closure.py
- data/audit/freshness_gap_outage_audit_and_v3_closure_lot36.json
- reports/lot_36_freshness_gap_outage_audit_and_v3_closure_report.md
- docs/LOT_36_FRESHNESS_GAP_OUTAGE_AUDIT_AND_V3_CLOSURE.md

### Observabilité minimale

- lot_36_records_processed_total
- lot_36_validation_failures_total
- lot_36_processing_latency_ms

### Tests et critères d’acceptation

- Aucun timestamp ambigu
- Aucun symbole non normalisé
- Anomalies injectées détectées
- Reconstruction déterministe
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Injection de chaque anomalie.
- Quarantaine sans modification des données raw.

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
- Données insuffisantes => BLOCK_ANALYSIS_OR_TRADING
- Aucune connectivité externe avant gate dédié

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 31–36 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
