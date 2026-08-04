# Standard de spécification des lots

Chaque lot doit être suffisamment précis pour qu'un agent puisse l'implémenter sans inventer une frontière, un contrat, une formule, une tolérance, une permission ou un critère de validation.

Ce standard est complété par :

- `TEST_STRATEGY_COVERAGE_AND_QUALITY_GATES.md` ;
- `MATHEMATICAL_MODELING_AND_NUMERICAL_VALIDATION_STANDARD.md` ;
- `DEVELOPMENT_ENGINEERING_STANDARD.md` ;
- `DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md` ;
- `LOT_FINAL_AUDIT_AND_GO_NO_GO_GATE.md`.

## Sections obligatoires de chaque lot

1. Identité, version, statut et runtime maximal.
2. Objectif falsifiable, responsabilité exacte et composant propriétaire.
3. Périmètre, non-objectifs et capabilities interdites.
4. Contrats d'entrée : types, versions, unités, fraîcheur, provenance et disponibilité temporelle.
5. Contrats de sortie : schémas, états, reason codes, incertitude, lineage et `DecisionEvidenceEnvelopeV1`.
6. Préconditions et gates d'entrée.
7. Séquence de traitement ordonnée, avec décisions intermédiaires.
8. Spécification mathématique : domaines, formules, hypothèses, unités, bornes et tolérances.
9. Règles métier et algorithmiques.
10. Machine d'état et transitions, lorsque applicable.
11. Modes de défaillance, edge cases, fault injection et comportement fail-closed.
12. Fichiers, modules, classes, fonctions publiques, scripts et artefacts attendus.
13. Configuration versionnée et valeurs conservatrices.
14. Observabilité : métriques, logs, traces, reason codes, alertes et conséquences.
15. Auditabilité : identifiants, checksums, DAG de lineage, replay et explication structurée.
16. Suites de tests obligatoires et mapping exigences → tests.
17. Seuils de coverage, branch coverage et mutation applicables.
18. Exigences de performance, complexité et ressources.
19. Migration, compatibilité, rollback et recovery.
20. Risques connus, limites et dette acceptée.
21. Définition de terminé.
22. Audit final et gate GO/NO-GO.
23. Gate de promotion et verrouillage du lot suivant.

## Exigences minimales des tests

Chaque lot déclare explicitement les suites applicables parmi :

```text
unit
mathematical_logic
property_based
contract_schema
integration
end_to_end_replay
non_regression
negative_failure_injection
security_permission
performance_resource
concurrency_idempotency
anti_lookahead_data
```

Seuils généraux :

```text
line coverage globale runtime >= 90 %
branch coverage globale runtime >= 85 %
line coverage ajouté/modifié >= 90 %
branch coverage ajouté/modifié >= 85 %
modules critiques : line >= 95 %, branch >= 90 %
mutation score critique >= 80 %
```

La couverture ne remplace pas les assertions métier, les tests de propriétés ni la validation indépendante.

## Convention de fichiers

```text
src/crypto_quant_bot/<domain>/<feature>.py
src/crypto_quant_bot/<domain>/<feature>_models.py
scripts/run_lot<N>_<feature>.py
scripts/validate_lot<N>.py
tests/unit/test_lot<N>_<feature>.py
tests/math/test_lot<N>_<feature>_properties.py
tests/contracts/test_lot<N>_<feature>_contracts.py
tests/integration/test_lot<N>_<feature>_integration.py
tests/regression/test_lot<N>_<feature>_regression.py
tests/failure/test_lot<N>_<feature>_failures.py
data/audit/<feature>_lot<N>.json
reports/lot_<N>_<feature>_report.md
reports/lot_<N>_test_report.md
reports/lot_<N>_coverage_report.md
reports/lot_<N>_mathematical_validation_report.md
reports/lot_<N>_final_audit_report.md
docs/LOT_<N>_<FEATURE>.md
docs/ACCEPTANCE_CRITERIA_LOT_<N>.md
```

Les lots de clôture ajoutent validate_all, required chain, exact replay, traceability manifest et closure manifest.

## Definition of Done minimale

Un lot n'est terminé que si :

- implémentation conforme à la spécification ;
- aucune duplication significative ni complexité injustifiée ;
- toutes les suites obligatoires PASS ;
- coverage/mutation conformes ;
- validation mathématique PASS ;
- auditabilité et replay PASS ;
- non-régression PASS ;
- sécurité et permissions PASS ;
- rapports et artefacts complets ;
- zéro BLOCKER et zéro MAJOR ;
- verdict final `GO` signé/revu.

## Interdictions

Aucun lot planifié ne peut être activé par documentation seule. Aucun seuil caché, aucune permission implicite, aucun fallback permissif, aucun accès direct aux internals d'un autre domaine, aucune formule sans domaine et tolérance, aucune décision sans preuve, aucun test critique skipped, aucune validation fondée uniquement sur le coverage ou une CI verte.