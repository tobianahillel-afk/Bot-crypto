# V19 — HFT Research

Identifiant : `V19_HFT_RESEARCH`  
Plage canonique : **Lots 166 à 171**  
Composant/domain owner : `HFTResearchDomain`  
Mode maximal autorisé : `HFT_RESEARCH_ONLY`

## Finalité de la version

Faire évoluer le système de **Données tick/L2/L3 historiques** vers **Conclusion de faisabilité research-only**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Données tick/L2/L3 historiques.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/hft_research`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 166 — HFT Scope & Feasibility Reality Check

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `HFT_RESEARCH_ONLY`  
**Composant propriétaire :** `HFTResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/hft_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « HFT Scope & Feasibility Reality Check » dans HFT Research, produire HFTScopeFeasibilityRealityCheckStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- HFTScopeFeasibilityRealityCheckStateV1
- HFTScopeFeasibilityRealityCheckAuditV1
- HFTScopeFeasibilityRealityCheckContractRegistryV1
- HFTScopeFeasibilityRealityCheckCapabilityMatrixV1
- HFTResearchResultV1
- QueueSimulationStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 166, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « HFT Scope & Feasibility Reality Check » dans le composant HFTResearchDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir frontières, responsabilités, dépendances autorisées, modes runtime et API publiques du domaine.
6. Classer chaque capability en REQUIRED, OPTIONAL_RESEARCH, DISABLED ou FORBIDDEN.
7. Rester offline/simulation : aucun adapter live.
8. Utiliser tick/L2/L3 avec nanosecond/microsecond precision conservée selon source.
9. Simuler matching rules, queue priority, cancel/replace latency, message budgets et exchange throttles.
10. Mesurer adverse selection, toxicity, inventory risk et fill realism.
11. Conclure feasibility/non-feasibility avec limitations infrastructure.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/hft_research/hft_scope_and_feasibility_reality_check.py
- src/crypto_quant_bot/hft_research/hft_scope_and_feasibility_reality_check_models.py
- scripts/run_lot166_hft_scope_and_feasibility_reality_check.py
- scripts/validate_lot166.py
- tests/test_lot166_hft_scope_and_feasibility_reality_check.py
- data/audit/hft_scope_and_feasibility_reality_check_lot166.json
- reports/lot_166_hft_scope_and_feasibility_reality_check_report.md
- docs/LOT_166_HFT_SCOPE_AND_FEASIBILITY_REALITY_CHECK.md
- docs/ACCEPTANCE_CRITERIA_LOT_166.md

### Observabilité minimale

