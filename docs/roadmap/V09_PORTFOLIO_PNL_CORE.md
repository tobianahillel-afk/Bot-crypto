# V9 — Portfolio / PnL Core

Identifiant : `V9_PORTFOLIO_PNL`  
Plage canonique : **Lots 88 à 95**  
Composant/domain owner : `PortfolioDomain`  
Mode maximal autorisé : `PORTFOLIO_ACCOUNTING`

## Finalité de la version

Faire évoluer le système de **Ledgers paper disponibles** vers **Portfolio/PnL unifiés et réconciliables**, sans activer les capabilities des versions suivantes.

## Gate d’entrée de version

- Ledgers paper disponibles.
- Les dépendances, schémas, configs et données d’entrée sont versionnés et validés.
- Les invariants V1 et les vetos transverses restent actifs.
- Une revue humaine approuve le scope avant le premier lot planifié.

## Frontières d’architecture

- Package propriétaire : `src/crypto_quant_bot/portfolio`.
- Les échanges avec les autres domaines passent par les contrats canoniques, jamais par accès interne direct.
- Toute sortie contient lineage, reason_codes, validation_state et runtime_mode.
- Le domaine ne peut ni contourner RiskDecision, ni augmenter ses propres permissions.

## Lot 88 — Portfolio Core & State Model

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PORTFOLIO_ACCOUNTING`  
**Composant propriétaire :** `PortfolioDomain`  
**Frontière de code :** `src/crypto_quant_bot/portfolio`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Portfolio Core & State Model » dans Portfolio / PnL Core, produire PortfolioCoreStateModelStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- PortfolioCoreStateModelStateV1
- PortfolioCoreStateModelAuditV1
- PortfolioStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 88, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Portfolio Core & State Model » dans le composant PortfolioDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Centraliser cash, collateral, reserved, available, positions, open orders et valuation timestamp.
6. Appliquer event sourcing ; chaque état dérive du ledger.
7. Marquer UNKNOWN/FROZEN si balance ou position non réconciliée.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/portfolio/portfolio_core_and_state_model.py
- src/crypto_quant_bot/portfolio/portfolio_core_and_state_model_models.py
- scripts/run_lot88_portfolio_core_and_state_model.py
- scripts/validate_lot88.py
- tests/test_lot88_portfolio_core_and_state_model.py
- data/audit/portfolio_core_and_state_model_lot88.json
- reports/lot_88_portfolio_core_and_state_model_report.md
- docs/LOT_88_PORTFOLIO_CORE_AND_STATE_MODEL.md
- docs/ACCEPTANCE_CRITERIA_LOT_88.md

### Observabilité minimale

- lot_88_records_processed_total
- lot_88_validation_failures_total
- lot_88_processing_latency_ms

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Rebuild from ledger = snapshot.
- Double event idempotent.

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
- Unknown balance/position => freeze portfolio

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 89 — Cash, Collateral, Margin & Buying Power

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PORTFOLIO_ACCOUNTING`  
**Composant propriétaire :** `PortfolioDomain`  
**Frontière de code :** `src/crypto_quant_bot/portfolio`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Cash, Collateral, Margin & Buying Power » dans Portfolio / PnL Core, produire CashCollateralMarginBuyingPowerStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- CashCollateralMarginBuyingPowerStateV1
- CashCollateralMarginBuyingPowerAuditV1
- CapitalStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 89, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Cash, Collateral, Margin & Buying Power » dans le composant PortfolioDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Distinguer total, reserved, available, collateral, margin_used et buying_power.
6. Appliquer haircuts, settlement et currency conversion versionnés.
7. Leverage reste FORBIDDEN pour le périmètre initial spot BTC/EUR.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/portfolio/cash_collateral_margin_and_buying_power.py
- src/crypto_quant_bot/portfolio/cash_collateral_margin_and_buying_power_models.py
- scripts/run_lot89_cash_collateral_margin_and_buying_power.py
- scripts/validate_lot89.py
- tests/test_lot89_cash_collateral_margin_and_buying_power.py
- data/audit/cash_collateral_margin_and_buying_power_lot89.json
- reports/lot_89_cash_collateral_margin_and_buying_power_report.md
- docs/LOT_89_CASH_COLLATERAL_MARGIN_AND_BUYING_POWER.md
- docs/ACCEPTANCE_CRITERIA_LOT_89.md

