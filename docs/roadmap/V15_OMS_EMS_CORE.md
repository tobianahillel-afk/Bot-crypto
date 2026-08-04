# V15 — OMS / EMS Core

Identifiant : `V15_OMS_EMS`  
Plage canonique : **Lots 133 à 141**  
Composant/domain owner : `OrderExecutionDomain`  
Mode maximal autorisé : `ORDER_MANAGEMENT_CORE`

## Finalité de la version

Faire évoluer le système de **OrderIntent risk-approved et contrats instrument** vers **Lifecycle ordre idempotent et réconciliable**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- OrderIntent risk-approved et contrats instrument.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/execution`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 133 — OMS / EMS Architecture & Contracts

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ORDER_MANAGEMENT_CORE`  
**Composant propriétaire :** `OrderExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/execution`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « OMS / EMS Architecture & Contracts » dans OMS / EMS Core, produire OMSEMSArchitectureContractsStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- OMSEMSArchitectureContractsStateV1
- OMSEMSArchitectureContractsAuditV1
- OMSEMSArchitectureContractsContractRegistryV1
- OMSEMSArchitectureContractsCapabilityMatrixV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 133, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « OMS / EMS Architecture & Contracts » dans le composant OrderExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir frontières, responsabilités, dépendances autorisées, modes runtime et API publiques du domaine.
6. Classer chaque capability en REQUIRED, OPTIONAL_RESEARCH, DISABLED ou FORBIDDEN.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/execution/oms_ems_architecture_and_contracts.py
- src/crypto_quant_bot/execution/oms_ems_architecture_and_contracts_models.py
- scripts/run_lot133_oms_ems_architecture_and_contracts.py
- scripts/validate_lot133.py
- tests/test_lot133_oms_ems_architecture_and_contracts.py
- data/audit/oms_ems_architecture_and_contracts_lot133.json
- reports/lot_133_oms_ems_architecture_and_contracts_report.md
- docs/LOT_133_OMS_EMS_ARCHITECTURE_AND_CONTRACTS.md
- docs/ACCEPTANCE_CRITERIA_LOT_133.md

### Observabilité minimale

- lot_133_records_processed_total
- lot_133_validation_failures_total
- lot_133_processing_latency_ms

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test de dépendances interdites entre domaines.
- Test de couverture : chaque capability a owner, contrat et gate.

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
- OMS cannot accept unapproved intent
- Retry bounded

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 134 — Order State Machine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ORDER_MANAGEMENT_CORE`  
**Composant propriétaire :** `OrderExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/execution`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Order State Machine » dans OMS / EMS Core, produire OrderStateMachineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- OrderStateMachineStateV1
- OrderStateMachineAuditV1
- OMSOrderStateV1
- OrderTransitionEventV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 134, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Order State Machine » dans le composant OrderExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Implémenter états RECEIVED, VALIDATED, REJECTED, PENDING_SUBMIT, SUBMITTED, ACKNOWLEDGED, PARTIALLY_FILLED, FILLED, CANCEL_PENDING, CANCELED, REPLACE_PENDING, EXPIRED, UNKNOWN, RECONCILIATION_REQUIRED.
6. Autoriser uniquement transitions listées dans une table versionnée.
7. Chaque transition porte event_id, previous_state, new_state, source et causal_event_id.
8. UNKNOWN/RECONCILIATION_REQUIRED interdit nouvelle action sauf cancel/reconcile policy.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/execution/order_state_machine.py
- src/crypto_quant_bot/execution/order_state_machine_models.py
- scripts/run_lot134_order_state_machine.py
- scripts/validate_lot134.py
- tests/test_lot134_order_state_machine.py
- data/audit/order_state_machine_lot134.json
- reports/lot_134_order_state_machine_report.md
- docs/LOT_134_ORDER_STATE_MACHINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_134.md

### Observabilité minimale

- lot_134_records_processed_total
- lot_134_validation_failures_total
- lot_134_processing_latency_ms

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Toutes transitions valides et invalides couvertes.
- Events dupliqués idempotents.

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
- OMS cannot accept unapproved intent
- Retry bounded

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 135 — Client Order IDs, Idempotency & Duplicate Prevention

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ORDER_MANAGEMENT_CORE`  
**Composant propriétaire :** `OrderExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/execution`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Client Order IDs, Idempotency & Duplicate Prevention » dans OMS / EMS Core, produire ClientOrderIDsIdempotencyDuplicatePreventionStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ClientOrderIDsIdempotencyDuplicatePreventionStateV1
- ClientOrderIDsIdempotencyDuplicatePreventionAuditV1
- IdempotencyRecordV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 135, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Client Order IDs, Idempotency & Duplicate Prevention » dans le composant OrderExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Construire client_order_id déterministe depuis account/strategy/intent/version/attempt.
6. Stocker mapping avant soumission via transaction durable.
7. Une même idempotency_key retourne le même résultat ou conflit explicite.
8. Interdire retry aveugle si submit outcome UNKNOWN.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/execution/client_order_ids_idempotency_and_duplicate_prevention.py
- src/crypto_quant_bot/execution/client_order_ids_idempotency_and_duplicate_prevention_models.py
- scripts/run_lot135_client_order_ids_idempotency_and_duplicate_prevention.py
- scripts/validate_lot135.py
- tests/test_lot135_client_order_ids_idempotency_and_duplicate_prevention.py
- data/audit/client_order_ids_idempotency_and_duplicate_prevention_lot135.json
- reports/lot_135_client_order_ids_idempotency_and_duplicate_prevention_report.md
- docs/LOT_135_CLIENT_ORDER_IDS_IDEMPOTENCY_AND_DUPLICATE_PREVENTION.md
- docs/ACCEPTANCE_CRITERIA_LOT_135.md

