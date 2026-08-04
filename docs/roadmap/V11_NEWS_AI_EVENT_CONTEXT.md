# V11 — News / AI / Event Context

Identifiant : `V11_NEWS_AI_EVENT`  
Plage canonique : **Lots 103 à 110**  
Composant/domain owner : `IntelligenceDomain`  
Mode maximal autorisé : `READ_ONLY_CONTEXT_ONLY`

## Finalité de la version

Faire évoluer le système de **Source registry approuvé** vers **Contexte événementiel audité et subordonné au risque**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Source registry approuvé.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/intelligence`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 103 — News / AI Scope Gate & Source Registry

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY_CONTEXT_ONLY`  
**Composant propriétaire :** `IntelligenceDomain`  
**Frontière de code :** `src/crypto_quant_bot/intelligence`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « News / AI Scope Gate & Source Registry » dans News / AI / Event Context, produire NewsAIScopeGateSourceRegistryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- SourceRegistryV1 produit par V3

### Contrats de sortie

- NewsAIScopeGateSourceRegistryStateV1
- NewsAIScopeGateSourceRegistryAuditV1
- NewsAIScopeGateSourceRegistryContractRegistryV1
- NewsAIScopeGateSourceRegistryCapabilityMatrixV1
- IntelligenceSourcePolicyV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 103, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « News / AI Scope Gate & Source Registry » dans le composant IntelligenceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Définir frontières, responsabilités, dépendances autorisées, modes runtime et API publiques du domaine.
6. Classer chaque capability en REQUIRED, OPTIONAL_RESEARCH, DISABLED ou FORBIDDEN.
7. Enregistrer source_id, provider, venue, endpoint/type, champs, cadence, timezone, licence, auth_mode, retention et criticité.
8. Définir source of truth, sources de secours et politique de révision.
9. Interdire toute source inconnue ou non approuvée dans une décision.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/intelligence/news_ai_scope_gate_and_source_registry.py
- src/crypto_quant_bot/intelligence/news_ai_scope_gate_and_source_registry_models.py
- scripts/run_lot103_news_ai_scope_gate_and_source_registry.py
- scripts/validate_lot103.py
- tests/test_lot103_news_ai_scope_gate_and_source_registry.py
- data/audit/news_ai_scope_gate_and_source_registry_lot103.json
- reports/lot_103_news_ai_scope_gate_and_source_registry_report.md
- docs/LOT_103_NEWS_AI_SCOPE_GATE_AND_SOURCE_REGISTRY.md
- docs/ACCEPTANCE_CRITERIA_LOT_103.md

### Observabilité minimale

