# Changelog

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
