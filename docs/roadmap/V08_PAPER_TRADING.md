# V8 — Paper Trading

Identifiant : `V8_PAPER_TRADING`  
Plage canonique : **Lots 81 à 87**  
Composant/domain owner : `PaperTradingDomain`  
Mode maximal autorisé : `PAPER`

## Finalité de la version

Faire évoluer le système de **V7 fermée** vers **Paper stable et réconcilié**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- V7 fermée.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/paper_trading`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 81 — Paper Trading Scope Gate & Runtime Mode

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PAPER`  
**Composant propriétaire :** `PaperTradingDomain`  
**Frontière de code :** `src/crypto_quant_bot/paper_trading`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Paper Trading Scope Gate & Runtime Mode » dans Paper Trading, produire PaperTradingScopeGateRuntimeModeStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ApprovedStrategyV1
- RiskDecisionV1
- PaperMarketDataV1

### Contrats de sortie

- PaperTradingScopeGateRuntimeModeStateV1
- PaperTradingScopeGateRuntimeModeAuditV1
- PaperTradingScopeGateRuntimeModeContractRegistryV1
- PaperTradingScopeGateRuntimeModeCapabilityMatrixV1
- PaperOrderV1
- PaperFillV1
- PaperPositionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 81, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Paper Trading Scope Gate & Runtime Mode » dans le composant PaperTradingDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir frontières, responsabilités, dépendances autorisées, modes runtime et API publiques du domaine.
6. Classer chaque capability en REQUIRED, OPTIONAL_RESEARCH, DISABLED ou FORBIDDEN.
7. Interdire tout client réseau exchange dans runtime PAPER.
8. Utiliser horloge/runtime isolé et mêmes contrats OMS/portfolio que les modes ultérieurs.
9. Simuler ack, partial/no-fill, fees, slippage et expiry.
10. Réconcilier ledger, positions et cash après chaque event batch.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/paper_trading/paper_trading_scope_gate_and_runtime_mode.py
- src/crypto_quant_bot/paper_trading/paper_trading_scope_gate_and_runtime_mode_models.py
- scripts/run_lot81_paper_trading_scope_gate_and_runtime_mode.py
- scripts/validate_lot81.py
- tests/test_lot81_paper_trading_scope_gate_and_runtime_mode.py
- data/audit/paper_trading_scope_gate_and_runtime_mode_lot81.json
- reports/lot_81_paper_trading_scope_gate_and_runtime_mode_report.md
- docs/LOT_81_PAPER_TRADING_SCOPE_GATE_AND_RUNTIME_MODE.md
- docs/ACCEPTANCE_CRITERIA_LOT_81.md

### Observabilité minimale

- lot_81_records_processed_total
- lot_81_validation_failures_total
- lot_81_processing_latency_ms

### Tests et critères d’acceptation

- Aucun réseau
- Aucun ordre réel
- Ledger équilibré
- Incidents simulés gérés
- Promotion explicite
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test de dépendances interdites entre domaines.
- Test de couverture : chaque capability a owner, contrat et gate.
- Test réseau interdit.
- Crash/restart reconstruit le même ledger.
- Aucun paper fill sans règle de fill satisfaite.

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
- runtime_mode=PAPER
- external_connectivity=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 82 — Paper Order / Fill Simulation

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PAPER`  
**Composant propriétaire :** `PaperTradingDomain`  
**Frontière de code :** `src/crypto_quant_bot/paper_trading`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Paper Order / Fill Simulation » dans Paper Trading, produire PaperOrderFillSimulationStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ApprovedStrategyV1
- RiskDecisionV1
- PaperMarketDataV1

### Contrats de sortie

- PaperOrderFillSimulationStateV1
- PaperOrderFillSimulationAuditV1
- PaperOrderV1
- PaperFillV1
- PaperPositionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 82, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Paper Order / Fill Simulation » dans le composant PaperTradingDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Interdire tout client réseau exchange dans runtime PAPER.
6. Utiliser horloge/runtime isolé et mêmes contrats OMS/portfolio que les modes ultérieurs.
7. Simuler ack, partial/no-fill, fees, slippage et expiry.
8. Réconcilier ledger, positions et cash après chaque event batch.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/paper_trading/paper_order_fill_simulation.py
- src/crypto_quant_bot/paper_trading/paper_order_fill_simulation_models.py
- scripts/run_lot82_paper_order_fill_simulation.py
- scripts/validate_lot82.py
- tests/test_lot82_paper_order_fill_simulation.py
- data/audit/paper_order_fill_simulation_lot82.json
- reports/lot_82_paper_order_fill_simulation_report.md
- docs/LOT_82_PAPER_ORDER_FILL_SIMULATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_82.md

### Observabilité minimale

- lot_82_records_processed_total
- lot_82_validation_failures_total
- lot_82_processing_latency_ms

### Tests et critères d’acceptation

- Aucun réseau
- Aucun ordre réel
- Ledger équilibré
- Incidents simulés gérés
- Promotion explicite
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test réseau interdit.
- Crash/restart reconstruit le même ledger.
- Aucun paper fill sans règle de fill satisfaite.

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
- runtime_mode=PAPER
- external_connectivity=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 83 — Signal-to-Paper Decision Mapping

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PAPER`  
**Composant propriétaire :** `PaperTradingDomain`  
**Frontière de code :** `src/crypto_quant_bot/paper_trading`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Signal-to-Paper Decision Mapping » dans Paper Trading, produire SignalToPaperDecisionMappingStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- SignalV1 produit par V5
- TradeIntentV1 produit par V5
- RiskDecisionV1 produit par V7

