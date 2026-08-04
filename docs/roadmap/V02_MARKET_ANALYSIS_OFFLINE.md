# V2 — Market Analysis Offline

Identifiant : `V2_MARKET_ANALYSIS`  
Plage canonique : **Lots 21 à 30**  
Composant/domain owner : `MarketAnalysisDomain`  
Mode maximal autorisé : `LOCAL_OFFLINE_ANALYSIS_ONLY`

## Finalité de la version

Faire évoluer le système de **V1 fermée** vers **Contexte 5m/15m explicable, déterministe et non exécutable**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- V1 fermée.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/market_analysis`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 21 — Product Scope Lock & Future Capability Registry

**Statut canonique :** `IMPLEMENTED_SCOPE_LOCK`  
**Runtime/mode autorisé :** `LOCAL_OFFLINE_ANALYSIS_ONLY`  
**Composant propriétaire :** `MarketAnalysisDomain`  
**Frontière de code :** `src/crypto_quant_bot/market_analysis`

### Objectif et responsabilité exacte

Figer le scope produit futur, les phases, les capabilities et les gates d’activation.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ProductScopeLockFutureCapabilityRegistryStateV1
- ProductScopeLockFutureCapabilityRegistryAuditV1
- ProductScopeLockFutureCapabilityRegistryContractRegistryV1
- ProductScopeLockFutureCapabilityRegistryCapabilityMatrixV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 21, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Product Scope Lock & Future Capability Registry » dans le composant MarketAnalysisDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/market_analysis/product_scope_lock_and_future_capability_registry.py
- src/crypto_quant_bot/market_analysis/product_scope_lock_and_future_capability_registry_models.py
- scripts/run_lot21_product_scope_lock_and_future_capability_registry.py
- scripts/validate_lot21.py
- tests/test_lot21_product_scope_lock_and_future_capability_registry.py
- data/audit/product_scope_lock_and_future_capability_registry_lot21.json
- reports/lot_21_product_scope_lock_and_future_capability_registry_report.md
- docs/LOT_21_PRODUCT_SCOPE_LOCK_AND_FUTURE_CAPABILITY_REGISTRY.md
- docs/ACCEPTANCE_CRITERIA_LOT_21.md
- reports/lot_21_validation_report.md

### Observabilité minimale

- lot_21_records_processed_total
- lot_21_validation_failures_total
- lot_21_processing_latency_ms

### Tests et critères d’acceptation

- Toutes les plages de lots sont couvertes sans collision
- Chaque capability a dépendances et gate
- Archive V1 inchangée
- Aucune capacité future activée
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

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 22 — Market Analysis Foundation

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `LOCAL_OFFLINE_ANALYSIS_ONLY`  
**Composant propriétaire :** `MarketAnalysisDomain`  
**Frontière de code :** `src/crypto_quant_bot/market_analysis`

### Objectif et responsabilité exacte

Créer le socle d’analyse de marché V2 sur données 5m/15m.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- MarketAnalysisFoundationStateV1
- MarketAnalysisFoundationAuditV1
- MarketAnalysisFoundationContractRegistryV1
- MarketAnalysisFoundationCapabilityMatrixV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 22, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Market Analysis Foundation » dans le composant MarketAnalysisDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/market_analysis/market_analysis_foundation.py
- src/crypto_quant_bot/market_analysis/market_analysis_foundation_models.py
- scripts/run_lot22_market_analysis_foundation.py
- scripts/validate_lot22.py
- tests/test_lot22_market_analysis_foundation.py
- data/audit/market_analysis_foundation_lot22.json
- reports/lot_22_market_analysis_foundation_report.md
- docs/LOT_22_MARKET_ANALYSIS_FOUNDATION.md
- docs/ACCEPTANCE_CRITERIA_LOT_22.md
- reports/lot_22_validation_report.md

### Observabilité minimale

- lot_22_records_processed_total
- lot_22_validation_failures_total
- lot_22_processing_latency_ms

### Tests et critères d’acceptation

- Scores bornés et déterministes
- Aucun signal, ordre, cible ou label futur
- Replay run1/run2 identique
- Invariants V1 préservés
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
- analysis_only=true
- used_for_decision=false
- order_routing_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 23 — Technical Indicators Pack

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `LOCAL_OFFLINE_ANALYSIS_ONLY`  
**Composant propriétaire :** `MarketAnalysisDomain`  
**Frontière de code :** `src/crypto_quant_bot/market_analysis`

### Objectif et responsabilité exacte

Calculer un pack cohérent d’indicateurs numériques par timeframe.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- TechnicalIndicatorsPackStateV1
- TechnicalIndicatorsPackAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 23, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Technical Indicators Pack » dans le composant MarketAnalysisDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/market_analysis/technical_indicators_pack.py
- src/crypto_quant_bot/market_analysis/technical_indicators_pack_models.py
- scripts/run_lot23_technical_indicators_pack.py
- scripts/validate_lot23.py
- tests/test_lot23_technical_indicators_pack.py
- data/audit/technical_indicators_pack_lot23.json
- reports/lot_23_technical_indicators_pack_report.md
- docs/LOT_23_TECHNICAL_INDICATORS_PACK.md
- docs/ACCEPTANCE_CRITERIA_LOT_23.md
- reports/lot_23_validation_report.md

### Observabilité minimale

- lot_23_records_processed_total
- lot_23_validation_failures_total
- lot_23_processing_latency_ms

### Tests et critères d’acceptation

- Scores bornés et déterministes
- Aucun signal, ordre, cible ou label futur
- Replay run1/run2 identique
- Invariants V1 préservés
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
- analysis_only=true
- used_for_decision=false
- order_routing_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 24 — Trend / Range / Momentum Engine

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `LOCAL_OFFLINE_ANALYSIS_ONLY`  
**Composant propriétaire :** `MarketAnalysisDomain`  
**Frontière de code :** `src/crypto_quant_bot/market_analysis`

### Objectif et responsabilité exacte

Interpréter tendance, range et momentum de façon descriptive.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- TrendRangeMomentumEngineStateV1
- TrendRangeMomentumEngineAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 24, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Trend / Range / Momentum Engine » dans le composant MarketAnalysisDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/market_analysis/trend_range_momentum_engine.py
- src/crypto_quant_bot/market_analysis/trend_range_momentum_engine_models.py
- scripts/run_lot24_trend_range_momentum_engine.py
- scripts/validate_lot24.py
- tests/test_lot24_trend_range_momentum_engine.py
- data/audit/trend_range_momentum_engine_lot24.json
- reports/lot_24_trend_range_momentum_engine_report.md
- docs/LOT_24_TREND_RANGE_MOMENTUM_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_24.md
- reports/lot_24_validation_report.md

### Observabilité minimale

- lot_24_records_processed_total
- lot_24_validation_failures_total
- lot_24_processing_latency_ms

### Tests et critères d’acceptation

- Scores bornés et déterministes
- Aucun signal, ordre, cible ou label futur
- Replay run1/run2 identique
- Invariants V1 préservés
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
- analysis_only=true
- used_for_decision=false
- order_routing_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 25 — Volatility / Regime / Confluence Engine

**Statut canonique :** `IMPLEMENTED_VALIDATED`  
**Runtime/mode autorisé :** `LOCAL_OFFLINE_ANALYSIS_ONLY`  
**Composant propriétaire :** `MarketAnalysisDomain`  
**Frontière de code :** `src/crypto_quant_bot/market_analysis`

### Objectif et responsabilité exacte

Fusionner volatilité, régime et confluence sans sortie exécutable.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- VolatilityRegimeConfluenceEngineStateV1
- VolatilityRegimeConfluenceEngineAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 25, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Volatility / Regime / Confluence Engine » dans le composant MarketAnalysisDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/market_analysis/volatility_regime_confluence_engine.py
- src/crypto_quant_bot/market_analysis/volatility_regime_confluence_engine_models.py
- scripts/run_lot25_volatility_regime_confluence_engine.py
- scripts/validate_lot25.py
- tests/test_lot25_volatility_regime_confluence_engine.py
- data/audit/volatility_regime_confluence_engine_lot25.json
- reports/lot_25_volatility_regime_confluence_engine_report.md
- docs/LOT_25_VOLATILITY_REGIME_CONFLUENCE_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_25.md
- reports/lot_25_validation_report.md

### Observabilité minimale

- lot_25_records_processed_total
- lot_25_validation_failures_total
- lot_25_processing_latency_ms

### Tests et critères d’acceptation

- Scores bornés et déterministes
- Aucun signal, ordre, cible ou label futur
- Replay run1/run2 identique
- Invariants V1 préservés
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
- analysis_only=true
- used_for_decision=false
- order_routing_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 26 — Multi-Timeframe Alignment Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LOCAL_OFFLINE_ANALYSIS_ONLY`  
**Composant propriétaire :** `MarketAnalysisDomain`  
**Frontière de code :** `src/crypto_quant_bot/market_analysis`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Multi-Timeframe Alignment Engine » dans Market Analysis Offline, produire MultiTimeframeAlignmentEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- MarketAnalysisStateV1 5m
- MarketAnalysisStateV1 15m
- ClosedBarAvailabilityV1

