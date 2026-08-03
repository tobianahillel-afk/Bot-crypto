# Standard de spécification des lots

Ce document définit la structure obligatoire de toute spécification de lot du projet **Crypto Quant Bot V3.1-Ops**.

## Champs obligatoires

Chaque lot doit documenter :

1. **Identité** : numéro, titre, version, statut.
2. **Objectif** : résultat fonctionnel attendu et limites.
3. **Dépendances / entrées** : artefacts, schémas, registres et lots préalables.
4. **Exigences d’implémentation** : composants à créer ou modifier, règles déterministes, modes dégradés et erreurs.
5. **Artefacts attendus** : code, configuration, données d’audit, rapports, registres et documentation.
6. **Tests d’acceptation** : tests unitaires, intégration, replay, déterminisme, cas négatifs et preuves.
7. **Invariants de sécurité** : interdictions et comportement fail-closed.
8. **Gate de promotion** : conditions nécessaires avant le lot ou la version suivante.

## Conventions

- Les lots principaux utilisent uniquement une numérotation entière `Lot 0` à `Lot 177`.
- Les suffixes historiques `bis`, `ter`, `quater`, etc. restent des correctifs d’audit et ne redéfinissent pas la roadmap canonique.
- Un lot planifié est `PLANNED_LOCKED` jusqu’à son activation explicite.
- Un lot ne peut activer que les capabilities documentées dans sa version.
- Toute sortie doit inclure `schema_version`, provenance, timestamps pertinents et statut de validation.
- Tout état inconnu, incohérent ou non réconcilié est traité en mode fail-closed.
- La documentation est la source de vérité produit ; les registres machine-readable doivent être dérivés de la même structure.

## Invariants transverses

```text
Analyse ≠ signal
Signal ≠ trade intent
Trade intent ≠ order intent
Order intent ≠ ordre soumis
Ordre ≠ position
Position ≠ stratégie validée
Stratégie validée ≠ autorisation live
```

Un LLM peut reformuler ou expliquer. Il ne peut jamais créer, approuver, dimensionner ou router un ordre.