### Observabilité minimale

- lot_135_records_processed_total
- lot_135_validation_failures_total
- lot_135_processing_latency_ms

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Concurrent duplicate submits.
- Crash entre persist et submit.
- Timeout après submit puis reconciliation.

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
- OMS cannot accept unapproved intent
- Retry bounded

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 136 — Order Validation & Contract Specification Rules

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ORDER_MANAGEMENT_CORE`  
**Composant propriétaire :** `OrderExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/execution`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Order Validation & Contract Specification Rules » dans OMS / EMS Core, produire OrderValidationContractSpecificationRulesStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ExchangeInstrumentMetadataV1
- InstrumentRegistryV1 produit par V3
- InstrumentSpecificationV1 produit par V3

### Contrats de sortie

- OrderValidationContractSpecificationRulesStateV1
- OrderValidationContractSpecificationRulesAuditV1
- OrderValidationResultV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 136, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Order Validation & Contract Specification Rules » dans le composant OrderExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Normaliser venue, base, quote, market_type, canonical_symbol et exchange_symbol.
6. Modéliser spot, perpetual, dated future et option avec champs non applicables explicitement null/forbidden.
7. Valider tick_size, lot_size, min_qty, min_notional, price/qty precision, fee tier, settlement, margin et leverage policy.
8. Valider approval hash, expiry, runtime mode, venue/symbol availability, side/type/TIF et instrument rules.
9. Quantize price/qty puis recalculer notional/risk.
10. Valider post-only, reduce-only et margin/leverage policy.
11. Retourner erreurs structurées ; ne jamais corriger silencieusement side/size.

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

- src/crypto_quant_bot/execution/order_validation_and_contract_specification_rules.py
- src/crypto_quant_bot/execution/order_validation_and_contract_specification_rules_models.py
- scripts/run_lot136_order_validation_and_contract_specification_rules.py
- scripts/validate_lot136.py
- tests/test_lot136_order_validation_and_contract_specification_rules.py
- data/audit/order_validation_and_contract_specification_rules_lot136.json
- reports/lot_136_order_validation_and_contract_specification_rules_report.md
- docs/LOT_136_ORDER_VALIDATION_AND_CONTRACT_SPECIFICATION_RULES.md
- docs/ACCEPTANCE_CRITERIA_LOT_136.md

### Observabilité minimale

- lot_136_records_processed_total
- lot_136_validation_failures_total
- lot_136_processing_latency_ms

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Round-trip symbol canonical ↔ venue.
- Tests de quantization aux frontières tick/lot/min_notional.
- Boundary tick/lot/min_notional.
- OrderIntent expiré/revoked.
- Leverage/futures interdits dans scope initial.

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
- OMS cannot accept unapproved intent
- Retry bounded

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 137 — Reject, Retry, Rate-Limit & Backoff Handling

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ORDER_MANAGEMENT_CORE`  
**Composant propriétaire :** `OrderExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/execution`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Reject, Retry, Rate-Limit & Backoff Handling » dans OMS / EMS Core, produire RejectRetryRateLimitBackoffHandlingStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- RejectRetryRateLimitBackoffHandlingStateV1
- RejectRetryRateLimitBackoffHandlingAuditV1
- ExecutionRetryStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 137, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Reject, Retry, Rate-Limit & Backoff Handling » dans le composant OrderExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Classifier reject permanent, transient, rate-limit, auth, instrument, risk ou unknown.
6. Retry uniquement classes autorisées avec max_attempts, exponential backoff+jitter et deadline.
7. Revalidation risk/instrument avant chaque retry.
8. Unknown submit outcome passe en reconciliation, jamais retry direct.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/execution/reject_retry_rate_limit_and_backoff_handling.py
- src/crypto_quant_bot/execution/reject_retry_rate_limit_and_backoff_handling_models.py
- scripts/run_lot137_reject_retry_rate_limit_and_backoff_handling.py
- scripts/validate_lot137.py
- tests/test_lot137_reject_retry_rate_limit_and_backoff_handling.py
- data/audit/reject_retry_rate_limit_and_backoff_handling_lot137.json
- reports/lot_137_reject_retry_rate_limit_and_backoff_handling_report.md
- docs/LOT_137_REJECT_RETRY_RATE_LIMIT_AND_BACKOFF_HANDLING.md
- docs/ACCEPTANCE_CRITERIA_LOT_137.md

