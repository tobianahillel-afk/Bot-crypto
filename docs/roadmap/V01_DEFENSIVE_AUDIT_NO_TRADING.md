# V1 — Defensive Audit / No Trading

Identifiant : `V1_DEFENSIVE_AUDIT`

Plage canonique : **Lots 0 à 20**

Statut : `CLOSED`

## Objectif de la version

Construire et fermer une base défensive, reproductible et strictement no-trading.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 0 — Project Bootstrap & Safety Baseline

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Établir l’identité, la structure, les conventions et les garde-fous initiaux du projet.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 1 — Data Platform Foundation

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Créer une plateforme de données locale, déterministe et contrôlée pour les premières fixtures BTC/EUR.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 2 — Multi-Timeframe Dataset & Basic Features

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Construire les datasets 5m/15m et les premières features mathématiques sans introduire de stratégie.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 3 — Pivot Engine & Support/Resistance Zones

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Détecter pivots et zones descriptives de support/résistance avec disponibilité temporelle explicite.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 4 — Volume Profile, VWAP & Anchored VWAP

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Calculer Volume Profile candle-based, VWAP et Anchored VWAP en mode analytique uniquement.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 5 — Volatility / ATR / Range Engine

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Mesurer ATR, true range, compression, expansion et volatilité descriptive.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 6 — Market Regime Engine

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Classifier le régime de marché sans produire de signal ou d’ordre.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 7 — Market State Engine

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Consolider un état marché local, versionné et rejouable.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 8 — Feature Registry & Anti-Lookahead Audit

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Centraliser les features et prouver l’absence de lookahead/future leakage.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 9 — Deterministic Replay / Backtest Skeleton

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Mettre en place un replay déterministe sans ordres, fills ni PnL exploitable.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 10 — Transaction Costs V0

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Modéliser les premières frictions de transaction sans activation décisionnelle.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 11 — Risk Engine & Decision Firewall

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Bloquer toute décision exploitable au moyen d’un moteur de risque fail-closed.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 12 — Exposure Guard & Capital Safety

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Empêcher toute exposition, allocation ou capital à risque.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 13 — Portfolio Freeze & Allocation Firewall

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Geler le portefeuille et toute modification d’allocation.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 14 — Final Decision Firewall

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Produire uniquement WAIT/BLOCK_TRADING et empêcher le routage d’ordre.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 15 — Decision Ledger & Immutable Audit Trail

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Journaliser les décisions bloquées dans un ledger auditable.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 16 — Dataset Lineage & Reproducibility Manifest

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Tracer lineage, checksums et reproductibilité des artefacts.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 17 — Local Health Monitor & Integrity Checks

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Surveiller intégrité, santé locale et cohérence des artefacts.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 18 — No-Trading Compliance Audit

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Prouver formellement le maintien des invariants no-trading.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 19 — Release Candidate Assembly

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Assembler un release candidate auditable sans modifier les garanties V1.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Lot 20 — V1 Defensive Closure & Frozen Archive

**Statut canonique :** `IMPLEMENTED_VALIDATED`

### Objectif

Fermer V1 et figer une archive vérifiée qui ne doit plus être régénérée.

### Dépendances et entrées

- Artefacts des lots précédents
- Configuration locale
- Fixtures déterministes

### Exigences d’implémentation

- Conserver l’implémentation historique et les correctifs bis/ter associés comme historique d’audit.
- Maintenir les scripts run/validate, les tests unitaires et les rapports déjà présents.
- Ne pas modifier les invariants validés sans lot correctif dédié.

### Artefacts attendus

- Artefacts data/audit
- Rapports Markdown
- Évidence de validation et checksums

### Tests et critères d’acceptation

- Script validate_lotX.py PASS
- Chaîne requise jusqu’au lot PASS
- Tests projet PASS
- Absence de champs/exécutions interdits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- `trade_allowed=false`
- `execution_allowed=false`
- `live_execution=DISABLED`
- `leverage=FORBIDDEN`

### Gate de promotion

Lot déjà validé ; toute modification future exige un correctif isolé et une nouvelle preuve.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
