# Standard de spécification des lots

Chaque lot doit être suffisamment précis pour qu’un agent puisse l’implémenter sans inventer une frontière, un contrat ou une permission.

## Sections obligatoires

1. Identité, version, statut, runtime maximal.
2. Responsabilité exacte et composant propriétaire.
3. Contrats d’entrée avec versions, fraîcheur et provenance.
4. Contrats de sortie avec états UNKNOWN/BLOCKED.
5. Séquence de traitement ordonnée.
6. Règles métier/algorithmiques et formules/politiques applicables.
7. Modes de défaillance, edge cases et comportement fail-closed.
8. Fichiers/modules/scripts/artefacts attendus.
9. Observabilité : métriques, logs, traces, reason codes.
10. Tests unitaires, intégration, négatifs, replay, anti-lookahead, sécurité.
11. Non-objectifs et capabilities interdites.
12. Définition de terminé et gate de promotion.

## Convention de fichiers

```text
src/crypto_quant_bot/<domain>/<feature>.py
src/crypto_quant_bot/<domain>/<feature>_models.py
scripts/run_lot<N>_<feature>.py
scripts/validate_lot<N>.py
tests/test_lot<N>_<feature>.py
data/audit/<feature>_lot<N>.json
reports/lot_<N>_<feature>_report.md
docs/LOT_<N>_<FEATURE>.md
docs/ACCEPTANCE_CRITERIA_LOT_<N>.md
```

Les lots de clôture ajoutent validate_all, required chain, exact replay et closure manifest.

## Interdictions

Aucun lot planifié ne peut être activé par documentation seule. Aucun seuil caché, aucune permission implicite, aucun fallback permissif, aucun accès direct aux internals d’un autre domaine.