### Contrats de sortie

- MultiTimeframeAlignmentEngineStateV1
- MultiTimeframeAlignmentEngineAuditV1
- MultiTimeframeAlignmentStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 26, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Multi-Timeframe Alignment Engine » dans le composant MarketAnalysisDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Joindre chaque état 5m uniquement au dernier état 15m dont available_at <= decision_time (as-of backward join).
6. Calculer alignment_state, divergence_state, coherence_state et les accords trend/regime/volatility/confluence.
7. Conserver séparément le contexte local 5m et le contexte supérieur 15m ; le 15m ne veto pas automatiquement une structure 5m.
8. Produire overall_agreement_score borné, component_scores et reason_codes sans direction BUY/SELL.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Bougie 15m non clôturée ou future → exclue.
- Écart de calendrier/timezone → BLOCKED_TIME_ALIGNMENT.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/market_analysis/multi_timeframe_alignment_engine.py
- src/crypto_quant_bot/market_analysis/multi_timeframe_alignment_engine_models.py
- scripts/run_lot26_multi_timeframe_alignment_engine.py
- scripts/validate_lot26.py
- tests/test_lot26_multi_timeframe_alignment_engine.py
- data/audit/multi_timeframe_alignment_engine_lot26.json
- reports/lot_26_multi_timeframe_alignment_engine_report.md
- docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_26.md

