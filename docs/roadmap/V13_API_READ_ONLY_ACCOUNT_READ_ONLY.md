# V13 — API Read-Only / Account Read-Only

Identifiant : `V13_API_READ_ONLY`  
Plage canonique : **Lots 119 à 125**  
Composant/domain owner : `ReadOnlyConnectorDomain`  
Mode maximal autorisé : `READ_ONLY`

## Finalité de la version

Faire évoluer le système de **Politique secrets et permissions approuvée** vers **Snapshots compte read-only réconciliés**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Politique secrets et permissions approuvée.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/connectors`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 119 — API Read-Only Scope & Secrets Policy

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY`  
**Composant propriétaire :** `ReadOnlyConnectorDomain`  
**Frontière de code :** `src/crypto_quant_bot/connectors`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « API Read-Only Scope & Secrets Policy » dans API Read-Only / Account Read-Only, produire APIReadOnlyScopeSecretsPolicyStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- APIReadOnlyScopeSecretsPolicyStateV1
- APIReadOnlyScopeSecretsPolicyAuditV1
- APIReadOnlyScopeSecretsPolicyContractRegistryV1
- APIReadOnlyScopeSecretsPolicyCapabilityMatrixV1
- ReadOnlyAccountSnapshotV1
- PermissionAuditV1
- SecretReferenceV1
- PermissionPolicyV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 119, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « API Read-Only Scope & Secrets Policy » dans le composant ReadOnlyConnectorDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir frontières, responsabilités, dépendances autorisées, modes runtime et API publiques du domaine.
6. Classer chaque capability en REQUIRED, OPTIONAL_RESEARCH, DISABLED ou FORBIDDEN.
7. Autoriser uniquement endpoints GET/read ; bloquer au code et à la permission toute écriture/trade/withdrawal.
8. Paginer et dédupliquer histories via IDs venue.
9. Conserver request_time, venue_time, cursor et completeness.
10. Scanner permissions et faire échouer si trading/withdrawal présent.
11. Secrets uniquement via secret manager/environment injecté, jamais sérialisés.
12. Séparer keys read-only/sandbox/live et interdire withdrawal.
13. Documenter rotation, revocation, break-glass et audit access.
14. Redacter logs/errors automatiquement.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/connectors/api_read_only_scope_and_secrets_policy.py
- src/crypto_quant_bot/connectors/api_read_only_scope_and_secrets_policy_models.py
- scripts/run_lot119_api_read_only_scope_and_secrets_policy.py
- scripts/validate_lot119.py
- tests/test_lot119_api_read_only_scope_and_secrets_policy.py
- data/audit/api_read_only_scope_and_secrets_policy_lot119.json
- reports/lot_119_api_read_only_scope_and_secrets_policy_report.md
- docs/LOT_119_API_READ_ONLY_SCOPE_AND_SECRETS_POLICY.md
- docs/ACCEPTANCE_CRITERIA_LOT_119.md

### Observabilité minimale

