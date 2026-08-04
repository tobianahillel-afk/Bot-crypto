# Acceptance Criteria — Lot 26

## AC-26-01 — Closed bars only

Aucun état provenant d’une barre ouverte ou incomplète n’est consommé.

## AC-26-02 — Temporal eligibility

Pour chaque source :

```text
bar_close_time <= available_at <= decision_time
```

## AC-26-03 — As-of backward join

Le 15m sélectionné est le plus récent admissible. Aucun état futur n’est choisi.

## AC-26-04 — Continuous flow semantics

Une nouvelle sortie est évaluée à chaque 5m fermé. Le dernier 15m fermé peut être réutilisé pour
plusieurs 5m jusqu’à disponibilité du suivant.

## AC-26-05 — No automatic higher-timeframe veto

Une divergence 5m/15m est publiée, expliquée et n’annule pas automatiquement le contexte local.

## AC-26-06 — Exact mathematics

Les six compatibilités, poids, couverture, formule, seuils, tolérances et classifications suivent
la spécification et la config versionnée.

## AC-26-07 — Missing data

`UNKNOWN`, enum absent, valeur non finie ou couverture insuffisante ne devient jamais zéro ni accord.

## AC-26-08 — Determinism

Deux replays identiques produisent mêmes sorties, reason codes et checksums.

## AC-26-09 — Schemas

Les trois JSON schemas sont respectés et les champs supplémentaires sont rejetés.

## AC-26-10 — Anti-lookahead

Fixtures obligatoires :

- 15m ouverte ;
- 15m future ;
- révision disponible après `decision_time` ;
- timestamp naïf/non UTC ;
- ordre inversé ;
- doublon ;
- gap temporel.

## AC-26-11 — Mathematical properties

Bornes, symétrie, identité, oppositions, permutation, couverture monotone et null propagation sont
testées par oracles et property-based testing.

## AC-26-12 — Quality gates

```text
line >= 90 %
branch >= 85 %
critical line >= 95 %
critical branch >= 90 %
mutation >= 80 %
```

Aucun test critique skipped/xfailed.

## AC-26-13 — Forbidden capabilities

Aucun champ ou comportement de signal, BUY/SELL, quantity, order, position, paper ou live.

## AC-26-14 — Audit evidence

Rapport, coverage, mutation, requirement-test matrix, fixtures checksums, config checksum,
replay evidence et verdict humain sont présents.

## AC-26-15 — Game Theory boundary

Aucune inférence de stops/participants n’est ajoutée au Lot 26. Le futur domaine V4 reste propriétaire.

## Verdict

Un seul échec → `NO_GO_LOT26`. Le Lot 27 reste verrouillé.