### Observabilité minimale

- lot_26_records_processed_total
- lot_26_validation_failures_total
- lot_26_processing_latency_ms
- mtf_alignment_score
- mtf_divergence_count_total

### Tests et critères d’acceptation

- Scores bornés et déterministes
- Aucun signal, ordre, cible ou label futur
- Replay run1/run2 identique
- Invariants V1 préservés
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Fixture où la dernière 15m ouverte est ignorée.
- Fixture divergence 5m/15m attendue sans veto automatique.

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
- analysis_only=true
- used_for_decision=false
- order_routing_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 27 — Global Market Context Aggregator

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LOCAL_OFFLINE_ANALYSIS_ONLY`  
**Composant propriétaire :** `MarketAnalysisDomain`  
**Frontière de code :** `src/crypto_quant_bot/market_analysis`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Global Market Context Aggregator » dans Market Analysis Offline, produire GlobalMarketContextAggregatorStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- GlobalMarketContextAggregatorStateV1
- GlobalMarketContextAggregatorAuditV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 27, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Global Market Context Aggregator » dans le composant MarketAnalysisDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Agrégater uniquement des composants validés et publier les poids/configs effectivement utilisés.
6. Conserver contribution, qualité et fraîcheur de chaque source ; une source manquante n’est jamais renormalisée silencieusement.
7. Produire état dominant, alternatives, conflits et confidence_interval lorsque disponible.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Composants contradictoires sans règle de résolution → CONTEXT_MIXED/UNKNOWN.
- Poids ou config non approuvé → BLOCKED_CONFIG.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/market_analysis/global_market_context_aggregator.py
- src/crypto_quant_bot/market_analysis/global_market_context_aggregator_models.py
- scripts/run_lot27_global_market_context_aggregator.py
- scripts/validate_lot27.py
- tests/test_lot27_global_market_context_aggregator.py
- data/audit/global_market_context_aggregator_lot27.json
- reports/lot_27_global_market_context_aggregator_report.md
- docs/LOT_27_GLOBAL_MARKET_CONTEXT_AGGREGATOR.md
- docs/ACCEPTANCE_CRITERIA_LOT_27.md

### Observabilité minimale

- lot_27_records_processed_total
- lot_27_validation_failures_total
- lot_27_processing_latency_ms

### Tests et critères d’acceptation

- Scores bornés et déterministes
- Aucun signal, ordre, cible ou label futur
- Replay run1/run2 identique
- Invariants V1 préservés
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test d’ablation de chaque composant.
- Test de source manquante sans changement silencieux de sens.

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
- analysis_only=true
- used_for_decision=false
- order_routing_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 28 — Explanation Core & Why-Not-Trade Layer

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LOCAL_OFFLINE_ANALYSIS_ONLY`  
**Composant propriétaire :** `MarketAnalysisDomain`  
**Frontière de code :** `src/crypto_quant_bot/market_analysis`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Explanation Core & Why-Not-Trade Layer » dans Market Analysis Offline, produire ExplanationCoreWhyNotTradeLayerStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ExplanationCoreWhyNotTradeLayerStateV1
- ExplanationCoreWhyNotTradeLayerAuditV1
- ExplanationBundleV1
- WhyNotTradeReasonSetV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 28, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Explanation Core & Why-Not-Trade Layer » dans le composant MarketAnalysisDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Transformer états et veto en reason_codes déterministes via templates versionnés.
6. Distinguer facts, inferences, uncertainties et non-applicable.
7. Expliquer pourquoi une action est impossible sans inventer de causalité ni recommander un ordre.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Reason code sans preuve source → rejet.
- Texte divergent du state machine → validation FAIL.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/market_analysis/explanation_core_and_why_not_trade_layer.py
- src/crypto_quant_bot/market_analysis/explanation_core_and_why_not_trade_layer_models.py
- scripts/run_lot28_explanation_core_and_why_not_trade_layer.py
- scripts/validate_lot28.py
- tests/test_lot28_explanation_core_and_why_not_trade_layer.py
- data/audit/explanation_core_and_why_not_trade_layer_lot28.json
- reports/lot_28_explanation_core_and_why_not_trade_layer_report.md
- docs/LOT_28_EXPLANATION_CORE_AND_WHY_NOT_TRADE_LAYER.md
- docs/ACCEPTANCE_CRITERIA_LOT_28.md