- lot_119_records_processed_total
- lot_119_validation_failures_total
- lot_119_processing_latency_ms

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test de dépendances interdites entre domaines.
- Test de couverture : chaque capability a owner, contrat et gate.
- Mock POST/DELETE interdit.
- Clé avec withdrawal fait échouer startup.
- Pagination duplicate/missing page.
- Secret scanning fixtures.
- Rotation sans downtime ou mode paused.
- Permission excess détectée.

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
- withdrawal_permission=FORBIDDEN
- trading_permission=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 120 — Exchange Connector Read-Only

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY`  
**Composant propriétaire :** `ReadOnlyConnectorDomain`  
**Frontière de code :** `src/crypto_quant_bot/connectors`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Exchange Connector Read-Only » dans API Read-Only / Account Read-Only, produire ExchangeConnectorReadOnlyStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ExchangeConnectorReadOnlyStateV1
- ExchangeConnectorReadOnlyAuditV1
- ReadOnlyAccountSnapshotV1
- PermissionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 120, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Exchange Connector Read-Only » dans le composant ReadOnlyConnectorDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Autoriser uniquement endpoints GET/read ; bloquer au code et à la permission toute écriture/trade/withdrawal.
6. Paginer et dédupliquer histories via IDs venue.
7. Conserver request_time, venue_time, cursor et completeness.
8. Scanner permissions et faire échouer si trading/withdrawal présent.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/connectors/exchange_connector_read_only.py
- src/crypto_quant_bot/connectors/exchange_connector_read_only_models.py
- scripts/run_lot120_exchange_connector_read_only.py
- scripts/validate_lot120.py
- tests/test_lot120_exchange_connector_read_only.py
- data/audit/exchange_connector_read_only_lot120.json
- reports/lot_120_exchange_connector_read_only_report.md
- docs/LOT_120_EXCHANGE_CONNECTOR_READ_ONLY.md
- docs/ACCEPTANCE_CRITERIA_LOT_120.md

### Observabilité minimale

- lot_120_records_processed_total
- lot_120_validation_failures_total
- lot_120_processing_latency_ms

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Mock POST/DELETE interdit.
- Clé avec withdrawal fait échouer startup.
- Pagination duplicate/missing page.

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
- withdrawal_permission=FORBIDDEN
- trading_permission=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 121 — Balances, Positions & Account Snapshot

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY`  
**Composant propriétaire :** `ReadOnlyConnectorDomain`  
**Frontière de code :** `src/crypto_quant_bot/connectors`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Balances, Positions & Account Snapshot » dans API Read-Only / Account Read-Only, produire BalancesPositionsAccountSnapshotStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- BalancesPositionsAccountSnapshotStateV1
- BalancesPositionsAccountSnapshotAuditV1
- ReadOnlyAccountSnapshotV1
- PermissionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 121, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Balances, Positions & Account Snapshot » dans le composant ReadOnlyConnectorDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Autoriser uniquement endpoints GET/read ; bloquer au code et à la permission toute écriture/trade/withdrawal.
6. Paginer et dédupliquer histories via IDs venue.
7. Conserver request_time, venue_time, cursor et completeness.
8. Scanner permissions et faire échouer si trading/withdrawal présent.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/connectors/balances_positions_and_account_snapshot.py
- src/crypto_quant_bot/connectors/balances_positions_and_account_snapshot_models.py
- scripts/run_lot121_balances_positions_and_account_snapshot.py
- scripts/validate_lot121.py
- tests/test_lot121_balances_positions_and_account_snapshot.py
- data/audit/balances_positions_and_account_snapshot_lot121.json
- reports/lot_121_balances_positions_and_account_snapshot_report.md
- docs/LOT_121_BALANCES_POSITIONS_AND_ACCOUNT_SNAPSHOT.md
- docs/ACCEPTANCE_CRITERIA_LOT_121.md

### Observabilité minimale

