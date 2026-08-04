# V21 — On-chain / Flow Intelligence

Identifiant : `V21_ONCHAIN_FLOW`  
Plage canonique : **Lots 175 à 177**  
Composant/domain owner : `OnChainContextDomain`  
Mode maximal autorisé : `ONCHAIN_CONTEXT_ONLY`

## Finalité de la version

Faire évoluer le système de **Sources on-chain enregistrées** vers **Contexte on-chain fiable et non exécutable**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Sources on-chain enregistrées.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/onchain`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 175 — On-Chain Source Registry & Reliability

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ONCHAIN_CONTEXT_ONLY`  
**Composant propriétaire :** `OnChainContextDomain`  
**Frontière de code :** `src/crypto_quant_bot/onchain`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « On-Chain Source Registry & Reliability » dans On-chain / Flow Intelligence, produire OnChainSourceRegistryReliabilityStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- SourceRegistryV1 produit par V3

### Contrats de sortie

- OnChainSourceRegistryReliabilityStateV1
- OnChainSourceRegistryReliabilityAuditV1
- OnChainContextStateV1
- OnChainSourcePolicyV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 175, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « On-Chain Source Registry & Reliability » dans le composant OnChainContextDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Enregistrer source_id, provider, venue, endpoint/type, champs, cadence, timezone, licence, auth_mode, retention et criticité.
6. Définir source of truth, sources de secours et politique de révision.
7. Interdire toute source inconnue ou non approuvée dans une décision.
8. Enregistrer chain, provider, block_height, observed_at, finality, revision et attribution confidence.
9. Dédupliquer transactions/entities et distinguer exchange inflow/outflow, stablecoin, miner et large-holder flows.
10. Mesurer lags et réorg risk.
11. Ne jamais présenter une attribution wallet/entity comme certaine sans preuve.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/onchain/on_chain_source_registry_and_reliability.py
- src/crypto_quant_bot/onchain/on_chain_source_registry_and_reliability_models.py
- scripts/run_lot175_on_chain_source_registry_and_reliability.py
- scripts/validate_lot175.py
- tests/test_lot175_on_chain_source_registry_and_reliability.py
- data/audit/on_chain_source_registry_and_reliability_lot175.json
- reports/lot_175_on_chain_source_registry_and_reliability_report.md
- docs/LOT_175_ON_CHAIN_SOURCE_REGISTRY_AND_RELIABILITY.md
- docs/ACCEPTANCE_CRITERIA_LOT_175.md

### Observabilité minimale

- lot_175_records_processed_total
- lot_175_validation_failures_total
- lot_175_processing_latency_ms

### Tests et critères d’acceptation

