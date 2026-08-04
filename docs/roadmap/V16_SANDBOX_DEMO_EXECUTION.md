# V16 — Sandbox / Demo Execution

Identifiant : `V16_SANDBOX_DEMO`  
Plage canonique : **Lots 142 à 149**  
Composant/domain owner : `SandboxExecutionDomain`  
Mode maximal autorisé : `SANDBOX`

## Finalité de la version

Faire évoluer le système de **OMS/EMS fermé** vers **Sandbox stable, incident-tested et réconcilié**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- OMS/EMS fermé.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/sandbox`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 142 — Sandbox Scope & Isolated Environment

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `SANDBOX`  
**Composant propriétaire :** `SandboxExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/sandbox`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Sandbox Scope & Isolated Environment » dans Sandbox / Demo Execution, produire SandboxScopeIsolatedEnvironmentStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SandboxScopeIsolatedEnvironmentStateV1
- SandboxScopeIsolatedEnvironmentAuditV1
- SandboxScopeIsolatedEnvironmentContractRegistryV1
- SandboxScopeIsolatedEnvironmentCapabilityMatrixV1
- SandboxExecutionStateV1
- FailureInjectionEvidenceV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 142, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Sandbox Scope & Isolated Environment » dans le composant SandboxExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir frontières, responsabilités, dépendances autorisées, modes runtime et API publiques du domaine.
6. Classer chaque capability en REQUIRED, OPTIONAL_RESEARCH, DISABLED ou FORBIDDEN.
7. Utiliser credentials/endpoints sandbox explicitement distincts du live.
8. Router uniquement OrderIntent sandbox-approved via OMS/EMS.
9. Injecter latency, rejects, disconnects, partial fills, stale data et restart.
10. Réconcilier orders/fills/portfolio après chaque drill.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/sandbox/sandbox_scope_and_isolated_environment.py
- src/crypto_quant_bot/sandbox/sandbox_scope_and_isolated_environment_models.py
- scripts/run_lot142_sandbox_scope_and_isolated_environment.py
- scripts/validate_lot142.py
- tests/test_lot142_sandbox_scope_and_isolated_environment.py
- data/audit/sandbox_scope_and_isolated_environment_lot142.json
- reports/lot_142_sandbox_scope_and_isolated_environment_report.md
- docs/LOT_142_SANDBOX_SCOPE_AND_ISOLATED_ENVIRONMENT.md
- docs/ACCEPTANCE_CRITERIA_LOT_142.md

### Observabilité minimale

- lot_142_records_processed_total
- lot_142_validation_failures_total
- lot_142_processing_latency_ms

### Tests et critères d’acceptation

- No live endpoint
- Failure injection passes
- Kill switch immediate
- No orphan order
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test de dépendances interdites entre domaines.
- Test de couverture : chaque capability a owner, contrat et gate.
- Live hostname/credential rejected.
- Kill switch sous charge.
- No orphan après failure matrix.

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
- runtime_mode=SANDBOX
- live_credentials forbidden

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 143 — Sandbox Exchange Adapter

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `SANDBOX`  
**Composant propriétaire :** `SandboxExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/sandbox`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Sandbox Exchange Adapter » dans Sandbox / Demo Execution, produire SandboxExchangeAdapterStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SandboxExchangeAdapterStateV1
- SandboxExchangeAdapterAuditV1
- SandboxExecutionStateV1
- FailureInjectionEvidenceV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 143, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Sandbox Exchange Adapter » dans le composant SandboxExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Utiliser credentials/endpoints sandbox explicitement distincts du live.
6. Router uniquement OrderIntent sandbox-approved via OMS/EMS.
7. Injecter latency, rejects, disconnects, partial fills, stale data et restart.
8. Réconcilier orders/fills/portfolio après chaque drill.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/sandbox/sandbox_exchange_adapter.py
- src/crypto_quant_bot/sandbox/sandbox_exchange_adapter_models.py
- scripts/run_lot143_sandbox_exchange_adapter.py
- scripts/validate_lot143.py
- tests/test_lot143_sandbox_exchange_adapter.py
- data/audit/sandbox_exchange_adapter_lot143.json
- reports/lot_143_sandbox_exchange_adapter_report.md
- docs/LOT_143_SANDBOX_EXCHANGE_ADAPTER.md
- docs/ACCEPTANCE_CRITERIA_LOT_143.md

### Observabilité minimale

- lot_143_records_processed_total
- lot_143_validation_failures_total
- lot_143_processing_latency_ms

### Tests et critères d’acceptation

- No live endpoint
- Failure injection passes
- Kill switch immediate
- No orphan order
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Live hostname/credential rejected.
- Kill switch sous charge.
- No orphan après failure matrix.

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
- runtime_mode=SANDBOX
- live_credentials forbidden

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 144 — Demo Routing & Execution Policy

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `SANDBOX`  
**Composant propriétaire :** `SandboxExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/sandbox`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Demo Routing & Execution Policy » dans Sandbox / Demo Execution, produire DemoRoutingExecutionPolicyStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- DemoRoutingExecutionPolicyStateV1
- DemoRoutingExecutionPolicyAuditV1
- SandboxExecutionStateV1
- FailureInjectionEvidenceV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 144, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Demo Routing & Execution Policy » dans le composant SandboxExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Utiliser credentials/endpoints sandbox explicitement distincts du live.
6. Router uniquement OrderIntent sandbox-approved via OMS/EMS.
7. Injecter latency, rejects, disconnects, partial fills, stale data et restart.
8. Réconcilier orders/fills/portfolio après chaque drill.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/sandbox/demo_routing_and_execution_policy.py
- src/crypto_quant_bot/sandbox/demo_routing_and_execution_policy_models.py
- scripts/run_lot144_demo_routing_and_execution_policy.py
- scripts/validate_lot144.py
- tests/test_lot144_demo_routing_and_execution_policy.py
- data/audit/demo_routing_and_execution_policy_lot144.json
- reports/lot_144_demo_routing_and_execution_policy_report.md
- docs/LOT_144_DEMO_ROUTING_AND_EXECUTION_POLICY.md
- docs/ACCEPTANCE_CRITERIA_LOT_144.md

### Observabilité minimale

- lot_144_records_processed_total
- lot_144_validation_failures_total
- lot_144_processing_latency_ms

### Tests et critères d’acceptation

- No live endpoint
- Failure injection passes
- Kill switch immediate
- No orphan order
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Live hostname/credential rejected.
- Kill switch sous charge.
- No orphan après failure matrix.

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
- runtime_mode=SANDBOX
- live_credentials forbidden

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 145 — Fill, Latency & Slippage Simulation

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `SANDBOX`  
**Composant propriétaire :** `SandboxExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/sandbox`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Fill, Latency & Slippage Simulation » dans Sandbox / Demo Execution, produire FillLatencySlippageSimulationStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- FillLatencySlippageSimulationStateV1
- FillLatencySlippageSimulationAuditV1
- SlippageImpactEstimateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 145, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Fill, Latency & Slippage Simulation » dans le composant SandboxExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Estimer slippage depuis spread, depth, participation, volatility et latency.
6. Séparer temporary impact, permanent proxy et adverse movement.
7. Calibrer par buckets instrument/régime/taille ; publier intervalle et fallback.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/sandbox/fill_latency_and_slippage_simulation.py
- src/crypto_quant_bot/sandbox/fill_latency_and_slippage_simulation_models.py
- scripts/run_lot145_fill_latency_and_slippage_simulation.py
- scripts/validate_lot145.py
- tests/test_lot145_fill_latency_and_slippage_simulation.py
- data/audit/fill_latency_and_slippage_simulation_lot145.json
- reports/lot_145_fill_latency_and_slippage_simulation_report.md
- docs/LOT_145_FILL_LATENCY_AND_SLIPPAGE_SIMULATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_145.md

### Observabilité minimale

- lot_145_records_processed_total
- lot_145_validation_failures_total
- lot_145_processing_latency_ms

### Tests et critères d’acceptation

- No live endpoint
- Failure injection passes
- Kill switch immediate
- No orphan order
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Slippage monotone avec taille.
- Book insuffisant → no-fill/partial-fill, pas prix inventé.

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
- runtime_mode=SANDBOX
- live_credentials forbidden

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 146 — Sandbox Risk Limits & Kill Switch

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `SANDBOX`  
**Composant propriétaire :** `SandboxExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/sandbox`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Sandbox Risk Limits & Kill Switch » dans Sandbox / Demo Execution, produire SandboxRiskLimitsKillSwitchStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SandboxRiskLimitsKillSwitchStateV1
- SandboxRiskLimitsKillSwitchAuditV1
- RiskDecisionV1
- KillSwitchStateV1
- SandboxExecutionStateV1
- FailureInjectionEvidenceV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 146, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Sandbox Risk Limits & Kill Switch » dans le composant SandboxExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Évaluer data, model, strategy, portfolio, exchange, execution et security vetos.
6. Résoudre action finale par priorité KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE.
7. Signer decision_hash sur intent+limits+state ids.
8. Approval expire et n’est valide que pour l’intent exact.
9. Utiliser credentials/endpoints sandbox explicitement distincts du live.
10. Router uniquement OrderIntent sandbox-approved via OMS/EMS.
11. Injecter latency, rejects, disconnects, partial fills, stale data et restart.
12. Réconcilier orders/fills/portfolio après chaque drill.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/sandbox/sandbox_risk_limits_and_kill_switch.py
- src/crypto_quant_bot/sandbox/sandbox_risk_limits_and_kill_switch_models.py
- scripts/run_lot146_sandbox_risk_limits_and_kill_switch.py
- scripts/validate_lot146.py
- tests/test_lot146_sandbox_risk_limits_and_kill_switch.py
- data/audit/sandbox_risk_limits_and_kill_switch_lot146.json
- reports/lot_146_sandbox_risk_limits_and_kill_switch_report.md
- docs/LOT_146_SANDBOX_RISK_LIMITS_AND_KILL_SWITCH.md
- docs/ACCEPTANCE_CRITERIA_LOT_146.md

### Observabilité minimale

- lot_146_records_processed_total
- lot_146_validation_failures_total
- lot_146_processing_latency_ms

### Tests et critères d’acceptation

- No live endpoint
- Failure injection passes
- Kill switch immediate
- No orphan order
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Bypass impossible.
- Toute mutation intent invalide decision_hash.
- Kill switch bloque tous les nouveaux intents immédiatement.
- Live hostname/credential rejected.
- Kill switch sous charge.
- No orphan après failure matrix.

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
- runtime_mode=SANDBOX
- live_credentials forbidden

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 147 — Failure Injection & Incident Drills

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `SANDBOX`  
**Composant propriétaire :** `SandboxExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/sandbox`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Failure Injection & Incident Drills » dans Sandbox / Demo Execution, produire FailureInjectionIncidentDrillsStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- FailureInjectionIncidentDrillsStateV1
- FailureInjectionIncidentDrillsAuditV1
- SandboxExecutionStateV1
- FailureInjectionEvidenceV1
- TelemetryEnvelopeV1
- IncidentRecordV1
- RecoveryEvidenceV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 147, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Failure Injection & Incident Drills » dans le composant SandboxExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Utiliser credentials/endpoints sandbox explicitement distincts du live.
6. Router uniquement OrderIntent sandbox-approved via OMS/EMS.
7. Injecter latency, rejects, disconnects, partial fills, stale data et restart.
8. Réconcilier orders/fills/portfolio après chaque drill.
9. Émettre logs JSON, metrics et traces avec run_id/correlation_id/strategy_id/order_id sans secrets.
10. Surveiller heartbeats, freshness, latency, veto, order lifecycle, positions, PnL et reconciliation.
11. Mapper alert severity vers acknowledge/escalate/pause/kill.
12. Tester backup, restore, replay, restart reconciliation et rollback.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/sandbox/failure_injection_and_incident_drills.py
- src/crypto_quant_bot/sandbox/failure_injection_and_incident_drills_models.py
- scripts/run_lot147_failure_injection_and_incident_drills.py
- scripts/validate_lot147.py
- tests/test_lot147_failure_injection_and_incident_drills.py
- data/audit/failure_injection_and_incident_drills_lot147.json
- reports/lot_147_failure_injection_and_incident_drills_report.md
- docs/LOT_147_FAILURE_INJECTION_AND_INCIDENT_DRILLS.md
- docs/ACCEPTANCE_CRITERIA_LOT_147.md

### Observabilité minimale

- lot_147_records_processed_total
- lot_147_validation_failures_total
- lot_147_processing_latency_ms

### Tests et critères d’acceptation

- No live endpoint
- Failure injection passes
- Kill switch immediate
- No orphan order
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Live hostname/credential rejected.
- Kill switch sous charge.
- No orphan après failure matrix.
- Lost heartbeat et stale data.
- Alert injection avec action attendue.
- Restore produit mêmes checksums.

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
- runtime_mode=SANDBOX
- live_credentials forbidden

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 148 — Sandbox Reconciliation & Performance Review

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `SANDBOX`  
**Composant propriétaire :** `SandboxExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/sandbox`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Sandbox Reconciliation & Performance Review » dans Sandbox / Demo Execution, produire SandboxReconciliationPerformanceReviewStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SandboxReconciliationPerformanceReviewStateV1
- SandboxReconciliationPerformanceReviewAuditV1
- ReconciliationReportV1
- ReconciliationVetoV1
- SandboxExecutionStateV1
- FailureInjectionEvidenceV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 148, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Sandbox Reconciliation & Performance Review » dans le composant SandboxExecutionDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Comparer identifiants, quantités, prix, frais, balances, positions et timestamps entre les deux sources concernées.
6. Classer MATCH, TOLERATED_DIFF, MINOR_DIVERGENCE, CRITICAL_DIVERGENCE.
7. Produire delta exact, tolérance versionnée, source de vérité et action corrective.
8. MINOR → PAUSE ; CRITICAL/unknown ownership → KILL_SWITCH ou BLOCK_TRADING selon matrice.
9. Utiliser credentials/endpoints sandbox explicitement distincts du live.
10. Router uniquement OrderIntent sandbox-approved via OMS/EMS.
11. Injecter latency, rejects, disconnects, partial fills, stale data et restart.
12. Réconcilier orders/fills/portfolio après chaque drill.

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

- src/crypto_quant_bot/sandbox/sandbox_reconciliation_and_performance_review.py
- src/crypto_quant_bot/sandbox/sandbox_reconciliation_and_performance_review_models.py
- scripts/run_lot148_sandbox_reconciliation_and_performance_review.py
- scripts/validate_lot148.py
- tests/test_lot148_sandbox_reconciliation_and_performance_review.py
- data/audit/sandbox_reconciliation_and_performance_review_lot148.json
- reports/lot_148_sandbox_reconciliation_and_performance_review_report.md
- docs/LOT_148_SANDBOX_RECONCILIATION_AND_PERFORMANCE_REVIEW.md
- docs/ACCEPTANCE_CRITERIA_LOT_148.md

### Observabilité minimale

- lot_148_records_processed_total
- lot_148_validation_failures_total
- lot_148_processing_latency_ms

### Tests et critères d’acceptation

- No live endpoint
- Failure injection passes
- Kill switch immediate
- No orphan order
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Ordre/fill/balance/frais divergents injectés.
- Reconciliation idempotente après restart.
- Live hostname/credential rejected.
- Kill switch sous charge.
- No orphan après failure matrix.

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
- runtime_mode=SANDBOX
- live_credentials forbidden

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 149 — Sandbox-to-Live Promotion Gate & V16 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `SANDBOX`  
**Composant propriétaire :** `SandboxExecutionDomain`  
**Frontière de code :** `src/crypto_quant_bot/sandbox`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Sandbox-to-Live Promotion Gate & V16 Closure » dans Sandbox / Demo Execution, produire SandboxToLivePromotionGateV16ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- SandboxToLivePromotionGateV16ClosureStateV1
- SandboxToLivePromotionGateV16ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- PromotionDecisionV1
- SandboxExecutionStateV1
- FailureInjectionEvidenceV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 149, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Sandbox-to-Live Promotion Gate & V16 Closure » dans le composant SandboxExecutionDomain sans effet de bord non déclaré.
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
13. Utiliser credentials/endpoints sandbox explicitement distincts du live.
14. Router uniquement OrderIntent sandbox-approved via OMS/EMS.
15. Injecter latency, rejects, disconnects, partial fills, stale data et restart.
16. Réconcilier orders/fills/portfolio après chaque drill.

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

- scripts/validate_all_until_lot149.py
- scripts/run_required_chain_until_lot149.sh
- scripts/diagnose_exact_chain_until_lot149.py
- tests/test_lot149_closure_contract.py
- data/audit/closure_manifest_lot149.json
- reports/lot_149_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_149.md
- src/crypto_quant_bot/sandbox/sandbox_to_live_promotion_gate_and_v16_closure.py
- src/crypto_quant_bot/sandbox/sandbox_to_live_promotion_gate_and_v16_closure_models.py
- scripts/run_lot149_sandbox_to_live_promotion_gate_and_v16_closure.py
- scripts/validate_lot149.py
- tests/test_lot149_sandbox_to_live_promotion_gate_and_v16_closure.py
- data/audit/sandbox_to_live_promotion_gate_and_v16_closure_lot149.json
- reports/lot_149_sandbox_to_live_promotion_gate_and_v16_closure_report.md
- docs/LOT_149_SANDBOX_TO_LIVE_PROMOTION_GATE_AND_V16_CLOSURE.md

### Observabilité minimale

- lot_149_records_processed_total
- lot_149_validation_failures_total
- lot_149_processing_latency_ms

### Tests et critères d’acceptation

- No live endpoint
- Failure injection passes
- Kill switch immediate
- No orphan order
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
- Live hostname/credential rejected.
- Kill switch sous charge.
- No orphan après failure matrix.

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
- runtime_mode=SANDBOX
- live_credentials forbidden

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 142–149 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
