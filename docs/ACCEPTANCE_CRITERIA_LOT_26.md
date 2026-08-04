# Acceptance Criteria — Lot 26

## AC-26-01 — Closed confirmed bars only

Aucun état confirmé provenant d'une barre ouverte ou incomplète n'est consommé. Les `open_bars` peuvent uniquement exister comme observations provisoires non consommables.

## AC-26-02 — Temporal eligibility

```text
bar_close_time <= available_at <= decision_time
```

Toute révision possède son propre `available_at`.

## AC-26-03 — ASOF_BACKWARD

L'état supérieur sélectionné est le plus récent admissible selon les règles de tie-break versionnées. Aucun état futur n'est choisi.

## AC-26-04 — Initial scale profile

Le profil v1 active exactement :

```text
timebar-5m → timebar-15m
```

Le moteur accepte une relation d'échelle fournie par contrat/configuration et ne duplique pas une fonction métier spécifique par paire.

## AC-26-05 — Extensibility without premature activation

Les autres échelles enregistrées restent `enabled_in_lot26=false`. Leur présence ne modifie ni score, ni checksum, ni résultat v1.

## AC-26-06 — Continuous flow semantics

Une sortie est évaluée à chaque 5m fermé. Le dernier 15m fermé peut être réutilisé jusqu'à disponibilité du suivant. Le Lot 26 ne consomme pas encore `ContinuousMarketStateV1`.

## AC-26-07 — No automatic higher-scale veto

Une divergence 5m/15m est publiée et n'annule pas automatiquement le contexte local.

## AC-26-08 — No naive voting

Aucun vote majoritaire entre timeframes, résolutions ou horizons n'existe. Toute future agrégation multi-arêtes nécessitera un contrat et une version distincts.

## AC-26-09 — Temporal dimension separation

Les contrats et tests distinguent explicitement :

```text
data_resolution
feature_lookback
forecast_horizon
decision_clock
signal_ttl
holding_horizon
```

Le timeframe ne permet pas de déduire un horizon de prévision ou de détention.

## AC-26-10 — Exact mathematics

Les six compatibilités, poids, couverture, formule, seuils, tolérances et classifications suivent la spécification et la configuration versionnée.

## AC-26-11 — Missing and invalid data

`UNKNOWN`, enum absent, valeur non finie ou couverture insuffisante ne devient jamais zéro ni accord.

## AC-26-12 — Determinism

Deux replays identiques produisent mêmes sorties, reason codes et checksums.

## AC-26-13 — Closed schemas

Tous les JSON schemas sont des objets fermés, possèdent une liste `required` et rejettent les champs supplémentaires.

## AC-26-14 — Anti-lookahead fixtures

- 15m ouverte ;
- 15m future ;
- révision disponible après `decision_time` ;
- timestamp naïf/non UTC ;
- ordre inversé ;
- doublon ;
- gap temporel ;
- égalité `available_at == decision_time` ;
- relation d'échelle non autorisée.

## AC-26-15 — Mathematical properties

Bornes, symétrie lorsque définie, identité, oppositions, permutation, couverture monotone, null propagation et invariance aux échelles désactivées sont testées.

## AC-26-16 — Decision clock

Seul `CLOSED_LOCAL_BAR` est activé. Les triggers événementiels futurs sont enregistrés mais désactivés.

## AC-26-17 — Forecast boundary

Aucun `MultiHorizonForecastV1`, expected return, probability, target-hit, stop-hit ou forecast distribution n'est produit. Le registre des horizons reste `PLANNED_LOCKED_NOT_IMPLEMENTED`.

## AC-26-18 — Game Theory boundary

Aucun participant, payoff, stop zone, take-profit, break-even, liquidation, sweep ou Game Theory n'est calculé dans le Lot 26. V4 reste propriétaire.

## AC-26-19 — Protective-order boundary

Aucun stop order, take-profit order, trailing, bracket, OCO ou `ProtectiveOrderPlanV1` n'est implémenté.

## AC-26-20 — Quality gates

```text
line >= 90 %
branch >= 85 %
critical line >= 95 %
critical branch >= 90 %
mutation >= 80 %
```

Aucun test critique skipped/xfailed.

## AC-26-21 — Forbidden capabilities

Aucun champ/comportement de BUY/SELL, quantity, order, position, paper, live ou external connectivity.

## AC-26-22 — Audit evidence

Rapport, coverage, mutation, requirement-test matrix, fixtures checksums, configs et registres checksums, replay evidence et verdict humain sont présents.

## AC-26-23 — Historical immutability

Aucun fichier source, critère, rapport ou artefact normatif des Lots 0–25 n'est modifié.

## Verdict

Un seul échec → `NO_GO_LOT26`. Le Lot 27 reste verrouillé.