- lot_166_records_processed_total
- lot_166_validation_failures_total
- lot_166_processing_latency_ms

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test de dépendances interdites entre domaines.
- Test de couverture : chaque capability a owner, contrat et gate.
- Aucun fill impossible ou avant ack.
- Sensitivity à latency/queue assumptions.
- Recherche de tout chemin live = FAIL.

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
- HFT_LIVE=FORBIDDEN
- research_only=true

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 167 — Tick / L2 / L3 Data & High-Resolution Time Policy

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `HFT_RESEARCH_ONLY`  
**Composant propriétaire :** `HFTResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/hft_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Tick / L2 / L3 Data & High-Resolution Time Policy » dans HFT Research, produire TickL2L3DataHighResolutionTimePolicyStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- RawTimestampEnvelopeV1

### Contrats de sortie

- TickL2L3DataHighResolutionTimePolicyStateV1
- TickL2L3DataHighResolutionTimePolicyAuditV1
- CanonicalTimeEnvelopeV1
- ClockHealthStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 167, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Tick / L2 / L3 Data & High-Resolution Time Policy » dans le composant HFTResearchDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/hft_research/tick_l2_l3_data_and_high_resolution_time_policy.py
- src/crypto_quant_bot/hft_research/tick_l2_l3_data_and_high_resolution_time_policy_models.py
- scripts/run_lot167_tick_l2_l3_data_and_high_resolution_time_policy.py
- scripts/validate_lot167.py
- tests/test_lot167_tick_l2_l3_data_and_high_resolution_time_policy.py
- data/audit/tick_l2_l3_data_and_high_resolution_time_policy_lot167.json
- reports/lot_167_tick_l2_l3_data_and_high_resolution_time_policy_report.md
- docs/LOT_167_TICK_L2_L3_DATA_AND_HIGH_RESOLUTION_TIME_POLICY.md
- docs/ACCEPTANCE_CRITERIA_LOT_167.md

### Observabilité minimale

- lot_167_records_processed_total
- lot_167_validation_failures_total
- lot_167_processing_latency_ms

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path
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
- HFT_LIVE=FORBIDDEN
- research_only=true

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 168 — Matching Engine & Queue-Position Simulator

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `HFT_RESEARCH_ONLY`  
**Composant propriétaire :** `HFTResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/hft_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Matching Engine & Queue-Position Simulator » dans HFT Research, produire MatchingEngineQueuePositionSimulatorStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MatchingEngineQueuePositionSimulatorStateV1
- MatchingEngineQueuePositionSimulatorAuditV1
- HFTResearchResultV1
- QueueSimulationStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 168, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Matching Engine & Queue-Position Simulator » dans le composant HFTResearchDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rester offline/simulation : aucun adapter live.
6. Utiliser tick/L2/L3 avec nanosecond/microsecond precision conservée selon source.
7. Simuler matching rules, queue priority, cancel/replace latency, message budgets et exchange throttles.
8. Mesurer adverse selection, toxicity, inventory risk et fill realism.
9. Conclure feasibility/non-feasibility avec limitations infrastructure.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/hft_research/matching_engine_and_queue_position_simulator.py
- src/crypto_quant_bot/hft_research/matching_engine_and_queue_position_simulator_models.py
- scripts/run_lot168_matching_engine_and_queue_position_simulator.py
- scripts/validate_lot168.py
- tests/test_lot168_matching_engine_and_queue_position_simulator.py
- data/audit/matching_engine_and_queue_position_simulator_lot168.json
- reports/lot_168_matching_engine_and_queue_position_simulator_report.md
- docs/LOT_168_MATCHING_ENGINE_AND_QUEUE_POSITION_SIMULATOR.md
- docs/ACCEPTANCE_CRITERIA_LOT_168.md

### Observabilité minimale

- lot_168_records_processed_total
- lot_168_validation_failures_total
- lot_168_processing_latency_ms

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Aucun fill impossible ou avant ack.
- Sensitivity à latency/queue assumptions.
- Recherche de tout chemin live = FAIL.

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
- HFT_LIVE=FORBIDDEN
- research_only=true

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 169 — Low-Latency, Cancel/Replace & Message Budget

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `HFT_RESEARCH_ONLY`  
**Composant propriétaire :** `HFTResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/hft_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Low-Latency, Cancel/Replace & Message Budget » dans HFT Research, produire LowLatencyCancelReplaceMessageBudgetStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- LowLatencyCancelReplaceMessageBudgetStateV1
- LowLatencyCancelReplaceMessageBudgetAuditV1
- HFTResearchResultV1
- QueueSimulationStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 169, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Low-Latency, Cancel/Replace & Message Budget » dans le composant HFTResearchDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rester offline/simulation : aucun adapter live.
6. Utiliser tick/L2/L3 avec nanosecond/microsecond precision conservée selon source.
7. Simuler matching rules, queue priority, cancel/replace latency, message budgets et exchange throttles.
8. Mesurer adverse selection, toxicity, inventory risk et fill realism.
9. Conclure feasibility/non-feasibility avec limitations infrastructure.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/hft_research/low_latency_cancel_replace_and_message_budget.py
- src/crypto_quant_bot/hft_research/low_latency_cancel_replace_and_message_budget_models.py
- scripts/run_lot169_low_latency_cancel_replace_and_message_budget.py
- scripts/validate_lot169.py
- tests/test_lot169_low_latency_cancel_replace_and_message_budget.py
- data/audit/low_latency_cancel_replace_and_message_budget_lot169.json
- reports/lot_169_low_latency_cancel_replace_and_message_budget_report.md
- docs/LOT_169_LOW_LATENCY_CANCEL_REPLACE_AND_MESSAGE_BUDGET.md
- docs/ACCEPTANCE_CRITERIA_LOT_169.md

### Observabilité minimale

- lot_169_records_processed_total
- lot_169_validation_failures_total
- lot_169_processing_latency_ms

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Aucun fill impossible ou avant ack.
- Sensitivity à latency/queue assumptions.
- Recherche de tout chemin live = FAIL.

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
- HFT_LIVE=FORBIDDEN
- research_only=true

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 170 — Market Making, Inventory Risk & Adverse Selection

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `HFT_RESEARCH_ONLY`  
**Composant propriétaire :** `HFTResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/hft_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Market Making, Inventory Risk & Adverse Selection » dans HFT Research, produire MarketMakingInventoryRiskAdverseSelectionStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MarketMakingInventoryRiskAdverseSelectionStateV1
- MarketMakingInventoryRiskAdverseSelectionAuditV1
- HFTResearchResultV1
- QueueSimulationStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 170, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Market Making, Inventory Risk & Adverse Selection » dans le composant HFTResearchDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rester offline/simulation : aucun adapter live.
6. Utiliser tick/L2/L3 avec nanosecond/microsecond precision conservée selon source.
7. Simuler matching rules, queue priority, cancel/replace latency, message budgets et exchange throttles.
8. Mesurer adverse selection, toxicity, inventory risk et fill realism.
9. Conclure feasibility/non-feasibility avec limitations infrastructure.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/hft_research/market_making_inventory_risk_and_adverse_selection.py
- src/crypto_quant_bot/hft_research/market_making_inventory_risk_and_adverse_selection_models.py
- scripts/run_lot170_market_making_inventory_risk_and_adverse_selection.py
- scripts/validate_lot170.py
- tests/test_lot170_market_making_inventory_risk_and_adverse_selection.py
- data/audit/market_making_inventory_risk_and_adverse_selection_lot170.json
- reports/lot_170_market_making_inventory_risk_and_adverse_selection_report.md
- docs/LOT_170_MARKET_MAKING_INVENTORY_RISK_AND_ADVERSE_SELECTION.md
- docs/ACCEPTANCE_CRITERIA_LOT_170.md

