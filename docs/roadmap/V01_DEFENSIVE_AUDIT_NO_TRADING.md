# V1 — Defensive Audit / No Trading

Identifiant : `V1_DEFENSIVE_AUDIT`  
Plage canonique : **Lots 0 à 20**  
Composant/domain owner : `SafetyKernel`  
Mode maximal autorisé : `EDUCATIONAL_AUDIT_ONLY`

## Finalité de la version

Faire évoluer le système de **Projet initial** vers **Archive V1 figée et invariants no-trading prouvés**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Projet initial.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/core`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 0 — Project Bootstrap & Safety Baseline

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Établir l’identité, la structure, les conventions et les garde-fous initiaux du projet.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ProjectBootstrapSafetyBaselineStateV1
- ProjectBootstrapSafetyBaselineAuditV1
- LiquidityBehaviorEventV1
- RobustnessSimulationResultV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 0, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Project Bootstrap & Safety Baseline » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.
6. Détecter breach de zone, excursion, volume/flow associé puis reclaim/acceptance dans fenêtre définie.
7. Classer SWEEP, BREAKOUT_ACCEPTED, FAKEOUT, LONG_TRAP, SHORT_TRAP ou FAILED_AUCTION.
8. Exiger séquence temporelle complète et publier evidence/invalidating_evidence.
9. Ne pas utiliser de barre future au-delà du temps de décision.
10. Bootstrap par blocs pour préserver dépendance temporelle.
11. Randomiser ordre des trades/cost shocks selon scénario.
12. Balayer paramètres autour du point choisi et détecter cliffs.
13. Publier risk-of-ruin et drawdown distribution.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/project_bootstrap_and_safety_baseline.py
- src/crypto_quant_bot/core/project_bootstrap_and_safety_baseline_models.py
- scripts/run_lot0_project_bootstrap_and_safety_baseline.py
- scripts/validate_lot0.py
- tests/test_lot0_project_bootstrap_and_safety_baseline.py
- data/audit/project_bootstrap_and_safety_baseline_lot0.json
- reports/lot_0_project_bootstrap_and_safety_baseline_report.md
- docs/LOT_0_PROJECT_BOOTSTRAP_AND_SAFETY_BASELINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_0.md
- reports/lot_0_validation_report.md

### Observabilité minimale

- lot_0_records_processed_total
- lot_0_validation_failures_total
- lot_0_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Breach sans reclaim ≠ fakeout.
- Late reclaim après expiration ≠ trap actif.
- Seed reproductible.
- Paramètre fragile marqué non promotable.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 1 — Data Platform Foundation

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Créer une plateforme de données locale, déterministe et contrôlée pour les premières fixtures BTC/EUR.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- DataPlatformFoundationStateV1
- DataPlatformFoundationAuditV1
- DataPlatformFoundationContractRegistryV1
- DataPlatformFoundationCapabilityMatrixV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 1, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Data Platform Foundation » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.
6. Définir frontières, responsabilités, dépendances autorisées, modes runtime et API publiques du domaine.
7. Classer chaque capability en REQUIRED, OPTIONAL_RESEARCH, DISABLED ou FORBIDDEN.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/data_platform_foundation.py
- src/crypto_quant_bot/core/data_platform_foundation_models.py
- scripts/run_lot1_data_platform_foundation.py
- scripts/validate_lot1.py
- tests/test_lot1_data_platform_foundation.py
- data/audit/data_platform_foundation_lot1.json
- reports/lot_1_data_platform_foundation_report.md
- docs/LOT_1_DATA_PLATFORM_FOUNDATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_1.md
- reports/lot_1_validation_report.md

### Observabilité minimale

- lot_1_records_processed_total
- lot_1_validation_failures_total
- lot_1_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
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
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.
- Ne pas implémenter prématurément les algorithmes métier décrits par l’architecture.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 2 — Multi-Timeframe Dataset & Basic Features

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Construire les datasets 5m/15m et les premières features mathématiques sans introduire de stratégie.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MultiTimeframeDatasetBasicFeaturesStateV1
- MultiTimeframeDatasetBasicFeaturesAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 2, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Multi-Timeframe Dataset & Basic Features » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/multi_timeframe_dataset_and_basic_features.py
- src/crypto_quant_bot/core/multi_timeframe_dataset_and_basic_features_models.py
- scripts/run_lot2_multi_timeframe_dataset_and_basic_features.py
- scripts/validate_lot2.py
- tests/test_lot2_multi_timeframe_dataset_and_basic_features.py
- data/audit/multi_timeframe_dataset_and_basic_features_lot2.json
- reports/lot_2_multi_timeframe_dataset_and_basic_features_report.md
- docs/LOT_2_MULTI_TIMEFRAME_DATASET_AND_BASIC_FEATURES.md
- docs/ACCEPTANCE_CRITERIA_LOT_2.md
- reports/lot_2_validation_report.md

### Observabilité minimale

- lot_2_records_processed_total
- lot_2_validation_failures_total
- lot_2_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 3 — Pivot Engine & Support/Resistance Zones

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Détecter pivots et zones descriptives de support/résistance avec disponibilité temporelle explicite.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- PivotEngineSupportResistanceZonesStateV1
- PivotEngineSupportResistanceZonesAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 3, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Pivot Engine & Support/Resistance Zones » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/pivot_engine_and_support_resistance_zones.py
- src/crypto_quant_bot/core/pivot_engine_and_support_resistance_zones_models.py
- scripts/run_lot3_pivot_engine_and_support_resistance_zones.py
- scripts/validate_lot3.py
- tests/test_lot3_pivot_engine_and_support_resistance_zones.py
- data/audit/pivot_engine_and_support_resistance_zones_lot3.json
- reports/lot_3_pivot_engine_and_support_resistance_zones_report.md
- docs/LOT_3_PIVOT_ENGINE_AND_SUPPORT_RESISTANCE_ZONES.md
- docs/ACCEPTANCE_CRITERIA_LOT_3.md
- reports/lot_3_validation_report.md

### Observabilité minimale

- lot_3_records_processed_total
- lot_3_validation_failures_total
- lot_3_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 4 — Volume Profile, VWAP & Anchored VWAP

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Calculer Volume Profile candle-based, VWAP et Anchored VWAP en mode analytique uniquement.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- VolumeProfileVWAPAnchoredVWAPStateV1
- VolumeProfileVWAPAnchoredVWAPAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 4, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Volume Profile, VWAP & Anchored VWAP » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/volume_profile_vwap_and_anchored_vwap.py
- src/crypto_quant_bot/core/volume_profile_vwap_and_anchored_vwap_models.py
- scripts/run_lot4_volume_profile_vwap_and_anchored_vwap.py
- scripts/validate_lot4.py
- tests/test_lot4_volume_profile_vwap_and_anchored_vwap.py
- data/audit/volume_profile_vwap_and_anchored_vwap_lot4.json
- reports/lot_4_volume_profile_vwap_and_anchored_vwap_report.md
- docs/LOT_4_VOLUME_PROFILE_VWAP_AND_ANCHORED_VWAP.md
- docs/ACCEPTANCE_CRITERIA_LOT_4.md
- reports/lot_4_validation_report.md

### Observabilité minimale

- lot_4_records_processed_total
- lot_4_validation_failures_total
- lot_4_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 5 — Volatility / ATR / Range Engine

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Mesurer ATR, true range, compression, expansion et volatilité descriptive.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- VolatilityATRRangeEngineStateV1
- VolatilityATRRangeEngineAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 5, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Volatility / ATR / Range Engine » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/volatility_atr_range_engine.py
- src/crypto_quant_bot/core/volatility_atr_range_engine_models.py
- scripts/run_lot5_volatility_atr_range_engine.py
- scripts/validate_lot5.py
- tests/test_lot5_volatility_atr_range_engine.py
- data/audit/volatility_atr_range_engine_lot5.json
- reports/lot_5_volatility_atr_range_engine_report.md
- docs/LOT_5_VOLATILITY_ATR_RANGE_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_5.md
- reports/lot_5_validation_report.md

### Observabilité minimale

- lot_5_records_processed_total
- lot_5_validation_failures_total
- lot_5_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 6 — Market Regime Engine

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Classifier le régime de marché sans produire de signal ou d’ordre.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MarketRegimeEngineStateV1
- MarketRegimeEngineAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 6, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Market Regime Engine » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/market_regime_engine.py
- src/crypto_quant_bot/core/market_regime_engine_models.py
- scripts/run_lot6_market_regime_engine.py
- scripts/validate_lot6.py
- tests/test_lot6_market_regime_engine.py
- data/audit/market_regime_engine_lot6.json
- reports/lot_6_market_regime_engine_report.md
- docs/LOT_6_MARKET_REGIME_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_6.md
- reports/lot_6_validation_report.md

### Observabilité minimale

- lot_6_records_processed_total
- lot_6_validation_failures_total
- lot_6_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 7 — Market State Engine

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Consolider un état marché local, versionné et rejouable.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MarketStateEngineStateV1
- MarketStateEngineAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 7, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Market State Engine » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/market_state_engine.py
- src/crypto_quant_bot/core/market_state_engine_models.py
- scripts/run_lot7_market_state_engine.py
- scripts/validate_lot7.py
- tests/test_lot7_market_state_engine.py
- data/audit/market_state_engine_lot7.json
- reports/lot_7_market_state_engine_report.md
- docs/LOT_7_MARKET_STATE_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_7.md
- reports/lot_7_validation_report.md

### Observabilité minimale

- lot_7_records_processed_total
- lot_7_validation_failures_total
- lot_7_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 8 — Feature Registry & Anti-Lookahead Audit

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Centraliser les features et prouver l’absence de lookahead/future leakage.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- FeatureRegistryAntiLookaheadAuditStateV1
- FeatureRegistryAntiLookaheadAuditAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 8, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Feature Registry & Anti-Lookahead Audit » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.
6. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
7. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
8. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
9. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.

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

- src/crypto_quant_bot/core/feature_registry_and_anti_lookahead_audit.py
- src/crypto_quant_bot/core/feature_registry_and_anti_lookahead_audit_models.py
- scripts/run_lot8_feature_registry_and_anti_lookahead_audit.py
- scripts/validate_lot8.py
- tests/test_lot8_feature_registry_and_anti_lookahead_audit.py
- data/audit/feature_registry_and_anti_lookahead_audit_lot8.json
- reports/lot_8_feature_registry_and_anti_lookahead_audit_report.md
- docs/LOT_8_FEATURE_REGISTRY_AND_ANTI_LOOKAHEAD_AUDIT.md
- docs/ACCEPTANCE_CRITERIA_LOT_8.md
- reports/lot_8_validation_report.md

### Observabilité minimale

- lot_8_records_processed_total
- lot_8_validation_failures_total
- lot_8_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
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
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 9 — Deterministic Replay / Backtest Skeleton

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Mettre en place un replay déterministe sans ordres, fills ni PnL exploitable.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- DeterministicReplayBacktestSkeletonStateV1
- DeterministicReplayBacktestSkeletonAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 9, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Deterministic Replay / Backtest Skeleton » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.
6. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
7. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
8. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
9. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.

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

- src/crypto_quant_bot/core/deterministic_replay_backtest_skeleton.py
- src/crypto_quant_bot/core/deterministic_replay_backtest_skeleton_models.py
- scripts/run_lot9_deterministic_replay_backtest_skeleton.py
- scripts/validate_lot9.py
- tests/test_lot9_deterministic_replay_backtest_skeleton.py
- data/audit/deterministic_replay_backtest_skeleton_lot9.json
- reports/lot_9_deterministic_replay_backtest_skeleton_report.md
- docs/LOT_9_DETERMINISTIC_REPLAY_BACKTEST_SKELETON.md
- docs/ACCEPTANCE_CRITERIA_LOT_9.md
- reports/lot_9_validation_report.md

### Observabilité minimale

- lot_9_records_processed_total
- lot_9_validation_failures_total
- lot_9_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
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
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 10 — Transaction Costs V0

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Modéliser les premières frictions de transaction sans activation décisionnelle.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- TransactionCostsV0StateV1
- TransactionCostsV0AuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 10, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Transaction Costs V0 » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/transaction_costs_v0.py
- src/crypto_quant_bot/core/transaction_costs_v0_models.py
- scripts/run_lot10_transaction_costs_v0.py
- scripts/validate_lot10.py
- tests/test_lot10_transaction_costs_v0.py
- data/audit/transaction_costs_v0_lot10.json
- reports/lot_10_transaction_costs_v0_report.md
- docs/LOT_10_TRANSACTION_COSTS_V0.md
- docs/ACCEPTANCE_CRITERIA_LOT_10.md
- reports/lot_10_validation_report.md

### Observabilité minimale

- lot_10_records_processed_total
- lot_10_validation_failures_total
- lot_10_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 11 — Risk Engine & Decision Firewall

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Bloquer toute décision exploitable au moyen d’un moteur de risque fail-closed.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- RiskEngineDecisionFirewallStateV1
- RiskEngineDecisionFirewallAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 11, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Risk Engine & Decision Firewall » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/risk_engine_and_decision_firewall.py
- src/crypto_quant_bot/core/risk_engine_and_decision_firewall_models.py
- scripts/run_lot11_risk_engine_and_decision_firewall.py
- scripts/validate_lot11.py
- tests/test_lot11_risk_engine_and_decision_firewall.py
- data/audit/risk_engine_and_decision_firewall_lot11.json
- reports/lot_11_risk_engine_and_decision_firewall_report.md
- docs/LOT_11_RISK_ENGINE_AND_DECISION_FIREWALL.md
- docs/ACCEPTANCE_CRITERIA_LOT_11.md
- reports/lot_11_validation_report.md

### Observabilité minimale

- lot_11_records_processed_total
- lot_11_validation_failures_total
- lot_11_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 12 — Exposure Guard & Capital Safety

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Empêcher toute exposition, allocation ou capital à risque.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ExposureGuardCapitalSafetyStateV1
- ExposureGuardCapitalSafetyAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 12, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Exposure Guard & Capital Safety » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/exposure_guard_and_capital_safety.py
- src/crypto_quant_bot/core/exposure_guard_and_capital_safety_models.py
- scripts/run_lot12_exposure_guard_and_capital_safety.py
- scripts/validate_lot12.py
- tests/test_lot12_exposure_guard_and_capital_safety.py
- data/audit/exposure_guard_and_capital_safety_lot12.json
- reports/lot_12_exposure_guard_and_capital_safety_report.md
- docs/LOT_12_EXPOSURE_GUARD_AND_CAPITAL_SAFETY.md
- docs/ACCEPTANCE_CRITERIA_LOT_12.md
- reports/lot_12_validation_report.md

### Observabilité minimale

- lot_12_records_processed_total
- lot_12_validation_failures_total
- lot_12_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 13 — Portfolio Freeze & Allocation Firewall

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Geler le portefeuille et toute modification d’allocation.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- PortfolioFreezeAllocationFirewallStateV1
- PortfolioFreezeAllocationFirewallAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 13, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Portfolio Freeze & Allocation Firewall » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/portfolio_freeze_and_allocation_firewall.py
- src/crypto_quant_bot/core/portfolio_freeze_and_allocation_firewall_models.py
- scripts/run_lot13_portfolio_freeze_and_allocation_firewall.py
- scripts/validate_lot13.py
- tests/test_lot13_portfolio_freeze_and_allocation_firewall.py
- data/audit/portfolio_freeze_and_allocation_firewall_lot13.json
- reports/lot_13_portfolio_freeze_and_allocation_firewall_report.md
- docs/LOT_13_PORTFOLIO_FREEZE_AND_ALLOCATION_FIREWALL.md
- docs/ACCEPTANCE_CRITERIA_LOT_13.md
- reports/lot_13_validation_report.md

### Observabilité minimale

- lot_13_records_processed_total
- lot_13_validation_failures_total
- lot_13_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 14 — Final Decision Firewall

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Produire uniquement WAIT/BLOCK_TRADING et empêcher le routage d’ordre.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- FinalDecisionFirewallStateV1
- FinalDecisionFirewallAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 14, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Final Decision Firewall » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/final_decision_firewall.py
- src/crypto_quant_bot/core/final_decision_firewall_models.py
- scripts/run_lot14_final_decision_firewall.py
- scripts/validate_lot14.py
- tests/test_lot14_final_decision_firewall.py
- data/audit/final_decision_firewall_lot14.json
- reports/lot_14_final_decision_firewall_report.md
- docs/LOT_14_FINAL_DECISION_FIREWALL.md
- docs/ACCEPTANCE_CRITERIA_LOT_14.md
- reports/lot_14_validation_report.md

### Observabilité minimale

- lot_14_records_processed_total
- lot_14_validation_failures_total
- lot_14_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 15 — Decision Ledger & Immutable Audit Trail

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Journaliser les décisions bloquées dans un ledger auditable.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- DecisionLedgerImmutableAuditTrailStateV1
- DecisionLedgerImmutableAuditTrailAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 15, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Decision Ledger & Immutable Audit Trail » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.
6. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
7. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
8. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
9. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.

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

- src/crypto_quant_bot/core/decision_ledger_and_immutable_audit_trail.py
- src/crypto_quant_bot/core/decision_ledger_and_immutable_audit_trail_models.py
- scripts/run_lot15_decision_ledger_and_immutable_audit_trail.py
- scripts/validate_lot15.py
- tests/test_lot15_decision_ledger_and_immutable_audit_trail.py
- data/audit/decision_ledger_and_immutable_audit_trail_lot15.json
- reports/lot_15_decision_ledger_and_immutable_audit_trail_report.md
- docs/LOT_15_DECISION_LEDGER_AND_IMMUTABLE_AUDIT_TRAIL.md
- docs/ACCEPTANCE_CRITERIA_LOT_15.md
- reports/lot_15_validation_report.md

### Observabilité minimale

- lot_15_records_processed_total
- lot_15_validation_failures_total
- lot_15_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
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
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 16 — Dataset Lineage & Reproducibility Manifest

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Tracer lineage, checksums et reproductibilité des artefacts.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- DatasetLineageReproducibilityManifestStateV1
- DatasetLineageReproducibilityManifestAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 16, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Dataset Lineage & Reproducibility Manifest » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/dataset_lineage_and_reproducibility_manifest.py
- src/crypto_quant_bot/core/dataset_lineage_and_reproducibility_manifest_models.py
- scripts/run_lot16_dataset_lineage_and_reproducibility_manifest.py
- scripts/validate_lot16.py
- tests/test_lot16_dataset_lineage_and_reproducibility_manifest.py
- data/audit/dataset_lineage_and_reproducibility_manifest_lot16.json
- reports/lot_16_dataset_lineage_and_reproducibility_manifest_report.md
- docs/LOT_16_DATASET_LINEAGE_AND_REPRODUCIBILITY_MANIFEST.md
- docs/ACCEPTANCE_CRITERIA_LOT_16.md
- reports/lot_16_validation_report.md

### Observabilité minimale

- lot_16_records_processed_total
- lot_16_validation_failures_total
- lot_16_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 17 — Local Health Monitor & Integrity Checks

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Surveiller intégrité, santé locale et cohérence des artefacts.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- LocalHealthMonitorIntegrityChecksStateV1
- LocalHealthMonitorIntegrityChecksAuditV1
- ExchangeHealthStateV1
- ExchangeRiskVetoV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 17, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Local Health Monitor & Integrity Checks » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.
6. Mesurer REST/WS availability, error rate, latency, reconnects, sequence gaps, maintenance et symbol status.
7. Appliquer circuit breakers et backoff avec budgets bornés.
8. Définir source de vérité pour maintenance/halts.
9. Unknown venue state interdit tout nouvel ordre.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/local_health_monitor_and_integrity_checks.py
- src/crypto_quant_bot/core/local_health_monitor_and_integrity_checks_models.py
- scripts/run_lot17_local_health_monitor_and_integrity_checks.py
- scripts/validate_lot17.py
- tests/test_lot17_local_health_monitor_and_integrity_checks.py
- data/audit/local_health_monitor_and_integrity_checks_lot17.json
- reports/lot_17_local_health_monitor_and_integrity_checks_report.md
- docs/LOT_17_LOCAL_HEALTH_MONITOR_AND_INTEGRITY_CHECKS.md
- docs/ACCEPTANCE_CRITERIA_LOT_17.md
- reports/lot_17_validation_report.md

### Observabilité minimale

- lot_17_records_processed_total
- lot_17_validation_failures_total
- lot_17_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
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
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 18 — No-Trading Compliance Audit

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Prouver formellement le maintien des invariants no-trading.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- NoTradingComplianceAuditStateV1
- NoTradingComplianceAuditAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 18, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « No-Trading Compliance Audit » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.
6. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
7. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
8. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
9. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.

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

- src/crypto_quant_bot/core/no_trading_compliance_audit.py
- src/crypto_quant_bot/core/no_trading_compliance_audit_models.py
- scripts/run_lot18_no_trading_compliance_audit.py
- scripts/validate_lot18.py
- tests/test_lot18_no_trading_compliance_audit.py
- data/audit/no_trading_compliance_audit_lot18.json
- reports/lot_18_no_trading_compliance_audit_report.md
- docs/LOT_18_NO_TRADING_COMPLIANCE_AUDIT.md
- docs/ACCEPTANCE_CRITERIA_LOT_18.md
- reports/lot_18_validation_report.md

### Observabilité minimale

- lot_18_records_processed_total
- lot_18_validation_failures_total
- lot_18_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
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
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 19 — Release Candidate Assembly

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Assembler un release candidate auditable sans modifier les garanties V1.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ReleaseCandidateAssemblyStateV1
- ReleaseCandidateAssemblyAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 19, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Release Candidate Assembly » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/core/release_candidate_assembly.py
- src/crypto_quant_bot/core/release_candidate_assembly_models.py
- scripts/run_lot19_release_candidate_assembly.py
- scripts/validate_lot19.py
- tests/test_lot19_release_candidate_assembly.py
- data/audit/release_candidate_assembly_lot19.json
- reports/lot_19_release_candidate_assembly_report.md
- docs/LOT_19_RELEASE_CANDIDATE_ASSEMBLY.md
- docs/ACCEPTANCE_CRITERIA_LOT_19.md
- reports/lot_19_validation_report.md

### Observabilité minimale

- lot_19_records_processed_total
- lot_19_validation_failures_total
- lot_19_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

### Non-objectifs

- Ne pas activer une capability d’une version ultérieure.
- Ne pas déduire une permission de trading à partir d’un score ou d’un succès technique.
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 20 — V1 Defensive Closure & Frozen Archive

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `EDUCATIONAL_AUDIT_ONLY`  
**Composant propriétaire :** `SafetyKernel`  
**Frontière de code :** `src/crypto_quant_bot/core`

### Objectif et responsabilité exacte

Fermer V1 et figer une archive vérifiée qui ne doit plus être régénérée.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- V1DefensiveClosureFrozenArchiveStateV1
- V1DefensiveClosureFrozenArchiveAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 20, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « V1 Defensive Closure & Frozen Archive » dans le composant SafetyKernel sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver l’implémentation historique et utiliser les documents LOT_x / ACCEPTANCE_CRITERIA_LOT_x existants comme preuve primaire.
6. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
7. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
8. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
9. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.

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

- scripts/validate_all_until_lot20.py
- scripts/run_required_chain_until_lot20.sh
- scripts/diagnose_exact_chain_until_lot20.py
- tests/test_lot20_closure_contract.py
- data/audit/closure_manifest_lot20.json
- reports/lot_20_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_20.md
- src/crypto_quant_bot/core/v1_defensive_closure_and_frozen_archive.py
- src/crypto_quant_bot/core/v1_defensive_closure_and_frozen_archive_models.py
- scripts/run_lot20_v1_defensive_closure_and_frozen_archive.py
- scripts/validate_lot20.py
- tests/test_lot20_v1_defensive_closure_and_frozen_archive.py
- data/audit/v1_defensive_closure_and_frozen_archive_lot20.json
- reports/lot_20_v1_defensive_closure_and_frozen_archive_report.md
- docs/LOT_20_V1_DEFENSIVE_CLOSURE_AND_FROZEN_ARCHIVE.md

### Observabilité minimale

- lot_20_records_processed_total
- lot_20_validation_failures_total
- lot_20_processing_latency_ms

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits
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
- Ne pas réécrire rétroactivement un lot validé ; toute évolution passe par un correctif isolé.

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- trade_allowed=false
- execution_allowed=false
- live_execution=DISABLED
- leverage=FORBIDDEN

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Gate de clôture de version

- Tous les Lots 0–20 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