- lot_103_records_processed_total
- lot_103_validation_failures_total
- lot_103_processing_latency_ms

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test de dépendances interdites entre domaines.
- Test de couverture : chaque capability a owner, contrat et gate.
- Source inconnue rejetée.
- Révision de source incrémente schema/config version.

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
- news_context cannot increase size alone
- LLM cannot approve trade

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 104 — Economic Calendar & Event Schema

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY_CONTEXT_ONLY`  
**Composant propriétaire :** `IntelligenceDomain`  
**Frontière de code :** `src/crypto_quant_bot/intelligence`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Economic Calendar & Event Schema » dans News / AI / Event Context, produire EconomicCalendarEventSchemaStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- EconomicCalendarEventSchemaStateV1
- EconomicCalendarEventSchemaAuditV1
- EventContextV1
- SourceReliabilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 104, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Economic Calendar & Event Schema » dans le composant IntelligenceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver source_id, published_at, event_at, received_at, revision_id et raw_content_hash.
6. Séparer extraction factuelle, classification, scoring et explanation.
7. Attribuer reliability/coverage et citer les source records.
8. Le contexte peut réduire/bloquer le risque mais jamais augmenter seul size ou créer signal.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/intelligence/economic_calendar_and_event_schema.py
- src/crypto_quant_bot/intelligence/economic_calendar_and_event_schema_models.py
- scripts/run_lot104_economic_calendar_and_event_schema.py
- scripts/validate_lot104.py
- tests/test_lot104_economic_calendar_and_event_schema.py
- data/audit/economic_calendar_and_event_schema_lot104.json
- reports/lot_104_economic_calendar_and_event_schema_report.md
- docs/LOT_104_ECONOMIC_CALENDAR_AND_EVENT_SCHEMA.md
- docs/ACCEPTANCE_CRITERIA_LOT_104.md

### Observabilité minimale

- lot_104_records_processed_total
- lot_104_validation_failures_total
- lot_104_processing_latency_ms

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Article publié après decision_time non visible.
- LLM output sans source reference rejeté.
- Prompt injection ne modifie aucun state exécutable.

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
- news_context cannot increase size alone
- LLM cannot approve trade

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 105 — News Ingestion Read-Only

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY_CONTEXT_ONLY`  
**Composant propriétaire :** `IntelligenceDomain`  
**Frontière de code :** `src/crypto_quant_bot/intelligence`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « News Ingestion Read-Only » dans News / AI / Event Context, produire NewsIngestionReadOnlyStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- NewsIngestionReadOnlyStateV1
- NewsIngestionReadOnlyAuditV1
- EventContextV1
- SourceReliabilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 105, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « News Ingestion Read-Only » dans le composant IntelligenceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver source_id, published_at, event_at, received_at, revision_id et raw_content_hash.
6. Séparer extraction factuelle, classification, scoring et explanation.
7. Attribuer reliability/coverage et citer les source records.
8. Le contexte peut réduire/bloquer le risque mais jamais augmenter seul size ou créer signal.
9. Utiliser uniquement des sources de news/événements enregistrées et des adapters contextuels read-only.
10. Ne produire aucun snapshot de compte, permission audit ou historique exchange appartenant à V13.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/intelligence/news_ingestion_read_only.py
- src/crypto_quant_bot/intelligence/news_ingestion_read_only_models.py
- scripts/run_lot105_news_ingestion_read_only.py
- scripts/validate_lot105.py
- tests/test_lot105_news_ingestion_read_only.py
- data/audit/news_ingestion_read_only_lot105.json
- reports/lot_105_news_ingestion_read_only_report.md
- docs/LOT_105_NEWS_INGESTION_READ_ONLY.md
- docs/ACCEPTANCE_CRITERIA_LOT_105.md

### Observabilité minimale

- lot_105_records_processed_total
- lot_105_validation_failures_total
- lot_105_processing_latency_ms

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Article publié après decision_time non visible.
- LLM output sans source reference rejeté.
- Prompt injection ne modifie aucun state exécutable.
- Aucun ReadOnlyAccountSnapshotV1 ou PermissionAuditV1 produit.
- Aucune dépendance vers les connecteurs compte/exchange de V13.

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
- news_context cannot increase size alone
- LLM cannot approve trade

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 106 — Sentiment & Narrative Engine

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY_CONTEXT_ONLY`  
**Composant propriétaire :** `IntelligenceDomain`  
**Frontière de code :** `src/crypto_quant_bot/intelligence`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Sentiment & Narrative Engine » dans News / AI / Event Context, produire SentimentNarrativeEngineStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SentimentNarrativeEngineStateV1
- SentimentNarrativeEngineAuditV1
- EventContextV1
- SourceReliabilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 106, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Sentiment & Narrative Engine » dans le composant IntelligenceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver source_id, published_at, event_at, received_at, revision_id et raw_content_hash.
6. Séparer extraction factuelle, classification, scoring et explanation.
7. Attribuer reliability/coverage et citer les source records.
8. Le contexte peut réduire/bloquer le risque mais jamais augmenter seul size ou créer signal.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/intelligence/sentiment_and_narrative_engine.py
- src/crypto_quant_bot/intelligence/sentiment_and_narrative_engine_models.py
- scripts/run_lot106_sentiment_and_narrative_engine.py
- scripts/validate_lot106.py
- tests/test_lot106_sentiment_and_narrative_engine.py
- data/audit/sentiment_and_narrative_engine_lot106.json
- reports/lot_106_sentiment_and_narrative_engine_report.md
- docs/LOT_106_SENTIMENT_AND_NARRATIVE_ENGINE.md
- docs/ACCEPTANCE_CRITERIA_LOT_106.md

### Observabilité minimale

- lot_106_records_processed_total
- lot_106_validation_failures_total
- lot_106_processing_latency_ms

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Article publié après decision_time non visible.
- LLM output sans source reference rejeté.
- Prompt injection ne modifie aucun state exécutable.

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
- news_context cannot increase size alone
- LLM cannot approve trade

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 107 — Event Impact & Crypto Event Risk

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY_CONTEXT_ONLY`  
**Composant propriétaire :** `IntelligenceDomain`  
**Frontière de code :** `src/crypto_quant_bot/intelligence`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Event Impact & Crypto Event Risk » dans News / AI / Event Context, produire EventImpactCryptoEventRiskStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- EventImpactCryptoEventRiskStateV1
- EventImpactCryptoEventRiskAuditV1
- EventContextV1
- SourceReliabilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 107, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Event Impact & Crypto Event Risk » dans le composant IntelligenceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver source_id, published_at, event_at, received_at, revision_id et raw_content_hash.
6. Séparer extraction factuelle, classification, scoring et explanation.
7. Attribuer reliability/coverage et citer les source records.
8. Le contexte peut réduire/bloquer le risque mais jamais augmenter seul size ou créer signal.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/intelligence/event_impact_and_crypto_event_risk.py
- src/crypto_quant_bot/intelligence/event_impact_and_crypto_event_risk_models.py
- scripts/run_lot107_event_impact_and_crypto_event_risk.py
- scripts/validate_lot107.py
- tests/test_lot107_event_impact_and_crypto_event_risk.py
- data/audit/event_impact_and_crypto_event_risk_lot107.json
- reports/lot_107_event_impact_and_crypto_event_risk_report.md
- docs/LOT_107_EVENT_IMPACT_AND_CRYPTO_EVENT_RISK.md
- docs/ACCEPTANCE_CRITERIA_LOT_107.md