- lot_121_records_processed_total
- lot_121_validation_failures_total
- lot_121_processing_latency_ms

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Mock POST/DELETE interdit.
- Clé avec withdrawal fait échouer startup.
- Pagination duplicate/missing page.

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
- withdrawal_permission=FORBIDDEN
- trading_permission=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 122 — Order, Trade & Funding History

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY`  
**Composant propriétaire :** `ReadOnlyConnectorDomain`  
**Frontière de code :** `src/crypto_quant_bot/connectors`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Order, Trade & Funding History » dans API Read-Only / Account Read-Only, produire OrderTradeFundingHistoryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- OrderTradeFundingHistoryStateV1
- OrderTradeFundingHistoryAuditV1
- DerivativesContextStateV1
- ReadOnlyAccountSnapshotV1
- PermissionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 122, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Order, Trade & Funding History » dans le composant ReadOnlyConnectorDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Normaliser OI, funding, mark/index, basis et liquidations par venue/contrat.
6. Aligner publication/effective_time et gérer révisions.
7. Calculer crowding, leverage build-up, squeeze/liquidation risk comme contexte probabiliste.
8. Interdire l’usage si spot/perp mapping ou notionals ne sont pas comparables.
9. Autoriser uniquement endpoints GET/read ; bloquer au code et à la permission toute écriture/trade/withdrawal.
10. Paginer et dédupliquer histories via IDs venue.
11. Conserver request_time, venue_time, cursor et completeness.
12. Scanner permissions et faire échouer si trading/withdrawal présent.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/connectors/order_trade_and_funding_history.py
- src/crypto_quant_bot/connectors/order_trade_and_funding_history_models.py
- scripts/run_lot122_order_trade_and_funding_history.py
- scripts/validate_lot122.py
- tests/test_lot122_order_trade_and_funding_history.py
- data/audit/order_trade_and_funding_history_lot122.json
- reports/lot_122_order_trade_and_funding_history_report.md
- docs/LOT_122_ORDER_TRADE_AND_FUNDING_HISTORY.md
- docs/ACCEPTANCE_CRITERIA_LOT_122.md

### Observabilité minimale

- lot_122_records_processed_total
- lot_122_validation_failures_total
- lot_122_processing_latency_ms

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Funding publication vs effective time.
- OI change sans prix/volume ne produit pas de scénario certain.
- Mock POST/DELETE interdit.
- Clé avec withdrawal fait échouer startup.
- Pagination duplicate/missing page.

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
- withdrawal_permission=FORBIDDEN
- trading_permission=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 123 — Read-Only Reconciliation Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY`  
**Composant propriétaire :** `ReadOnlyConnectorDomain`  
**Frontière de code :** `src/crypto_quant_bot/connectors`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Read-Only Reconciliation Engine » dans API Read-Only / Account Read-Only, produire ReadOnlyReconciliationEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ReadOnlyReconciliationEngineStateV1
- ReadOnlyReconciliationEngineAuditV1
- ReconciliationReportV1
- ReconciliationVetoV1
- ReadOnlyAccountSnapshotV1
- PermissionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 123, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Read-Only Reconciliation Engine » dans le composant ReadOnlyConnectorDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Comparer identifiants, quantités, prix, frais, balances, positions et timestamps entre les deux sources concernées.
6. Classer MATCH, TOLERATED_DIFF, MINOR_DIVERGENCE, CRITICAL_DIVERGENCE.
7. Produire delta exact, tolérance versionnée, source de vérité et action corrective.
8. MINOR → PAUSE ; CRITICAL/unknown ownership → KILL_SWITCH ou BLOCK_TRADING selon matrice.
9. Autoriser uniquement endpoints GET/read ; bloquer au code et à la permission toute écriture/trade/withdrawal.
10. Paginer et dédupliquer histories via IDs venue.
11. Conserver request_time, venue_time, cursor et completeness.
12. Scanner permissions et faire échouer si trading/withdrawal présent.

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

- src/crypto_quant_bot/connectors/read_only_reconciliation_engine.py
- src/crypto_quant_bot/connectors/read_only_reconciliation_engine_models.py
- scripts/run_lot123_read_only_reconciliation_engine.py
- scripts/validate_lot123.py
- tests/test_lot123_read_only_reconciliation_engine.py
- data/audit/read_only_reconciliation_engine_lot123.json
- reports/lot_123_read_only_reconciliation_engine_report.md
- docs/LOT_123_READ_ONLY_RECONCILIATION_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_123.md

### Observabilité minimale