### Observabilité minimale

- lot_89_records_processed_total
- lot_89_validation_failures_total
- lot_89_processing_latency_ms

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Accounting identity total = available + reserved selon policy.
- Conversion FX stale bloque valuation.

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
- Unknown balance/position => freeze portfolio

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 90 — Position Lifecycle & Corporate/Instrument Events

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PORTFOLIO_ACCOUNTING`  
**Composant propriétaire :** `PortfolioDomain`  
**Frontière de code :** `src/crypto_quant_bot/portfolio`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Position Lifecycle & Corporate/Instrument Events » dans Portfolio / PnL Core, produire PositionLifecycleCorporateInstrumentEventsStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ExchangeInstrumentMetadataV1

### Contrats de sortie

- PositionLifecycleCorporateInstrumentEventsStateV1
- PositionLifecycleCorporateInstrumentEventsAuditV1
- InstrumentRegistryV1
- InstrumentSpecificationV1
- PositionStateV1
- PositionEventV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 90, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Position Lifecycle & Corporate/Instrument Events » dans le composant PortfolioDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Normaliser venue, base, quote, market_type, canonical_symbol et exchange_symbol.
6. Modéliser spot, perpetual, dated future et option avec champs non applicables explicitement null/forbidden.
7. Valider tick_size, lot_size, min_qty, min_notional, price/qty precision, fee tier, settlement, margin et leverage policy.
8. Appliquer fills, fees, funding, transfers et instrument events dans ordre déterministe.
9. Gérer increase/reduce/close/reopen et average cost selon méthode documentée.
10. Distinguer position économique, venue position et strategy attribution.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Métadonnée instrument ambiguë ou révisée → INSTRUMENT_FROZEN.
- Arrondi qui viole min_notional → order intent rejeté.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/portfolio/position_lifecycle_and_corporate_instrument_events.py
- src/crypto_quant_bot/portfolio/position_lifecycle_and_corporate_instrument_events_models.py
- scripts/run_lot90_position_lifecycle_and_corporate_instrument_events.py
- scripts/validate_lot90.py
- tests/test_lot90_position_lifecycle_and_corporate_instrument_events.py
- data/audit/position_lifecycle_and_corporate_instrument_events_lot90.json
- reports/lot_90_position_lifecycle_and_corporate_instrument_events_report.md
- docs/LOT_90_POSITION_LIFECYCLE_AND_CORPORATE_INSTRUMENT_EVENTS.md
- docs/ACCEPTANCE_CRITERIA_LOT_90.md

### Observabilité minimale

- lot_90_records_processed_total
- lot_90_validation_failures_total
- lot_90_processing_latency_ms

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Round-trip symbol canonical ↔ venue.
- Tests de quantization aux frontières tick/lot/min_notional.
- Long→flat→long ne mélange pas lots.
- Out-of-order fill event réconcilié.

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
- Unknown balance/position => freeze portfolio

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 91 — Unified PnL Core

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PORTFOLIO_ACCOUNTING`  
**Composant propriétaire :** `PortfolioDomain`  
**Frontière de code :** `src/crypto_quant_bot/portfolio`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Unified PnL Core » dans Portfolio / PnL Core, produire UnifiedPnLCoreStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- UnifiedPnLCoreStateV1
- UnifiedPnLCoreAuditV1
- PnLLedgerV1
- PnLStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 91, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Unified PnL Core » dans le composant PortfolioDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Séparer realized, unrealized, fees, funding, spread, slippage, impact et FX.
6. Définir mark price source/freshness par instrument.
7. Réutiliser le même core avec adapters paper/sandbox/live.
8. Garantir absence de double comptage et accounting identity.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/portfolio/unified_pnl_core.py
- src/crypto_quant_bot/portfolio/unified_pnl_core_models.py
- scripts/run_lot91_unified_pnl_core.py
- scripts/validate_lot91.py
- tests/test_lot91_unified_pnl_core.py
- data/audit/unified_pnl_core_lot91.json
- reports/lot_91_unified_pnl_core_report.md
- docs/LOT_91_UNIFIED_PNL_CORE.md
- docs/ACCEPTANCE_CRITERIA_LOT_91.md

