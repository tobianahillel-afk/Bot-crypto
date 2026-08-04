# V17 — Live Governance / Human Approval

Identifiant : `V17_LIVE_GOVERNANCE`  
Plage canonique : **Lots 150 à 157**  
Composant/domain owner : `LiveGovernanceDomain`  
Mode maximal autorisé : `LIVE_DISABLED_BY_DEFAULT`

## Finalité de la version

Faire évoluer le système de **Sandbox promotion gate** vers **Live eligibility gouvernée, pas activation autonome**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Sandbox promotion gate.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/live_governance`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 150 — Live Scope & Runtime Modes

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LIVE_DISABLED_BY_DEFAULT`  
**Composant propriétaire :** `LiveGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/live_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Live Scope & Runtime Modes » dans Live Governance / Human Approval, produire LiveScopeRuntimeModesStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- LiveScopeRuntimeModesStateV1
- LiveScopeRuntimeModesAuditV1
- LiveScopeRuntimeModesContractRegistryV1
- LiveScopeRuntimeModesCapabilityMatrixV1
- RuntimeModeStateV1
- HumanApprovalV1
- LiveEligibilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 150, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Live Scope & Runtime Modes » dans le composant LiveGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir frontières, responsabilités, dépendances autorisées, modes runtime et API publiques du domaine.
6. Classer chaque capability en REQUIRED, OPTIONAL_RESEARCH, DISABLED ou FORBIDDEN.
7. Default LIVE_DISABLED ; transitions uniquement via state machine et preuves signées.
8. Modes autorisés : READ_ONLY, SHADOW_LIVE, LIVE_MANUAL_APPROVAL, LIVE_SMALL_CAPITAL, LIVE_REDUCED_RISK, LIVE_PAUSED, EMERGENCY_STOP.
9. Human approval lie stratégie, intent/order scope, capital tier, expiry et approver.
10. Aucun scale-up autonome ; pause/kill ont priorité et sont idempotents.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/live_governance/live_scope_and_runtime_modes.py
- src/crypto_quant_bot/live_governance/live_scope_and_runtime_modes_models.py
- scripts/run_lot150_live_scope_and_runtime_modes.py
- scripts/validate_lot150.py
- tests/test_lot150_live_scope_and_runtime_modes.py
- data/audit/live_scope_and_runtime_modes_lot150.json
- reports/lot_150_live_scope_and_runtime_modes_report.md
- docs/LOT_150_LIVE_SCOPE_AND_RUNTIME_MODES.md
- docs/ACCEPTANCE_CRITERIA_LOT_150.md

### Observabilité minimale

- lot_150_records_processed_total
- lot_150_validation_failures_total
- lot_150_processing_latency_ms

### Tests et critères d’acceptation

- No transition sans gate
- Emergency stop verified
- Small-cap limits enforced
- Withdrawal disabled
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test de dépendances interdites entre domaines.
- Test de couverture : chaque capability a owner, contrat et gate.
- Transition non autorisée rejetée.
- Approval expirée ou pour autre hash rejetée.
- Withdrawal permission toujours interdite.

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
- Default runtime=LIVE_DISABLED
- Human approval mandatory
- No autonomous scale-up

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 151 — Secrets, Key Management & Permission Governance

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LIVE_DISABLED_BY_DEFAULT`  
**Composant propriétaire :** `LiveGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/live_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Secrets, Key Management & Permission Governance » dans Live Governance / Human Approval, produire SecretsKeyManagementPermissionGovernanceStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SecretsKeyManagementPermissionGovernanceStateV1
- SecretsKeyManagementPermissionGovernanceAuditV1
- SecretReferenceV1
- PermissionPolicyV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 151, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Secrets, Key Management & Permission Governance » dans le composant LiveGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Secrets uniquement via secret manager/environment injecté, jamais sérialisés.
6. Séparer keys read-only/sandbox/live et interdire withdrawal.
7. Documenter rotation, revocation, break-glass et audit access.
8. Redacter logs/errors automatiquement.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/live_governance/secrets_key_management_and_permission_governance.py
- src/crypto_quant_bot/live_governance/secrets_key_management_and_permission_governance_models.py
- scripts/run_lot151_secrets_key_management_and_permission_governance.py
- scripts/validate_lot151.py
- tests/test_lot151_secrets_key_management_and_permission_governance.py
- data/audit/secrets_key_management_and_permission_governance_lot151.json
- reports/lot_151_secrets_key_management_and_permission_governance_report.md
- docs/LOT_151_SECRETS_KEY_MANAGEMENT_AND_PERMISSION_GOVERNANCE.md
- docs/ACCEPTANCE_CRITERIA_LOT_151.md

### Observabilité minimale

- lot_151_records_processed_total
- lot_151_validation_failures_total
- lot_151_processing_latency_ms

### Tests et critères d’acceptation

- No transition sans gate
- Emergency stop verified
- Small-cap limits enforced
- Withdrawal disabled
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Secret scanning fixtures.
- Rotation sans downtime ou mode paused.
- Permission excess détectée.

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
- Default runtime=LIVE_DISABLED
- Human approval mandatory
- No autonomous scale-up

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 152 — Human Approval Workflow

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LIVE_DISABLED_BY_DEFAULT`  
**Composant propriétaire :** `LiveGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/live_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Human Approval Workflow » dans Live Governance / Human Approval, produire HumanApprovalWorkflowStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- HumanApprovalWorkflowStateV1
- HumanApprovalWorkflowAuditV1
- RuntimeModeStateV1
- HumanApprovalV1
- LiveEligibilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 152, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Human Approval Workflow » dans le composant LiveGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Default LIVE_DISABLED ; transitions uniquement via state machine et preuves signées.
6. Modes autorisés : READ_ONLY, SHADOW_LIVE, LIVE_MANUAL_APPROVAL, LIVE_SMALL_CAPITAL, LIVE_REDUCED_RISK, LIVE_PAUSED, EMERGENCY_STOP.
7. Human approval lie stratégie, intent/order scope, capital tier, expiry et approver.
8. Aucun scale-up autonome ; pause/kill ont priorité et sont idempotents.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/live_governance/human_approval_workflow.py
- src/crypto_quant_bot/live_governance/human_approval_workflow_models.py
- scripts/run_lot152_human_approval_workflow.py
- scripts/validate_lot152.py
- tests/test_lot152_human_approval_workflow.py
- data/audit/human_approval_workflow_lot152.json
- reports/lot_152_human_approval_workflow_report.md
- docs/LOT_152_HUMAN_APPROVAL_WORKFLOW.md
- docs/ACCEPTANCE_CRITERIA_LOT_152.md

### Observabilité minimale

- lot_152_records_processed_total
- lot_152_validation_failures_total
- lot_152_processing_latency_ms

### Tests et critères d’acceptation

- No transition sans gate
- Emergency stop verified
- Small-cap limits enforced
- Withdrawal disabled
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Transition non autorisée rejetée.
- Approval expirée ou pour autre hash rejetée.
- Withdrawal permission toujours interdite.

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
- Default runtime=LIVE_DISABLED
- Human approval mandatory
- No autonomous scale-up

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 153 — Small-Capital Guard & Exposure Tiers

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LIVE_DISABLED_BY_DEFAULT`  
**Composant propriétaire :** `LiveGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/live_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Small-Capital Guard & Exposure Tiers » dans Live Governance / Human Approval, produire SmallCapitalGuardExposureTiersStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SmallCapitalGuardExposureTiersStateV1
- SmallCapitalGuardExposureTiersAuditV1
- RuntimeModeStateV1
- HumanApprovalV1
- LiveEligibilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 153, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Small-Capital Guard & Exposure Tiers » dans le composant LiveGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Default LIVE_DISABLED ; transitions uniquement via state machine et preuves signées.
6. Modes autorisés : READ_ONLY, SHADOW_LIVE, LIVE_MANUAL_APPROVAL, LIVE_SMALL_CAPITAL, LIVE_REDUCED_RISK, LIVE_PAUSED, EMERGENCY_STOP.
7. Human approval lie stratégie, intent/order scope, capital tier, expiry et approver.
8. Aucun scale-up autonome ; pause/kill ont priorité et sont idempotents.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/live_governance/small_capital_guard_and_exposure_tiers.py
- src/crypto_quant_bot/live_governance/small_capital_guard_and_exposure_tiers_models.py
- scripts/run_lot153_small_capital_guard_and_exposure_tiers.py
- scripts/validate_lot153.py
- tests/test_lot153_small_capital_guard_and_exposure_tiers.py
- data/audit/small_capital_guard_and_exposure_tiers_lot153.json
- reports/lot_153_small_capital_guard_and_exposure_tiers_report.md
- docs/LOT_153_SMALL_CAPITAL_GUARD_AND_EXPOSURE_TIERS.md
- docs/ACCEPTANCE_CRITERIA_LOT_153.md

### Observabilité minimale

- lot_153_records_processed_total
- lot_153_validation_failures_total
- lot_153_processing_latency_ms

### Tests et critères d’acceptation

- No transition sans gate
- Emergency stop verified
- Small-cap limits enforced
- Withdrawal disabled
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Transition non autorisée rejetée.
- Approval expirée ou pour autre hash rejetée.
- Withdrawal permission toujours interdite.

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
- Default runtime=LIVE_DISABLED
- Human approval mandatory
- No autonomous scale-up

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 154 — Live Risk Limits & Emergency Kill Switch

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LIVE_DISABLED_BY_DEFAULT`  
**Composant propriétaire :** `LiveGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/live_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Live Risk Limits & Emergency Kill Switch » dans Live Governance / Human Approval, produire LiveRiskLimitsEmergencyKillSwitchStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- LiveRiskLimitsEmergencyKillSwitchStateV1
- LiveRiskLimitsEmergencyKillSwitchAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 154, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Live Risk Limits & Emergency Kill Switch » dans le composant LiveGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/live_governance/live_risk_limits_and_emergency_kill_switch.py
- src/crypto_quant_bot/live_governance/live_risk_limits_and_emergency_kill_switch_models.py
- scripts/run_lot154_live_risk_limits_and_emergency_kill_switch.py
- scripts/validate_lot154.py
- tests/test_lot154_live_risk_limits_and_emergency_kill_switch.py
- data/audit/live_risk_limits_and_emergency_kill_switch_lot154.json
- reports/lot_154_live_risk_limits_and_emergency_kill_switch_report.md
- docs/LOT_154_LIVE_RISK_LIMITS_AND_EMERGENCY_KILL_SWITCH.md
- docs/ACCEPTANCE_CRITERIA_LOT_154.md

### Observabilité minimale

- lot_154_records_processed_total
- lot_154_validation_failures_total
- lot_154_processing_latency_ms

### Tests et critères d’acceptation

- No transition sans gate
- Emergency stop verified
- Small-cap limits enforced
- Withdrawal disabled
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.

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
- Default runtime=LIVE_DISABLED
- Human approval mandatory
- No autonomous scale-up

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 155 — Manual Override, Pause, Restart & Degraded Mode

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LIVE_DISABLED_BY_DEFAULT`  
**Composant propriétaire :** `LiveGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/live_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Manual Override, Pause, Restart & Degraded Mode » dans Live Governance / Human Approval, produire ManualOverridePauseRestartDegradedModeStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ManualOverridePauseRestartDegradedModeStateV1
- ManualOverridePauseRestartDegradedModeAuditV1
- RuntimeModeStateV1
- HumanApprovalV1
- LiveEligibilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 155, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Manual Override, Pause, Restart & Degraded Mode » dans le composant LiveGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Default LIVE_DISABLED ; transitions uniquement via state machine et preuves signées.
6. Modes autorisés : READ_ONLY, SHADOW_LIVE, LIVE_MANUAL_APPROVAL, LIVE_SMALL_CAPITAL, LIVE_REDUCED_RISK, LIVE_PAUSED, EMERGENCY_STOP.
7. Human approval lie stratégie, intent/order scope, capital tier, expiry et approver.
8. Aucun scale-up autonome ; pause/kill ont priorité et sont idempotents.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/live_governance/manual_override_pause_restart_and_degraded_mode.py
- src/crypto_quant_bot/live_governance/manual_override_pause_restart_and_degraded_mode_models.py
- scripts/run_lot155_manual_override_pause_restart_and_degraded_mode.py
- scripts/validate_lot155.py
- tests/test_lot155_manual_override_pause_restart_and_degraded_mode.py
- data/audit/manual_override_pause_restart_and_degraded_mode_lot155.json
- reports/lot_155_manual_override_pause_restart_and_degraded_mode_report.md
- docs/LOT_155_MANUAL_OVERRIDE_PAUSE_RESTART_AND_DEGRADED_MODE.md
- docs/ACCEPTANCE_CRITERIA_LOT_155.md

### Observabilité minimale

- lot_155_records_processed_total
- lot_155_validation_failures_total
- lot_155_processing_latency_ms

### Tests et critères d’acceptation

- No transition sans gate
- Emergency stop verified
- Small-cap limits enforced
- Withdrawal disabled
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Transition non autorisée rejetée.
- Approval expirée ou pour autre hash rejetée.
- Withdrawal permission toujours interdite.

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
- Default runtime=LIVE_DISABLED
- Human approval mandatory
- No autonomous scale-up

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 156 — Live Reconciliation, Compliance & Evidence

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LIVE_DISABLED_BY_DEFAULT`  
**Composant propriétaire :** `LiveGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/live_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Live Reconciliation, Compliance & Evidence » dans Live Governance / Human Approval, produire LiveReconciliationComplianceEvidenceStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- LiveReconciliationComplianceEvidenceStateV1
- LiveReconciliationComplianceEvidenceAuditV1
- ReconciliationReportV1
- ReconciliationVetoV1
- RuntimeModeStateV1
- HumanApprovalV1
- LiveEligibilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 156, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Live Reconciliation, Compliance & Evidence » dans le composant LiveGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Comparer identifiants, quantités, prix, frais, balances, positions et timestamps entre les deux sources concernées.
6. Classer MATCH, TOLERATED_DIFF, MINOR_DIVERGENCE, CRITICAL_DIVERGENCE.
7. Produire delta exact, tolérance versionnée, source de vérité et action corrective.
8. MINOR → PAUSE ; CRITICAL/unknown ownership → KILL_SWITCH ou BLOCK_TRADING selon matrice.
9. Default LIVE_DISABLED ; transitions uniquement via state machine et preuves signées.
10. Modes autorisés : READ_ONLY, SHADOW_LIVE, LIVE_MANUAL_APPROVAL, LIVE_SMALL_CAPITAL, LIVE_REDUCED_RISK, LIVE_PAUSED, EMERGENCY_STOP.
11. Human approval lie stratégie, intent/order scope, capital tier, expiry et approver.
12. Aucun scale-up autonome ; pause/kill ont priorité et sont idempotents.

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

- src/crypto_quant_bot/live_governance/live_reconciliation_compliance_and_evidence.py
- src/crypto_quant_bot/live_governance/live_reconciliation_compliance_and_evidence_models.py
- scripts/run_lot156_live_reconciliation_compliance_and_evidence.py
- scripts/validate_lot156.py
- tests/test_lot156_live_reconciliation_compliance_and_evidence.py
- data/audit/live_reconciliation_compliance_and_evidence_lot156.json
- reports/lot_156_live_reconciliation_compliance_and_evidence_report.md
- docs/LOT_156_LIVE_RECONCILIATION_COMPLIANCE_AND_EVIDENCE.md
- docs/ACCEPTANCE_CRITERIA_LOT_156.md

### Observabilité minimale

- lot_156_records_processed_total
- lot_156_validation_failures_total
- lot_156_processing_latency_ms

### Tests et critères d’acceptation

- No transition sans gate
- Emergency stop verified
- Small-cap limits enforced
- Withdrawal disabled
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Ordre/fill/balance/frais divergents injectés.
- Reconciliation idempotente après restart.
- Transition non autorisée rejetée.
- Approval expirée ou pour autre hash rejetée.
- Withdrawal permission toujours interdite.

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
- Default runtime=LIVE_DISABLED
- Human approval mandatory
- No autonomous scale-up

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 157 — Live Eligibility Gate & V17 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LIVE_DISABLED_BY_DEFAULT`  
**Composant propriétaire :** `LiveGovernanceDomain`  
**Frontière de code :** `src/crypto_quant_bot/live_governance`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Live Eligibility Gate & V17 Closure » dans Live Governance / Human Approval, produire LiveEligibilityGateV17ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- LiveEligibilityGateV17ClosureStateV1
- LiveEligibilityGateV17ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- PromotionDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 157, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Live Eligibility Gate & V17 Closure » dans le composant LiveGovernanceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Assembler preuves requises, seuils versionnés, exceptions et sign-offs.
10. Évaluer chaque critère PASS/FAIL/NOT_APPLICABLE avec justification.
11. Toute donnée manquante → FAIL ; aucun override silencieux.
12. Enregistrer approver, timestamp, expiry et scope exact de la promotion.

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

