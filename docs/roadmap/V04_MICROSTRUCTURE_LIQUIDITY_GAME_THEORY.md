# V4 — Microstructure / Liquidity / Game Theory

Identifiant : `V4_MICROSTRUCTURE_LIQUIDITY`  
Plage canonique : **Lots 37 à 52**  
Composant/domain owner : `MicrostructureDomain`  
Mode maximal autorisé : `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`

## Finalité de la version

Faire évoluer le système de **V3 fermée et données L2/trades disponibles** vers **Scénarios microstructure audités et non exécutables**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- V3 fermée et données L2/trades disponibles.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/microstructure`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 37 — Microstructure Scope & Offline Data Contracts

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Microstructure Scope & Offline Data Contracts » dans Microstructure / Liquidity / Game Theory, produire MicrostructureScopeOfflineDataContractsStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MicrostructureScopeOfflineDataContractsStateV1
- MicrostructureScopeOfflineDataContractsAuditV1
- MicrostructureScopeOfflineDataContractsContractRegistryV1
- MicrostructureScopeOfflineDataContractsCapabilityMatrixV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 37, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Microstructure Scope & Offline Data Contracts » dans le composant MicrostructureDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/microstructure/microstructure_scope_and_offline_data_contracts.py
- src/crypto_quant_bot/microstructure/microstructure_scope_and_offline_data_contracts_models.py
- scripts/run_lot37_microstructure_scope_and_offline_data_contracts.py
- scripts/validate_lot37.py
- tests/test_lot37_microstructure_scope_and_offline_data_contracts.py
- data/audit/microstructure_scope_and_offline_data_contracts_lot37.json
- reports/lot_37_microstructure_scope_and_offline_data_contracts_report.md
- docs/LOT_37_MICROSTRUCTURE_SCOPE_AND_OFFLINE_DATA_CONTRACTS.md
- docs/ACCEPTANCE_CRITERIA_LOT_37.md

### Observabilité minimale

- lot_37_records_processed_total
- lot_37_validation_failures_total
- lot_37_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 38 — Order Book L2 Snapshot Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Order Book L2 Snapshot Engine » dans Microstructure / Liquidity / Game Theory, produire OrderBookL2SnapshotEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- OrderBookSnapshotRawV1

### Contrats de sortie

- OrderBookL2SnapshotEngineStateV1
- OrderBookL2SnapshotEngineAuditV1
- OrderBookSnapshotV1
- BookHealthStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 38, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Order Book L2 Snapshot Engine » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Trier bids décroissants et asks croissants, agréger prix identiques, rejeter quantités négatives.
6. Valider best_bid < best_ask sauf état venue explicitement locked.
7. Limiter profondeur selon config tout en conservant source depth.
8. Calculer snapshot checksum et sequence anchor.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/order_book_l2_snapshot_engine.py
- src/crypto_quant_bot/microstructure/order_book_l2_snapshot_engine_models.py
- scripts/run_lot38_order_book_l2_snapshot_engine.py
- scripts/validate_lot38.py
- tests/test_lot38_order_book_l2_snapshot_engine.py
- data/audit/order_book_l2_snapshot_engine_lot38.json
- reports/lot_38_order_book_l2_snapshot_engine_report.md
- docs/LOT_38_ORDER_BOOK_L2_SNAPSHOT_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_38.md

### Observabilité minimale

- lot_38_records_processed_total
- lot_38_validation_failures_total
- lot_38_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Crossed book, duplicate level et negative quantity.
- Checksum stable indépendamment de l’ordre brut des niveaux.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 39 — Order Book Delta & Sequence Reconstructor

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Order Book Delta & Sequence Reconstructor » dans Microstructure / Liquidity / Game Theory, produire OrderBookDeltaSequenceReconstructorStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- OrderBookSnapshotV1
- OrderBookDeltaV1

### Contrats de sortie

- OrderBookDeltaSequenceReconstructorStateV1
- OrderBookDeltaSequenceReconstructorAuditV1
- ReconstructedOrderBookV1
- SequenceGapEventV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 39, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Order Book Delta & Sequence Reconstructor » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Appliquer deltas uniquement si sequence_id/prev_sequence satisfont la politique venue.
6. Supprimer un niveau lorsque quantité devient zéro ; interdire quantité négative.
7. Déclencher resync complet sur gap, duplicate ambigu ou checksum mismatch.
8. Ne publier le book que lorsque synchronization_state=SYNCED.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor.py
- src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor_models.py
- scripts/run_lot39_order_book_delta_and_sequence_reconstructor.py
- scripts/validate_lot39.py
- tests/test_lot39_order_book_delta_and_sequence_reconstructor.py
- data/audit/order_book_delta_and_sequence_reconstructor_lot39.json
- reports/lot_39_order_book_delta_and_sequence_reconstructor_report.md
- docs/LOT_39_ORDER_BOOK_DELTA_AND_SEQUENCE_RECONSTRUCTOR.md
- docs/ACCEPTANCE_CRITERIA_LOT_39.md

### Observabilité minimale

- lot_39_records_processed_total
- lot_39_validation_failures_total
- lot_39_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Gap, duplicate, reorder et resync.
- Replay exact snapshot+deltas.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 40 — Book Integrity / Desynchronization Detector

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Book Integrity / Desynchronization Detector » dans Microstructure / Liquidity / Game Theory, produire BookIntegrityDesynchronizationDetectorStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- BookIntegrityDesynchronizationDetectorStateV1
- BookIntegrityDesynchronizationDetectorAuditV1
- BookIntegrityStateV1
- BookHealthVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 40, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Book Integrity / Desynchronization Detector » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Contrôler sequence continuity, crossed/locked state, stale age, checksum, depth collapse et level monotonicity.
6. Calculer book_health_score avec composants publiés.
7. Appliquer WAIT si score sous seuil trade ; BLOCK/PAUSE si sous seuil système selon config.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/book_integrity_desynchronization_detector.py
- src/crypto_quant_bot/microstructure/book_integrity_desynchronization_detector_models.py
- scripts/run_lot40_book_integrity_desynchronization_detector.py
- scripts/validate_lot40.py
- tests/test_lot40_book_integrity_desynchronization_detector.py
- data/audit/book_integrity_desynchronization_detector_lot40.json
- reports/lot_40_book_integrity_desynchronization_detector_report.md
- docs/LOT_40_BOOK_INTEGRITY_DESYNCHRONIZATION_DETECTOR.md
- docs/ACCEPTANCE_CRITERIA_LOT_40.md

### Observabilité minimale

- lot_40_records_processed_total
- lot_40_validation_failures_total
- lot_40_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Chaque composant de santé dégradé isolément.
- Aucun score global vert si un veto critique est actif.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 41 — Spread, Depth & Imbalance Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Spread, Depth & Imbalance Engine » dans Microstructure / Liquidity / Game Theory, produire SpreadDepthImbalanceEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SpreadDepthImbalanceEngineStateV1
- SpreadDepthImbalanceEngineAuditV1
- BookFeatureStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 41, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Spread, Depth & Imbalance Engine » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Calculer spread absolu/bps, mid, microprice, depth par bande bps et cumulative depth.
6. Calculer imbalance symétrique avec gestion du dénominateur nul.
7. Publier valeurs par horizon/niveau et qualité du book.
8. Ne pas extrapoler au-delà de la profondeur observée.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine.py
- src/crypto_quant_bot/microstructure/spread_depth_and_imbalance_engine_models.py
- scripts/run_lot41_spread_depth_and_imbalance_engine.py
- scripts/validate_lot41.py
- tests/test_lot41_spread_depth_and_imbalance_engine.py
- data/audit/spread_depth_and_imbalance_engine_lot41.json
- reports/lot_41_spread_depth_and_imbalance_engine_report.md
- docs/LOT_41_SPREAD_DEPTH_AND_IMBALANCE_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_41.md

### Observabilité minimale

- lot_41_records_processed_total
- lot_41_validation_failures_total
- lot_41_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Book vide/unilatéral.
- Invariance à l’unité de cotation et contrôle des bornes.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 42 — Liquidity Zones, Walls & Voids Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Liquidity Zones, Walls & Voids Engine » dans Microstructure / Liquidity / Game Theory, produire LiquidityZonesWallsVoidsEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- LiquidityZonesWallsVoidsEngineStateV1
- LiquidityZonesWallsVoidsEngineAuditV1
- LiquidityZoneSetV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 42, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Liquidity Zones, Walls & Voids Engine » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Clusteriser niveaux adjacents selon distance bps versionnée.
6. Mesurer notional, persistence, replenishment, cancellation rate et distance au mid.
7. Distinguer displayed_wall, persistent_zone et liquidity_void ; ne pas affirmer une intention.
8. Expirer les zones lorsque freshness/persistence ne satisfait plus le contrat.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine.py
- src/crypto_quant_bot/microstructure/liquidity_zones_walls_and_voids_engine_models.py
- scripts/run_lot42_liquidity_zones_walls_and_voids_engine.py
- scripts/validate_lot42.py
- tests/test_lot42_liquidity_zones_walls_and_voids_engine.py
- data/audit/liquidity_zones_walls_and_voids_engine_lot42.json
- reports/lot_42_liquidity_zones_walls_and_voids_engine_report.md
- docs/LOT_42_LIQUIDITY_ZONES_WALLS_AND_VOIDS_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_42.md

### Observabilité minimale

- lot_42_records_processed_total
- lot_42_validation_failures_total
- lot_42_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Mur instantanément annulé classé faible confiance.
- Void détecté des deux côtés du carnet.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 43 — Book Resilience & Replenishment Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Book Resilience & Replenishment Engine » dans Microstructure / Liquidity / Game Theory, produire BookResilienceReplenishmentEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- BookResilienceReplenishmentEngineStateV1
- BookResilienceReplenishmentEngineAuditV1
- BookResilienceStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 43, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Book Resilience & Replenishment Engine » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Détecter événements de depletion puis mesurer temps/quantité de replenishment.
6. Séparer replenishment au même prix, adjacent et déplacement du mid.
7. Calculer resilience par côté, horizon et régime de volatilité.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine.py
- src/crypto_quant_bot/microstructure/book_resilience_and_replenishment_engine_models.py
- scripts/run_lot43_book_resilience_and_replenishment_engine.py
- scripts/validate_lot43.py
- tests/test_lot43_book_resilience_and_replenishment_engine.py
- data/audit/book_resilience_and_replenishment_engine_lot43.json
- reports/lot_43_book_resilience_and_replenishment_engine_report.md
- docs/LOT_43_BOOK_RESILIENCE_AND_REPLENISHMENT_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_43.md

### Observabilité minimale

- lot_43_records_processed_total
- lot_43_validation_failures_total
- lot_43_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Depletion sans replenishment.
- Replenishment après fenêtre expirée non compté.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 44 — Trades & Aggressor Classification Schema

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Trades & Aggressor Classification Schema » dans Microstructure / Liquidity / Game Theory, produire TradesAggressorClassificationSchemaStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- TradesAggressorClassificationSchemaStateV1
- TradesAggressorClassificationSchemaAuditV1
- ClassifiedTradeV1
- AggressorConfidenceStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 44, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Trades & Aggressor Classification Schema » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Classer par quote test ; utiliser tick rule seulement lorsque quote indisponible selon policy.
6. Marquer BUY_AGGRESSOR, SELL_AGGRESSOR ou UNKNOWN avec method et confidence.
7. Mesurer unknown_volume_ratio et interdire sa suppression des agrégats.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Quote stale ou locked → confidence réduite/UNKNOWN.
- Unknown ratio > seuil → order-flow veto.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py
- src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py
- scripts/run_lot44_trades_and_aggressor_classification_schema.py
- scripts/validate_lot44.py
- tests/test_lot44_trades_and_aggressor_classification_schema.py
- data/audit/trades_and_aggressor_classification_schema_lot44.json
- reports/lot_44_trades_and_aggressor_classification_schema_report.md
- docs/LOT_44_TRADES_AND_AGGRESSOR_CLASSIFICATION_SCHEMA.md
- docs/ACCEPTANCE_CRITERIA_LOT_44.md

### Observabilité minimale

- lot_44_records_processed_total
- lot_44_validation_failures_total
- lot_44_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Trades au bid/ask/mid et hors ordre.
- Volume total = buy + sell + unknown.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 45 — Order Flow, Delta & CVD Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Order Flow, Delta & CVD Engine » dans Microstructure / Liquidity / Game Theory, produire OrderFlowDeltaCVDEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- OrderFlowDeltaCVDEngineStateV1
- OrderFlowDeltaCVDEngineAuditV1
- OrderFlowStateV1
- CVDSeriesV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 45, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Order Flow, Delta & CVD Engine » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Agrégater buy/sell/unknown volume par fenêtres event-time.
6. Calculer delta, imbalance, CVD et impulsion sans backfill futur.
7. Réinitialiser ou segmenter CVD selon session policy explicitement versionnée.
8. Associer coverage et confidence issue de la classification.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine.py
- src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_models.py
- scripts/run_lot45_order_flow_delta_and_cvd_engine.py
- scripts/validate_lot45.py
- tests/test_lot45_order_flow_delta_and_cvd_engine.py
- data/audit/order_flow_delta_and_cvd_engine_lot45.json
- reports/lot_45_order_flow_delta_and_cvd_engine_report.md
- docs/LOT_45_ORDER_FLOW_DELTA_AND_CVD_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_45.md

### Observabilité minimale

- lot_45_records_processed_total
- lot_45_validation_failures_total
- lot_45_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Conservation du volume.
- CVD identique en replay avec événements hors ordre réordonnés par politique.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 46 — Trade Classification Confidence Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Trade Classification Confidence Engine » dans Microstructure / Liquidity / Game Theory, produire TradeClassificationConfidenceEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- TradeClassificationConfidenceEngineStateV1
- TradeClassificationConfidenceEngineAuditV1
- ClassifiedTradeV1
- AggressorConfidenceStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 46, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Trade Classification Confidence Engine » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Classer par quote test ; utiliser tick rule seulement lorsque quote indisponible selon policy.
6. Marquer BUY_AGGRESSOR, SELL_AGGRESSOR ou UNKNOWN avec method et confidence.
7. Mesurer unknown_volume_ratio et interdire sa suppression des agrégats.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Quote stale ou locked → confidence réduite/UNKNOWN.
- Unknown ratio > seuil → order-flow veto.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/trade_classification_confidence_engine.py
- src/crypto_quant_bot/microstructure/trade_classification_confidence_engine_models.py
- scripts/run_lot46_trade_classification_confidence_engine.py
- scripts/validate_lot46.py
- tests/test_lot46_trade_classification_confidence_engine.py
- data/audit/trade_classification_confidence_engine_lot46.json
- reports/lot_46_trade_classification_confidence_engine_report.md
- docs/LOT_46_TRADE_CLASSIFICATION_CONFIDENCE_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_46.md

### Observabilité minimale

- lot_46_records_processed_total
- lot_46_validation_failures_total
- lot_46_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Trades au bid/ask/mid et hors ordre.
- Volume total = buy + sell + unknown.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 47 — Absorption, Defense & Hidden Liquidity Proxy

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Absorption, Defense & Hidden Liquidity Proxy » dans Microstructure / Liquidity / Game Theory, produire AbsorptionDefenseHiddenLiquidityProxyStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- AbsorptionDefenseHiddenLiquidityProxyStateV1
- AbsorptionDefenseHiddenLiquidityProxyAuditV1
- AbsorptionDefenseStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 47, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Absorption, Defense & Hidden Liquidity Proxy » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Identifier volume agressif élevé combiné à faible déplacement du prix et replenishment du côté passif.
6. Comparer au baseline de volatilité/liquidité du même régime.
7. Produire absorption_proxy, defense_proxy et hidden_liquidity_hypothesis avec confidence.
8. Interdire les libellés affirmant l’identité ou l’intention d’un market maker.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/absorption_defense_and_hidden_liquidity_proxy.py
- src/crypto_quant_bot/microstructure/absorption_defense_and_hidden_liquidity_proxy_models.py
- scripts/run_lot47_absorption_defense_and_hidden_liquidity_proxy.py
- scripts/validate_lot47.py
- tests/test_lot47_absorption_defense_and_hidden_liquidity_proxy.py
- data/audit/absorption_defense_and_hidden_liquidity_proxy_lot47.json
- reports/lot_47_absorption_defense_and_hidden_liquidity_proxy_report.md
- docs/LOT_47_ABSORPTION_DEFENSE_AND_HIDDEN_LIQUIDITY_PROXY.md
- docs/ACCEPTANCE_CRITERIA_LOT_47.md

### Observabilité minimale

- lot_47_records_processed_total
- lot_47_validation_failures_total
- lot_47_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Volume élevé avec fort déplacement ne doit pas être absorption.
- Replenishment absent réduit la confiance.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 48 — Volume Clusters & Time-at-Level Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Volume Clusters & Time-at-Level Engine » dans Microstructure / Liquidity / Game Theory, produire VolumeClustersTimeAtLevelEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- VolumeClustersTimeAtLevelEngineStateV1
- VolumeClustersTimeAtLevelEngineAuditV1
- VolumeClusterSetV1
- TimeAtLevelStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 48, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Volume Clusters & Time-at-Level Engine » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Bucketiser prix avec tick/volatility-aware step.
6. Cumuler trade volume, aggressive split, visits, dwell time et rejection count par niveau.
7. Distinguer volume cluster, acceptance zone et rejection zone.
8. Éviter double comptage lorsque plusieurs timeframes se chevauchent.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/volume_clusters_and_time_at_level_engine.py
- src/crypto_quant_bot/microstructure/volume_clusters_and_time_at_level_engine_models.py
- scripts/run_lot48_volume_clusters_and_time_at_level_engine.py
- scripts/validate_lot48.py
- tests/test_lot48_volume_clusters_and_time_at_level_engine.py
- data/audit/volume_clusters_and_time_at_level_engine_lot48.json
- reports/lot_48_volume_clusters_and_time_at_level_engine_report.md
- docs/LOT_48_VOLUME_CLUSTERS_AND_TIME_AT_LEVEL_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_48.md

### Observabilité minimale

- lot_48_records_processed_total
- lot_48_validation_failures_total
- lot_48_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Même événement non compté deux fois.
- Changement de tick size crée une nouvelle version.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 49 — Stop Zones, Liquidity Pools & Breakout Attraction

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Stop Zones, Liquidity Pools & Breakout Attraction » dans Microstructure / Liquidity / Game Theory, produire StopZonesLiquidityPoolsBreakoutAttractionStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- StopZonesLiquidityPoolsBreakoutAttractionStateV1
- StopZonesLiquidityPoolsBreakoutAttractionAuditV1
- ProbableLiquidityPoolSetV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 49, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Stop Zones, Liquidity Pools & Breakout Attraction » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Construire candidats depuis swings confirmés, égalités de highs/lows, round levels et zones de liquidité persistantes.
6. Calculer stop_cluster_probability avec evidence_components et uncertainty.
7. Mesurer attraction de breakout via proximité, participation et historique de réaction.
8. Nommer ces zones probables ; ne jamais présenter des stops réels observés.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/stop_zones_liquidity_pools_and_breakout_attraction.py
- src/crypto_quant_bot/microstructure/stop_zones_liquidity_pools_and_breakout_attraction_models.py
- scripts/run_lot49_stop_zones_liquidity_pools_and_breakout_attraction.py
- scripts/validate_lot49.py
- tests/test_lot49_stop_zones_liquidity_pools_and_breakout_attraction.py
- data/audit/stop_zones_liquidity_pools_and_breakout_attraction_lot49.json
- reports/lot_49_stop_zones_liquidity_pools_and_breakout_attraction_report.md
- docs/LOT_49_STOP_ZONES_LIQUIDITY_POOLS_AND_BREAKOUT_ATTRACTION.md
- docs/ACCEPTANCE_CRITERIA_LOT_49.md

### Observabilité minimale

- lot_49_records_processed_total
- lot_49_validation_failures_total
- lot_49_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Pivot non confirmé non utilisé.
- Round level seul produit faible confiance.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 50 — Sweep, Fakeout, Trap & Failed Auction Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Sweep, Fakeout, Trap & Failed Auction Engine » dans Microstructure / Liquidity / Game Theory, produire SweepFakeoutTrapFailedAuctionEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SweepFakeoutTrapFailedAuctionEngineStateV1
- SweepFakeoutTrapFailedAuctionEngineAuditV1
- LiquidityBehaviorEventV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 50, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Sweep, Fakeout, Trap & Failed Auction Engine » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Détecter breach de zone, excursion, volume/flow associé puis reclaim/acceptance dans fenêtre définie.
6. Classer SWEEP, BREAKOUT_ACCEPTED, FAKEOUT, LONG_TRAP, SHORT_TRAP ou FAILED_AUCTION.
7. Exiger séquence temporelle complète et publier evidence/invalidating_evidence.
8. Ne pas utiliser de barre future au-delà du temps de décision.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/sweep_fakeout_trap_and_failed_auction_engine.py
- src/crypto_quant_bot/microstructure/sweep_fakeout_trap_and_failed_auction_engine_models.py
- scripts/run_lot50_sweep_fakeout_trap_and_failed_auction_engine.py
- scripts/validate_lot50.py
- tests/test_lot50_sweep_fakeout_trap_and_failed_auction_engine.py
- data/audit/sweep_fakeout_trap_and_failed_auction_engine_lot50.json
- reports/lot_50_sweep_fakeout_trap_and_failed_auction_engine_report.md
- docs/LOT_50_SWEEP_FAKEOUT_TRAP_AND_FAILED_AUCTION_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_50.md

### Observabilité minimale

- lot_50_records_processed_total
- lot_50_validation_failures_total
- lot_50_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Breach sans reclaim ≠ fakeout.
- Late reclaim après expiration ≠ trap actif.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 51 — Derivatives Context: OI, Funding, Basis & Liquidations

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Derivatives Context: OI, Funding, Basis & Liquidations » dans Microstructure / Liquidity / Game Theory, produire DerivativesContextOIFundingBasisLiquidationsStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- DerivativesContextOIFundingBasisLiquidationsStateV1
- DerivativesContextOIFundingBasisLiquidationsAuditV1
- DerivativesContextStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 51, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Derivatives Context: OI, Funding, Basis & Liquidations » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Normaliser OI, funding, mark/index, basis et liquidations par venue/contrat.
6. Aligner publication/effective_time et gérer révisions.
7. Calculer crowding, leverage build-up, squeeze/liquidation risk comme contexte probabiliste.
8. Interdire l’usage si spot/perp mapping ou notionals ne sont pas comparables.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/microstructure/derivatives_context_oi_funding_basis_and_liquidations.py
- src/crypto_quant_bot/microstructure/derivatives_context_oi_funding_basis_and_liquidations_models.py
- scripts/run_lot51_derivatives_context_oi_funding_basis_and_liquidations.py
- scripts/validate_lot51.py
- tests/test_lot51_derivatives_context_oi_funding_basis_and_liquidations.py
- data/audit/derivatives_context_oi_funding_basis_and_liquidations_lot51.json
- reports/lot_51_derivatives_context_oi_funding_basis_and_liquidations_report.md
- docs/LOT_51_DERIVATIVES_CONTEXT_OI_FUNDING_BASIS_AND_LIQUIDATIONS.md
- docs/ACCEPTANCE_CRITERIA_LOT_51.md

### Observabilité minimale

- lot_51_records_processed_total
- lot_51_validation_failures_total
- lot_51_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Funding publication vs effective time.
- OI change sans prix/volume ne produit pas de scénario certain.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 52 — Game Theory, Scenario Aggregation & V4 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`  
**Composant propriétaire :** `MicrostructureDomain`  
**Frontière de code :** `src/crypto_quant_bot/microstructure`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Game Theory, Scenario Aggregation & V4 Closure » dans Microstructure / Liquidity / Game Theory, produire GameTheoryScenarioAggregationV4ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- GameTheoryScenarioAggregationV4ClosureStateV1
- GameTheoryScenarioAggregationV4ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- ScenarioSetV1
- ScenarioConflictMatrixV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 52, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Game Theory, Scenario Aggregation & V4 Closure » dans le composant MicrostructureDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Agrégater uniquement des composants validés et publier les poids/configs effectivement utilisés.
6. Conserver contribution, qualité et fraîcheur de chaque source ; une source manquante n’est jamais renormalisée silencieusement.
7. Produire état dominant, alternatives, conflits et confidence_interval lorsque disponible.
8. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
9. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
10. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
11. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
12. Construire scénarios concurrents à partir de faits mesurés et d’hypothèses explicitement étiquetées.
13. Pour chaque scénario : preconditions, evidence, counter_evidence, invalidation, horizon, confidence et observability.
14. Normaliser les scores sans forcer leur somme à 1 sauf modèle calibré.
15. Scenario score reste non exécutable et ne produit aucun OrderIntent.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Composants contradictoires sans règle de résolution → CONTEXT_MIXED/UNKNOWN.
- Poids ou config non approuvé → BLOCKED_CONFIG.
- Checksum différent → NON_DETERMINISTIC_FAIL.
- Lot antérieur non PASS → closure refusée.

