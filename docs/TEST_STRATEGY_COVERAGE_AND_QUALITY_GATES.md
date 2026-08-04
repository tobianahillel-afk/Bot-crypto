# Test Strategy, Coverage and Quality Gates

Ce document est normatif pour tous les Lots 26–177 de **Crypto Quant Bot V3.1-Ops**.

## 1. Principe

Un lot n'est pas validé parce que son scénario nominal passe. Il est validé seulement si ses propriétés, erreurs, contrats, invariants, performances et comportements de récupération sont démontrés par des suites de tests distinctes, reproductibles et auditables.

## 2. Couverture minimale obligatoire

Pour tout nouveau lot ou correctif :

```text
line coverage global du code ajouté/modifié >= 90 %
branch coverage global du code ajouté/modifié >= 85 %
line coverage des modules critiques >= 95 %
branch coverage des modules critiques >= 90 %
mutation score des modules mathématiques/risque/exécution >= 80 %
```

Modules critiques : data quality gates, anti-lookahead, calculs mathématiques, calibration, sizing, risk approval, OMS/EMS, reconciliation, accounting/PnL, kill switch, permissions et runtime state machines.

La couverture n'est jamais une preuve suffisante : un test sans assertion métier utile ne compte pas dans le gate qualité.

## 3. Suites de tests obligatoires

Chaque lot doit déclarer et exécuter les suites applicables suivantes.

### 3.1 Unit Test Suite

- une unité logique isolée ;
- cas nominaux, limites, zéros, valeurs manquantes et erreurs ;
- aucune dépendance réseau réelle ;
- déterminisme sous seed/config identiques.

### 3.2 Mathematical Logic Test Suite

- propriétés algébriques et statistiques ;
- bornes, monotonie, invariance, conservation et symétrie ;
- comparaison à une implémentation de référence indépendante ;
- cas analytiques à résultat fermé ;
- tolérances absolues et relatives explicites ;
- tests de stabilité numérique et sensibilité.

### 3.3 Property-Based Test Suite

- génération de domaines valides et invalides ;
- invariants démontrés sur de nombreuses entrées ;
- shrinking des contre-exemples ;
- seeds persistées dans les rapports d'échec.

### 3.4 Contract and Schema Test Suite

- sérialisation/désérialisation ;
- compatibilité de versions ;
- champs obligatoires ;
- enums fermés ;
- timestamps, lineage, checksums et reason codes ;
- rejet des contrats inconnus ou incomplets.

### 3.5 Integration Test Suite

- intégration avec le lot précédent et le gate suivant ;
- ordre réel des composants ;
- transactions atomiques ;
- idempotence ;
- aucun accès direct aux internals d'un autre domaine.

### 3.6 End-to-End Deterministic Replay Suite

- replay complet avec horloge simulée ;
- run1/run2 identiques ;
- checksums, comptes, décisions et reason codes identiques ;
- absence de lecture future ;
- état final réconcilié.

### 3.7 Non-Regression Test Suite

- chaque bug corrigé obtient un test permanent ;
- golden fixtures et snapshots versionnés ;
- comparaison aux rapports PASS historiques ;
- aucun changement de comportement silencieux ;
- toute modification intentionnelle exige une migration et une approbation.

### 3.8 Negative and Failure Injection Suite

- données stale, absentes, dupliquées, corrompues et hors ordre ;
- exceptions, timeouts, crash entre deux écritures ;
- partial state, duplicate event, unknown submit outcome ;
- perte de heartbeat, ledger divergence et reconciliation failure ;
- comportement attendu toujours fail-closed.

### 3.9 Security and Permission Test Suite

- absence de secrets ;
- permissions minimales ;
- withdrawal et leverage interdits ;
- runtime non autorisé rejeté ;
- approval expirée ou pour autre hash rejetée ;
- kill switch prioritaire et idempotent.

### 3.10 Performance and Resource Test Suite

- budget de latence par étape ;
- complexité temporelle et mémoire ;
- absence de croissance non bornée ;
- charge nominale, pointe et endurance ;
- pas de dégradation silencieuse.

### 3.11 Concurrency and Idempotency Test Suite

- exécutions concurrentes ;
- duplicate submit ;
- races sur state/ledger ;
- verrouillage et transactions ;
- résultat unique et réconciliable.

### 3.12 Data and Anti-Lookahead Test Suite

- `available_at <= decision_time` ;
- dernière bougie non clôturée exclue ;
- labels et outcomes jamais accessibles comme features ;
- split temporel purgé et embargo lorsque nécessaire ;
- event-time et processing-time séparés.

## 4. Matrice minimale par type de lot

| Type | Suites obligatoires supplémentaires |
|---|---|
| Math/indicateur | math, property-based, reference implementation, stability |
| Backtest/EV | anti-lookahead, purged split, replay, cost/fill realism, placebo |
| Risk/sizing | monotonicity, hard-limit boundaries, zero-on-veto, stress/tail |
| OMS/EMS | state transitions, concurrency, idempotency, crash recovery |
| Portfolio/PnL | conservation/accounting identities, reconciliation, rounding |
| Live governance | permissions, approval hash/expiry, pause/kill, rollback |
| Monitoring | fault injection, alert consequence, no silent degradation |

## 5. Qualité des assertions

Chaque test doit déclarer :

```text
test_id
requirement_id
property_or_scenario
input_fixture_or_generator
expected_result
numerical_tolerance
failure_consequence
```

Les assertions triviales, les mocks qui reproduisent exactement l'implémentation et les tests uniquement basés sur l'absence d'exception ne sont pas acceptés.

## 6. Artefacts de preuve

Chaque lot produit :

- rapport de tests par suite ;
- rapport coverage line/branch ;
- rapport mutation lorsque applicable ;
- liste des tests skipped/xfailed avec justification et échéance ;
- seeds des property-based tests en échec ;
- métriques de performance ;
- checksums des fixtures ;
- mapping requirement → tests → résultat.

## 7. Gate GO/NO-GO tests

`GO` uniquement si :

- toutes les suites obligatoires sont PASS ;
- aucun test critique skipped/xfailed ;
- seuils de coverage atteints ;
- mutation score atteint lorsque requis ;
- aucun flake non résolu sur plusieurs répétitions ;
- non-régression historique PASS ;
- rapport signé/revu.

Sinon : `NO_GO_TEST_QUALITY`.