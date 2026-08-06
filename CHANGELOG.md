# Changelog

## 0.28.0 — Lot 28 Explanation Core & Why-Not-Trade Layer

- couche d’explication structurée, déterministe et strictement offline au-dessus des preuves certifiées Lots 26–27 ;
- 14 déclarations versionnées séparant faits, features, inférences, hypothèses, preuves, contradictions, incertitudes, règles, vetos, non-applicable et conséquence finale ;
- 3 raisons why-not-trade ordonnées et dédupliquées : `WNT_CONTEXT_MIXED`, `WNT_MTF_DIVERGENCE`, `WNT_PERMISSIONS_DISABLED` ;
- chaque déclaration est liée à un checksum d’artefact exact et à un JSON pointer vérifié ;
- replay déterministe `MATCH`, checksum de sortie `e5e23e67e5d033d449b4ca46b6cdae2f6a7aad9649266ce3ad21f42de1d16e02` ;
- 35 tests ciblés, couverture lignes 99.42% et branches 98.39% ;
- mutation critique 1 620/1 830, score 88.52% PASS ;
- 930 tests globaux PASS, trois répétitions Lot 28 PASS, Ruff, mypy, Bandit, pip-audit, architecture, traçabilité, roadmap, lifecycle et qualité institutionnelle PASS ;
- aucune prévision, probabilité, recommandation, approbation risque, permission de trading ou exécution activée.

## 0.27.0 — Lot 27 Global Market Context Aggregator

- agrégation descriptive déterministe des sorties validées des Lots 22–26 ;
- poids fixes publiés et aucune renormalisation silencieuse des sources absentes ;
- qualité, fraîcheur, checksum, état, catégorie et contribution conservés par source ;
- support `TRENDING`, `RANGE`, `MIXED`, `CONFLICT`, alternatives et conflits explicites ;
- oracle global `GLOBAL_CONTEXT_MIXED`, score `0.5646`, couverture `1.0` ;
- 57 tests ciblés, couverture lignes 97.18% et branches 91.07% ;
- mutation critique 803/948, score 84.70% PASS ;
- Ruff, mypy, Bandit, pip-audit, architecture, traçabilité, régression et anti-flake PASS ;
- aucune prévision, probabilité, décision, permission de trading ou exécution activée.

## 0.26.0 — Lot 26 Multi-Timeframe Alignment

- moteur descriptif `timebar-5m → timebar-15m` avec jointure `ASOF_BACKWARD` ;
- contrats immuables et schémas JSON fermés ;
- couverture pondérée, agreement, divergence, cohérence et incertitude descriptive ;
- lineage, checksums, `DecisionEvidenceEnvelopeV1`, replay et détection de falsification ;
- 108 tests Lot 26, couverture lignes 98.73% et branches 97.12% ;
- mutation critique 82.43% sur 552 mutants ;
- audit dépôt 832 tests, couverture lignes 94.63% et branches 86.77% ;
- Ruff, mypy, Bandit, pip-audit, architecture, traçabilité et anti-flake PASS ;
- aucune prévision, probabilité, décision, permission de trading ou exécution activée.

## 0.25.1-p0

- CI institutionnelle ;
- validation numérique fail-closed ;
- paramètres mathématiques versionnés ;
- coverage, mypy, Ruff, Bandit, dependency audit et mutation testing.