### Fichiers et artefacts d’implémentation attendus

- scripts/validate_all_until_lot52.py
- scripts/run_required_chain_until_lot52.sh
- scripts/diagnose_exact_chain_until_lot52.py
- tests/test_lot52_closure_contract.py
- data/audit/closure_manifest_lot52.json
- reports/lot_52_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_52.md
- src/crypto_quant_bot/microstructure/game_theory_scenario_aggregation_and_v4_closure.py
- src/crypto_quant_bot/microstructure/game_theory_scenario_aggregation_and_v4_closure_models.py
- scripts/run_lot52_game_theory_scenario_aggregation_and_v4_closure.py
- scripts/validate_lot52.py
- tests/test_lot52_game_theory_scenario_aggregation_and_v4_closure.py
- data/audit/game_theory_scenario_aggregation_and_v4_closure_lot52.json
- reports/lot_52_game_theory_scenario_aggregation_and_v4_closure_report.md
- docs/LOT_52_GAME_THEORY_SCENARIO_AGGREGATION_AND_V4_CLOSURE.md

### Observabilité minimale

- lot_52_records_processed_total
- lot_52_validation_failures_total
- lot_52_processing_latency_ms

### Tests et critères d’acceptation

- Séquence de book cohérente
- Aucun crossed/locked book silencieux
- Classification agressor avec confidence
- Pas de future leakage
- Scénarios non exécutables
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test d’ablation de chaque composant.
- Test de source manquante sans changement silencieux de sens.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Scénarios contradictoires conservés.
- Absence de calibration interdit le champ probability.

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
- participant_behavior = inference_explicitly_labeled
- scenario_score != signal
- execution_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 37–52 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
