# Economic Objective and Risk Utility Policy

Statut : `P0_6_NORMATIVE`  
Applicabilité : V5–V21, avec validation économique obligatoire en V6 et contraintes de risque obligatoires en V7.

## 1. Objectif

Le système cherche à maximiser la valeur économique nette démontrée, jamais le PnL brut isolé.

```text
maximize expected_net_utility
subject to hard_risk_constraints
```

Aucune métrique unique de rendement ne peut autoriser une promotion ou une augmentation d'exposition.

## 2. PnL net

Le calcul économique inclut au minimum :

```text
gross_trading_pnl
- maker_taker_fees
- spread_cost
- slippage
- market_impact
- funding
- borrow_and_settlement_costs
- adverse_selection
- latency_cost
- missed_fill_opportunity_cost
- infrastructure_and_data_cost_allocation
= expected_net_pnl
```

Toute composante inconnue est explicitement `UNKNOWN` ou utilise un fallback conservateur approuvé. Un coût absent ne devient jamais zéro silencieusement.

## 3. Fonction d'utilité

Chaque stratégie possède un `EconomicObjectiveAndUtilityPolicyV1` versionné contenant :

```text
objective_id
capital_base
currency
forecast_horizon
holding_horizon
expected_net_pnl
expected_shortfall
maximum_drawdown_limit
risk_of_ruin_limit
daily_loss_limit
volatility_target
liquidity_limit
capacity_limit
turnover_limit
concentration_limit
correlation_limit
model_uncertainty_penalty
data_uncertainty_penalty
operational_risk_penalty
utility_function
hard_constraints
soft_penalties
approval_id
config_checksum
```

La fonction peut être une utilité pénalisée, une croissance logarithmique bornée ou une autre forme approuvée. Elle doit être explicite, dimensionnellement cohérente et testable.

## 4. Contraintes dures

Les contraintes dures dominent toujours l'objectif économique :

- risque de ruine ;
- drawdown et perte journalière ;
- capital et exposition ;
- concentration et corrélation ;
- liquidité, capacité et participation ;
- limites de venue et d'instrument ;
- disponibilité et qualité des données ;
- incertitude excessive ;
- statut exchange ou runtime inconnu ;
- approbation expirée ;
- pause ou kill switch.

Une stratégie à EV positive reste non éligible si une contrainte dure échoue.

## 5. Comparaison et promotion

La comparaison champion/challenger utilise :

- distributions de PnL, pas uniquement moyenne ou Sharpe ;
- médiane, quantiles et expected shortfall ;
- drawdown, durée de récupération et risque de ruine ;
- stabilité par régime, instrument, période et venue ;
- capacité et dégradation avec taille ;
- sensibilité aux coûts et aux hypothèses de fill ;
- turnover et consommation de liquidité ;
- calibration des probabilités ;
- incertitude statistique et économique.

Les critères de promotion et de rejet sont définis avant le test final.

## 6. Prévention du sur-risque

Le système ne peut améliorer artificiellement son objectif en augmentant sans borne la taille, le levier ou la concentration. Le sizing final appartient au RiskDomain et respecte :

```text
approved_size <= min(
  volatility_limit,
  liquidity_limit,
  slippage_limit,
  capacity_limit,
  concentration_limit,
  drawdown_limit,
  capital_tier_limit
)
```

Dans le périmètre initial, le levier et les withdrawals restent interdits.

## 7. Incertitude

L'incertitude data, modèle, calibration, régime, coût et exécution est conservée séparément. Une incertitude élevée réduit l'utilité, réduit la taille ou bloque la décision ; elle ne peut jamais être interprétée comme un potentiel de rendement supplémentaire.

## 8. Attribution

Chaque résultat économique est attribué à :

```text
alpha
forecast
scenario
strategy
regime
instrument
venue
holding_horizon
execution_policy
cost_component
risk_constraint
```

Le résiduel inexpliqué est conservé. Une attribution ne réécrit jamais le ledger comptable.

## 9. Tests obligatoires

- identité comptable et conservation ;
- signe des coûts ;
- monotonie du coût avec taille lorsque attendue ;
- invariance aux unités et devises après conversion ;
- stress des frais, spread, slippage, impact et funding ;
- no-fill et partial-fill ;
- capacité et saturation ;
- drawdown et risque de ruine ;
- scénarios extrêmes et ruptures de régime ;
- comparaison à stratégies naïves et aléatoires ;
- walk-forward, OOS, placebo, bootstrap et Monte Carlo ;
- replay et non-régression.

## 10. Interdictions

```text
gross_pnl_only_promotion = FORBIDDEN
sharpe_only_promotion = FORBIDDEN
unknown_cost_as_zero = FORBIDDEN
autonomous_risk_limit_increase = FORBIDDEN
autonomous_live_scale_up = FORBIDDEN
```

## 11. Gate

`GO_ECONOMIC_VALIDATION` exige une valeur nette positive et robuste sous les hypothèses conservatrices approuvées, toutes les contraintes dures respectées et une revue humaine. Sinon :

```text
NO_GO_ECONOMIC_VALIDATION
```
