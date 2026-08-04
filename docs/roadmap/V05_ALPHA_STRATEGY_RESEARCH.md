# V5 — Alpha / Strategy Research

Identifiant : `V5_ALPHA_STRATEGY_RESEARCH`  
Plage canonique : **Lots 53 à 59**  
Composant/domain owner : `StrategyResearchDomain`  
Mode maximal autorisé : `OFFLINE_STRATEGY_RESEARCH_ONLY`

## Finalité de la version

Faire évoluer le système de **V4 fermée** vers **Candidates falsifiables éligibles au backtest**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- V4 fermée.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/strategy_research`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 53 — Alpha Governance & Hypothesis Registry

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_STRATEGY_RESEARCH_ONLY`  
**Composant propriétaire :** `StrategyResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/strategy_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Alpha Governance & Hypothesis Registry » dans Alpha / Strategy Research, produire AlphaGovernanceHypothesisRegistryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- AlphaGovernanceHypothesisRegistryStateV1
- AlphaGovernanceHypothesisRegistryAuditV1
- AlphaHypothesisV1
- FalsificationPlanV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 53, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Alpha Governance & Hypothesis Registry » dans le composant StrategyResearchDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/strategy_research/alpha_governance_and_hypothesis_registry.py
- src/crypto_quant_bot/strategy_research/alpha_governance_and_hypothesis_registry_models.py
- scripts/run_lot53_alpha_governance_and_hypothesis_registry.py
- scripts/validate_lot53.py
- tests/test_lot53_alpha_governance_and_hypothesis_registry.py
- data/audit/alpha_governance_and_hypothesis_registry_lot53.json
- reports/lot_53_alpha_governance_and_hypothesis_registry_report.md
- docs/LOT_53_ALPHA_GOVERNANCE_AND_HYPOTHESIS_REGISTRY.md
- docs/ACCEPTANCE_CRITERIA_LOT_53.md

### Observabilité minimale

- lot_53_records_processed_total
- lot_53_validation_failures_total
- lot_53_processing_latency_ms

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate
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
- signal != order
- trade_intent != order_intent
- LLM cannot create signal

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 54 — Strategy Candidate Contract

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_STRATEGY_RESEARCH_ONLY`  
**Composant propriétaire :** `StrategyResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/strategy_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Strategy Candidate Contract » dans Alpha / Strategy Research, produire StrategyCandidateContractStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- StrategyCandidateContractStateV1
- StrategyCandidateContractAuditV1
- StrategyCandidateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 54, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Strategy Candidate Contract » dans le composant StrategyResearchDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Figer strategy_id/version, alpha_ids, universe, timeframe, entry/exit/invalidation, holding horizon, sizing placeholder et dependencies.
6. Séparer paramètres recherchés, paramètres gelés et plages autorisées.
7. Inclure forbidden_data, leakage controls et expected cost model.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/strategy_research/strategy_candidate_contract.py
- src/crypto_quant_bot/strategy_research/strategy_candidate_contract_models.py
- scripts/run_lot54_strategy_candidate_contract.py
- scripts/validate_lot54.py
- tests/test_lot54_strategy_candidate_contract.py
- data/audit/strategy_candidate_contract_lot54.json
- reports/lot_54_strategy_candidate_contract_report.md
- docs/LOT_54_STRATEGY_CANDIDATE_CONTRACT.md
- docs/ACCEPTANCE_CRITERIA_LOT_54.md

### Observabilité minimale

- lot_54_records_processed_total
- lot_54_validation_failures_total
- lot_54_processing_latency_ms

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Candidate immuable après soumission.
- Candidate sans data lineage ou exit policy rejetée.

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
- signal != order
- trade_intent != order_intent
- LLM cannot create signal

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 55 — Signal Schema, Calibration & Expiration

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_STRATEGY_RESEARCH_ONLY`  
**Composant propriétaire :** `StrategyResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/strategy_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Signal Schema, Calibration & Expiration » dans Alpha / Strategy Research, produire SignalSchemaCalibrationExpirationStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SignalSchemaCalibrationExpirationStateV1
- SignalSchemaCalibrationExpirationAuditV1
- SignalV1
- SignalCalibrationStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 55, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Signal Schema, Calibration & Expiration » dans le composant StrategyResearchDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Produire signal_id, strategy_version, direction hypothesis, strength, confidence/calibration_id, created_at, expires_at et invalidation_reason.
6. Refuser confidence probabiliste sans calibration.
7. Expirer automatiquement le signal lorsque data/config/regime change ou TTL dépassé.
8. Le signal ne contient ni exchange, ni order type, ni quantity finale.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/strategy_research/signal_schema_calibration_and_expiration.py
- src/crypto_quant_bot/strategy_research/signal_schema_calibration_and_expiration_models.py
- scripts/run_lot55_signal_schema_calibration_and_expiration.py
- scripts/validate_lot55.py
- tests/test_lot55_signal_schema_calibration_and_expiration.py
- data/audit/signal_schema_calibration_and_expiration_lot55.json
- reports/lot_55_signal_schema_calibration_and_expiration_report.md
- docs/LOT_55_SIGNAL_SCHEMA_CALIBRATION_AND_EXPIRATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_55.md

### Observabilité minimale

- lot_55_records_processed_total
- lot_55_validation_failures_total
- lot_55_processing_latency_ms

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Signal expiré ne peut créer TradeIntent.
- Signal non calibré n’expose pas probability.

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
- signal != order
- trade_intent != order_intent
- LLM cannot create signal

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 56 — Trade Intent / Order Intent Boundary

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_STRATEGY_RESEARCH_ONLY`  
**Composant propriétaire :** `StrategyResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/strategy_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Trade Intent / Order Intent Boundary » dans Alpha / Strategy Research, produire TradeIntentOrderIntentBoundaryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- TradeIntentOrderIntentBoundaryStateV1
- TradeIntentOrderIntentBoundaryAuditV1
- TradeIntentV1
- OrderIntentV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 56, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Trade Intent / Order Intent Boundary » dans le composant StrategyResearchDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/strategy_research/trade_intent_order_intent_boundary.py
- src/crypto_quant_bot/strategy_research/trade_intent_order_intent_boundary_models.py
- scripts/run_lot56_trade_intent_order_intent_boundary.py
- scripts/validate_lot56.py
- tests/test_lot56_trade_intent_order_intent_boundary.py
- data/audit/trade_intent_order_intent_boundary_lot56.json
- reports/lot_56_trade_intent_order_intent_boundary_report.md
- docs/LOT_56_TRADE_INTENT_ORDER_INTENT_BOUNDARY.md
- docs/ACCEPTANCE_CRITERIA_LOT_56.md

### Observabilité minimale

- lot_56_records_processed_total
- lot_56_validation_failures_total
- lot_56_processing_latency_ms

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate
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
- signal != order
- trade_intent != order_intent
- LLM cannot create signal

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 57 — Regime Eligibility, Holding Horizon & Invalidation

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_STRATEGY_RESEARCH_ONLY`  
**Composant propriétaire :** `StrategyResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/strategy_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Regime Eligibility, Holding Horizon & Invalidation » dans Alpha / Strategy Research, produire RegimeEligibilityHoldingHorizonInvalidationStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- RegimeEligibilityHoldingHorizonInvalidationStateV1
- RegimeEligibilityHoldingHorizonInvalidationAuditV1
- StrategyEligibilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 57, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Regime Eligibility, Holding Horizon & Invalidation » dans le composant StrategyResearchDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Évaluer régime courant contre allow/deny lists versionnées.
6. Définir max_holding_time, review cadence et invalidation triggers.
7. Expirer candidate/signal lorsque l’horizon ou l’état de marché sort des limites.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/strategy_research/regime_eligibility_holding_horizon_and_invalidation.py
- src/crypto_quant_bot/strategy_research/regime_eligibility_holding_horizon_and_invalidation_models.py
- scripts/run_lot57_regime_eligibility_holding_horizon_and_invalidation.py
- scripts/validate_lot57.py
- tests/test_lot57_regime_eligibility_holding_horizon_and_invalidation.py
- data/audit/regime_eligibility_holding_horizon_and_invalidation_lot57.json
- reports/lot_57_regime_eligibility_holding_horizon_and_invalidation_report.md
- docs/LOT_57_REGIME_ELIGIBILITY_HOLDING_HORIZON_AND_INVALIDATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_57.md

### Observabilité minimale

- lot_57_records_processed_total
- lot_57_validation_failures_total
- lot_57_processing_latency_ms

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Transition de régime invalide un signal.
- Holding horizon boundary test.

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
- signal != order
- trade_intent != order_intent
- LLM cannot create signal

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 58 — Alpha Decay, Stability & Retirement Rules

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_STRATEGY_RESEARCH_ONLY`  
**Composant propriétaire :** `StrategyResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/strategy_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Alpha Decay, Stability & Retirement Rules » dans Alpha / Strategy Research, produire AlphaDecayStabilityRetirementRulesStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- AlphaDecayStabilityRetirementRulesStateV1
- AlphaDecayStabilityRetirementRulesAuditV1
- AlphaHypothesisV1
- FalsificationPlanV1
- StrategyHealthStateV1
- RetirementDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 58, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Alpha Decay, Stability & Retirement Rules » dans le composant StrategyResearchDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Décrire mécanisme économique/microstructure, population, horizon, régime, features permises et prédiction falsifiable.
6. Définir null hypothesis, métriques primaires, coûts attendus et conditions de rejet.
7. Enregistrer avant test pour éviter HARKing ; conserver résultats négatifs.
8. Comparer performance récente aux distributions backtest/paper approuvées.
9. Mesurer feature drift, prediction drift, calibration drift et cost drift.
10. Déclencher REVIEW, DE_RISK, PAUSE ou RETIRE selon politique ; jamais auto-scale-up.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/strategy_research/alpha_decay_stability_and_retirement_rules.py
- src/crypto_quant_bot/strategy_research/alpha_decay_stability_and_retirement_rules_models.py
- scripts/run_lot58_alpha_decay_stability_and_retirement_rules.py
- scripts/validate_lot58.py
- tests/test_lot58_alpha_decay_stability_and_retirement_rules.py
- data/audit/alpha_decay_stability_and_retirement_rules_lot58.json
- reports/lot_58_alpha_decay_stability_and_retirement_rules_report.md
- docs/LOT_58_ALPHA_DECAY_STABILITY_AND_RETIREMENT_RULES.md
- docs/ACCEPTANCE_CRITERIA_LOT_58.md

### Observabilité minimale

- lot_58_records_processed_total
- lot_58_validation_failures_total
- lot_58_processing_latency_ms

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Hypothèse sans falsification rejetée.
- Modification post-résultat crée une nouvelle version.
- Drift synthétique détecté.
- Retour à la normale ne réactive pas sans gate.

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
- signal != order
- trade_intent != order_intent
- LLM cannot create signal

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 59 — Research-to-Backtest Promotion Gate & V5 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OFFLINE_STRATEGY_RESEARCH_ONLY`  
**Composant propriétaire :** `StrategyResearchDomain`  
**Frontière de code :** `src/crypto_quant_bot/strategy_research`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Research-to-Backtest Promotion Gate & V5 Closure » dans Alpha / Strategy Research, produire ResearchToBacktestPromotionGateV5ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- ResearchToBacktestPromotionGateV5ClosureStateV1
- ResearchToBacktestPromotionGateV5ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- PromotionDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 59, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Research-to-Backtest Promotion Gate & V5 Closure » dans le composant StrategyResearchDomain sans effet de bord non déclaré.
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

