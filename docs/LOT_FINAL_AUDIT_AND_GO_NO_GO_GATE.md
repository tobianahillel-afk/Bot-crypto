# Lot Final Audit and GO / NO-GO Gate

Aucun lot n'est déclaré `IMPLEMENTED_VALIDATED` sans audit final indépendant et verdict explicite.

## 1. Entrées obligatoires de l'audit

- spécification du lot ;
- critères d'acceptation ;
- diff complet depuis le lot précédent ;
- liste des fichiers ajoutés/modifiés/supprimés ;
- rapports de toutes les suites de tests ;
- coverage line/branch et mutation ;
- rapport mathématique ;
- rapport sécurité ;
- rapport performance ;
- matrice de traçabilité ;
- manifest et replay ;
- liste des écarts, dettes et limites connues ;
- preuve de préservation des invariants historiques.

## 2. Axes d'audit

### A. Scope et architecture

- objectif intégralement couvert ;
- aucun scope caché ou capability future activée ;
- owner et frontières respectés ;
- dépendances autorisées seulement ;
- documentation et code cohérents.

### B. Correction fonctionnelle

- scénario nominal ;
- cas limites ;
- erreurs ;
- modes dégradés ;
- recovery ;
- absence de comportement silencieux.

### C. Correction mathématique

- formules, domaines, unités et hypothèses ;
- propriétés et bornes ;
- référence indépendante ;
- stabilité numérique ;
- calibration et incertitude ;
- anti-lookahead.

### D. Qualité des tests

- suites obligatoires présentes ;
- couverture >= seuil ;
- mutation >= seuil applicable ;
- aucun test critique skipped ;
- absence de flakes ;
- non-régression historique.

### E. Qualité d'ingénierie

- complexité et tailles sous seuil ;
- aucune duplication significative ;
- contrats typés ;
- erreurs et config propres ;
- code mort/TODO critiques absents ;
- migration et rollback définis.

### F. Auditabilité

- reconstruction décisionnelle complète ;
- lineage et checksums ;
- reason/veto codes ;
- replay identique ;
- matrices requirement/test/evidence complètes.

### G. Sécurité et gouvernance

- secrets absents ;
- permissions minimales ;
- runtime correct ;
- levier/withdrawal interdits ;
- kill switch et approbation ;
- aucun contournement du RiskDecision.

### H. Performance et résilience

- budgets respectés ;
- charge et endurance ;
- mémoire bornée ;
- crash recovery ;
- reprise/reconciliation ;
- alerting adéquat.

## 3. Classification des constats

```text
BLOCKER  : violation sécurité, argent, audit, données, math, invariants ou corruption
MAJOR    : fonctionnalité/contrat/test essentiel incomplet ou résultat non fiable
MINOR    : défaut non bloquant mais réel, avec correction planifiée
INFO     : amélioration ou observation
```

## 4. Règles de verdict

### GO

- zéro BLOCKER ;
- zéro MAJOR ;
- suites obligatoires PASS ;
- couverture et mutation conformes ;
- replay PASS ;
- auditabilité PASS ;
- math validation PASS ;
- invariants PASS ;
- dette MINOR acceptée avec owner et échéance ;
- revue humaine signée.

### CONDITIONAL_GO

Autorisé uniquement pour un lot non critique et non promu vers live, avec :

- zéro BLOCKER ;
- zéro MAJOR touchant math, sécurité, audit, données, risque ou exécution ;
- conditions, owner et échéance explicites ;
- lot suivant bloqué tant que les conditions ne sont pas levées.

### NO_GO

Tout autre état. Le lot reste `PLANNED_LOCKED` ou `IMPLEMENTED_NOT_VALIDATED`.

## 5. Codes de NO-GO

```text
NO_GO_SCOPE
NO_GO_ARCHITECTURE
NO_GO_FUNCTIONAL
NO_GO_MATHEMATICAL_VALIDATION
NO_GO_TEST_QUALITY
NO_GO_COVERAGE
NO_GO_NON_REGRESSION
NO_GO_ENGINEERING_QUALITY
NO_GO_AUDITABILITY
NO_GO_SECURITY
NO_GO_PERFORMANCE
NO_GO_REPLAY
NO_GO_RECONCILIATION
NO_GO_INVARIANT_VIOLATION
```

## 6. Rapport final obligatoire

```text
lot_number
commit_sha
archive/checksum si applicable
auditor
scope_verdict
math_verdict
test_verdict
coverage_metrics
mutation_metrics
auditability_verdict
security_verdict
performance_verdict
replay_verdict
findings[]
accepted_debt[]
final_verdict
promotion_allowed
next_lot_locked
signatures/reviewers
```

## 7. Promotion

Le passage au lot suivant nécessite :

1. rapport final `GO` ;
2. commit/artefacts figés ;
3. CI verte sur le commit exact ;
4. preuve de replay ;
5. mise à jour registry/roadmap ;
6. validation humaine.

Une CI verte seule ne donne jamais GO.