# V10 — Research OS

Identifiant : `V10_RESEARCH_OS`  
Plage canonique : **Lots 96 à 102**  
Composant/domain owner : `ResearchOSDomain`  
Mode maximal autorisé : `RESEARCH_GOVERNANCE_ONLY`

## Finalité de la version

Faire évoluer le système de **Artefacts research disponibles** vers **Expériences, configs, releases et résultats traçables**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Artefacts research disponibles.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/research_os`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 96 — Research OS Foundation

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RESEARCH_GOVERNANCE_ONLY`  
**Composant propriétaire :** `ResearchOSDomain`  
**Frontière de code :** `src/crypto_quant_bot/research_os`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Research OS Foundation » dans Research OS, produire ResearchOSFoundationStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ResearchOSFoundationStateV1
- ResearchOSFoundationAuditV1
- ResearchOSFoundationContractRegistryV1
- ResearchOSFoundationCapabilityMatrixV1
- ExperimentRecordV1
- ResearchArtifactManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 96, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Research OS Foundation » dans le composant ResearchOSDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir frontières, responsabilités, dépendances autorisées, modes runtime et API publiques du domaine.
6. Classer chaque capability en REQUIRED, OPTIONAL_RESEARCH, DISABLED ou FORBIDDEN.
7. Enregistrer hypothesis, dataset, feature set, config, code commit, seed, metrics, result et conclusion.
8. Conserver résultats négatifs, superseded et rejected.
9. Relier tous les artefacts par content hash et lineage graph.
10. Empêcher metadata research de modifier permissions runtime.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/research_os/research_os_foundation.py
- src/crypto_quant_bot/research_os/research_os_foundation_models.py
- scripts/run_lot96_research_os_foundation.py
- scripts/validate_lot96.py
- tests/test_lot96_research_os_foundation.py
- data/audit/research_os_foundation_lot96.json
- reports/lot_96_research_os_foundation_report.md
- docs/LOT_96_RESEARCH_OS_FOUNDATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_96.md

### Observabilité minimale

- lot_96_records_processed_total
- lot_96_validation_failures_total
- lot_96_processing_latency_ms

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test de dépendances interdites entre domaines.
- Test de couverture : chaque capability a owner, contrat et gate.
- Re-run exact depuis registry.
- Suppression d’un résultat négatif détectée.

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
- Research metadata cannot alter runtime permissions

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 97 — Experiment Registry

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RESEARCH_GOVERNANCE_ONLY`  
**Composant propriétaire :** `ResearchOSDomain`  
**Frontière de code :** `src/crypto_quant_bot/research_os`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Experiment Registry » dans Research OS, produire ExperimentRegistryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ExperimentRegistryStateV1
- ExperimentRegistryAuditV1
- ExperimentRecordV1
- ResearchArtifactManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 97, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Experiment Registry » dans le composant ResearchOSDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Enregistrer hypothesis, dataset, feature set, config, code commit, seed, metrics, result et conclusion.
6. Conserver résultats négatifs, superseded et rejected.
7. Relier tous les artefacts par content hash et lineage graph.
8. Empêcher metadata research de modifier permissions runtime.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/research_os/experiment_registry.py
- src/crypto_quant_bot/research_os/experiment_registry_models.py
- scripts/run_lot97_experiment_registry.py
- scripts/validate_lot97.py
- tests/test_lot97_experiment_registry.py
- data/audit/experiment_registry_lot97.json
- reports/lot_97_experiment_registry_report.md
- docs/LOT_97_EXPERIMENT_REGISTRY.md
- docs/ACCEPTANCE_CRITERIA_LOT_97.md

### Observabilité minimale

- lot_97_records_processed_total
- lot_97_validation_failures_total
- lot_97_processing_latency_ms

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Re-run exact depuis registry.
- Suppression d’un résultat négatif détectée.

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
- Research metadata cannot alter runtime permissions

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 98 — Dataset, Feature, Configuration & Environment Versioning

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RESEARCH_GOVERNANCE_ONLY`  
**Composant propriétaire :** `ResearchOSDomain`  
**Frontière de code :** `src/crypto_quant_bot/research_os`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Dataset, Feature, Configuration & Environment Versioning » dans Research OS, produire DatasetFeatureConfigurationEnvironmentVersioningStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- DatasetFeatureConfigurationEnvironmentVersioningStateV1
- DatasetFeatureConfigurationEnvironmentVersioningAuditV1
- ConfigurationManifestV1
- EnvironmentProfileV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 98, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Dataset, Feature, Configuration & Environment Versioning » dans le composant ResearchOSDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir schémas config typés pour dev/test/backtest/paper/read-only/sandbox/live-disabled.
6. Séparer secrets des configs ; stocker uniquement secret references.
7. Calculer config checksum, approver, effective_from, expiry et rollback target.
8. Interdire différences non documentées entre backtest/paper/sandbox.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/research_os/dataset_feature_configuration_and_environment_versioning.py
- src/crypto_quant_bot/research_os/dataset_feature_configuration_and_environment_versioning_models.py
- scripts/run_lot98_dataset_feature_configuration_and_environment_versioning.py
- scripts/validate_lot98.py
- tests/test_lot98_dataset_feature_configuration_and_environment_versioning.py
- data/audit/dataset_feature_configuration_and_environment_versioning_lot98.json
- reports/lot_98_dataset_feature_configuration_and_environment_versioning_report.md
- docs/LOT_98_DATASET_FEATURE_CONFIGURATION_AND_ENVIRONMENT_VERSIONING.md
- docs/ACCEPTANCE_CRITERIA_LOT_98.md