- scripts/validate_all_until_lot59.py
- scripts/run_required_chain_until_lot59.sh
- scripts/diagnose_exact_chain_until_lot59.py
- tests/test_lot59_closure_contract.py
- data/audit/closure_manifest_lot59.json
- reports/lot_59_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_59.md
- src/crypto_quant_bot/strategy_research/research_to_backtest_promotion_gate_and_v5_closure.py
- src/crypto_quant_bot/strategy_research/research_to_backtest_promotion_gate_and_v5_closure_models.py
- scripts/run_lot59_research_to_backtest_promotion_gate_and_v5_closure.py
- scripts/validate_lot59.py
- tests/test_lot59_research_to_backtest_promotion_gate_and_v5_closure.py
- data/audit/research_to_backtest_promotion_gate_and_v5_closure_lot59.json
- reports/lot_59_research_to_backtest_promotion_gate_and_v5_closure_report.md
- docs/LOT_59_RESEARCH_TO_BACKTEST_PROMOTION_GATE_AND_V5_CLOSURE.md

### Observabilité minimale

- lot_59_records_processed_total
- lot_59_validation_failures_total
- lot_59_processing_latency_ms

### Tests et critères d’acceptation

- Chaque alpha est falsifiable
- Signal non exécutable
- Intent expiré refusé
- Aucune promotion sans gate
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
- signal != order
- trade_intent != order_intent
- LLM cannot create signal

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 53–59 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