### Observabilité minimale

- lot_28_records_processed_total
- lot_28_validation_failures_total
- lot_28_processing_latency_ms

### Tests et critères d’acceptation

- Scores bornés et déterministes
- Aucun signal, ordre, cible ou label futur
- Replay run1/run2 identique
- Invariants V1 préservés
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Golden tests des explications.
- Test qu’aucun token BUY/SELL/position_size n’est produit par la couche descriptive.

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
- analysis_only=true
- used_for_decision=false
- order_routing_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 29 — V2 Deterministic Replay & Audit

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LOCAL_OFFLINE_ANALYSIS_ONLY`  
**Composant propriétaire :** `MarketAnalysisDomain`  
**Frontière de code :** `src/crypto_quant_bot/market_analysis`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « V2 Deterministic Replay & Audit » dans Market Analysis Offline, produire V2DeterministicReplayAuditStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- V2DeterministicReplayAuditStateV1
- V2DeterministicReplayAuditAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 29, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « V2 Deterministic Replay & Audit » dans le composant MarketAnalysisDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.

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

- src/crypto_quant_bot/market_analysis/v2_deterministic_replay_and_audit.py
- src/crypto_quant_bot/market_analysis/v2_deterministic_replay_and_audit_models.py
- scripts/run_lot29_v2_deterministic_replay_and_audit.py
- scripts/validate_lot29.py
- tests/test_lot29_v2_deterministic_replay_and_audit.py
- data/audit/v2_deterministic_replay_and_audit_lot29.json
- reports/lot_29_v2_deterministic_replay_and_audit_report.md
- docs/LOT_29_V2_DETERMINISTIC_REPLAY_AND_AUDIT.md
- docs/ACCEPTANCE_CRITERIA_LOT_29.md

### Observabilité minimale

- lot_29_records_processed_total
- lot_29_validation_failures_total
- lot_29_processing_latency_ms

### Tests et critères d’acceptation

- Scores bornés et déterministes
- Aucun signal, ordre, cible ou label futur
- Replay run1/run2 identique
- Invariants V1 préservés
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

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- analysis_only=true
- used_for_decision=false
- order_routing_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 30 — V2 Market Analysis Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `LOCAL_OFFLINE_ANALYSIS_ONLY`  
**Composant propriétaire :** `MarketAnalysisDomain`  
**Frontière de code :** `src/crypto_quant_bot/market_analysis`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « V2 Market Analysis Closure » dans Market Analysis Offline, produire V2MarketAnalysisClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- V2MarketAnalysisClosureStateV1
- V2MarketAnalysisClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 30, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « V2 Market Analysis Closure » dans le composant MarketAnalysisDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.

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

- scripts/validate_all_until_lot30.py
- scripts/run_required_chain_until_lot30.sh
- scripts/diagnose_exact_chain_until_lot30.py
- tests/test_lot30_closure_contract.py
- data/audit/closure_manifest_lot30.json
- reports/lot_30_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_30.md
- src/crypto_quant_bot/market_analysis/v2_market_analysis_closure.py
- src/crypto_quant_bot/market_analysis/v2_market_analysis_closure_models.py
- scripts/run_lot30_v2_market_analysis_closure.py
- scripts/validate_lot30.py
- tests/test_lot30_v2_market_analysis_closure.py
- data/audit/v2_market_analysis_closure_lot30.json
- reports/lot_30_v2_market_analysis_closure_report.md
- docs/LOT_30_V2_MARKET_ANALYSIS_CLOSURE.md

### Observabilité minimale

- lot_30_records_processed_total
- lot_30_validation_failures_total
- lot_30_processing_latency_ms

### Tests et critères d’acceptation

- Scores bornés et déterministes
- Aucun signal, ordre, cible ou label futur
- Replay run1/run2 identique
- Invariants V1 préservés
- Tous les lots de la version sont couverts et leurs gates satisfaits
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

### Invariants de sécurité

- schema_version, event_time, generated_at, lineage_id et validation_state sont explicites.
- Toute erreur de contrat, donnée inconnue ou état non réconcilié est fail-closed.
- Aucun secret réel ne figure dans le code, les fixtures, les rapports ou les artefacts.
- Les écritures d’artefacts sont atomiques ; un fichier partiel n’est jamais accepté.
- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- analysis_only=true
- used_for_decision=false
- order_routing_allowed=false

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 21–30 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