### Observabilité minimale

- lot_98_records_processed_total
- lot_98_validation_failures_total
- lot_98_processing_latency_ms

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Unknown config key rejetée.
- Rollback restaure checksum exact.

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
- Research metadata cannot alter runtime permissions

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 99 — Hypothesis & Strategy Lifecycle Governance

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RESEARCH_GOVERNANCE_ONLY`  
**Composant propriétaire :** `ResearchOSDomain`  
**Frontière de code :** `src/crypto_quant_bot/research_os`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Hypothesis & Strategy Lifecycle Governance » dans Research OS, produire HypothesisStrategyLifecycleGovernanceStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- HypothesisStrategyLifecycleGovernanceStateV1
- HypothesisStrategyLifecycleGovernanceAuditV1
- AlphaHypothesisV1
- FalsificationPlanV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 99, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Hypothesis & Strategy Lifecycle Governance » dans le composant ResearchOSDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Décrire mécanisme économique/microstructure, population, horizon, régime, features permises et prédiction falsifiable.
6. Définir null hypothesis, métriques primaires, coûts attendus et conditions de rejet.
7. Enregistrer avant test pour éviter HARKing ; conserver résultats négatifs.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/research_os/hypothesis_and_strategy_lifecycle_governance.py
- src/crypto_quant_bot/research_os/hypothesis_and_strategy_lifecycle_governance_models.py
- scripts/run_lot99_hypothesis_and_strategy_lifecycle_governance.py
- scripts/validate_lot99.py
- tests/test_lot99_hypothesis_and_strategy_lifecycle_governance.py
- data/audit/hypothesis_and_strategy_lifecycle_governance_lot99.json
- reports/lot_99_hypothesis_and_strategy_lifecycle_governance_report.md
- docs/LOT_99_HYPOTHESIS_AND_STRATEGY_LIFECYCLE_GOVERNANCE.md
- docs/ACCEPTANCE_CRITERIA_LOT_99.md

### Observabilité minimale

- lot_99_records_processed_total
- lot_99_validation_failures_total
- lot_99_processing_latency_ms

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Hypothèse sans falsification rejetée.
- Modification post-résultat crée une nouvelle version.

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
- Research metadata cannot alter runtime permissions

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 100 — Ablation, Placebo & OOS Tracking

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RESEARCH_GOVERNANCE_ONLY`  
**Composant propriétaire :** `ResearchOSDomain`  
**Frontière de code :** `src/crypto_quant_bot/research_os`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Ablation, Placebo & OOS Tracking » dans Research OS, produire AblationPlaceboOOSTrackingStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- AblationPlaceboOOSTrackingStateV1
- AblationPlaceboOOSTrackingAuditV1
- PlaceboTestResultV1
- MultipleTestingReportV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 100, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Ablation, Placebo & OOS Tracking » dans le composant ResearchOSDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Comparer à labels/permutations/signaux aléatoires compatibles avec la dépendance temporelle.
6. Enregistrer nombre total d’hypothèses testées et correction choisie.
7. Refuser promotion si performance n’excède pas baselines/placebos de façon robuste.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/research_os/ablation_placebo_and_oos_tracking.py
- src/crypto_quant_bot/research_os/ablation_placebo_and_oos_tracking_models.py
- scripts/run_lot100_ablation_placebo_and_oos_tracking.py
- scripts/validate_lot100.py
- tests/test_lot100_ablation_placebo_and_oos_tracking.py
- data/audit/ablation_placebo_and_oos_tracking_lot100.json
- reports/lot_100_ablation_placebo_and_oos_tracking_report.md
- docs/LOT_100_ABLATION_PLACEBO_AND_OOS_TRACKING.md
- docs/ACCEPTANCE_CRITERIA_LOT_100.md

