# V12 — UI / Operator Console

Identifiant : `V12_UI_OPERATOR_CONSOLE`  
Plage canonique : **Lots 111 à 118**  
Composant/domain owner : `OperatorConsoleDomain`  
Mode maximal autorisé : `OPERATOR_UI`

## Finalité de la version

Faire évoluer le système de **Read models stables** vers **Console opérateur sans contournement backend**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Read models stables.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/ui`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 111 — UI Scope, Information Architecture & Design System

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPERATOR_UI`  
**Composant propriétaire :** `OperatorConsoleDomain`  
**Frontière de code :** `src/crypto_quant_bot/ui`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « UI Scope, Information Architecture & Design System » dans UI / Operator Console, produire UIScopeInformationArchitectureDesignSystemStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- UIScopeInformationArchitectureDesignSystemStateV1
- UIScopeInformationArchitectureDesignSystemAuditV1
- UIScopeInformationArchitectureDesignSystemContractRegistryV1
- UIScopeInformationArchitectureDesignSystemCapabilityMatrixV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 111, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « UI Scope, Information Architecture & Design System » dans le composant OperatorConsoleDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/ui/ui_scope_information_architecture_and_design_system.py
- src/crypto_quant_bot/ui/ui_scope_information_architecture_and_design_system_models.py
- scripts/run_lot111_ui_scope_information_architecture_and_design_system.py
- scripts/validate_lot111.py
- tests/test_lot111_ui_scope_information_architecture_and_design_system.py
- data/audit/ui_scope_information_architecture_and_design_system_lot111.json
- reports/lot_111_ui_scope_information_architecture_and_design_system_report.md
- docs/LOT_111_UI_SCOPE_INFORMATION_ARCHITECTURE_AND_DESIGN_SYSTEM.md
- docs/ACCEPTANCE_CRITERIA_LOT_111.md

### Observabilité minimale

- lot_111_records_processed_total
- lot_111_validation_failures_total
- lot_111_processing_latency_ms

### Tests et critères d’acceptation

- Aucune action non autorisée
- Freshness visible
- Risk/veto visible
- Keyboard/accessibility checks
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
- UI does not bypass backend gates

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 112 — Market Context & Multi-Timeframe Dashboard

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPERATOR_UI`  
**Composant propriétaire :** `OperatorConsoleDomain`  
**Frontière de code :** `src/crypto_quant_bot/ui`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Market Context & Multi-Timeframe Dashboard » dans UI / Operator Console, produire MarketContextMultiTimeframeDashboardStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MarketContextMultiTimeframeDashboardStateV1
- MarketContextMultiTimeframeDashboardAuditV1
- UIReadModelV1
- OperatorActionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 112, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Market Context & Multi-Timeframe Dashboard » dans le composant OperatorConsoleDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Consommer uniquement read models backend ; aucune logique de gate n’est réimplémentée côté UI.
6. Afficher freshness, uncertainty, veto, lineage et state version.
7. Contrôler RBAC et confirmation renforcée pour pause/kill/approval lorsque ces actions existent.
8. Conserver audit de chaque action opérateur et résultat backend.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/ui/market_context_and_multi_timeframe_dashboard.py
- src/crypto_quant_bot/ui/market_context_and_multi_timeframe_dashboard_models.py
- scripts/run_lot112_market_context_and_multi_timeframe_dashboard.py
- scripts/validate_lot112.py
- tests/test_lot112_market_context_and_multi_timeframe_dashboard.py
- data/audit/market_context_and_multi_timeframe_dashboard_lot112.json
- reports/lot_112_market_context_and_multi_timeframe_dashboard_report.md
- docs/LOT_112_MARKET_CONTEXT_AND_MULTI_TIMEFRAME_DASHBOARD.md
- docs/ACCEPTANCE_CRITERIA_LOT_112.md

### Observabilité minimale

- lot_112_records_processed_total
- lot_112_validation_failures_total
- lot_112_processing_latency_ms

### Tests et critères d’acceptation

- Aucune action non autorisée
- Freshness visible
- Risk/veto visible
- Keyboard/accessibility checks
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- UI ne peut appeler endpoint non autorisé.
- Stale state clairement visible.
- Keyboard/accessibility et permission matrix.

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
- UI does not bypass backend gates

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 113 — Microstructure & Liquidity Dashboard

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPERATOR_UI`  
**Composant propriétaire :** `OperatorConsoleDomain`  
**Frontière de code :** `src/crypto_quant_bot/ui`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Microstructure & Liquidity Dashboard » dans UI / Operator Console, produire MicrostructureLiquidityDashboardStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MicrostructureLiquidityDashboardStateV1
- MicrostructureLiquidityDashboardAuditV1
- UIReadModelV1
- OperatorActionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 113, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Microstructure & Liquidity Dashboard » dans le composant OperatorConsoleDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Consommer uniquement read models backend ; aucune logique de gate n’est réimplémentée côté UI.
6. Afficher freshness, uncertainty, veto, lineage et state version.
7. Contrôler RBAC et confirmation renforcée pour pause/kill/approval lorsque ces actions existent.
8. Conserver audit de chaque action opérateur et résultat backend.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/ui/microstructure_and_liquidity_dashboard.py
- src/crypto_quant_bot/ui/microstructure_and_liquidity_dashboard_models.py
- scripts/run_lot113_microstructure_and_liquidity_dashboard.py
- scripts/validate_lot113.py
- tests/test_lot113_microstructure_and_liquidity_dashboard.py
- data/audit/microstructure_and_liquidity_dashboard_lot113.json
- reports/lot_113_microstructure_and_liquidity_dashboard_report.md
- docs/LOT_113_MICROSTRUCTURE_AND_LIQUIDITY_DASHBOARD.md
- docs/ACCEPTANCE_CRITERIA_LOT_113.md

