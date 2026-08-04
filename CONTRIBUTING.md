# Contributing to Crypto Quant Bot V3.1-Ops

## Principe

Une contribution doit être petite, déterministe, auditée et fail-closed. La documentation,
les contrats, les tests, la configuration et le code doivent évoluer ensemble.

## Workflow obligatoire

1. Partir du dernier `main` vert.
2. Une branche par lot ou correctif cohérent.
3. Déclarer scope, non-objectifs, risques et rollback.
4. Ajouter les contrats et la spécification mathématique avant l’implémentation.
5. Ajouter les tests avant ou avec le code.
6. Exécuter toutes les gates locales applicables.
7. Ouvrir une PR avec preuves et checksums.
8. Ne fusionner qu’après CI verte et revue humaine.

## Règles de code

- une responsabilité par fonction/module ;
- aucun seuil métier caché ;
- aucun fallback permissif ;
- aucune conversion silencieuse d’une donnée invalide en zéro ;
- aucune duplication métier non qualifiée ;
- aucune dépendance directe à l’interne d’un autre domaine ;
- aucune barre future ou ouverte consommée ;
- aucune décision sans `reason_codes`, lineage et replay ;
- pas de refactoring opportuniste des lots historiques.

Seuils par défaut :

```text
fonction <= 50 lignes logiques
classe <= 400 lignes logiques
module <= 800 lignes logiques
complexité cyclomatique <= 10
imbrication <= 4
paramètres <= 7
```

Toute dérogation exige justification, owner, tests renforcés et échéance.

## Gates minimales

```bash
python -m compileall -q src scripts tests
ruff check <fichiers modifiés>
mypy src/crypto_quant_bot
python scripts/validate_architecture_boundaries.py
python scripts/validate_domain_architecture.py
python scripts/audit_roadmap_semantics.py
python scripts/validate_traceability_contract.py
python scripts/check_no_silent_numeric_coercion.py
python scripts/validate_roadmap_documentation.py
python scripts/validate_pre_lot26_readiness.py
pytest -q --cov --cov-branch --cov-report=json:coverage.json
python scripts/validate_global_coverage.py
```

Dépôt et nouveau code :

```text
line coverage globale runtime >= 90 %
branch coverage globale runtime >= 85 %
line coverage du code modifié >= 90 %
branch coverage du code modifié >= 85 %
module critique : line >= 95 %, branch >= 90 %
mutation score critique >= 80 %
```

## Commits

Un commit doit être atomique et expliquer le pourquoi. Interdits :

- changements massifs sans séparation ;
- artefacts générés sans provenance ;
- tests désactivés ;
- `skip` critique sans ticket ;
- écrasement d’une preuve historique ;
- renommage d’un artefact validé sans migration.

## Definition of Done

La PR contient zéro BLOCKER, zéro MAJOR, toutes les suites PASS, les rapports à jour,
un rollback explicite et un verdict humain.