### Observabilité minimale

- lot_107_records_processed_total
- lot_107_validation_failures_total
- lot_107_processing_latency_ms

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Article publié après decision_time non visible.
- LLM output sans source reference rejeté.
- Prompt injection ne modifie aucun state exécutable.

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
- news_context cannot increase size alone
- LLM cannot approve trade

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 108 — Source Reliability & Hallucination Guard

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY_CONTEXT_ONLY`  
**Composant propriétaire :** `IntelligenceDomain`  
**Frontière de code :** `src/crypto_quant_bot/intelligence`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Source Reliability & Hallucination Guard » dans News / AI / Event Context, produire SourceReliabilityHallucinationGuardStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- SourceReliabilityHallucinationGuardStateV1
- SourceReliabilityHallucinationGuardAuditV1
- EventContextV1
- SourceReliabilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 108, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Source Reliability & Hallucination Guard » dans le composant IntelligenceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Conserver source_id, published_at, event_at, received_at, revision_id et raw_content_hash.
6. Séparer extraction factuelle, classification, scoring et explanation.
7. Attribuer reliability/coverage et citer les source records.
8. Le contexte peut réduire/bloquer le risque mais jamais augmenter seul size ou créer signal.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/intelligence/source_reliability_and_hallucination_guard.py
- src/crypto_quant_bot/intelligence/source_reliability_and_hallucination_guard_models.py
- scripts/run_lot108_source_reliability_and_hallucination_guard.py
- scripts/validate_lot108.py
- tests/test_lot108_source_reliability_and_hallucination_guard.py
- data/audit/source_reliability_and_hallucination_guard_lot108.json
- reports/lot_108_source_reliability_and_hallucination_guard_report.md
- docs/LOT_108_SOURCE_RELIABILITY_AND_HALLUCINATION_GUARD.md
- docs/ACCEPTANCE_CRITERIA_LOT_108.md

### Observabilité minimale

- lot_108_records_processed_total
- lot_108_validation_failures_total
- lot_108_processing_latency_ms

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Article publié après decision_time non visible.
- LLM output sans source reference rejeté.
- Prompt injection ne modifie aucun state exécutable.

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
- news_context cannot increase size alone
- LLM cannot approve trade

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 109 — LLM Explanation & Context Fusion

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY_CONTEXT_ONLY`  
**Composant propriétaire :** `IntelligenceDomain`  
**Frontière de code :** `src/crypto_quant_bot/intelligence`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « LLM Explanation & Context Fusion » dans News / AI / Event Context, produire LLMExplanationContextFusionStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- LLMExplanationContextFusionStateV1
- LLMExplanationContextFusionAuditV1
- ExplanationBundleV1
- WhyNotTradeReasonSetV1
- EventContextV1
- SourceReliabilityStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 109, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « LLM Explanation & Context Fusion » dans le composant IntelligenceDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Agrégater uniquement des composants validés et publier les poids/configs effectivement utilisés.
6. Conserver contribution, qualité et fraîcheur de chaque source ; une source manquante n’est jamais renormalisée silencieusement.
7. Produire état dominant, alternatives, conflits et confidence_interval lorsque disponible.
8. Transformer états et veto en reason_codes déterministes via templates versionnés.
9. Distinguer facts, inferences, uncertainties et non-applicable.
10. Expliquer pourquoi une action est impossible sans inventer de causalité ni recommander un ordre.
11. Conserver source_id, published_at, event_at, received_at, revision_id et raw_content_hash.
12. Séparer extraction factuelle, classification, scoring et explanation.
13. Attribuer reliability/coverage et citer les source records.
14. Le contexte peut réduire/bloquer le risque mais jamais augmenter seul size ou créer signal.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Composants contradictoires sans règle de résolution → CONTEXT_MIXED/UNKNOWN.
- Poids ou config non approuvé → BLOCKED_CONFIG.
- Reason code sans preuve source → rejet.
- Texte divergent du state machine → validation FAIL.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/intelligence/llm_explanation_and_context_fusion.py
- src/crypto_quant_bot/intelligence/llm_explanation_and_context_fusion_models.py
- scripts/run_lot109_llm_explanation_and_context_fusion.py
- scripts/validate_lot109.py
- tests/test_lot109_llm_explanation_and_context_fusion.py
- data/audit/llm_explanation_and_context_fusion_lot109.json
- reports/lot_109_llm_explanation_and_context_fusion_report.md
- docs/LOT_109_LLM_EXPLANATION_AND_CONTEXT_FUSION.md
- docs/ACCEPTANCE_CRITERIA_LOT_109.md