### Contrats de sortie

- SignalToPaperDecisionMappingStateV1
- SignalToPaperDecisionMappingAuditV1
- PaperOrderIntentV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 83, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Signal-to-Paper Decision Mapping » dans le composant PaperTradingDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. TradeIntent exprime proposition instrument/horizon/side/max-risk sans route venue.
6. RiskDecision APPROVE est requis pour créer OrderIntent.
7. OrderIntent ajoute venue, order_type, qty/price constraints, TIF, idempotency_key et approval references.
8. Toute modification après approval invalide l’approbation et impose une nouvelle décision risk.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/paper_trading/signal_to_paper_decision_mapping.py
- src/crypto_quant_bot/paper_trading/signal_to_paper_decision_mapping_models.py
- scripts/run_lot83_signal_to_paper_decision_mapping.py
- scripts/validate_lot83.py
- tests/test_lot83_signal_to_paper_decision_mapping.py
- data/audit/signal_to_paper_decision_mapping_lot83.json
- reports/lot_83_signal_to_paper_decision_mapping_report.md
- docs/LOT_83_SIGNAL_TO_PAPER_DECISION_MAPPING.md
- docs/ACCEPTANCE_CRITERIA_LOT_83.md

### Observabilité minimale

- lot_83_records_processed_total
- lot_83_validation_failures_total
- lot_83_processing_latency_ms

### Tests et critères d’acceptation