### Observabilité minimale

- lot_91_records_processed_total
- lot_91_validation_failures_total
- lot_91_processing_latency_ms

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Round-trip position close.
- Mark stale gèle unrealized PnL.
- Somme components = total PnL.

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
- Unknown balance/position => freeze portfolio

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 92 — Fee, Funding, Slippage & Attribution

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PORTFOLIO_ACCOUNTING`  
**Composant propriétaire :** `PortfolioDomain`  
**Frontière de code :** `src/crypto_quant_bot/portfolio`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Fee, Funding, Slippage & Attribution » dans Portfolio / PnL Core, produire FeeFundingSlippageAttributionStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- FeeFundingSlippageAttributionStateV1
- FeeFundingSlippageAttributionAuditV1
- DerivativesContextStateV1
- SlippageImpactEstimateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 92, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Fee, Funding, Slippage & Attribution » dans le composant PortfolioDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Normaliser OI, funding, mark/index, basis et liquidations par venue/contrat.
6. Aligner publication/effective_time et gérer révisions.
7. Calculer crowding, leverage build-up, squeeze/liquidation risk comme contexte probabiliste.
8. Interdire l’usage si spot/perp mapping ou notionals ne sont pas comparables.
9. Estimer slippage depuis spread, depth, participation, volatility et latency.
10. Séparer temporary impact, permanent proxy et adverse movement.
11. Calibrer par buckets instrument/régime/taille ; publier intervalle et fallback.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/portfolio/fee_funding_slippage_and_attribution.py
- src/crypto_quant_bot/portfolio/fee_funding_slippage_and_attribution_models.py
- scripts/run_lot92_fee_funding_slippage_and_attribution.py
- scripts/validate_lot92.py
- tests/test_lot92_fee_funding_slippage_and_attribution.py
- data/audit/fee_funding_slippage_and_attribution_lot92.json
- reports/lot_92_fee_funding_slippage_and_attribution_report.md
- docs/LOT_92_FEE_FUNDING_SLIPPAGE_AND_ATTRIBUTION.md
- docs/ACCEPTANCE_CRITERIA_LOT_92.md

### Observabilité minimale

- lot_92_records_processed_total
- lot_92_validation_failures_total
- lot_92_processing_latency_ms

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Funding publication vs effective time.
- OI change sans prix/volume ne produit pas de scénario certain.
- Slippage monotone avec taille.
- Book insuffisant → no-fill/partial-fill, pas prix inventé.

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
- Unknown balance/position => freeze portfolio

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 93 — Exposure, Correlation, Concentration & Portfolio Heat

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PORTFOLIO_ACCOUNTING`  
**Composant propriétaire :** `PortfolioDomain`  
**Frontière de code :** `src/crypto_quant_bot/portfolio`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Exposure, Correlation, Concentration & Portfolio Heat » dans Portfolio / PnL Core, produire ExposureCorrelationConcentrationPortfolioHeatStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables

### Contrats de sortie

- ExposureCorrelationConcentrationPortfolioHeatStateV1
- ExposureCorrelationConcentrationPortfolioHeatAuditV1
- PortfolioRiskStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 93, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Exposure, Correlation, Concentration & Portfolio Heat » dans le composant PortfolioDomain sans effet de bord non déclaré.
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

- src/crypto_quant_bot/portfolio/exposure_correlation_concentration_and_portfolio_heat.py
- src/crypto_quant_bot/portfolio/exposure_correlation_concentration_and_portfolio_heat_models.py
- scripts/run_lot93_exposure_correlation_concentration_and_portfolio_heat.py
- scripts/validate_lot93.py
- tests/test_lot93_exposure_correlation_concentration_and_portfolio_heat.py
- data/audit/exposure_correlation_concentration_and_portfolio_heat_lot93.json
- reports/lot_93_exposure_correlation_concentration_and_portfolio_heat_report.md
- docs/LOT_93_EXPOSURE_CORRELATION_CONCENTRATION_AND_PORTFOLIO_HEAT.md
- docs/ACCEPTANCE_CRITERIA_LOT_93.md