### Observabilité minimale

- lot_100_records_processed_total
- lot_100_validation_failures_total
- lot_100_processing_latency_ms

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Random baseline reproduite par seed.
- Correction multiple-testing appliquée au bon univers.

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
- Research metadata cannot alter runtime permissions

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 101 — Research Report, Knowledge Base & Artifact Registry

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RESEARCH_GOVERNANCE_ONLY`  
**Composant propriétaire :** `ResearchOSDomain`  
**Frontière de code :** `src/crypto_quant_bot/research_os`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Research Report, Knowledge Base & Artifact Registry » dans Research OS, produire ResearchReportKnowledgeBaseArtifactRegistryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ResearchReportKnowledgeBaseArtifactRegistryStateV1
- ResearchReportKnowledgeBaseArtifactRegistryAuditV1
- ExperimentRecordV1
- ResearchArtifactManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 101, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Research Report, Knowledge Base & Artifact Registry » dans le composant ResearchOSDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Enregistrer hypothesis, dataset, feature set, config, code commit, seed, metrics, result et conclusion.
6. Conserver résultats négatifs, superseded et rejected.
7. Relier tous les artefacts par content hash et lineage graph.
8. Empêcher metadata research de modifier permissions runtime.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/research_os/research_report_knowledge_base_and_artifact_registry.py
- src/crypto_quant_bot/research_os/research_report_knowledge_base_and_artifact_registry_models.py
- scripts/run_lot101_research_report_knowledge_base_and_artifact_registry.py
- scripts/validate_lot101.py
- tests/test_lot101_research_report_knowledge_base_and_artifact_registry.py
- data/audit/research_report_knowledge_base_and_artifact_registry_lot101.json
- reports/lot_101_research_report_knowledge_base_and_artifact_registry_report.md
- docs/LOT_101_RESEARCH_REPORT_KNOWLEDGE_BASE_AND_ARTIFACT_REGISTRY.md
- docs/ACCEPTANCE_CRITERIA_LOT_101.md

### Observabilité minimale

- lot_101_records_processed_total
- lot_101_validation_failures_total
- lot_101_processing_latency_ms

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Re-run exact depuis registry.
- Suppression d’un résultat négatif détectée.

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
- Research metadata cannot alter runtime permissions

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 102 — CI/CD, Release Governance & V10 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RESEARCH_GOVERNANCE_ONLY`  
**Composant propriétaire :** `ResearchOSDomain`  
**Frontière de code :** `src/crypto_quant_bot/research_os`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « CI/CD, Release Governance & V10 Closure » dans Research OS, produire CICDReleaseGovernanceV10ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- CICDReleaseGovernanceV10ClosureStateV1
- CICDReleaseGovernanceV10ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- ReleaseManifestV1
- CIEvidenceV1
- RollbackPlanV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 102, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « CI/CD, Release Governance & V10 Closure » dans le composant ResearchOSDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Exécuter unit, integration, contract, replay, anti-lookahead, security, dependency et forbidden-capability tests.
10. Signer/hasher artefacts, configs et source commit.
11. Définir promotion environment, rollback conditions et immutable release id.
12. Aucun déploiement si check requis absent/neutralisé.

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

- scripts/validate_all_until_lot102.py
- scripts/run_required_chain_until_lot102.sh
- scripts/diagnose_exact_chain_until_lot102.py
- tests/test_lot102_closure_contract.py
- data/audit/closure_manifest_lot102.json
- reports/lot_102_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_102.md
- src/crypto_quant_bot/research_os/ci_cd_release_governance_and_v10_closure.py
- src/crypto_quant_bot/research_os/ci_cd_release_governance_and_v10_closure_models.py
- scripts/run_lot102_ci_cd_release_governance_and_v10_closure.py
- scripts/validate_lot102.py
- tests/test_lot102_ci_cd_release_governance_and_v10_closure.py
- data/audit/ci_cd_release_governance_and_v10_closure_lot102.json
- reports/lot_102_ci_cd_release_governance_and_v10_closure_report.md
- docs/LOT_102_CI_CD_RELEASE_GOVERNANCE_AND_V10_CLOSURE.md

### Observabilité minimale

- lot_102_records_processed_total
- lot_102_validation_failures_total
- lot_102_processing_latency_ms

### Tests et critères d’acceptation

- Chaque résultat lié à versions exactes
- Résultats négatifs conservés
- Re-run reproductible
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Mutation d’un gate fait échouer CI.
- Rollback dry-run reproductible.

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
- Research metadata cannot alter runtime permissions

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 96–102 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
