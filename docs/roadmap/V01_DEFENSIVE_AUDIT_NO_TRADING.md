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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `docs/ACCEPTANCE_CRITERIA_LOT_00.md`
- `docs/LOT_00_REPORT.md`
- `reports/lot_00_validation_report.md`
- `scripts/validate_lot0.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/lot_01_data_quality_report.json`
- `docs/ACCEPTANCE_CRITERIA_LOT_01.md`
- `docs/LOT_01_REPORT.md`
- `reports/lot_01_data_quality_report.md`
- `reports/lot_01_ingestion_validation_stdout.txt`
- `reports/lot_01_validation_report.md`
- `scripts/run_lot1_fixture_parse.py`
- `scripts/validate_lot1.py`
- `tests/__pycache__/test_lot1_catalog.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot1_data_dirs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot1_data_quality.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot1_data_writer_and_checksum.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot1_default_safety_unchanged.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot1_ohlcvt_parser.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot1_required_scripts_and_validation.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot1_catalog.py`
- `tests/test_lot1_data_dirs.py`
- `tests/test_lot1_data_quality.py`
- `tests/test_lot1_data_writer_and_checksum.py`
- `tests/test_lot1_default_safety_unchanged.py`
- `tests/test_lot1_ohlcvt_parser.py`
- `tests/test_lot1_required_scripts_and_validation.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `docs/ACCEPTANCE_CRITERIA_LOT_02.md`
- `docs/LOT_02_REPORT.md`
- `reports/lot_02_feature_report.md`
- `reports/lot_02_multitimeframe_report.md`
- `scripts/build_lot2_datasets.py`
- `scripts/validate_lot2.py`
- `tests/__pycache__/test_lot2_build_datasets.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot2_feature_registry.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot2_features_basic.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot2_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot2_resampler.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot2_build_datasets.py`
- `tests/test_lot2_feature_registry.py`
- `tests/test_lot2_features_basic.py`
- `tests/test_lot2_invariants.py`
- `tests/test_lot2_resampler.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `docs/ACCEPTANCE_CRITERIA_LOT_03.md`
- `docs/LOT_03_REPORT.md`
- `reports/lot_03_pivot_report.md`
- `reports/lot_03_zone_report.md`
- `scripts/build_lot3_pivots.py`
- `scripts/validate_lot3.py`
- `tests/__pycache__/test_lot3_build_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot3_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot3_pivot_anti_lookahead.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot3_pivot_detector.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot3_price_zones.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot3_build_outputs.py`
- `tests/test_lot3_invariants.py`
- `tests/test_lot3_pivot_anti_lookahead.py`
- `tests/test_lot3_pivot_detector.py`
- `tests/test_lot3_price_zones.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `docs/ACCEPTANCE_CRITERIA_LOT_04.md`
- `docs/LOT_04_REPORT.md`
- `reports/lot_04_bis_validation_report.md`
- `reports/lot_04_quater_validation_report.md`
- `reports/lot_04_quinquies_validation_report.md`
- `reports/lot_04_septies_validation_report.md`
- `reports/lot_04_sexies_validation_report.md`
- `reports/lot_04_sexies_validation_report_full.md`
- `reports/lot_04_ter_validation_report.md`
- `reports/lot_04_volume_profile_report.md`
- `reports/lot_04_vwap_report.md`
- `reports/lot_10_octodecies_command_logs/02_diagnose_lot4_fd_lingering_owner.log`
- `reports/lot_10_octodecies_command_logs/02_diagnose_lot4_fd_lingering_owner.rc`
- `reports/lot_10_octodecies_command_logs/03_validate_lot4_exact_mini_chain.log`
- `reports/lot_10_octodecies_command_logs/03_validate_lot4_exact_mini_chain.rc`
- `reports/lot_10_octodecies_command_logs/04_diagnose_lot4_validate_after_chain.log`
- `reports/lot_10_octodecies_command_logs/04_diagnose_lot4_validate_after_chain.rc`
- `reports/lot_10_quindecies_command_logs/02_diagnose_lot4_validate_after_chain.log`
- `reports/lot_10_quindecies_command_logs/10_validate_lot4_exact_mini_chain.log`
- `reports/lot_10_septendecies_command_logs/04_diagnose_lot4_validate_after_chain.log`
- `reports/lot_10_sexdecies_command_logs/02_diagnose_lot4_validate_after_chain.log`
- `reports/lot_10_sexdecies_command_logs/02_diagnose_lot4_validate_after_chain.rc`
- `scripts/build_lot4_volume_vwap.py`
- `scripts/diagnose_lot4_fd_lingering_owner.py`
- `scripts/diagnose_lot4_validate_after_chain.py`
- `scripts/validate_all_until_lot4.py`
- `scripts/validate_all_until_lot4.sh`
- `scripts/validate_lot4.py`
- `tests/__pycache__/test_aaa_lot4_validate_all_terminates.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot4_anchored_vwap.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot4_build_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot4_chain_scripts_no_background_or_fd_hacks.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot4_fd_lingering_owner_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot4_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot4_pytest_config.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot4_validate_after_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot4_validation_terminates.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot4_volume_profile.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot4_vwap.cpython-313-pytest-9.0.2.pyc`
- `tests/test_aaa_lot4_validate_all_terminates.py`
- `tests/test_lot4_anchored_vwap.py`
- `tests/test_lot4_build_outputs.py`
- `tests/test_lot4_chain_scripts_no_background_or_fd_hacks.py`
- `tests/test_lot4_fd_lingering_owner_static.py`
- `tests/test_lot4_invariants.py`
- `tests/test_lot4_pytest_config.py`
- `tests/test_lot4_validate_after_chain_static.py`
- `tests/test_lot4_validation_terminates.py`
- `tests/test_lot4_volume_profile.py`
- `tests/test_lot4_vwap.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `docs/ACCEPTANCE_CRITERIA_LOT_05.md`
- `docs/LOT_05_REPORT.md`
- `reports/lot_05_bis_validation_report.md`
- `reports/lot_05_range_state_report.md`
- `reports/lot_05_ter_validation_report.md`
- `reports/lot_05_validation_report.md`
- `reports/lot_05_volatility_report.md`
- `reports/lot_10_octodecies_command_logs/05_diagnose_lot5_validate_after_chain.log`
- `reports/lot_10_octodecies_command_logs/05_diagnose_lot5_validate_after_chain.rc`
- `reports/lot_10_quaterdecies_command_logs/02_diagnose_lot5_validate_after_chain.duration`
- `reports/lot_10_quaterdecies_command_logs/02_diagnose_lot5_validate_after_chain.log`
- `reports/lot_10_quaterdecies_command_logs/02_diagnose_lot5_validate_after_chain.rc`
- `reports/lot_10_quaterdecies_command_logs/09_validate_lot5_exact_mini_chain.duration`
- `reports/lot_10_quaterdecies_command_logs/09_validate_lot5_exact_mini_chain.log`
- `reports/lot_10_quaterdecies_command_logs/09_validate_lot5_exact_mini_chain.rc`
- `reports/lot_10_quindecies_command_logs/03_diagnose_lot5_validate_after_chain.log`
- `reports/lot_10_septendecies_command_logs/02_diagnose_lot5_fd_lingering_owner.log`
- `reports/lot_10_septendecies_command_logs/05_diagnose_lot5_validate_after_chain.log`
- `reports/lot_10_sexdecies_command_logs/03_diagnose_lot5_validate_after_chain.log`
- `reports/lot_10_sexdecies_command_logs/03_diagnose_lot5_validate_after_chain.rc`
- `scripts/build_lot5_volatility.py`
- `scripts/build_lot5_volatility_impl.py`
- `scripts/diagnose_lot5_fd_lingering_owner.py`
- `scripts/diagnose_lot5_validate_after_chain.py`
- `scripts/validate_all_until_lot5.py`
- `scripts/validate_all_until_lot5.sh`
- `scripts/validate_lot5.py`
- `tests/__pycache__/test_lot5_atr.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot5_build_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot5_diagnostics_return_shell_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot5_feature_registry.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot5_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot5_orchestrator_smoke_mode.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot5_range_state.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot5_validate_after_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot5_validate_all_terminates.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot5_volatility.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot5_atr.py`
- `tests/test_lot5_build_outputs.py`
- `tests/test_lot5_diagnostics_return_shell_static.py`
- `tests/test_lot5_feature_registry.py`
- `tests/test_lot5_invariants.py`
- `tests/test_lot5_orchestrator_smoke_mode.py`
- `tests/test_lot5_range_state.py`
- `tests/test_lot5_validate_after_chain_static.py`
- `tests/test_lot5_validate_all_terminates.py`
- `tests/test_lot5_volatility.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `docs/ACCEPTANCE_CRITERIA_LOT_06.md`
- `docs/LOT_06_REPORT.md`
- `reports/lot_06_regime_report.md`
- `reports/lot_06_validation_report.md`
- `scripts/build_lot6_regime.py`
- `scripts/diagnose_lot6_validate_after_chain.py`
- `scripts/validate_all_until_lot6.py`
- `scripts/validate_all_until_lot6.sh`
- `scripts/validate_lot6.py`
- `tests/__pycache__/test_lot6_build_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot6_classifier.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot6_feature_registry.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot6_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot6_orchestrator_smoke_mode.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot6_regime_contract.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot6_trend_score.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot6_validate_after_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot6_validate_all_terminates.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot6_build_outputs.py`
- `tests/test_lot6_classifier.py`
- `tests/test_lot6_feature_registry.py`
- `tests/test_lot6_invariants.py`
- `tests/test_lot6_orchestrator_smoke_mode.py`
- `tests/test_lot6_regime_contract.py`
- `tests/test_lot6_trend_score.py`
- `tests/test_lot6_validate_after_chain_static.py`
- `tests/test_lot6_validate_all_terminates.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `docs/ACCEPTANCE_CRITERIA_LOT_07.md`
- `docs/LOT_07_REPORT.md`
- `reports/lot_07_market_state_report.md`
- `reports/lot_07_validation_report.md`
- `reports/lot_10_duodecies_command_logs/02_diagnose_lot7_build_after_chain.log`
- `reports/lot_10_duodecies_command_logs/02_diagnose_lot7_build_after_chain.rc`
- `reports/lot_10_octodecies_command_logs/06_diagnose_lot7_build_after_chain.log`
- `reports/lot_10_octodecies_command_logs/06_diagnose_lot7_build_after_chain.rc`
- `reports/lot_10_quaterdecies_command_logs/03_diagnose_lot7_build_after_chain.duration`
- `reports/lot_10_quaterdecies_command_logs/03_diagnose_lot7_build_after_chain.log`
- `reports/lot_10_quaterdecies_command_logs/03_diagnose_lot7_build_after_chain.rc`
- `reports/lot_10_quindecies_command_logs/04_diagnose_lot7_build_after_chain.log`
- `reports/lot_10_septendecies_command_logs/06_diagnose_lot7_build_after_chain.log`
- `reports/lot_10_sexdecies_command_logs/04_diagnose_lot7_build_after_chain.log`
- `reports/lot_10_sexdecies_command_logs/04_diagnose_lot7_build_after_chain.rc`
- `reports/lot_10_terdecies_command_logs/02_diagnose_lot7_build_after_chain.log`
- `reports/lot_10_terdecies_command_logs/02_diagnose_lot7_build_after_chain.rc`
- `reports/lot_10_undecies_command_logs/02_diagnose_lot7_build_after_chain.log`
- `reports/lot_10_undecies_command_logs/02_diagnose_lot7_build_after_chain.rc`
- `reports/lot_10_undecies_command_logs/02_diagnose_lot7_build_after_chain.seconds`
- `reports/lot_10_undecies_command_logs/12_build_lot7_exact_mini_chain.log`
- `reports/lot_10_undecies_command_logs/12_build_lot7_exact_mini_chain.rc`
- `reports/lot_10_undecies_command_logs/12_build_lot7_exact_mini_chain.seconds`
- `reports/lot_23_bis_lot7_jsonl_robustness_report.md`
- `scripts/__pycache__/build_lot7_market_state.cpython-313.pyc`
- `scripts/__pycache__/diagnose_lot7_market_state_jsonl.cpython-313.pyc`
- `scripts/__pycache__/validate_lot7.cpython-313.pyc`
- `scripts/build_lot7_market_state.py`
- `scripts/diagnose_lot7_build_after_chain.py`
- `scripts/diagnose_lot7_market_state_jsonl.py`
- `scripts/validate_all_until_lot7.py`
- `scripts/validate_all_until_lot7.sh`
- `scripts/validate_lot7.py`
- `tests/__pycache__/test_lot23_bis_lot7_chain_stability.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_bis_lot7_chain_stability.cpython-313.pyc`
- `tests/__pycache__/test_lot7_available_at.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot7_build_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot7_build_terminates_after_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot7_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot7_market_state_assembly.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot7_market_state_contract.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot7_market_state_jsonl_robustness.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot7_nearest_pivots_zones.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot7_orchestrator_smoke_mode.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot7_validate_all_terminates.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot23_bis_lot7_chain_stability.py`
- `tests/test_lot7_available_at.py`
- `tests/test_lot7_build_outputs.py`
- `tests/test_lot7_build_terminates_after_chain_static.py`
- `tests/test_lot7_invariants.py`
- `tests/test_lot7_market_state_assembly.py`
- `tests/test_lot7_market_state_contract.py`
- `tests/test_lot7_market_state_jsonl_robustness.py`
- `tests/test_lot7_nearest_pivots_zones.py`
- `tests/test_lot7_orchestrator_smoke_mode.py`
- `tests/test_lot7_validate_all_terminates.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/feature_registry_audit_lot8.json`
- `data/audit/no_lookahead_audit_lot8.json`
- `docs/ACCEPTANCE_CRITERIA_LOT_08.md`
- `docs/LOT_08_REPORT.md`
- `reports/lot_08_feature_registry_audit_report.md`
- `reports/lot_08_no_lookahead_report.md`
- `reports/lot_10_decies_command_logs/02_audit_lot8_no_lookahead.log`
- `reports/lot_10_decies_command_logs/02_audit_lot8_no_lookahead.rc`
- `reports/lot_10_decies_command_logs/03_diagnose_lot8_no_lookahead_after_chain.log`
- `reports/lot_10_decies_command_logs/03_diagnose_lot8_no_lookahead_after_chain.rc`
- `reports/lot_10_duodecies_command_logs/03_diagnose_lot8_no_lookahead_after_chain.log`
- `reports/lot_10_duodecies_command_logs/03_diagnose_lot8_no_lookahead_after_chain.rc`
- `reports/lot_10_octodecies_command_logs/07_diagnose_lot8_no_lookahead_after_chain.log`
- `reports/lot_10_octodecies_command_logs/07_diagnose_lot8_no_lookahead_after_chain.rc`
- `reports/lot_10_quaterdecies_command_logs/04_diagnose_lot8_no_lookahead_after_chain.duration`
- `reports/lot_10_quaterdecies_command_logs/04_diagnose_lot8_no_lookahead_after_chain.log`
- `reports/lot_10_quaterdecies_command_logs/04_diagnose_lot8_no_lookahead_after_chain.rc`
- `reports/lot_10_quindecies_command_logs/05_diagnose_lot8_no_lookahead_after_chain.log`
- `reports/lot_10_septendecies_command_logs/07_diagnose_lot8_no_lookahead_after_chain.log`
- `reports/lot_10_sexdecies_command_logs/05_diagnose_lot8_no_lookahead_after_chain.log`
- `reports/lot_10_sexdecies_command_logs/05_diagnose_lot8_no_lookahead_after_chain.rc`
- `reports/lot_10_terdecies_command_logs/03_diagnose_lot8_no_lookahead_after_chain.log`
- `reports/lot_10_terdecies_command_logs/03_diagnose_lot8_no_lookahead_after_chain.rc`
- `reports/lot_10_undecies_command_logs/03_audit_lot8_no_lookahead.log`
- `reports/lot_10_undecies_command_logs/03_audit_lot8_no_lookahead.rc`
- `reports/lot_10_undecies_command_logs/03_audit_lot8_no_lookahead.seconds`
- `reports/lot_10_undecies_command_logs/04_diagnose_lot8_no_lookahead_after_chain.log`
- `reports/lot_10_undecies_command_logs/04_diagnose_lot8_no_lookahead_after_chain.rc`
- `reports/lot_10_undecies_command_logs/04_diagnose_lot8_no_lookahead_after_chain.seconds`
- `scripts/audit_lot8_feature_registry.py`
- `scripts/audit_lot8_no_lookahead.py`
- `scripts/diagnose_lot8_no_lookahead_after_chain.py`
- `scripts/validate_all_until_lot8.py`
- `scripts/validate_all_until_lot8.sh`
- `scripts/validate_lot8.py`
- `tests/__pycache__/test_lot8_audit_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot8_available_at_audit.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot8_feature_registry_atomic_write_shared_fs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot8_feature_registry_audit.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot8_forbidden_names.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot8_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot8_no_lookahead_after_chain_terminates.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot8_no_lookahead_audit.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot8_no_lookahead_audit_is_bounded.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot8_orchestrator_smoke_mode.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot8_validate_all_terminates.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot8_audit_outputs.py`
- `tests/test_lot8_available_at_audit.py`
- `tests/test_lot8_feature_registry_atomic_write_shared_fs.py`
- `tests/test_lot8_feature_registry_audit.py`
- `tests/test_lot8_forbidden_names.py`
- `tests/test_lot8_invariants.py`
- `tests/test_lot8_no_lookahead_after_chain_terminates.py`
- `tests/test_lot8_no_lookahead_audit.py`
- `tests/test_lot8_no_lookahead_audit_is_bounded.py`
- `tests/test_lot8_orchestrator_smoke_mode.py`
- `tests/test_lot8_validate_all_terminates.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/backtest_lot9_15m_steps.jsonl`
- `data/audit/backtest_lot9_5m_steps.jsonl`
- `data/audit/backtest_lot9_run_config.json`
- `data/audit/backtest_lot9_run_result.json`
- `docs/ACCEPTANCE_CRITERIA_LOT_09.md`
- `docs/LOT_09_REPORT.md`
- `reports/lot_09_backtest_replay_report.md`
- `reports/lot_09_bis_validation_report.md`
- `reports/lot_09_quater_validation_report.md`
- `reports/lot_09_quinquies_validation_report.md`
- `reports/lot_09_sexies_validation_report.md`
- `reports/lot_09_ter_validation_report.md`
- `scripts/run_lot9_backtest_replay.py`
- `scripts/run_required_chain_until_lot9.sh`
- `scripts/validate_all_until_lot9.py`
- `scripts/validate_all_until_lot9.sh`
- `scripts/validate_lot9.py`
- `tests/__pycache__/test_lot9_backtest_contracts.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_dataset_catalog_stability.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_dataset_catalog_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_lingering_process_diagnostic.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_lookahead_guard.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_noop_policy.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_orchestrator_smoke_mode.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_pytest_after_chain_diagnostic.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_replay_ordering.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_required_chain_smoke_subset_is_passive.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_required_chain_stability.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_run_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot9_validate_all_terminates.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot9_backtest_contracts.py`
- `tests/test_lot9_dataset_catalog_stability.py`
- `tests/test_lot9_dataset_catalog_static.py`
- `tests/test_lot9_invariants.py`
- `tests/test_lot9_lingering_process_diagnostic.py`
- `tests/test_lot9_lookahead_guard.py`
- `tests/test_lot9_noop_policy.py`
- `tests/test_lot9_orchestrator_smoke_mode.py`
- `tests/test_lot9_pytest_after_chain_diagnostic.py`
- `tests/test_lot9_replay_ordering.py`
- `tests/test_lot9_required_chain_smoke_subset_is_passive.py`
- `tests/test_lot9_required_chain_stability.py`
- `tests/test_lot9_run_outputs.py`
- `tests/test_lot9_validate_all_terminates.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/transaction_cost_lot10_15m_estimates.jsonl`
- `data/audit/transaction_cost_lot10_5m_estimates.jsonl`
- `data/audit/transaction_cost_lot10_run_result.json`
- `docs/ACCEPTANCE_CRITERIA_LOT_10.md`
- `docs/LOT_10_REPORT.md`
- `reports/lot_10_bis_validation_report.md`
- `reports/lot_10_decies_command_logs/04_run_lot10_transaction_costs.log`
- `reports/lot_10_decies_command_logs/04_run_lot10_transaction_costs.rc`
- `reports/lot_10_decies_command_logs/05_validate_lot10.log`
- `reports/lot_10_decies_command_logs/05_validate_lot10.rc`
- `reports/lot_10_decies_command_logs/06_validate_all_until_lot10.log`
- `reports/lot_10_decies_command_logs/06_validate_all_until_lot10.rc`
- `reports/lot_10_decies_command_logs/07_run_required_chain_until_lot10.log`
- `reports/lot_10_decies_command_logs/07_run_required_chain_until_lot10.rc`
- `reports/lot_10_decies_command_logs/08_diagnose_lot10_required_chain_timing.log`
- `reports/lot_10_decies_command_logs/08_diagnose_lot10_required_chain_timing.rc`
- `reports/lot_10_decies_command_logs/09_diagnose_exact_chain_until_lot10.log`
- `reports/lot_10_decies_command_logs/09_diagnose_exact_chain_until_lot10.rc`
- `reports/lot_10_decies_validation_report.md`
- `reports/lot_10_duodecies_command_logs/04_diagnose_exact_chain_until_lot10.log`
- `reports/lot_10_duodecies_command_logs/04_diagnose_exact_chain_until_lot10.rc`
- `reports/lot_10_duodecies_command_logs/diagnose_after_pytest_lingering_pytest_after_lot10.log`
- `reports/lot_10_duodecies_validation_report.md`
- `reports/lot_10_nonies_command_logs/diagnose_exact_chain_until_lot10.log`
- `reports/lot_10_nonies_command_logs/diagnose_exact_chain_until_lot10.rc`
- `reports/lot_10_nonies_command_logs/diagnose_lot10_required_chain_timing.log`
- `reports/lot_10_nonies_command_logs/diagnose_lot10_required_chain_timing.rc`
- `reports/lot_10_nonies_command_logs/run_lot10_transaction_costs.log`
- `reports/lot_10_nonies_command_logs/run_lot10_transaction_costs.rc`
- `reports/lot_10_nonies_command_logs/run_required_chain_until_lot10.log`
- `reports/lot_10_nonies_command_logs/run_required_chain_until_lot10.rc`
- `reports/lot_10_nonies_command_logs/validate_all_until_lot10.log`
- `reports/lot_10_nonies_command_logs/validate_all_until_lot10.rc`
- `reports/lot_10_nonies_command_logs/validate_all_until_lot10_smoke.log`
- `reports/lot_10_nonies_command_logs/validate_all_until_lot10_smoke.rc`
- `reports/lot_10_nonies_command_logs/validate_lot10.log`
- `reports/lot_10_nonies_command_logs/validate_lot10.rc`
- `reports/lot_10_nonies_validation_report.md`
- `reports/lot_10_novemdecies_validation_report.md`
- `reports/lot_10_octies_validation_report.md`
- `reports/lot_10_octodecies_command_logs/08_diagnose_exact_chain_until_lot10.log`
- `reports/lot_10_octodecies_command_logs/08_diagnose_exact_chain_until_lot10.rc`
- `reports/lot_10_octodecies_validation_report.md`
- `reports/lot_10_quater_validation_report.md`
- `reports/lot_10_quaterdecies_command_logs/05_diagnose_exact_chain_until_lot10.duration`
- `reports/lot_10_quaterdecies_command_logs/05_diagnose_exact_chain_until_lot10.log`
- `reports/lot_10_quaterdecies_command_logs/05_diagnose_exact_chain_until_lot10.rc`
- `reports/lot_10_quaterdecies_validation_report.md`
- `reports/lot_10_quindecies_command_logs/06_diagnose_exact_chain_until_lot10.log`
- `reports/lot_10_quindecies_validation_report.md`
- `reports/lot_10_quinquies_validation_report.md`
- `reports/lot_10_septendecies_command_logs/08_diagnose_exact_chain_until_lot10.log`
- `reports/lot_10_septendecies_validation_report.md`
- `reports/lot_10_septies_validation_report.md`
- `reports/lot_10_sexdecies_command_logs/06_diagnose_exact_chain_until_lot10.log`
- `reports/lot_10_sexdecies_command_logs/06_diagnose_exact_chain_until_lot10.rc`
- `reports/lot_10_sexdecies_validation_report.md`
- `reports/lot_10_sexies_validation_report.md`
- `reports/lot_10_ter_validation_report.md`
- `reports/lot_10_terdecies_command_logs/04_diagnose_exact_chain_until_lot10.log`
- `reports/lot_10_terdecies_command_logs/04_diagnose_exact_chain_until_lot10.meta`
- `reports/lot_10_terdecies_command_logs/04_diagnose_exact_chain_until_lot10.rc`
- `reports/lot_10_terdecies_command_logs/diagnose_after_pytest_lingering_pytest_after_lot10.log`
- `reports/lot_10_terdecies_validation_report.md`
- `reports/lot_10_transaction_costs_report.md`
- `reports/lot_10_undecies_command_logs/05_run_lot10_transaction_costs.log`
- `reports/lot_10_undecies_command_logs/05_run_lot10_transaction_costs.rc`
- `reports/lot_10_undecies_command_logs/05_run_lot10_transaction_costs.seconds`
- `reports/lot_10_undecies_command_logs/06_validate_lot10.log`
- `reports/lot_10_undecies_command_logs/06_validate_lot10.rc`
- `reports/lot_10_undecies_command_logs/06_validate_lot10.seconds`
- `reports/lot_10_undecies_command_logs/07_validate_all_until_lot10.log`
- `reports/lot_10_undecies_command_logs/07_validate_all_until_lot10.rc`
- `reports/lot_10_undecies_command_logs/07_validate_all_until_lot10.seconds`
- `reports/lot_10_undecies_command_logs/08_run_required_chain_until_lot10.log`
- `reports/lot_10_undecies_command_logs/08_run_required_chain_until_lot10.rc`
- `reports/lot_10_undecies_command_logs/08_run_required_chain_until_lot10.seconds`
- `reports/lot_10_undecies_command_logs/09_diagnose_lot10_required_chain_timing.log`
- `reports/lot_10_undecies_command_logs/09_diagnose_lot10_required_chain_timing.rc`
- `reports/lot_10_undecies_command_logs/09_diagnose_lot10_required_chain_timing.seconds`
- `reports/lot_10_undecies_command_logs/10_diagnose_exact_chain_until_lot10.log`
- `reports/lot_10_undecies_command_logs/10_diagnose_exact_chain_until_lot10.rc`
- `reports/lot_10_undecies_command_logs/10_diagnose_exact_chain_until_lot10.seconds`
- `reports/lot_10_undecies_validation_report.md`
- `reports/lot_10_validation_report.md`
- `reports/lot_23_quinquies_lot16_after_lot10_diagnostic_report.md`
- `reports/lot_23_ter_lot10_writer_robustness_report.md`
- `scripts/check_lot10_passive_smoke.py`
- `scripts/diagnose_exact_chain_until_lot10.py`
- `scripts/diagnose_lot10_chain.py`
- `scripts/diagnose_lot10_lingering_processes.py`
- `scripts/diagnose_lot10_required_chain_timing.py`
- `scripts/diagnose_lot10_transaction_cost_writer.py`
- `scripts/run_lot10_transaction_costs.py`
- `scripts/run_required_chain_until_lot10.sh`
- `scripts/validate_all_until_lot10.py`
- `scripts/validate_all_until_lot10.sh`
- `scripts/validate_lot10.py`
- `tests/__pycache__/test_lot10_cost_contracts.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_diagnostic_is_non_mutating.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_estimator_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_fee_model.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_lingering_process_diagnostic.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_orchestrator_smoke_mode.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_outputs_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_required_chain_fast_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_required_chain_no_shell_lingering_check.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_required_chain_smoke_subset_is_passive.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_spread_slippage.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_transaction_cost_writer_atomicity.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_validate_all_fast_is_passive.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_validate_all_no_pytest_nested.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot10_validate_all_terminates.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_quinquies_lot16_after_lot10_diagnostic.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_ter_lot10_chain_stability.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_ter_lot10_chain_stability.cpython-313.pyc`
- `tests/test_lot10_cost_contracts.py`
- `tests/test_lot10_diagnostic_is_non_mutating.py`
- `tests/test_lot10_estimator_outputs.py`
- `tests/test_lot10_fee_model.py`
- `tests/test_lot10_invariants.py`
- `tests/test_lot10_lingering_process_diagnostic.py`
- `tests/test_lot10_orchestrator_smoke_mode.py`
- `tests/test_lot10_outputs_static.py`
- `tests/test_lot10_required_chain_fast_static.py`
- `tests/test_lot10_required_chain_no_shell_lingering_check.py`
- `tests/test_lot10_required_chain_smoke_subset_is_passive.py`
- `tests/test_lot10_spread_slippage.py`
- `tests/test_lot10_transaction_cost_writer_atomicity.py`
- `tests/test_lot10_validate_all_fast_is_passive.py`
- `tests/test_lot10_validate_all_no_pytest_nested.py`
- `tests/test_lot10_validate_all_terminates.py`
- `tests/test_lot23_quinquies_lot16_after_lot10_diagnostic.py`
- `tests/test_lot23_ter_lot10_chain_stability.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/risk_engine_lot11_15m.jsonl`
- `data/audit/risk_engine_lot11_5m.jsonl`
- `docs/ACCEPTANCE_CRITERIA_LOT_11.md`
- `docs/LOT_11_RISK_ENGINE.md`
- `reports/lot_11_risk_engine_report.md`
- `reports/lot_11_validation_report.md`
- `scripts/diagnose_exact_chain_until_lot11.py`
- `scripts/diagnose_lot11_required_chain_timing.py`
- `scripts/run_lot11_risk_engine.py`
- `scripts/run_required_chain_until_lot11.sh`
- `scripts/validate_all_until_lot11.py`
- `scripts/validate_all_until_lot11.sh`
- `scripts/validate_lot11.py`
- `tests/__pycache__/test_lot11_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot11_no_trading_semantics.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot11_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot11_risk_engine_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot11_risk_engine_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot11_diagnostics_static.py`
- `tests/test_lot11_no_trading_semantics.py`
- `tests/test_lot11_required_chain_static.py`
- `tests/test_lot11_risk_engine_invariants.py`
- `tests/test_lot11_risk_engine_outputs.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/exposure_guard_lot12_15m.jsonl`
- `data/audit/exposure_guard_lot12_5m.jsonl`
- `docs/ACCEPTANCE_CRITERIA_LOT_12.md`
- `docs/LOT_12_EXPOSURE_GUARD.md`
- `reports/lot_12_exposure_guard_report.md`
- `reports/lot_12_validation_report.md`
- `scripts/diagnose_exact_chain_until_lot12.py`
- `scripts/diagnose_lot12_required_chain_timing.py`
- `scripts/run_lot12_exposure_guard.py`
- `scripts/run_required_chain_until_lot12.sh`
- `scripts/validate_all_until_lot12.py`
- `scripts/validate_all_until_lot12.sh`
- `scripts/validate_lot12.py`
- `tests/__pycache__/test_lot12_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot12_exposure_guard_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot12_exposure_guard_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot12_no_trading_semantics.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot12_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot12_diagnostics_static.py`
- `tests/test_lot12_exposure_guard_invariants.py`
- `tests/test_lot12_exposure_guard_outputs.py`
- `tests/test_lot12_no_trading_semantics.py`
- `tests/test_lot12_required_chain_static.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/portfolio_freeze_lot13_15m.jsonl`
- `data/audit/portfolio_freeze_lot13_5m.jsonl`
- `docs/ACCEPTANCE_CRITERIA_LOT_13.md`
- `docs/LOT_13_PORTFOLIO_FREEZE.md`
- `reports/lot_13_portfolio_freeze_report.md`
- `reports/lot_13_validation_report.md`
- `scripts/diagnose_exact_chain_until_lot13.py`
- `scripts/diagnose_lot13_required_chain_timing.py`
- `scripts/run_lot13_portfolio_freeze.py`
- `scripts/run_required_chain_until_lot13.sh`
- `scripts/validate_all_until_lot13.py`
- `scripts/validate_lot13.py`
- `tests/__pycache__/test_lot13_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot13_no_trading_semantics.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot13_portfolio_freeze_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot13_portfolio_freeze_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot13_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot13_diagnostics_static.py`
- `tests/test_lot13_no_trading_semantics.py`
- `tests/test_lot13_portfolio_freeze_invariants.py`
- `tests/test_lot13_portfolio_freeze_outputs.py`
- `tests/test_lot13_required_chain_static.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/final_decision_firewall_lot14_15m.jsonl`
- `data/audit/final_decision_firewall_lot14_5m.jsonl`
- `docs/ACCEPTANCE_CRITERIA_LOT_14.md`
- `docs/LOT_14_DECISION_FIREWALL.md`
- `reports/lot_14_decision_firewall_report.md`
- `reports/lot_14_validation_report.md`
- `scripts/diagnose_exact_chain_until_lot14.py`
- `scripts/diagnose_lot14_required_chain_timing.py`
- `scripts/run_lot14_decision_firewall.py`
- `scripts/run_required_chain_until_lot14.sh`
- `scripts/validate_all_until_lot14.py`
- `scripts/validate_lot14.py`
- `tests/__pycache__/test_lot14_decision_firewall_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot14_decision_firewall_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot14_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot14_exact_chain_starts_clean_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot14_no_trading_semantics.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot14_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot14_decision_firewall_invariants.py`
- `tests/test_lot14_decision_firewall_outputs.py`
- `tests/test_lot14_diagnostics_static.py`
- `tests/test_lot14_exact_chain_starts_clean_static.py`
- `tests/test_lot14_no_trading_semantics.py`
- `tests/test_lot14_required_chain_static.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/decision_ledger_lot15_15m.jsonl`
- `data/audit/decision_ledger_lot15_5m.jsonl`
- `docs/ACCEPTANCE_CRITERIA_LOT_15.md`
- `docs/LOT_15_DECISION_LEDGER.md`
- `reports/lot_15_decision_ledger_report.md`
- `reports/lot_15_validation_report.md`
- `scripts/diagnose_exact_chain_until_lot15.py`
- `scripts/diagnose_lot15_required_chain_timing.py`
- `scripts/run_lot15_decision_ledger.py`
- `scripts/run_required_chain_until_lot15.sh`
- `scripts/validate_all_until_lot15.py`
- `scripts/validate_lot15.py`
- `tests/__pycache__/test_lot15_checksum_chain.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot15_decision_ledger_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot15_decision_ledger_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot15_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot15_no_trading_semantics.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot15_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot15_checksum_chain.py`
- `tests/test_lot15_decision_ledger_invariants.py`
- `tests/test_lot15_decision_ledger_outputs.py`
- `tests/test_lot15_diagnostics_static.py`
- `tests/test_lot15_no_trading_semantics.py`
- `tests/test_lot15_required_chain_static.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/reproducibility_artifacts_lot16.jsonl`
- `data/audit/reproducibility_manifest_lot16.json`
- `docs/ACCEPTANCE_CRITERIA_LOT_16.md`
- `docs/LOT_16_REPRODUCIBILITY.md`
- `reports/lot_16_reproducibility_report.md`
- `reports/lot_16_validation_report.md`
- `reports/lot_22_bis_lot16_checksum_stability_report.md`
- `reports/lot_23_quater_lot16_checksum_single_source_report.md`
- `reports/lot_23_quinquies_lot16_after_lot10_diagnostic_report.md`
- `scripts/__pycache__/run_lot16_reproducibility_manifest.cpython-313.pyc`
- `scripts/diagnose_exact_chain_until_lot16.py`
- `scripts/diagnose_lot16_required_chain_timing.py`
- `scripts/diagnose_lot16_source_catalog_checksum.py`
- `scripts/run_lot16_reproducibility_manifest.py`
- `scripts/run_required_chain_until_lot16.sh`
- `scripts/validate_all_until_lot16.py`
- `scripts/validate_lot16.py`
- `tests/__pycache__/test_lot16_artifact_lineage_checksums.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot16_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot16_no_trading_semantics.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot16_reproducibility_manifest_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot16_reproducibility_manifest_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot16_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot16_source_catalog_checksum_single_source.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot16_source_catalog_checksum_stable_after_v2_entries.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot16_source_catalog_checksum_stable_after_v2_entries.cpython-313.pyc`
- `tests/__pycache__/test_lot23_quater_lot16_return_shell_stability.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_quater_lot16_return_shell_stability.cpython-313.pyc`
- `tests/__pycache__/test_lot23_quinquies_lot16_after_lot10_diagnostic.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot16_artifact_lineage_checksums.py`
- `tests/test_lot16_diagnostics_static.py`
- `tests/test_lot16_no_trading_semantics.py`
- `tests/test_lot16_reproducibility_manifest_invariants.py`
- `tests/test_lot16_reproducibility_manifest_outputs.py`
- `tests/test_lot16_required_chain_static.py`
- `tests/test_lot16_source_catalog_checksum_single_source.py`
- `tests/test_lot16_source_catalog_checksum_stable_after_v2_entries.py`
- `tests/test_lot23_quater_lot16_return_shell_stability.py`
- `tests/test_lot23_quinquies_lot16_after_lot10_diagnostic.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/health_checks_lot17.jsonl`
- `data/audit/health_monitor_lot17.json`
- `docs/ACCEPTANCE_CRITERIA_LOT_17.md`
- `docs/LOT_17_HEALTH_MONITOR.md`
- `reports/lot_17_health_monitor_report.md`
- `reports/lot_17_validation_report.md`
- `scripts/__pycache__/run_lot17_health_monitor.cpython-313.pyc`
- `scripts/diagnose_exact_chain_until_lot17.py`
- `scripts/diagnose_lot17_required_chain_timing.py`
- `scripts/run_lot17_health_monitor.py`
- `scripts/run_required_chain_until_lot17.sh`
- `scripts/validate_all_until_lot17.py`
- `scripts/validate_lot17.py`
- `tests/__pycache__/test_lot17_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot17_health_monitor_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot17_health_monitor_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot17_integrity_checks.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot17_no_trading_semantics.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot17_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot17_diagnostics_static.py`
- `tests/test_lot17_health_monitor_invariants.py`
- `tests/test_lot17_health_monitor_outputs.py`
- `tests/test_lot17_integrity_checks.py`
- `tests/test_lot17_no_trading_semantics.py`
- `tests/test_lot17_required_chain_static.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/no_trading_compliance_checks_lot18.jsonl`
- `data/audit/no_trading_compliance_lot18.json`
- `docs/ACCEPTANCE_CRITERIA_LOT_18.md`
- `docs/LOT_18_NO_TRADING_COMPLIANCE.md`
- `reports/lot_18_no_trading_compliance_report.md`
- `reports/lot_18_validation_report.md`
- `scripts/diagnose_exact_chain_until_lot18.py`
- `scripts/diagnose_lot18_required_chain_timing.py`
- `scripts/run_lot18_no_trading_compliance.py`
- `scripts/run_required_chain_until_lot18.sh`
- `scripts/validate_all_until_lot18.py`
- `scripts/validate_lot18.py`
- `tests/__pycache__/test_lot18_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot18_forbidden_semantics.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot18_no_trading_compliance_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot18_no_trading_compliance_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot18_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot18_diagnostics_static.py`
- `tests/test_lot18_forbidden_semantics.py`
- `tests/test_lot18_no_trading_compliance_invariants.py`
- `tests/test_lot18_no_trading_compliance_outputs.py`
- `tests/test_lot18_required_chain_static.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/release_candidate_checks_lot19.jsonl`
- `data/audit/release_candidate_lot19.json`
- `docs/ACCEPTANCE_CRITERIA_LOT_19.md`
- `docs/LOT_19_RELEASE_CANDIDATE.md`
- `reports/lot_19_acceptance_bundle.md`
- `reports/lot_19_release_candidate_report.md`
- `reports/lot_19_validation_report.md`
- `scripts/__pycache__/diagnose_exact_chain_until_lot19.cpython-313.pyc`
- `scripts/diagnose_exact_chain_until_lot19.py`
- `scripts/diagnose_lot19_required_chain_timing.py`
- `scripts/run_lot19_release_candidate.py`
- `scripts/run_required_chain_until_lot19.sh`
- `scripts/validate_all_until_lot19.py`
- `scripts/validate_lot19.py`
- `tests/__pycache__/test_lot19_acceptance_bundle.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot19_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot19_no_archive_created.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot19_release_candidate_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot19_release_candidate_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot19_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot19_acceptance_bundle.py`
- `tests/test_lot19_diagnostics_static.py`
- `tests/test_lot19_no_archive_created.py`
- `tests/test_lot19_release_candidate_invariants.py`
- `tests/test_lot19_release_candidate_outputs.py`
- `tests/test_lot19_required_chain_static.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/v1_closure_checks_lot20.jsonl`
- `data/audit/v1_closure_lot20.json`
- `docs/ACCEPTANCE_CRITERIA_LOT_20.md`
- `docs/LOT_20_V1_CLOSURE.md`
- `reports/lot_20_archive_manifest.md`
- `reports/lot_20_v1_closure_report.md`
- `reports/lot_20_validation_report.md`
- `scripts/__pycache__/diagnose_exact_chain_until_lot20.cpython-313.pyc`
- `scripts/__pycache__/run_lot20_v1_closure.cpython-313.pyc`
- `scripts/__pycache__/validate_all_until_lot20.cpython-313.pyc`
- `scripts/__pycache__/validate_lot20.cpython-313.pyc`
- `scripts/__pycache__/validate_lot20_archive_extracted.cpython-313.pyc`
- `scripts/diagnose_exact_chain_until_lot20.py`
- `scripts/diagnose_lot20_required_chain_timing.py`
- `scripts/run_lot20_v1_closure.py`
- `scripts/run_required_chain_until_lot20.sh`
- `scripts/validate_all_until_lot20.py`
- `scripts/validate_lot20.py`
- `scripts/validate_lot20_archive_extracted.py`
- `tests/__pycache__/test_lot20_archive_integrity.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot20_closure_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot20_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot20_no_trading_semantics.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot20_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot20_v1_closure_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot20_archive_integrity.py`
- `tests/test_lot20_closure_invariants.py`
- `tests/test_lot20_diagnostics_static.py`
- `tests/test_lot20_no_trading_semantics.py`
- `tests/test_lot20_required_chain_static.py`
- `tests/test_lot20_v1_closure_outputs.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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