### Observabilité minimale

- lot_109_records_processed_total
- lot_109_validation_failures_total
- lot_109_processing_latency_ms

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test d’ablation de chaque composant.
- Test de source manquante sans changement silencieux de sens.
- Golden tests des explications.
- Test qu’aucun token BUY/SELL/position_size n’est produit par la couche descriptive.
- Article publié après decision_time non visible.
- LLM output sans source reference rejeté.
- Prompt injection ne modifie aucun state exécutable.

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
- news_context cannot increase size alone
- LLM cannot approve trade

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 110 — News/Event Replay, Audit & V11 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `READ_ONLY_CONTEXT_ONLY`  
**Composant propriétaire :** `IntelligenceDomain`  
**Frontière de code :** `src/crypto_quant_bot/intelligence`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « News/Event Replay, Audit & V11 Closure » dans News / AI / Event Context, produire NewsEventReplayAuditV11ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- NewsEventReplayAuditV11ClosureStateV1
- NewsEventReplayAuditV11ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 110, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « News/Event Replay, Audit & V11 Closure » dans le composant IntelligenceDomain sans effet de bord non déclaré.
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

- scripts/validate_all_until_lot110.py
- scripts/run_required_chain_until_lot110.sh
- scripts/diagnose_exact_chain_until_lot110.py
- tests/test_lot110_closure_contract.py
- data/audit/closure_manifest_lot110.json
- reports/lot_110_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_110.md
- src/crypto_quant_bot/intelligence/news_event_replay_audit_and_v11_closure.py
- src/crypto_quant_bot/intelligence/news_event_replay_audit_and_v11_closure_models.py
- scripts/run_lot110_news_event_replay_audit_and_v11_closure.py
- scripts/validate_lot110.py
- tests/test_lot110_news_event_replay_audit_and_v11_closure.py
- data/audit/news_event_replay_audit_and_v11_closure_lot110.json
- reports/lot_110_news_event_replay_audit_and_v11_closure_report.md
- docs/LOT_110_NEWS_EVENT_REPLAY_AUDIT_AND_V11_CLOSURE.md

### Observabilité minimale

- lot_110_records_processed_total
- lot_110_validation_failures_total
- lot_110_processing_latency_ms

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel
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
- news_context cannot increase size alone
- LLM cannot approve trade

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 103–110 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