### Observabilité minimale

- lot_113_records_processed_total
- lot_113_validation_failures_total
- lot_113_processing_latency_ms

### Tests et critères d’acceptation

- Aucune action non autorisée
- Freshness visible
- Risk/veto visible
- Keyboard/accessibility checks
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- UI ne peut appeler endpoint non autorisé.
- Stale state clairement visible.
- Keyboard/accessibility et permission matrix.

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
- UI does not bypass backend gates

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 114 — Scenario, Signal & Strategy Dashboard

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPERATOR_UI`  
**Composant propriétaire :** `OperatorConsoleDomain`  
**Frontière de code :** `src/crypto_quant_bot/ui`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Scenario, Signal & Strategy Dashboard » dans UI / Operator Console, produire ScenarioSignalStrategyDashboardStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ScenarioSignalStrategyDashboardStateV1
- ScenarioSignalStrategyDashboardAuditV1
- ScenarioSetV1
- ScenarioConflictMatrixV1
- UIReadModelV1
- OperatorActionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 114, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Scenario, Signal & Strategy Dashboard » dans le composant OperatorConsoleDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Construire scénarios concurrents à partir de faits mesurés et d’hypothèses explicitement étiquetées.
6. Pour chaque scénario : preconditions, evidence, counter_evidence, invalidation, horizon, confidence et observability.
7. Normaliser les scores sans forcer leur somme à 1 sauf modèle calibré.
8. Scenario score reste non exécutable et ne produit aucun OrderIntent.
9. Consommer uniquement read models backend ; aucune logique de gate n’est réimplémentée côté UI.
10. Afficher freshness, uncertainty, veto, lineage et state version.
11. Contrôler RBAC et confirmation renforcée pour pause/kill/approval lorsque ces actions existent.
12. Conserver audit de chaque action opérateur et résultat backend.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/ui/scenario_signal_and_strategy_dashboard.py
- src/crypto_quant_bot/ui/scenario_signal_and_strategy_dashboard_models.py
- scripts/run_lot114_scenario_signal_and_strategy_dashboard.py
- scripts/validate_lot114.py
- tests/test_lot114_scenario_signal_and_strategy_dashboard.py
- data/audit/scenario_signal_and_strategy_dashboard_lot114.json
- reports/lot_114_scenario_signal_and_strategy_dashboard_report.md
- docs/LOT_114_SCENARIO_SIGNAL_AND_STRATEGY_DASHBOARD.md
- docs/ACCEPTANCE_CRITERIA_LOT_114.md

### Observabilité minimale

- lot_114_records_processed_total
- lot_114_validation_failures_total
- lot_114_processing_latency_ms

### Tests et critères d’acceptation

- Aucune action non autorisée
- Freshness visible
- Risk/veto visible
- Keyboard/accessibility checks
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Scénarios contradictoires conservés.
- Absence de calibration interdit le champ probability.
- UI ne peut appeler endpoint non autorisé.
- Stale state clairement visible.
- Keyboard/accessibility et permission matrix.

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
- UI does not bypass backend gates

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 115 — Risk Command Center

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPERATOR_UI`  
**Composant propriétaire :** `OperatorConsoleDomain`  
**Frontière de code :** `src/crypto_quant_bot/ui`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Risk Command Center » dans UI / Operator Console, produire RiskCommandCenterStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- RiskCommandCenterStateV1
- RiskCommandCenterAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 115, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Risk Command Center » dans le composant OperatorConsoleDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/ui/risk_command_center.py
- src/crypto_quant_bot/ui/risk_command_center_models.py
- scripts/run_lot115_risk_command_center.py
- scripts/validate_lot115.py
- tests/test_lot115_risk_command_center.py
- data/audit/risk_command_center_lot115.json
- reports/lot_115_risk_command_center_report.md
- docs/LOT_115_RISK_COMMAND_CENTER.md
- docs/ACCEPTANCE_CRITERIA_LOT_115.md