- scripts/validate_all_until_lot157.py
- scripts/run_required_chain_until_lot157.sh
- scripts/diagnose_exact_chain_until_lot157.py
- tests/test_lot157_closure_contract.py
- data/audit/closure_manifest_lot157.json
- reports/lot_157_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_157.md
- src/crypto_quant_bot/live_governance/live_eligibility_gate_and_v17_closure.py
- src/crypto_quant_bot/live_governance/live_eligibility_gate_and_v17_closure_models.py
- scripts/run_lot157_live_eligibility_gate_and_v17_closure.py
- scripts/validate_lot157.py
- tests/test_lot157_live_eligibility_gate_and_v17_closure.py
- data/audit/live_eligibility_gate_and_v17_closure_lot157.json
- reports/lot_157_live_eligibility_gate_and_v17_closure_report.md
- docs/LOT_157_LIVE_ELIGIBILITY_GATE_AND_V17_CLOSURE.md

### Observabilité minimale

- lot_157_records_processed_total
- lot_157_validation_failures_total
- lot_157_processing_latency_ms

### Tests et critères d’acceptation

- No transition sans gate
- Emergency stop verified
- Small-cap limits enforced
- Withdrawal disabled
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Preuve manquante bloque promotion.
- Promotion expirée ne peut être consommée.

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
- Default runtime=LIVE_DISABLED
- Human approval mandatory
- No autonomous scale-up

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 150–157 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