- Aucun réseau
- Aucun ordre réel
- Ledger équilibré
- Incidents simulés gérés
- Promotion explicite
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- TradeIntent sans Signal valide rejeté.
- OrderIntent sans RiskDecision APPROVE rejeté.
- Mutation quantité après approval détectée.

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
- runtime_mode=PAPER
- external_connectivity=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 84 — Paper Ledger, Position State & Reconciliation

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PAPER`  
**Composant propriétaire :** `PaperTradingDomain`  
**Frontière de code :** `src/crypto_quant_bot/paper_trading`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Paper Ledger, Position State & Reconciliation » dans Paper Trading, produire PaperLedgerPositionStateReconciliationStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ApprovedStrategyV1
- RiskDecisionV1
- PaperMarketDataV1

### Contrats de sortie

- PaperLedgerPositionStateReconciliationStateV1
- PaperLedgerPositionStateReconciliationAuditV1
- ReconciliationReportV1
- ReconciliationVetoV1
- PaperOrderV1
- PaperFillV1
- PaperPositionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 84, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Paper Ledger, Position State & Reconciliation » dans le composant PaperTradingDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Comparer identifiants, quantités, prix, frais, balances, positions et timestamps entre les deux sources concernées.
6. Classer MATCH, TOLERATED_DIFF, MINOR_DIVERGENCE, CRITICAL_DIVERGENCE.
7. Produire delta exact, tolérance versionnée, source de vérité et action corrective.
8. MINOR → PAUSE ; CRITICAL/unknown ownership → KILL_SWITCH ou BLOCK_TRADING selon matrice.
9. Interdire tout client réseau exchange dans runtime PAPER.
10. Utiliser horloge/runtime isolé et mêmes contrats OMS/portfolio que les modes ultérieurs.
11. Simuler ack, partial/no-fill, fees, slippage et expiry.
12. Réconcilier ledger, positions et cash après chaque event batch.

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

- src/crypto_quant_bot/paper_trading/paper_ledger_position_state_and_reconciliation.py
- src/crypto_quant_bot/paper_trading/paper_ledger_position_state_and_reconciliation_models.py
- scripts/run_lot84_paper_ledger_position_state_and_reconciliation.py
- scripts/validate_lot84.py
- tests/test_lot84_paper_ledger_position_state_and_reconciliation.py
- data/audit/paper_ledger_position_state_and_reconciliation_lot84.json
- reports/lot_84_paper_ledger_position_state_and_reconciliation_report.md
- docs/LOT_84_PAPER_LEDGER_POSITION_STATE_AND_RECONCILIATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_84.md

### Observabilité minimale

- lot_84_records_processed_total
- lot_84_validation_failures_total
- lot_84_processing_latency_ms

### Tests et critères d’acceptation

- Aucun réseau
- Aucun ordre réel
- Ledger équilibré
- Incidents simulés gérés
- Promotion explicite
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Ordre/fill/balance/frais divergents injectés.
- Reconciliation idempotente après restart.
- Test réseau interdit.
- Crash/restart reconstruit le même ledger.
- Aucun paper fill sans règle de fill satisfaite.

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
- runtime_mode=PAPER
- external_connectivity=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 85 — Paper Risk Controls & Incident Handling

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PAPER`  
**Composant propriétaire :** `PaperTradingDomain`  
**Frontière de code :** `src/crypto_quant_bot/paper_trading`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Paper Risk Controls & Incident Handling » dans Paper Trading, produire PaperRiskControlsIncidentHandlingStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ApprovedStrategyV1
- RiskDecisionV1
- PaperMarketDataV1

### Contrats de sortie

- PaperRiskControlsIncidentHandlingStateV1
- PaperRiskControlsIncidentHandlingAuditV1
- PaperOrderV1
- PaperFillV1
- PaperPositionV1
- PaperIncidentEventV1
- PaperRiskActionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 85, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Paper Risk Controls & Incident Handling » dans le composant PaperTradingDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Interdire tout client réseau exchange dans runtime PAPER.
6. Utiliser horloge/runtime isolé et mêmes contrats OMS/portfolio que les modes ultérieurs.
7. Simuler ack, partial/no-fill, fees, slippage et expiry.
8. Réconcilier ledger, positions et cash après chaque event batch.
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

- src/crypto_quant_bot/paper_trading/paper_risk_controls_and_incident_handling.py
- src/crypto_quant_bot/paper_trading/paper_risk_controls_and_incident_handling_models.py
- scripts/run_lot85_paper_risk_controls_and_incident_handling.py
- scripts/validate_lot85.py
- tests/test_lot85_paper_risk_controls_and_incident_handling.py
- data/audit/paper_risk_controls_and_incident_handling_lot85.json
- reports/lot_85_paper_risk_controls_and_incident_handling_report.md
- docs/LOT_85_PAPER_RISK_CONTROLS_AND_INCIDENT_HANDLING.md
- docs/ACCEPTANCE_CRITERIA_LOT_85.md

### Observabilité minimale

- lot_85_records_processed_total
- lot_85_validation_failures_total
- lot_85_processing_latency_ms

### Tests et critères d’acceptation