### Observabilité minimale

- lot_115_records_processed_total
- lot_115_validation_failures_total
- lot_115_processing_latency_ms

### Tests et critères d’acceptation

- Aucune action non autorisée
- Freshness visible
- Risk/veto visible
- Keyboard/accessibility checks
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
- UI does not bypass backend gates

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 116 — Paper, Portfolio & PnL Dashboard

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPERATOR_UI`  
**Composant propriétaire :** `OperatorConsoleDomain`  
**Frontière de code :** `src/crypto_quant_bot/ui`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Paper, Portfolio & PnL Dashboard » dans UI / Operator Console, produire PaperPortfolioPnLDashboardStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- PaperPortfolioPnLDashboardStateV1
- PaperPortfolioPnLDashboardAuditV1
- UIReadModelV1
- OperatorActionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 116, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Paper, Portfolio & PnL Dashboard » dans le composant OperatorConsoleDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Consommer uniquement read models backend ; aucune logique de gate n’est réimplémentée côté UI.
6. Afficher freshness, uncertainty, veto, lineage et state version.
7. Contrôler RBAC et confirmation renforcée pour pause/kill/approval lorsque ces actions existent.
8. Conserver audit de chaque action opérateur et résultat backend.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/ui/paper_portfolio_and_pnl_dashboard.py
- src/crypto_quant_bot/ui/paper_portfolio_and_pnl_dashboard_models.py
- scripts/run_lot116_paper_portfolio_and_pnl_dashboard.py
- scripts/validate_lot116.py
- tests/test_lot116_paper_portfolio_and_pnl_dashboard.py
- data/audit/paper_portfolio_and_pnl_dashboard_lot116.json
- reports/lot_116_paper_portfolio_and_pnl_dashboard_report.md
- docs/LOT_116_PAPER_PORTFOLIO_AND_PNL_DASHBOARD.md
- docs/ACCEPTANCE_CRITERIA_LOT_116.md

### Observabilité minimale

- lot_116_records_processed_total
- lot_116_validation_failures_total
- lot_116_processing_latency_ms

### Tests et critères d’acceptation

- Aucune action non autorisée
- Freshness visible
- Risk/veto visible
- Keyboard/accessibility checks
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- UI ne peut appeler endpoint non autorisé.
- Stale state clairement visible.
- Keyboard/accessibility et permission matrix.

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
- UI does not bypass backend gates

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 117 — Audit Replay & Human Operator Console

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPERATOR_UI`  
**Composant propriétaire :** `OperatorConsoleDomain`  
**Frontière de code :** `src/crypto_quant_bot/ui`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Audit Replay & Human Operator Console » dans UI / Operator Console, produire AuditReplayHumanOperatorConsoleStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- AuditReplayHumanOperatorConsoleStateV1
- AuditReplayHumanOperatorConsoleAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- UIReadModelV1
- OperatorActionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 117, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Audit Replay & Human Operator Console » dans le composant OperatorConsoleDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Consommer uniquement read models backend ; aucune logique de gate n’est réimplémentée côté UI.
10. Afficher freshness, uncertainty, veto, lineage et state version.
11. Contrôler RBAC et confirmation renforcée pour pause/kill/approval lorsque ces actions existent.
12. Conserver audit de chaque action opérateur et résultat backend.

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