- lot_123_records_processed_total
- lot_123_validation_failures_total
- lot_123_processing_latency_ms

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Ordre/fill/balance/frais divergents injectés.
- Reconciliation idempotente après restart.
- Mock POST/DELETE interdit.
- Clé avec withdrawal fait échouer startup.
- Pagination duplicate/missing page.

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
- withdrawal_permission=FORBIDDEN
- trading_permission=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 124 — Permission Scanner & Least-Privilege Audit

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY`  
**Composant propriétaire :** `ReadOnlyConnectorDomain`  
**Frontière de code :** `src/crypto_quant_bot/connectors`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Permission Scanner & Least-Privilege Audit » dans API Read-Only / Account Read-Only, produire PermissionScannerLeastPrivilegeAuditStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- PermissionScannerLeastPrivilegeAuditStateV1
- PermissionScannerLeastPrivilegeAuditAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- ReadOnlyAccountSnapshotV1
- PermissionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 124, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Permission Scanner & Least-Privilege Audit » dans le composant ReadOnlyConnectorDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Autoriser uniquement endpoints GET/read ; bloquer au code et à la permission toute écriture/trade/withdrawal.
10. Paginer et dédupliquer histories via IDs venue.
11. Conserver request_time, venue_time, cursor et completeness.
12. Scanner permissions et faire échouer si trading/withdrawal présent.

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

- src/crypto_quant_bot/connectors/permission_scanner_and_least_privilege_audit.py
- src/crypto_quant_bot/connectors/permission_scanner_and_least_privilege_audit_models.py
- scripts/run_lot124_permission_scanner_and_least_privilege_audit.py
- scripts/validate_lot124.py
- tests/test_lot124_permission_scanner_and_least_privilege_audit.py
- data/audit/permission_scanner_and_least_privilege_audit_lot124.json
- reports/lot_124_permission_scanner_and_least_privilege_audit_report.md
- docs/LOT_124_PERMISSION_SCANNER_AND_LEAST_PRIVILEGE_AUDIT.md
- docs/ACCEPTANCE_CRITERIA_LOT_124.md

### Observabilité minimale

- lot_124_records_processed_total
- lot_124_validation_failures_total
- lot_124_processing_latency_ms

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Mock POST/DELETE interdit.
- Clé avec withdrawal fait échouer startup.
- Pagination duplicate/missing page.

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
- withdrawal_permission=FORBIDDEN
- trading_permission=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 125 — V13 API Read-Only Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY`  
**Composant propriétaire :** `ReadOnlyConnectorDomain`  
**Frontière de code :** `src/crypto_quant_bot/connectors`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « V13 API Read-Only Closure » dans API Read-Only / Account Read-Only, produire V13APIReadOnlyClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- V13APIReadOnlyClosureStateV1
- V13APIReadOnlyClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- ReadOnlyAccountSnapshotV1
- PermissionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 125, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « V13 API Read-Only Closure » dans le composant ReadOnlyConnectorDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Autoriser uniquement endpoints GET/read ; bloquer au code et à la permission toute écriture/trade/withdrawal.
10. Paginer et dédupliquer histories via IDs venue.
11. Conserver request_time, venue_time, cursor et completeness.
12. Scanner permissions et faire échouer si trading/withdrawal présent.

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

- scripts/validate_all_until_lot125.py
- scripts/run_required_chain_until_lot125.sh
- scripts/diagnose_exact_chain_until_lot125.py
- tests/test_lot125_closure_contract.py
- data/audit/closure_manifest_lot125.json
- reports/lot_125_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_125.md
- src/crypto_quant_bot/connectors/v13_api_read_only_closure.py
- src/crypto_quant_bot/connectors/v13_api_read_only_closure_models.py
- scripts/run_lot125_v13_api_read_only_closure.py
- scripts/validate_lot125.py
- tests/test_lot125_v13_api_read_only_closure.py
- data/audit/v13_api_read_only_closure_lot125.json
- reports/lot_125_v13_api_read_only_closure_report.md
- docs/LOT_125_V13_API_READ_ONLY_CLOSURE.md

### Observabilité minimale

- lot_125_records_processed_total
- lot_125_validation_failures_total
- lot_125_processing_latency_ms

### Tests et critères d’acceptation

- Trade/withdraw permissions absentes
- No POST trading endpoints
- Secret leak scan
- Read-only failure handling
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Mock POST/DELETE interdit.
- Clé avec withdrawal fait échouer startup.
- Pagination duplicate/missing page.

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
- withdrawal_permission=FORBIDDEN
- trading_permission=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 119–125 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