- Aucun réseau
- Aucun ordre réel
- Ledger équilibré
- Incidents simulés gérés
- Promotion explicite
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test réseau interdit.
- Crash/restart reconstruit le même ledger.
- Aucun paper fill sans règle de fill satisfaite.
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
- runtime_mode=PAPER
- external_connectivity=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 86 — Paper Performance & Sandbox Promotion Gate

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PAPER`  
**Composant propriétaire :** `PaperTradingDomain`  
**Frontière de code :** `src/crypto_quant_bot/paper_trading`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Paper Performance & Sandbox Promotion Gate » dans Paper Trading, produire PaperPerformanceSandboxPromotionGateStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ApprovedStrategyV1
- RiskDecisionV1
- PaperMarketDataV1

### Contrats de sortie

- PaperPerformanceSandboxPromotionGateStateV1
- PaperPerformanceSandboxPromotionGateAuditV1
- PromotionDecisionV1
- PaperOrderV1
- PaperFillV1
- PaperPositionV1
- SandboxPromotionDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 86, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Paper Performance & Sandbox Promotion Gate » dans le composant PaperTradingDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Assembler preuves requises, seuils versionnés, exceptions et sign-offs.
6. Évaluer chaque critère PASS/FAIL/NOT_APPLICABLE avec justification.
7. Toute donnée manquante → FAIL ; aucun override silencieux.
8. Enregistrer approver, timestamp, expiry et scope exact de la promotion.
9. Interdire tout client réseau exchange dans runtime PAPER.
10. Utiliser horloge/runtime isolé et mêmes contrats OMS/portfolio que les modes ultérieurs.
11. Simuler ack, partial/no-fill, fees, slippage et expiry.
12. Réconcilier ledger, positions et cash après chaque event batch.
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

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/paper_trading/paper_performance_and_sandbox_promotion_gate.py
- src/crypto_quant_bot/paper_trading/paper_performance_and_sandbox_promotion_gate_models.py
- scripts/run_lot86_paper_performance_and_sandbox_promotion_gate.py
- scripts/validate_lot86.py
- tests/test_lot86_paper_performance_and_sandbox_promotion_gate.py
- data/audit/paper_performance_and_sandbox_promotion_gate_lot86.json
- reports/lot_86_paper_performance_and_sandbox_promotion_gate_report.md
- docs/LOT_86_PAPER_PERFORMANCE_AND_SANDBOX_PROMOTION_GATE.md
- docs/ACCEPTANCE_CRITERIA_LOT_86.md

### Observabilité minimale

- lot_86_records_processed_total
- lot_86_validation_failures_total
- lot_86_processing_latency_ms

### Tests et critères d’acceptation

- Aucun réseau
- Aucun ordre réel
- Ledger équilibré
- Incidents simulés gérés
- Promotion explicite
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Preuve manquante bloque promotion.
- Promotion expirée ne peut être consommée.
- Test réseau interdit.
- Crash/restart reconstruit le même ledger.
- Aucun paper fill sans règle de fill satisfaite.
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
- runtime_mode=PAPER
- external_connectivity=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 87 — V8 Paper Trading Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PAPER`  
**Composant propriétaire :** `PaperTradingDomain`  
**Frontière de code :** `src/crypto_quant_bot/paper_trading`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « V8 Paper Trading Closure » dans Paper Trading, produire V8PaperTradingClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models
- ApprovedStrategyV1
- RiskDecisionV1
- PaperMarketDataV1

### Contrats de sortie

- V8PaperTradingClosureStateV1
- V8PaperTradingClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- PaperOrderV1
- PaperFillV1
- PaperPositionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 87, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « V8 Paper Trading Closure » dans le composant PaperTradingDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Interdire tout client réseau exchange dans runtime PAPER.
10. Utiliser horloge/runtime isolé et mêmes contrats OMS/portfolio que les modes ultérieurs.
11. Simuler ack, partial/no-fill, fees, slippage et expiry.
12. Réconcilier ledger, positions et cash après chaque event batch.

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

- scripts/validate_all_until_lot87.py
- scripts/run_required_chain_until_lot87.sh
- scripts/diagnose_exact_chain_until_lot87.py
- tests/test_lot87_closure_contract.py
- data/audit/closure_manifest_lot87.json
- reports/lot_87_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_87.md
- src/crypto_quant_bot/paper_trading/v8_paper_trading_closure.py
- src/crypto_quant_bot/paper_trading/v8_paper_trading_closure_models.py
- scripts/run_lot87_v8_paper_trading_closure.py
- scripts/validate_lot87.py
- tests/test_lot87_v8_paper_trading_closure.py
- data/audit/v8_paper_trading_closure_lot87.json
- reports/lot_87_v8_paper_trading_closure_report.md
- docs/LOT_87_V8_PAPER_TRADING_CLOSURE.md

### Observabilité minimale

- lot_87_records_processed_total
- lot_87_validation_failures_total
- lot_87_processing_latency_ms

### Tests et critères d’acceptation

- Aucun réseau
- Aucun ordre réel
- Ledger équilibré
- Incidents simulés gérés
- Promotion explicite
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Test réseau interdit.
- Crash/restart reconstruit le même ledger.
- Aucun paper fill sans règle de fill satisfaite.

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
- runtime_mode=PAPER
- external_connectivity=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 81–87 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
