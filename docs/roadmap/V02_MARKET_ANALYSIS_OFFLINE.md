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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/product_scope_capabilities_lot21.jsonl`
- `data/audit/product_scope_lot21.json`
- `data/audit/product_scope_roadmap_lot21.jsonl`
- `docs/ACCEPTANCE_CRITERIA_LOT_21.md`
- `docs/LOT_21_PRODUCT_SCOPE.md`
- `reports/lot_21_product_scope_report.md`
- `reports/lot_21_v1_archive_freeze_report.md`
- `reports/lot_21_validation_report.md`
- `scripts/__pycache__/diagnose_exact_chain_until_lot21.cpython-313.pyc`
- `scripts/__pycache__/run_lot21_product_scope.cpython-313.pyc`
- `scripts/__pycache__/validate_all_until_lot21.cpython-313.pyc`
- `scripts/__pycache__/validate_lot21.cpython-313.pyc`
- `scripts/diagnose_exact_chain_until_lot21.py`
- `scripts/diagnose_lot21_required_chain_timing.py`
- `scripts/run_lot21_product_scope.py`
- `scripts/run_required_chain_until_lot21.sh`
- `scripts/validate_all_until_lot21.py`
- `scripts/validate_lot21.py`
- `tests/__pycache__/test_lot21_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot21_functional_capabilities.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot21_no_active_trading.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot21_product_scope_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot21_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot21_roadmap_phases.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot21_v1_archive_freeze.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot21_diagnostics_static.py`
- `tests/test_lot21_functional_capabilities.py`
- `tests/test_lot21_no_active_trading.py`
- `tests/test_lot21_product_scope_outputs.py`
- `tests/test_lot21_required_chain_static.py`
- `tests/test_lot21_roadmap_phases.py`
- `tests/test_lot21_v1_archive_freeze.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/market_analysis_lot22.json`
- `data/audit/market_analysis_timeframes_lot22.jsonl`
- `docs/ACCEPTANCE_CRITERIA_LOT_22.md`
- `docs/ACCEPTANCE_CRITERIA_LOT_22_BIS.md`
- `docs/LOT_22_MARKET_ANALYSIS.md`
- `reports/lot_22_bis_lot16_checksum_stability_report.md`
- `reports/lot_22_market_analysis_report.md`
- `reports/lot_22_validation_report.md`
- `scripts/__pycache__/diagnose_exact_chain_until_lot22.cpython-313.pyc`
- `scripts/__pycache__/diagnose_lot22_required_chain_timing.cpython-313.pyc`
- `scripts/__pycache__/run_lot22_market_analysis.cpython-313.pyc`
- `scripts/__pycache__/validate_all_until_lot22.cpython-313.pyc`
- `scripts/__pycache__/validate_lot22.cpython-313.pyc`
- `scripts/diagnose_exact_chain_until_lot22.py`
- `scripts/diagnose_lot22_required_chain_timing.py`
- `scripts/run_lot22_market_analysis.py`
- `scripts/run_required_chain_until_lot22.sh`
- `scripts/validate_all_until_lot22.py`
- `scripts/validate_lot22.py`
- `tests/__pycache__/test_lot22_archive_freeze_guard.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot22_bis_exact_chain_return_shell_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot22_bis_exact_chain_return_shell_static.cpython-313.pyc`
- `tests/__pycache__/test_lot22_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot22_market_analysis_invariants.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot22_market_analysis_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot22_market_context_labels.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot22_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot22_archive_freeze_guard.py`
- `tests/test_lot22_bis_exact_chain_return_shell_static.py`
- `tests/test_lot22_diagnostics_static.py`
- `tests/test_lot22_market_analysis_invariants.py`
- `tests/test_lot22_market_analysis_outputs.py`
- `tests/test_lot22_market_context_labels.py`
- `tests/test_lot22_required_chain_static.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/technical_indicators_lot23.json`
- `data/audit/technical_indicators_timeframes_lot23.jsonl`
- `docs/ACCEPTANCE_CRITERIA_LOT_23.md`
- `docs/ACCEPTANCE_CRITERIA_LOT_23_BIS.md`
- `docs/ACCEPTANCE_CRITERIA_LOT_23_QUATER.md`
- `docs/ACCEPTANCE_CRITERIA_LOT_23_QUINQUIES.md`
- `docs/ACCEPTANCE_CRITERIA_LOT_23_TER.md`
- `docs/LOT_23_TECHNICAL_INDICATORS.md`
- `reports/lot_23_bis_lot7_jsonl_robustness_report.md`
- `reports/lot_23_quater_lot16_checksum_single_source_report.md`
- `reports/lot_23_quinquies_lot16_after_lot10_diagnostic_report.md`
- `reports/lot_23_technical_indicators_report.md`
- `reports/lot_23_ter_lot10_writer_robustness_report.md`
- `reports/lot_23_validation_report.md`
- `scripts/__pycache__/diagnose_exact_chain_until_lot23.cpython-313.pyc`
- `scripts/__pycache__/diagnose_lot23_required_chain_timing.cpython-313.pyc`
- `scripts/__pycache__/run_lot23_technical_indicators.cpython-313.pyc`
- `scripts/__pycache__/validate_all_until_lot23.cpython-313.pyc`
- `scripts/__pycache__/validate_lot23.cpython-313.pyc`
- `scripts/diagnose_exact_chain_until_lot23.py`
- `scripts/diagnose_lot23_required_chain_timing.py`
- `scripts/run_lot23_technical_indicators.py`
- `scripts/run_required_chain_until_lot23.sh`
- `scripts/validate_all_until_lot23.py`
- `scripts/validate_lot23.py`
- `tests/__pycache__/test_lot23_archive_freeze_guard.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_archive_freeze_guard.cpython-313.pyc`
- `tests/__pycache__/test_lot23_bis_lot7_chain_stability.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_bis_lot7_chain_stability.cpython-313.pyc`
- `tests/__pycache__/test_lot23_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_diagnostics_static.cpython-313.pyc`
- `tests/__pycache__/test_lot23_indicator_states.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_indicator_states.cpython-313.pyc`
- `tests/__pycache__/test_lot23_indicator_values.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_indicator_values.cpython-313.pyc`
- `tests/__pycache__/test_lot23_quater_lot16_return_shell_stability.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_quater_lot16_return_shell_stability.cpython-313.pyc`
- `tests/__pycache__/test_lot23_quinquies_lot16_after_lot10_diagnostic.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_required_chain_static.cpython-313.pyc`
- `tests/__pycache__/test_lot23_technical_indicators_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_technical_indicators_outputs.cpython-313.pyc`
- `tests/__pycache__/test_lot23_ter_lot10_chain_stability.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot23_ter_lot10_chain_stability.cpython-313.pyc`
- `tests/test_lot23_archive_freeze_guard.py`
- `tests/test_lot23_bis_lot7_chain_stability.py`
- `tests/test_lot23_diagnostics_static.py`
- `tests/test_lot23_indicator_states.py`
- `tests/test_lot23_indicator_values.py`
- `tests/test_lot23_quater_lot16_return_shell_stability.py`
- `tests/test_lot23_quinquies_lot16_after_lot10_diagnostic.py`
- `tests/test_lot23_required_chain_static.py`
- `tests/test_lot23_technical_indicators_outputs.py`
- `tests/test_lot23_ter_lot10_chain_stability.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/trend_range_momentum_lot24.json`
- `data/audit/trend_range_momentum_timeframes_lot24.jsonl`
- `docs/ACCEPTANCE_CRITERIA_LOT_24.md`
- `docs/LOT_24_TREND_RANGE_MOMENTUM.md`
- `reports/lot_24_trend_range_momentum_report.md`
- `reports/lot_24_validation_report.md`
- `scripts/__pycache__/diagnose_exact_chain_until_lot24.cpython-313.pyc`
- `scripts/__pycache__/diagnose_lot24_required_chain_timing.cpython-313.pyc`
- `scripts/__pycache__/run_lot24_trend_range_momentum.cpython-313.pyc`
- `scripts/__pycache__/validate_all_until_lot24.cpython-313.pyc`
- `scripts/__pycache__/validate_lot24.cpython-313.pyc`
- `scripts/diagnose_exact_chain_until_lot24.py`
- `scripts/diagnose_lot24_required_chain_timing.py`
- `scripts/run_lot24_trend_range_momentum.py`
- `scripts/run_required_chain_until_lot24.sh`
- `scripts/validate_all_until_lot24.py`
- `scripts/validate_lot24.py`
- `tests/__pycache__/test_lot24_archive_freeze_guard.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot24_context_states.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot24_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot24_no_forbidden_fields.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot24_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot24_trend_range_momentum_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot24_trend_range_momentum_values.cpython-313-pytest-9.0.2.pyc`
- `tests/test_lot24_archive_freeze_guard.py`
- `tests/test_lot24_context_states.py`
- `tests/test_lot24_diagnostics_static.py`
- `tests/test_lot24_no_forbidden_fields.py`
- `tests/test_lot24_required_chain_static.py`
- `tests/test_lot24_trend_range_momentum_outputs.py`
- `tests/test_lot24_trend_range_momentum_values.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

