# V20 — Options Context

Identifiant : `V20_OPTIONS_CONTEXT`  
Plage canonique : **Lots 172 à 174**  
Composant/domain owner : `OptionsContextDomain`  
Mode maximal autorisé : `OPTIONS_CONTEXT_ONLY`

## Finalité de la version

Faire évoluer le système de **Données options read-only/offline** vers **Contexte IV/skew/expiry non exécutable**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Données options read-only/offline.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/options`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 172 — Options Data & Contract Registry

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPTIONS_CONTEXT_ONLY`  
**Composant propriétaire :** `OptionsContextDomain`  
**Frontière de code :** `src/crypto_quant_bot/options`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Options Data & Contract Registry » dans Options Context, produire OptionsDataContractRegistryStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- OptionsDataContractRegistryStateV1
- OptionsDataContractRegistryAuditV1
- OptionsContextStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 172, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Options Data & Contract Registry » dans le composant OptionsContextDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Normaliser underlying, expiry, strike, option_type, multiplier, quote currency et settlement.
6. Calculer/ingérer IV avec source/method, bid/ask quality et no-arbitrage checks.
7. Construire skew/term structure et greeks avec model assumptions explicites.
8. Contexte options ne produit aucun signal direct et ne bloque pas le core si module absent.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/options/options_data_and_contract_registry.py
- src/crypto_quant_bot/options/options_data_and_contract_registry_models.py
- scripts/run_lot172_options_data_and_contract_registry.py
- scripts/validate_lot172.py
- tests/test_lot172_options_data_and_contract_registry.py
- data/audit/options_data_and_contract_registry_lot172.json
- reports/lot_172_options_data_and_contract_registry_report.md
- docs/LOT_172_OPTIONS_DATA_AND_CONTRACT_REGISTRY.md
- docs/ACCEPTANCE_CRITERIA_LOT_172.md

### Observabilité minimale

- lot_172_records_processed_total
- lot_172_validation_failures_total
- lot_172_processing_latency_ms

### Tests et critères d’acceptation

- Contract normalization
- No stale surface accepted
- No direct trade signal
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Put/call, expiry timezone et stale surface.
- Arbitrage violations marquées invalid.

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
- Options module optional and non-blocking for core roadmap

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 173 — Implied Volatility, Skew & Term Structure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPTIONS_CONTEXT_ONLY`  
**Composant propriétaire :** `OptionsContextDomain`  
**Frontière de code :** `src/crypto_quant_bot/options`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Implied Volatility, Skew & Term Structure » dans Options Context, produire ImpliedVolatilitySkewTermStructureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ImpliedVolatilitySkewTermStructureStateV1
- ImpliedVolatilitySkewTermStructureAuditV1
- OptionsContextStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 173, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Implied Volatility, Skew & Term Structure » dans le composant OptionsContextDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Normaliser underlying, expiry, strike, option_type, multiplier, quote currency et settlement.
6. Calculer/ingérer IV avec source/method, bid/ask quality et no-arbitrage checks.
7. Construire skew/term structure et greeks avec model assumptions explicites.
8. Contexte options ne produit aucun signal direct et ne bloque pas le core si module absent.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/options/implied_volatility_skew_and_term_structure.py
- src/crypto_quant_bot/options/implied_volatility_skew_and_term_structure_models.py
- scripts/run_lot173_implied_volatility_skew_and_term_structure.py
- scripts/validate_lot173.py
- tests/test_lot173_implied_volatility_skew_and_term_structure.py
- data/audit/implied_volatility_skew_and_term_structure_lot173.json
- reports/lot_173_implied_volatility_skew_and_term_structure_report.md
- docs/LOT_173_IMPLIED_VOLATILITY_SKEW_AND_TERM_STRUCTURE.md
- docs/ACCEPTANCE_CRITERIA_LOT_173.md

### Observabilité minimale

- lot_173_records_processed_total
- lot_173_validation_failures_total
- lot_173_processing_latency_ms

### Tests et critères d’acceptation

- Contract normalization
- No stale surface accepted
- No direct trade signal
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Put/call, expiry timezone et stale surface.
- Arbitrage violations marquées invalid.

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
- Options module optional and non-blocking for core roadmap

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 174 — Expiry, Greeks, Context Fusion & V20 Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `OPTIONS_CONTEXT_ONLY`  
**Composant propriétaire :** `OptionsContextDomain`  
**Frontière de code :** `src/crypto_quant_bot/options`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Expiry, Greeks, Context Fusion & V20 Closure » dans Options Context, produire ExpiryGreeksContextFusionV20ClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- ExpiryGreeksContextFusionV20ClosureStateV1
- ExpiryGreeksContextFusionV20ClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- OptionsContextStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 174, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Expiry, Greeks, Context Fusion & V20 Closure » dans le composant OptionsContextDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Agrégater uniquement des composants validés et publier les poids/configs effectivement utilisés.
6. Conserver contribution, qualité et fraîcheur de chaque source ; une source manquante n’est jamais renormalisée silencieusement.
7. Produire état dominant, alternatives, conflits et confidence_interval lorsque disponible.
8. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
9. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
10. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
11. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
12. Normaliser underlying, expiry, strike, option_type, multiplier, quote currency et settlement.
13. Calculer/ingérer IV avec source/method, bid/ask quality et no-arbitrage checks.
14. Construire skew/term structure et greeks avec model assumptions explicites.
15. Contexte options ne produit aucun signal direct et ne bloque pas le core si module absent.

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

- scripts/validate_all_until_lot174.py
- scripts/run_required_chain_until_lot174.sh
- scripts/diagnose_exact_chain_until_lot174.py
- tests/test_lot174_closure_contract.py
- data/audit/closure_manifest_lot174.json
- reports/lot_174_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_174.md
- src/crypto_quant_bot/options/expiry_greeks_context_fusion_and_v20_closure.py
- src/crypto_quant_bot/options/expiry_greeks_context_fusion_and_v20_closure_models.py
- scripts/run_lot174_expiry_greeks_context_fusion_and_v20_closure.py
- scripts/validate_lot174.py
- tests/test_lot174_expiry_greeks_context_fusion_and_v20_closure.py
- data/audit/expiry_greeks_context_fusion_and_v20_closure_lot174.json
- reports/lot_174_expiry_greeks_context_fusion_and_v20_closure_report.md
- docs/LOT_174_EXPIRY_GREEKS_CONTEXT_FUSION_AND_V20_CLOSURE.md

### Observabilité minimale

- lot_174_records_processed_total
- lot_174_validation_failures_total
- lot_174_processing_latency_ms

### Tests et critères d’acceptation

- Contract normalization
- No stale surface accepted
- No direct trade signal
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
- Put/call, expiry timezone et stale surface.
- Arbitrage violations marquées invalid.

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
- Options module optional and non-blocking for core roadmap

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 172–174 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
