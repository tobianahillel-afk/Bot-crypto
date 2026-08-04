# V7 — Model Risk / Sizing / Risk

Identifiant : `V7_MODEL_RISK_SIZING`  
Plage canonique : **Lots 72 à 80**  
Composant/domain owner : `RiskDomain`  
Mode maximal autorisé : `RISK_SIMULATION_ONLY`

## Finalité de la version

Faire évoluer le système de **V6 backtest gate** vers **Risk approval et sizing borné disponibles**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- V6 backtest gate.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/risk`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 72 — Model Inventory, Model Cards & Assumption Registry

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RISK_SIMULATION_ONLY`  
**Composant propriétaire :** `RiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Model Inventory, Model Cards & Assumption Registry » dans Model Risk / Sizing / Risk, produire ModelInventoryModelCardsAssumptionRegistryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ModelInventoryModelCardsAssumptionRegistryStateV1
- ModelInventoryModelCardsAssumptionRegistryAuditV1
- ModelCardV1
- ModelInventoryV1
- AssumptionRegistryV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 72, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Model Inventory, Model Cards & Assumption Registry » dans le composant RiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Documenter owner, purpose, data, features, algorithm, calibration, limitations, monitoring et forbidden uses.
6. Versionner assumptions et dépendances.
7. Interdire consommation d’un modèle sans status APPROVED_FOR_MODE.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/risk/model_inventory_model_cards_and_assumption_registry.py
- src/crypto_quant_bot/risk/model_inventory_model_cards_and_assumption_registry_models.py
- scripts/run_lot72_model_inventory_model_cards_and_assumption_registry.py
- scripts/validate_lot72.py
- tests/test_lot72_model_inventory_model_cards_and_assumption_registry.py
- data/audit/model_inventory_model_cards_and_assumption_registry_lot72.json
- reports/lot_72_model_inventory_model_cards_and_assumption_registry_report.md
- docs/LOT_72_MODEL_INVENTORY_MODEL_CARDS_AND_ASSUMPTION_REGISTRY.md
- docs/ACCEPTANCE_CRITERIA_LOT_72.md

### Observabilité minimale

- lot_72_records_processed_total
- lot_72_validation_failures_total
- lot_72_processing_latency_ms

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Model card incomplète rejetée.
- Mode runtime non autorisé bloque le modèle.

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
- No position without risk approval
- Default sizing=0

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 73 — Model Risk, Drift & Performance Decay

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RISK_SIMULATION_ONLY`  
**Composant propriétaire :** `RiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Model Risk, Drift & Performance Decay » dans Model Risk / Sizing / Risk, produire ModelRiskDriftPerformanceDecayStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ModelRiskDriftPerformanceDecayStateV1
- ModelRiskDriftPerformanceDecayAuditV1
- StrategyHealthStateV1
- RetirementDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 73, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Model Risk, Drift & Performance Decay » dans le composant RiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Comparer performance récente aux distributions backtest/paper approuvées.
6. Mesurer feature drift, prediction drift, calibration drift et cost drift.
7. Déclencher REVIEW, DE_RISK, PAUSE ou RETIRE selon politique ; jamais auto-scale-up.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/risk/model_risk_drift_and_performance_decay.py
- src/crypto_quant_bot/risk/model_risk_drift_and_performance_decay_models.py
- scripts/run_lot73_model_risk_drift_and_performance_decay.py
- scripts/validate_lot73.py
- tests/test_lot73_model_risk_drift_and_performance_decay.py
- data/audit/model_risk_drift_and_performance_decay_lot73.json
- reports/lot_73_model_risk_drift_and_performance_decay_report.md
- docs/LOT_73_MODEL_RISK_DRIFT_AND_PERFORMANCE_DECAY.md
- docs/ACCEPTANCE_CRITERIA_LOT_73.md

### Observabilité minimale

- lot_73_records_processed_total
- lot_73_validation_failures_total
- lot_73_processing_latency_ms

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
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
- No position without risk approval
- Default sizing=0

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 74 — Risk Limits Framework

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RISK_SIMULATION_ONLY`  
**Composant propriétaire :** `RiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Risk Limits Framework » dans Model Risk / Sizing / Risk, produire RiskLimitsFrameworkStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- RiskLimitsFrameworkStateV1
- RiskLimitsFrameworkAuditV1
- RiskLimitSetV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 74, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Risk Limits Framework » dans le composant RiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir limites hiérarchiques global/account/strategy/instrument/order/time-window.
6. Résoudre la limite effective comme la plus restrictive.
7. Versionner hard vs soft limits et action WAIT/BLOCK/PAUSE/KILL_SWITCH.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/risk/risk_limits_framework.py
- src/crypto_quant_bot/risk/risk_limits_framework_models.py
- scripts/run_lot74_risk_limits_framework.py
- scripts/validate_lot74.py
- tests/test_lot74_risk_limits_framework.py
- data/audit/risk_limits_framework_lot74.json
- reports/lot_74_risk_limits_framework_report.md
- docs/LOT_74_RISK_LIMITS_FRAMEWORK.md
- docs/ACCEPTANCE_CRITERIA_LOT_74.md

### Observabilité minimale

- lot_74_records_processed_total
- lot_74_validation_failures_total
- lot_74_processing_latency_ms

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Conflit de limites résolu par la plus restrictive.
- Unknown limit → zero exposure.

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
- No position without risk approval
- Default sizing=0

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 75 — Volatility- and Confidence-Adjusted Sizing

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RISK_SIMULATION_ONLY`  
**Composant propriétaire :** `RiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Volatility- and Confidence-Adjusted Sizing » dans Model Risk / Sizing / Risk, produire VolatilityAndConfidenceAdjustedSizingStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- VolatilityAndConfidenceAdjustedSizingStateV1
- VolatilityAndConfidenceAdjustedSizingAuditV1
- SizingDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 75, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Volatility- and Confidence-Adjusted Sizing » dans le composant RiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Commencer à size=0 puis appliquer budget de risque, volatilité, confidence calibrée, liquidité, slippage, capacity et portfolio heat.
6. Arrondir via InstrumentSpecification puis revalider min/max/notional.
7. Produire requested_size, approved_size, binding_constraints et reason_codes.
8. Aucun Kelly brut ou levier implicite.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/risk/volatility_and_confidence_adjusted_sizing.py
- src/crypto_quant_bot/risk/volatility_and_confidence_adjusted_sizing_models.py
- scripts/run_lot75_volatility_and_confidence_adjusted_sizing.py
- scripts/validate_lot75.py
- tests/test_lot75_volatility_and_confidence_adjusted_sizing.py
- data/audit/volatility_and_confidence_adjusted_sizing_lot75.json
- reports/lot_75_volatility_and_confidence_adjusted_sizing_report.md
- docs/LOT_75_VOLATILITY_AND_CONFIDENCE_ADJUSTED_SIZING.md
- docs/ACCEPTANCE_CRITERIA_LOT_75.md

### Observabilité minimale

- lot_75_records_processed_total
- lot_75_validation_failures_total
- lot_75_processing_latency_ms

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Chaque veto force approved_size=0.
- Sizing monotone sous réduction du risk budget.

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
- No position without risk approval
- Default sizing=0

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 76 — Liquidity- and Slippage-Adjusted Sizing

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RISK_SIMULATION_ONLY`  
**Composant propriétaire :** `RiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Liquidity- and Slippage-Adjusted Sizing » dans Model Risk / Sizing / Risk, produire LiquidityAndSlippageAdjustedSizingStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- LiquidityAndSlippageAdjustedSizingStateV1
- LiquidityAndSlippageAdjustedSizingAuditV1
- SlippageImpactEstimateV1
- SizingDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 76, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Liquidity- and Slippage-Adjusted Sizing » dans le composant RiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Estimer slippage depuis spread, depth, participation, volatility et latency.
6. Séparer temporary impact, permanent proxy et adverse movement.
7. Calibrer par buckets instrument/régime/taille ; publier intervalle et fallback.
8. Commencer à size=0 puis appliquer budget de risque, volatilité, confidence calibrée, liquidité, slippage, capacity et portfolio heat.
9. Arrondir via InstrumentSpecification puis revalider min/max/notional.
10. Produire requested_size, approved_size, binding_constraints et reason_codes.
11. Aucun Kelly brut ou levier implicite.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/risk/liquidity_and_slippage_adjusted_sizing.py
- src/crypto_quant_bot/risk/liquidity_and_slippage_adjusted_sizing_models.py
- scripts/run_lot76_liquidity_and_slippage_adjusted_sizing.py
- scripts/validate_lot76.py
- tests/test_lot76_liquidity_and_slippage_adjusted_sizing.py
- data/audit/liquidity_and_slippage_adjusted_sizing_lot76.json
- reports/lot_76_liquidity_and_slippage_adjusted_sizing_report.md
- docs/LOT_76_LIQUIDITY_AND_SLIPPAGE_ADJUSTED_SIZING.md
- docs/ACCEPTANCE_CRITERIA_LOT_76.md

### Observabilité minimale

- lot_76_records_processed_total
- lot_76_validation_failures_total
- lot_76_processing_latency_ms

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Slippage monotone avec taille.
- Book insuffisant → no-fill/partial-fill, pas prix inventé.
- Chaque veto force approved_size=0.
- Sizing monotone sous réduction du risk budget.

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
- No position without risk approval
- Default sizing=0

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 77 — Drawdown De-Risking, Tail Risk & Risk of Ruin

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RISK_SIMULATION_ONLY`  
**Composant propriétaire :** `RiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Drawdown De-Risking, Tail Risk & Risk of Ruin » dans Model Risk / Sizing / Risk, produire DrawdownDeRiskingTailRiskRiskOfRuinStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- DrawdownDeRiskingTailRiskRiskOfRuinStateV1
- DrawdownDeRiskingTailRiskRiskOfRuinAuditV1
- DrawdownRiskStateV1
- DeRiskingDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 77, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Drawdown De-Risking, Tail Risk & Risk of Ruin » dans le composant RiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Mesurer drawdown peak-to-trough par stratégie/portfolio.
6. Appliquer paliers de de-risking versionnés.
7. Estimer tail loss et risk-of-ruin sous stress.
8. Réactivation après drawdown exige gate humaine.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/risk/drawdown_de_risking_tail_risk_and_risk_of_ruin.py
- src/crypto_quant_bot/risk/drawdown_de_risking_tail_risk_and_risk_of_ruin_models.py
- scripts/run_lot77_drawdown_de_risking_tail_risk_and_risk_of_ruin.py
- scripts/validate_lot77.py
- tests/test_lot77_drawdown_de_risking_tail_risk_and_risk_of_ruin.py
- data/audit/drawdown_de_risking_tail_risk_and_risk_of_ruin_lot77.json
- reports/lot_77_drawdown_de_risking_tail_risk_and_risk_of_ruin_report.md
- docs/LOT_77_DRAWDOWN_DE_RISKING_TAIL_RISK_AND_RISK_OF_RUIN.md
- docs/ACCEPTANCE_CRITERIA_LOT_77.md

### Observabilité minimale

- lot_77_records_processed_total
- lot_77_validation_failures_total
- lot_77_processing_latency_ms

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Paliers exacts aux frontières.
- Emergency threshold déclenche pause/kill.

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
- No position without risk approval
- Default sizing=0

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 78 — Correlation, Concentration & Portfolio Pre-Checks

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RISK_SIMULATION_ONLY`  
**Composant propriétaire :** `RiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Correlation, Concentration & Portfolio Pre-Checks » dans Model Risk / Sizing / Risk, produire CorrelationConcentrationPortfolioPreChecksStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- CorrelationConcentrationPortfolioPreChecksStateV1
- CorrelationConcentrationPortfolioPreChecksAuditV1
- PortfolioRiskStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 78, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Correlation, Concentration & Portfolio Pre-Checks » dans le composant RiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Calculer exposures net/gross, factor/asset correlation, concentration et aggregate risk budget.
6. Utiliser fenêtres et méthodes robustes versionnées.
7. Appliquer pre-trade incremental risk check.
8. Unknown correlation en période courte utilise conservative cap.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/risk/correlation_concentration_and_portfolio_pre_checks.py
- src/crypto_quant_bot/risk/correlation_concentration_and_portfolio_pre_checks_models.py
- scripts/run_lot78_correlation_concentration_and_portfolio_pre_checks.py
- scripts/validate_lot78.py
- tests/test_lot78_correlation_concentration_and_portfolio_pre_checks.py
- data/audit/correlation_concentration_and_portfolio_pre_checks_lot78.json
- reports/lot_78_correlation_concentration_and_portfolio_pre_checks_report.md
- docs/LOT_78_CORRELATION_CONCENTRATION_AND_PORTFOLIO_PRE_CHECKS.md
- docs/ACCEPTANCE_CRITERIA_LOT_78.md

### Observabilité minimale

- lot_78_records_processed_total
- lot_78_validation_failures_total
- lot_78_processing_latency_ms

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Nouvelle position augmente heat attendue.
- Corrélation manquante réduit la capacité.

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
- No position without risk approval
- Default sizing=0

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 79 — Risk Approval Gate & Kill-Switch Policy

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RISK_SIMULATION_ONLY`  
**Composant propriétaire :** `RiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Risk Approval Gate & Kill-Switch Policy » dans Model Risk / Sizing / Risk, produire RiskApprovalGateKillSwitchPolicyStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- RiskApprovalGateKillSwitchPolicyStateV1
- RiskApprovalGateKillSwitchPolicyAuditV1
- RiskDecisionV1
- KillSwitchStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 79, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Risk Approval Gate & Kill-Switch Policy » dans le composant RiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Évaluer data, model, strategy, portfolio, exchange, execution et security vetos.
6. Résoudre action finale par priorité KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE.
7. Signer decision_hash sur intent+limits+state ids.
8. Approval expire et n’est valide que pour l’intent exact.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/risk/risk_approval_gate_and_kill_switch_policy.py
- src/crypto_quant_bot/risk/risk_approval_gate_and_kill_switch_policy_models.py
- scripts/run_lot79_risk_approval_gate_and_kill_switch_policy.py
- scripts/validate_lot79.py
- tests/test_lot79_risk_approval_gate_and_kill_switch_policy.py
- data/audit/risk_approval_gate_and_kill_switch_policy_lot79.json
- reports/lot_79_risk_approval_gate_and_kill_switch_policy_report.md
- docs/LOT_79_RISK_APPROVAL_GATE_AND_KILL_SWITCH_POLICY.md
- docs/ACCEPTANCE_CRITERIA_LOT_79.md

### Observabilité minimale

- lot_79_records_processed_total
- lot_79_validation_failures_total
- lot_79_processing_latency_ms

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Bypass impossible.
- Toute mutation intent invalide decision_hash.
- Kill switch bloque tous les nouveaux intents immédiatement.

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
- No position without risk approval
- Default sizing=0

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 80 — V7 Model Risk / Sizing Audit & Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `RISK_SIMULATION_ONLY`  
**Composant propriétaire :** `RiskDomain`  
**Frontière de code :** `src/crypto_quant_bot/risk`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « V7 Model Risk / Sizing Audit & Closure » dans Model Risk / Sizing / Risk, produire V7ModelRiskSizingAuditClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- V7ModelRiskSizingAuditClosureStateV1
- V7ModelRiskSizingAuditClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- SizingDecisionV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 80, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « V7 Model Risk / Sizing Audit & Closure » dans le composant RiskDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Commencer à size=0 puis appliquer budget de risque, volatilité, confidence calibrée, liquidité, slippage, capacity et portfolio heat.
10. Arrondir via InstrumentSpecification puis revalider min/max/notional.
11. Produire requested_size, approved_size, binding_constraints et reason_codes.
12. Aucun Kelly brut ou levier implicite.

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

- scripts/validate_all_until_lot80.py
- scripts/run_required_chain_until_lot80.sh
- scripts/diagnose_exact_chain_until_lot80.py
- tests/test_lot80_closure_contract.py
- data/audit/closure_manifest_lot80.json
- reports/lot_80_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_80.md
- src/crypto_quant_bot/risk/v7_model_risk_sizing_audit_and_closure.py
- src/crypto_quant_bot/risk/v7_model_risk_sizing_audit_and_closure_models.py
- scripts/run_lot80_v7_model_risk_sizing_audit_and_closure.py
- scripts/validate_lot80.py
- tests/test_lot80_v7_model_risk_sizing_audit_and_closure.py
- data/audit/v7_model_risk_sizing_audit_and_closure_lot80.json
- reports/lot_80_v7_model_risk_sizing_audit_and_closure_report.md
- docs/LOT_80_V7_MODEL_RISK_SIZING_AUDIT_AND_CLOSURE.md

### Observabilité minimale

- lot_80_records_processed_total
- lot_80_validation_failures_total
- lot_80_processing_latency_ms

### Tests et critères d’acceptation

- Sizing à zéro en cas de veto
- Limites jamais dépassées
- Drift synthétique détecté
- Kill switch bloque tous les intents
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Chaque veto force approved_size=0.
- Sizing monotone sous réduction du risk budget.

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
- No position without risk approval
- Default sizing=0

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 72–80 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