### Observabilité minimale

- lot_93_records_processed_total
- lot_93_validation_failures_total
- lot_93_processing_latency_ms

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance
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
- Unknown balance/position => freeze portfolio

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 94 — Statements, Reconciliation & Audit Export

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PORTFOLIO_ACCOUNTING`  
**Composant propriétaire :** `PortfolioDomain`  
**Frontière de code :** `src/crypto_quant_bot/portfolio`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « Statements, Reconciliation & Audit Export » dans Portfolio / PnL Core, produire StatementsReconciliationAuditExportStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- StatementsReconciliationAuditExportStateV1
- StatementsReconciliationAuditExportAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- ReconciliationReportV1
- ReconciliationVetoV1
- AccountStatementV1
- AuditExportManifestV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 94, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « Statements, Reconciliation & Audit Export » dans le composant PortfolioDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Comparer identifiants, quantités, prix, frais, balances, positions et timestamps entre les deux sources concernées.
10. Classer MATCH, TOLERATED_DIFF, MINOR_DIVERGENCE, CRITICAL_DIVERGENCE.
11. Produire delta exact, tolérance versionnée, source de vérité et action corrective.
12. MINOR → PAUSE ; CRITICAL/unknown ownership → KILL_SWITCH ou BLOCK_TRADING selon matrice.
13. Générer période, opening/closing balances, cashflows, trades, fees, funding et PnL.
14. Inclure checksums et liens aux ledgers source.
15. Rendre exports immuables et vérifiables.

### Règles métier et algorithmiques

- Aucune valeur implicite ne peut transformer UNKNOWN en autorisation.
- Les seuils sont lus depuis une configuration versionnée ; aucun seuil live n’est caché dans le code.

### Modes de défaillance et comportement fail-closed

- Entrée absente, obsolète, hors séquence ou de version incompatible → état BLOCKED/UNKNOWN.
- Divergence entre état calculé et artefact réconcilié → veto et rapport de divergence.
- Exception non classifiée → aucun output valide, incident auditable et arrêt fail-closed.
- Checksum différent → NON_DETERMINISTIC_FAIL.
- Lot antérieur non PASS → closure refusée.
- Élément orphelin ou duplicate → RECONCILIATION_REQUIRED.
- Différence de frais non expliquée → PAUSE.

### Fichiers et artefacts d’implémentation attendus

- src/crypto_quant_bot/portfolio/statements_reconciliation_and_audit_export.py
- src/crypto_quant_bot/portfolio/statements_reconciliation_and_audit_export_models.py
- scripts/run_lot94_statements_reconciliation_and_audit_export.py
- scripts/validate_lot94.py
- tests/test_lot94_statements_reconciliation_and_audit_export.py
- data/audit/statements_reconciliation_and_audit_export_lot94.json
- reports/lot_94_statements_reconciliation_and_audit_export_report.md
- docs/LOT_94_STATEMENTS_RECONCILIATION_AND_AUDIT_EXPORT.md
- docs/ACCEPTANCE_CRITERIA_LOT_94.md

### Observabilité minimale

- lot_94_records_processed_total
- lot_94_validation_failures_total
- lot_94_processing_latency_ms

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Ordre/fill/balance/frais divergents injectés.
- Reconciliation idempotente après restart.
- Statement reconcilable to ledger.
- Tamper detection par checksum.

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
- Unknown balance/position => freeze portfolio

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 95 — V9 Portfolio / PnL Closure

**Statut canonique :** `PLANNED_LOCKED`  
**Runtime/mode autorisé :** `PORTFOLIO_ACCOUNTING`  
**Composant propriétaire :** `PortfolioDomain`  
**Frontière de code :** `src/crypto_quant_bot/portfolio`

### Objectif et responsabilité exacte

Être l’unique propriétaire de « V9 Portfolio / PnL Closure » dans Portfolio / PnL Core, produire V9PortfolioPnLClosureStateV1 et refuser tout état ambigu avant publication. Le lot doit être directement implémentable à partir des contrats, étapes, erreurs, fichiers et tests ci-dessous.

### Contrats d’entrée

- RunContextV1 (run_id, runtime_mode, config_version, code_commit, correlation_id)
- LineageEnvelopeV1 des artefacts produits par les lots préalables
- ReplayManifestV1
- Checksums des inputs/configs/code/models

### Contrats de sortie

- V9PortfolioPnLClosureStateV1
- V9PortfolioPnLClosureAuditV1
- ReplayEvidenceV1
- LotValidationReportV1
- ClosureManifestV1
- PnLLedgerV1
- PnLStateV1

### Séquence de traitement obligatoire

1. Valider les gates d’entrée du Lot 95, les versions de schéma et la fraîcheur de chaque dépendance.
2. Exécuter la responsabilité « V9 Portfolio / PnL Closure » dans le composant PortfolioDomain sans effet de bord non déclaré.
3. Associer à chaque résultat les identifiants de données, features, modèle, configuration, code et replay.
4. Persister état, reason_codes, incertitude, veto éventuel, métriques et checksum par écriture atomique.
5. Rejouer la chaîne exacte depuis les artefacts immuables et l’ordre canonique event_time/sequence_id.
6. Comparer checksums, counts, reason_codes et états finaux entre run1/run2.
7. Exécuter les cas négatifs et les recherches de champs/capabilities interdits.
8. Figer le manifest de clôture uniquement après PASS de tous les validators et revue humaine.
9. Séparer realized, unrealized, fees, funding, spread, slippage, impact et FX.
10. Définir mark price source/freshness par instrument.
11. Réutiliser le même core avec adapters paper/sandbox/live.
12. Garantir absence de double comptage et accounting identity.

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

- scripts/validate_all_until_lot95.py
- scripts/run_required_chain_until_lot95.sh
- scripts/diagnose_exact_chain_until_lot95.py
- tests/test_lot95_closure_contract.py
- data/audit/closure_manifest_lot95.json
- reports/lot_95_validation_report.md
- docs/ACCEPTANCE_CRITERIA_LOT_95.md
- src/crypto_quant_bot/portfolio/v9_portfolio_pnl_closure.py
- src/crypto_quant_bot/portfolio/v9_portfolio_pnl_closure_models.py
- scripts/run_lot95_v9_portfolio_pnl_closure.py
- scripts/validate_lot95.py
- tests/test_lot95_v9_portfolio_pnl_closure.py
- data/audit/v9_portfolio_pnl_closure_lot95.json
- reports/lot_95_v9_portfolio_pnl_closure_report.md
- docs/LOT_95_V9_PORTFOLIO_PNL_CLOSURE.md

### Observabilité minimale

- lot_95_records_processed_total
- lot_95_validation_failures_total
- lot_95_processing_latency_ms

### Tests et critères d’acceptation

- Accounting identity
- Realized/unrealized separation
- No double counting
- Reconciliation within tolerance
- Tous les lots de la version sont couverts et leurs gates satisfaits
- Test déterministe run1/run2 avec checksums identiques.
- Test négatif : schéma incompatible rejeté.
- Test négatif : donnée stale/incomplète bloque le résultat.
- Test anti-lookahead ou anti-future-state adapté au domaine.
- Test de sérialisation/désérialisation du contrat de sortie.
- Test d’intégration avec le lot précédent et le gate suivant.
- Validation de continuité de chaîne.
- Mutation test d’un invariant de sécurité qui doit faire échouer la clôture.
- Round-trip position close.
- Mark stale gèle unrealized PnL.
- Somme components = total PnL.

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
- Unknown balance/position => freeze portfolio

### Définition de terminé

- Tous les fichiers et contrats listés existent ou sont explicitement marqués non applicables avec justification.
- Les validations unitaires, intégration, négatives, replay et sécurité sont PASS.
- Le rapport de lot contient commandes, résultats, limites connues, checksums et conclusion humaine.
- Le lot suivant reste verrouillé jusqu’au gate de promotion.

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Gate de clôture de version

- Tous les Lots 88–95 ont un rapport PASS ou un statut explicitement non applicable.
- La chaîne exacte est rejouée deux fois avec checksums identiques.
- Les cas négatifs et vetos du domaine ont été injectés.
- La revue humaine confirme limites, risques résiduels et version suivante autorisée.