### Observabilité minimale

- lot_137_records_processed_total
- lot_137_validation_failures_total
- lot_137_processing_latency_ms

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Retry budget exhaust.
- 429 Retry-After respecté.
- Permanent reject jamais retry.

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
- OMS cannot accept unapproved intent
- Retry bounded

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 138 — Partial Fills, Average Price & Residual Quantity

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ORDER_MANAGEMENT_CORE`  
**Composant propriétaire :** `OrderExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/execution`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Partial Fills, Average Price & Residual Quantity » dans OMS / EMS Core, produire PartialFillsAveragePriceResidualQuantityStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- PartialFillsAveragePriceResidualQuantityStateV1
- PartialFillsAveragePriceResidualQuantityAuditV1
- FillAggregateStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 138, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Partial Fills, Average Price & Residual Quantity » dans le composant OrderExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Dédupliquer fills par venue_fill_id.
6. Mettre à jour cumulative_qty, leaves_qty, weighted_avg_price, fees et last_fill_time.
7. Valider cumulative_qty <= order_qty avec tolérance precision.
8. Appliquer residual policy cancel/leave/replace uniquement après risk recheck.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/execution/partial_fills_average_price_and_residual_quantity.py
- src/crypto_quant_bot/execution/partial_fills_average_price_and_residual_quantity_models.py
- scripts/run_lot138_partial_fills_average_price_and_residual_quantity.py
- scripts/validate_lot138.py
- tests/test_lot138_partial_fills_average_price_and_residual_quantity.py
- data/audit/partial_fills_average_price_and_residual_quantity_lot138.json
- reports/lot_138_partial_fills_average_price_and_residual_quantity_report.md
- docs/LOT_138_PARTIAL_FILLS_AVERAGE_PRICE_AND_RESIDUAL_QUANTITY.md
- docs/ACCEPTANCE_CRITERIA_LOT_138.md

### Observabilité minimale

- lot_138_records_processed_total
- lot_138_validation_failures_total
- lot_138_processing_latency_ms

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Fills hors ordre/dupliqués.
- Overfill déclenche incident critique.

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
- OMS cannot accept unapproved intent
- Retry bounded

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 139 — Cancel / Replace & Race-Condition Handling

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ORDER_MANAGEMENT_CORE`  
**Composant propriétaire :** `OrderExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/execution`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Cancel / Replace & Race-Condition Handling » dans OMS / EMS Core, produire CancelReplaceRaceConditionHandlingStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- CancelReplaceRaceConditionHandlingStateV1
- CancelReplaceRaceConditionHandlingAuditV1
- CancelReplaceStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 139, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Cancel / Replace & Race-Condition Handling » dans le composant OrderExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Modéliser race fill-vs-cancel et ack-vs-timeout.
6. Replace = cancel+new order ou native amend selon venue contract, avec lineage entre versions.
7. Ne jamais supposer cancel réussi sans ack/reconciliation.
8. Recalculer risk sur residual/new parameters.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/execution/cancel_replace_and_race_condition_handling.py
- src/crypto_quant_bot/execution/cancel_replace_and_race_condition_handling_models.py
- scripts/run_lot139_cancel_replace_and_race_condition_handling.py
- scripts/validate_lot139.py
- tests/test_lot139_cancel_replace_and_race_condition_handling.py
- data/audit/cancel_replace_and_race_condition_handling_lot139.json
- reports/lot_139_cancel_replace_and_race_condition_handling_report.md
- docs/LOT_139_CANCEL_REPLACE_AND_RACE_CONDITION_HANDLING.md
- docs/ACCEPTANCE_CRITERIA_LOT_139.md

### Observabilité minimale