- src/crypto_quant_bot/ui/audit_replay_and_human_operator_console.py
- src/crypto_quant_bot/ui/audit_replay_and_human_operator_console_models.py
- scripts/run_lot117_audit_replay_and_human_operator_console.py
- scripts/validate_lot117.py
- tests/test_lot117_audit_replay_and_human_operator_console.py
- data/audit/audit_replay_and_human_operator_console_lot117.json
- reports/lot_117_audit_replay_and_human_operator_console_report.md
- docs/LOT_117_AUDIT_REPLAY_AND_HUMAN_OPERATOR_CONSOLE.md
- docs/ACCEPTANCE_CRITERIA_LOT_117.md

### Observabilité minimale

- lot_117_records_processed_total
- lot_117_validation_failures_total
- lot_117_processing_latency_ms

### Tests et critères d’acceptation

- Aucune action non autorisée
- Freshness visible
- Risk/veto visible
- Keyboard/accessibility checks
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- UI ne peut appeler endpoint non autorisé.
- Stale state clairement visible.
- Keyboard/accessibility et permission matrix.

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
- UI does not bypass backend gates

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 118 — UI Security, Accessibility & V12 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPERATOR_UI`  
**Composant propriétaire :** `OperatorConsoleDomain`  
**Frontière de code :** `src/crypto_quant_bot/ui`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « UI Security, Accessibility & V12 Closure » dans UI / Operator Console, produire UISecurityAccessibilityV12ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- UISecurityAccessibilityV12ClosureStateV1
- UISecurityAccessibilityV12ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- UIReadModelV1
- OperatorActionAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 118, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « UI Security, Accessibility & V12 Closure » dans le composant OperatorConsoleDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Consommer uniquement read models backend ; aucune logique de gate n’est réimplémentée côté UI.
10. Afficher freshness, uncertainty, veto, lineage et state version.
11. Contrôler RBAC et confirmation renforcée pour pause/kill/approval lorsque ces actions existent.
12. Conserver audit de chaque action opérateur et résultat backend.

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

- scripts/validate_all_until_lot118.py
- scripts/run_required_chain_until_lot118.sh
- scripts/diagnose_exact_chain_until_lot118.py
- tests/test_lot118_closure_contract.py
- data/audit/closure_manifest_lot118.json
- reports/lot_118_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_118.md
- src/crypto_quant_bot/ui/ui_security_accessibility_and_v12_closure.py
- src/crypto_quant_bot/ui/ui_security_accessibility_and_v12_closure_models.py
- scripts/run_lot118_ui_security_accessibility_and_v12_closure.py
- scripts/validate_lot118.py
- tests/test_lot118_ui_security_accessibility_and_v12_closure.py
- data/audit/ui_security_accessibility_and_v12_closure_lot118.json
- reports/lot_118_ui_security_accessibility_and_v12_closure_report.md
- docs/LOT_118_UI_SECURITY_ACCESSIBILITY_AND_V12_CLOSURE.md

### Observabilité minimale

- lot_118_records_processed_total
- lot_118_validation_failures_total
- lot_118_processing_latency_ms

### Tests et critères d’acceptation

- Aucune action non autorisée
- Freshness visible
- Risk/veto visible
- Keyboard/accessibility checks
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- UI ne peut appeler endpoint non autorisé.
- Stale state clairement visible.
- Keyboard/accessibility et permission matrix.

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
- UI does not bypass backend gates

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 111–118 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