### Observabilité minimale

- lot_170_records_processed_total
- lot_170_validation_failures_total
- lot_170_processing_latency_ms

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Aucun fill impossible ou avant ack.
- Sensitivity à latency/queue assumptions.
- Recherche de tout chemin live = FAIL.

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
- HFT_LIVE=FORBIDDEN
- research_only=true

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 171 — HFT Replay, Risk Audit & Research Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `HFT_RESEARCH_ONLY`  
**Composant propriétaire :** `HFTResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/hft_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « HFT Replay, Risk Audit & Research Closure » dans HFT Research, produire HFTReplayRiskAuditResearchClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- HFTReplayRiskAuditResearchClosureStateV1
- HFTReplayRiskAuditResearchClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- HFTResearchResultV1
- QueueSimulationStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 171, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « HFT Replay, Risk Audit & Research Closure » dans le composant HFTResearchDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Rester offline/simulation : aucun adapter live.
10. Utiliser tick/L2/L3 avec nanosecond/microsecond precision conservée selon source.
11. Simuler matching rules, queue priority, cancel/replace latency, message budgets et exchange throttles.
12. Mesurer adverse selection, toxicity, inventory risk et fill realism.
13. Conclure feasibility/non-feasibility avec limitations infrastructure.

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

- scripts/validate_all_until_lot171.py
- scripts/run_required_chain_until_lot171.sh
- scripts/diagnose_exact_chain_until_lot171.py
- tests/test_lot171_closure_contract.py
- data/audit/closure_manifest_lot171.json
- reports/lot_171_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_171.md
- src/crypto_quant_bot/hft_research/hft_replay_risk_audit_and_research_closure.py
- src/crypto_quant_bot/hft_research/hft_replay_risk_audit_and_research_closure_models.py
- scripts/run_lot171_hft_replay_risk_audit_and_research_closure.py
- scripts/validate_lot171.py
- tests/test_lot171_hft_replay_risk_audit_and_research_closure.py
- data/audit/hft_replay_risk_audit_and_research_closure_lot171.json
- reports/lot_171_hft_replay_risk_audit_and_research_closure_report.md
- docs/LOT_171_HFT_REPLAY_RISK_AUDIT_AND_RESEARCH_CLOSURE.md

### Observabilité minimale

- lot_171_records_processed_total
- lot_171_validation_failures_total
- lot_171_processing_latency_ms

### Tests et critères d’acceptation

- No impossible fills
- Latency sensitivity
- Queue model validation
- No live path
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Aucun fill impossible ou avant ack.
- Sensitivity à latency/queue assumptions.
- Recherche de tout chemin live = FAIL.

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
- HFT_LIVE=FORBIDDEN
- research_only=true

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 166–171 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