### Preuves historiques et fichiers réels

Ce lot est déjà implémenté. La roadmap ne renomme, ne déplace et ne recrée aucun fichier historique.
Les critères d’acceptation, rapports PASS, artefacts et commit validé sont normatifs ; en cas de divergence, ils prévalent sur cette synthèse.

Fichiers de preuve détectés dans le dépôt :

- `data/audit/volatility_regime_confluence_lot25.json`
- `data/audit/volatility_regime_confluence_timeframes_lot25.jsonl`
- `docs/ACCEPTANCE_CRITERIA_LOT_25.md`
- `docs/LOT_25_VOLATILITY_REGIME_CONFLUENCE.md`
- `reports/lot_25_validation_report.md`
- `reports/lot_25_volatility_regime_confluence_report.md`
- `scripts/__pycache__/diagnose_exact_chain_until_lot25.cpython-313.pyc`
- `scripts/__pycache__/diagnose_lot25_required_chain_timing.cpython-313.pyc`
- `scripts/__pycache__/run_lot25_volatility_regime_confluence.cpython-313.pyc`
- `scripts/__pycache__/validate_all_until_lot25.cpython-313.pyc`
- `scripts/__pycache__/validate_lot25.cpython-313.pyc`
- `scripts/diagnose_exact_chain_until_lot25.py`
- `scripts/diagnose_lot25_required_chain_timing.py`
- `scripts/run_lot25_volatility_regime_confluence.py`
- `scripts/run_required_chain_until_lot25.sh`
- `scripts/validate_all_until_lot25.py`
- `scripts/validate_lot25.py`
- `tests/__pycache__/test_lot25_archive_freeze_guard.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot25_archive_freeze_guard.cpython-313.pyc`
- `tests/__pycache__/test_lot25_context_states.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot25_context_states.cpython-313.pyc`
- `tests/__pycache__/test_lot25_diagnostics_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot25_diagnostics_static.cpython-313.pyc`
- `tests/__pycache__/test_lot25_no_forbidden_fields.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot25_no_forbidden_fields.cpython-313.pyc`
- `tests/__pycache__/test_lot25_required_chain_static.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot25_required_chain_static.cpython-313.pyc`
- `tests/__pycache__/test_lot25_volatility_regime_confluence_outputs.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot25_volatility_regime_confluence_outputs.cpython-313.pyc`
- `tests/__pycache__/test_lot25_volatility_regime_confluence_values.cpython-313-pytest-9.0.2.pyc`
- `tests/__pycache__/test_lot25_volatility_regime_confluence_values.cpython-313.pyc`
- `tests/test_lot25_archive_freeze_guard.py`
- `tests/test_lot25_context_states.py`
- `tests/test_lot25_diagnostics_static.py`
- `tests/test_lot25_no_forbidden_fields.py`
- `tests/test_lot25_required_chain_static.py`
- `tests/test_lot25_volatility_regime_confluence_outputs.py`
- `tests/test_lot25_volatility_regime_confluence_values.py`

Les chemins des modules source sont ceux des critères d’acceptation historiques et du dépôt réel. Aucun chemin synthétique futur n’est normatif pour ce lot.
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

**Statut canonique :** `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`  
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

**Statut canonique :** `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`  
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