- lot_139_records_processed_total
- lot_139_validation_failures_total
- lot_139_processing_latency_ms

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Fill pendant cancel pending.
- Late ack et duplicate cancel.
- Replace ne crée pas double exposure.

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
- OMS cannot accept unapproved intent
- Retry bounded

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 140 — Orphan Order Reconciliation & Crash Recovery

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ORDER_MANAGEMENT_CORE`  
**Composant propriétaire :** `OrderExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/execution`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Orphan Order Reconciliation & Crash Recovery » dans OMS / EMS Core, produire OrphanOrderReconciliationCrashRecoveryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- OrphanOrderReconciliationCrashRecoveryStateV1
- OrphanOrderReconciliationCrashRecoveryAuditV1
- ReconciliationReportV1
- ReconciliationVetoV1
- RecoveryReconciliationStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 140, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Orphan Order Reconciliation & Crash Recovery » dans le composant OrderExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Comparer identifiants, quantités, prix, frais, balances, positions et timestamps entre les deux sources concernées.
6. Classer MATCH, TOLERATED_DIFF, MINOR_DIVERGENCE, CRITICAL_DIVERGENCE.
7. Produire delta exact, tolérance versionnée, source de vérité et action corrective.
8. MINOR → PAUSE ; CRITICAL/unknown ownership → KILL_SWITCH ou BLOCK_TRADING selon matrice.
9. Au startup, charger ledger durable puis interroger open orders/fills/balances selon mode.
10. Identifier local-only, venue-only et state-mismatch.
11. Geler nouvelles soumissions jusqu’à reconciliation clean.
12. Appliquer compensation explicite, jamais suppression d’historique.

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

- src/crypto_quant_bot/execution/orphan_order_reconciliation_and_crash_recovery.py
- src/crypto_quant_bot/execution/orphan_order_reconciliation_and_crash_recovery_models.py
- scripts/run_lot140_orphan_order_reconciliation_and_crash_recovery.py
- scripts/validate_lot140.py
- tests/test_lot140_orphan_order_reconciliation_and_crash_recovery.py
- data/audit/orphan_order_reconciliation_and_crash_recovery_lot140.json
- reports/lot_140_orphan_order_reconciliation_and_crash_recovery_report.md
- docs/LOT_140_ORPHAN_ORDER_RECONCILIATION_AND_CRASH_RECOVERY.md
- docs/ACCEPTANCE_CRITERIA_LOT_140.md

### Observabilité minimale

- lot_140_records_processed_total
- lot_140_validation_failures_total
- lot_140_processing_latency_ms

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Ordre/fill/balance/frais divergents injectés.
- Reconciliation idempotente après restart.
- Crash aux points persist/submit/ack/fill.
- Venue-only order déclenche policy orpheline.

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
- OMS cannot accept unapproved intent
- Retry bounded

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 141 — OMS / EMS Replay, Audit & V15 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ORDER_MANAGEMENT_CORE`  
**Composant propriétaire :** `OrderExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/execution`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « OMS / EMS Replay, Audit & V15 Closure » dans OMS / EMS Core, produire OMSEMSReplayAuditV15ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- OMSEMSReplayAuditV15ClosureStateV1
- OMSEMSReplayAuditV15ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 141, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « OMS / EMS Replay, Audit & V15 Closure » dans le composant OrderExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.

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

- scripts/validate_all_until_lot141.py
- scripts/run_required_chain_until_lot141.sh
- scripts/diagnose_exact_chain_until_lot141.py
- tests/test_lot141_closure_contract.py
- data/audit/closure_manifest_lot141.json
- reports/lot_141_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_141.md
- src/crypto_quant_bot/execution/oms_ems_replay_audit_and_v15_closure.py
- src/crypto_quant_bot/execution/oms_ems_replay_audit_and_v15_closure_models.py
- scripts/run_lot141_oms_ems_replay_audit_and_v15_closure.py
- scripts/validate_lot141.py
- tests/test_lot141_oms_ems_replay_audit_and_v15_closure.py
- data/audit/oms_ems_replay_audit_and_v15_closure_lot141.json
- reports/lot_141_oms_ems_replay_audit_and_v15_closure_report.md
- docs/LOT_141_OMS_EMS_REPLAY_AUDIT_AND_V15_CLOSURE.md

### Observabilité minimale

- lot_141_records_processed_total
- lot_141_validation_failures_total
- lot_141_processing_latency_ms

### Tests et critères d’acceptation

- Transitions invalides rejetées
- Duplicate submit impossible
- Partial fill correct
- Crash recovery deterministic
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.

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
- OMS cannot accept unapproved intent
- Retry bounded

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 133–141 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