- Provenance complete
- Lag visible
- No wallet attribution presented as certainty
- No direct signal
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Source inconnue rejetée.
- Révision de source incrémente schema/config version.
- Reorg/revision.
- Duplicate transaction/provider.
- Lag visible et contexte non exécutable.

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
- On-chain context cannot authorize trading alone

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 176 — Exchange, Stablecoin, Miner & Whale Flow Context

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ONCHAIN_CONTEXT_ONLY`  
**Composant propriétaire :** `OnChainContextDomain`  
**Frontière de code :** `src/crypto_quant_bot/onchain`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Exchange, Stablecoin, Miner & Whale Flow Context » dans On-chain / Flow Intelligence, produire ExchangeStablecoinMinerWhaleFlowContextStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ExchangeStablecoinMinerWhaleFlowContextStateV1
- ExchangeStablecoinMinerWhaleFlowContextAuditV1
- OnChainContextStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 176, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Exchange, Stablecoin, Miner & Whale Flow Context » dans le composant OnChainContextDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Enregistrer chain, provider, block_height, observed_at, finality, revision et attribution confidence.
6. Dédupliquer transactions/entities et distinguer exchange inflow/outflow, stablecoin, miner et large-holder flows.
7. Mesurer lags et réorg risk.
8. Ne jamais présenter une attribution wallet/entity comme certaine sans preuve.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/onchain/exchange_stablecoin_miner_and_whale_flow_context.py
- src/crypto_quant_bot/onchain/exchange_stablecoin_miner_and_whale_flow_context_models.py
- scripts/run_lot176_exchange_stablecoin_miner_and_whale_flow_context.py
- scripts/validate_lot176.py
- tests/test_lot176_exchange_stablecoin_miner_and_whale_flow_context.py
- data/audit/exchange_stablecoin_miner_and_whale_flow_context_lot176.json
- reports/lot_176_exchange_stablecoin_miner_and_whale_flow_context_report.md
- docs/LOT_176_EXCHANGE_STABLECOIN_MINER_AND_WHALE_FLOW_CONTEXT.md
- docs/ACCEPTANCE_CRITERIA_LOT_176.md

### Observabilité minimale

- lot_176_records_processed_total
- lot_176_validation_failures_total
- lot_176_processing_latency_ms

### Tests et critères d’acceptation

- Provenance complete
- Lag visible
- No wallet attribution presented as certainty
- No direct signal
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Reorg/revision.
- Duplicate transaction/provider.
- Lag visible et contexte non exécutable.

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
- On-chain context cannot authorize trading alone

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 177 — On-Chain / Market Fusion & Final Roadmap Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `ONCHAIN_CONTEXT_ONLY`  
**Composant propriétaire :** `OnChainContextDomain`  
**Frontière de code :** `src/crypto_quant_bot/onchain`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « On-Chain / Market Fusion & Final Roadmap Closure » dans On-chain / Flow Intelligence, produire OnChainMarketFusionFinalRoadmapClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- OnChainMarketFusionFinalRoadmapClosureStateV1
- OnChainMarketFusionFinalRoadmapClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- OnChainContextStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 177, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « On-Chain / Market Fusion & Final Roadmap Closure » dans le composant OnChainContextDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Agrégater uniquement des composants validés et publier les poids/configs effectivement utilisés.
6. Conserver contribution, qualité et fraîcheur de chaque source ; une source manquante n’est jamais renormalisée silencieusement.
7. Produire état dominant, alternatives, conflits et confidence_interval lorsque disponible.
8. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
9. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
10. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
11. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
12. Enregistrer chain, provider, block_height, observed_at, finality, revision et attribution confidence.
13. Dédupliquer transactions/entities et distinguer exchange inflow/outflow, stablecoin, miner et large-holder flows.
14. Mesurer lags et réorg risk.
15. Ne jamais présenter une attribution wallet/entity comme certaine sans preuve.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Composants contradictoires sans règle de résolution → CONTEXT_MIXED/UNKNOWN.
- Poids ou config non approuvé → BLOCKED_CONFIG.
- Checksum différent → NON_DETERMINISTIC_FAIL.
- Lot antérieur non PASS → closure refusée.

### Fichiers et artefacts d’implémentation attendus

- scripts/validate_all_until_lot177.py
- scripts/run_required_chain_until_lot177.sh
- scripts/diagnose_exact_chain_until_lot177.py
- tests/test_lot177_closure_contract.py
- data/audit/closure_manifest_lot177.json
- reports/lot_177_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_177.md
- src/crypto_quant_bot/onchain/on_chain_market_fusion_and_final_roadmap_closure.py
- src/crypto_quant_bot/onchain/on_chain_market_fusion_and_final_roadmap_closure_models.py
- scripts/run_lot177_on_chain_market_fusion_and_final_roadmap_closure.py
- scripts/validate_lot177.py
- tests/test_lot177_on_chain_market_fusion_and_final_roadmap_closure.py
- data/audit/on_chain_market_fusion_and_final_roadmap_closure_lot177.json
- reports/lot_177_on_chain_market_fusion_and_final_roadmap_closure_report.md
- docs/LOT_177_ON_CHAIN_MARKET_FUSION_AND_FINAL_ROADMAP_CLOSURE.md

### Observabilité minimale

- lot_177_records_processed_total
- lot_177_validation_failures_total
- lot_177_processing_latency_ms

### Tests et critères d’acceptation

- Provenance complete
- Lag visible
- No wallet attribution presented as certainty
- No direct signal
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Test d’ablation de chaque composant.
- Test de source manquante sans changement silencieux de sens.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Reorg/revision.
- Duplicate transaction/provider.
- Lag visible et contexte non exécutable.

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
- On-chain context cannot authorize trading alone

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Clôture documentaire de la roadmap ; aucune activation live/HFT implicite.

## Gate de clôture de version

- Tous les Lots 175–177 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
