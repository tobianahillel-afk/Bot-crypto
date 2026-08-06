# V7 / V9 — Portfolio Risk, Sizing, Reservation and Exit Normative Addendum

Statut : `PLANNED_LOCKED_NORMATIVE_ADDENDUM`  
Document parent obligatoire : `docs/CANONICAL_PORTFOLIO_RISK_SIZING_AND_EXIT_STANDARD.md`

## 1. But

Cet addendum empêche les Lots V7 et V9 d'implémenter des variantes incompatibles du snapshot portefeuille, du sizing, des réservations ou des sorties.

La norme parent est obligatoire pour toute décision qui peut :

```text
OPEN
ADD
REDUCE
EXIT
TIME_EXIT
EMERGENCY_EXIT
```

Aucun lot ne peut déclarer `PASS` en se limitant à une formule de taille isolée qui ignore les positions, ordres, intents, réservations ou risques déjà engagés.

## 2. Contrats obligatoires avant le Lot 74

Les contrats suivants doivent être présents, versionnés et validés avant l'implémentation du Risk Limits Framework :

```text
PortfolioDecisionSnapshotV1
RiskLimitSetV1
SizingDecisionV1
RiskDecisionV1
RiskReservationRequestV1
RiskReservationV1
ExitPolicyV1
AddPolicyV1
```

Schémas déjà préparés par cet addendum :

- `contracts/schemas/portfolio_decision_snapshot_v1.schema.json` ;
- `contracts/schemas/risk_reservation_v1.schema.json`.

Tout autre contrat doit référencer ces schémas au lieu de dupliquer leurs champs sous un autre nom.

## 3. Lot 74 — Risk Limits Framework

Le Lot 74 doit :

1. définir les limites `global/account/strategy/instrument/order/time-window` ;
2. résoudre la limite effective par le minimum ;
3. publier les caps dans une configuration versionnée ;
4. distinguer hard limits, soft limits et conséquence ;
5. traiter toute limite inconnue comme `approved_size=0` ;
6. vérifier le risque déjà engagé et les réservations actives ;
7. interdire qu'une limite plus permissive masque une limite plus restrictive.

Tests supplémentaires obligatoires :

- permutation de l'ordre des limites sans changement du résultat ;
- conflit entre limites résolu par la plus restrictive ;
- limite absente ou stale => zéro exposition nouvelle ;
- limite consommée par une réservation concurrente => recalcul obligatoire.

## 4. Lot 75 — Volatility- and Confidence-Adjusted Sizing

Le Lot 75 doit implémenter les équations de :

```text
R_trade(q)
B_base
B_effective
q_trade_risk
q_incremental_risk
q_portfolio_heat
q_capital
q_concentration
q_correlation
q_approved
```

La taille commence toujours à zéro. Elle ne peut augmenter que par satisfaction explicite de tous les caps.

Tests supplémentaires obligatoires :

- monotonie de la taille sous hausse de volatilité ;
- monotonie sous baisse de budget ;
- toute baisse de santé modèle/donnée/régime ne peut augmenter la taille ;
- coûts non linéaires résolus par un solveur déterministe ;
- revalidation complète après arrondi instrument ;
- Kelly brut et levier implicite détectés comme violation.

## 5. Lot 76 — Liquidity- and Slippage-Adjusted Sizing

Le Lot 76 doit calculer :

```text
q_participation
q_depth
q_impact
q_adverse
q_liquidity
```

Il doit inclure spread, profondeur, participation, volatilité, latence, temporary impact, permanent impact proxy et adverse selection.

Tests supplémentaires obligatoires :

- coûts monotones avec la taille ;
- carnet insuffisant => `NO_FILL` ou `PARTIAL_FILL_CAP` ;
- aucune extrapolation de prix silencieuse ;
- liquidation urgente et sortie normale utilisent des politiques différentes ;
- nouvelle entrée bloquée lorsque l'exit capacity n'est pas démontrée.

## 6. Lot 77 — Drawdown, Tail Risk and Risk of Ruin

Le Lot 77 doit implémenter :

```text
PeakNAV_t
Drawdown_t
m_drawdown
stress loss
ExpectedShortfall_alpha lorsque validé
risk-of-ruin stress
```

Les points `(d_k, m_k)` sont versionnés, monotones et audités. Le dernier palier produit `m_drawdown=0` et au moins `PAUSE`.

Tests supplémentaires obligatoires :

- valeurs exactes aux frontières ;
- interpolation déterministe ;
- aucune réactivation automatique après palier critique ;
- retrait des données ES => fallback stress conservateur ;
- mutation d'un palier ou d'une action critique détectée.

## 7. Lot 78 — Correlation, Concentration and Portfolio Pre-Checks

Le Lot 78 doit calculer :

```text
MaxWeight
HHI
GrossExposureRatio
NetExposureRatio
sigma_P
MRC_i
DeltaSigma(q)
DeltaR(q)
PortfolioHeat_before
PortfolioHeat_after
```

La matrice de covariance doit être robuste, versionnée et validée. Une corrélation inconnue utilise un fallback conservateur, jamais une diversification supposée.

Tests supplémentaires obligatoires :

- nouvelle position augmente la heat attendue ;
- corrélation manquante réduit la capacité ;
- matrice non définie positive => fallback ou blocage ;
- ajout d'un actif parfaitement corrélé n'est pas considéré diversifiant ;
- concentration BTC/EUR limitée même avec un seul instrument actif.

## 8. Lot 79 — Risk Approval Gate and Kill-Switch

Le Lot 79 doit consommer le snapshot exact et signer :

```text
decision_hash = hash(
    intent_hash,
    snapshot_id,
    snapshot_sequence,
    risk_limit_set_id,
    model_state_ids,
    market_state_ids,
    approved_size,
    approved_risk,
    expiry
)
```

Une modification d'un seul élément invalide l'approbation.

Le Lot 79 doit émettre `RiskReservationRequestV1`. Une décision `APPROVE` sans réservation obtenue ne peut jamais devenir `OrderIntent` augmentant le risque.

Tests supplémentaires obligatoires :

- bypass impossible ;
- intent muté => hash invalide ;
- snapshot modifié => nouvelle décision obligatoire ;
- kill switch bloque immédiatement les nouveaux intents ;
- action reduce-only correctement reconnue ;
- `AVERAGING_DOWN_FORBIDDEN` force `approved_size=0`.

## 9. Lot 80 — V7 Closure

Le Lot 80 ne peut conclure `GO` que si :

- toutes les équations ont des oracles indépendants ;
- les schémas sont validés ;
- la concurrence et l'idempotence sont testées ;
- la matrice de sorties possède une couverture tabulaire complète ;
- l'interdiction de moyenne à la baisse résiste au mutation testing ;
- run1/run2 produisent les mêmes checksums ;
- V7 reste `RISK_SIMULATION_ONLY`.

## 10. Lot 88 — Portfolio Core and State Model

Le Lot 88 doit rendre `PortfolioDecisionSnapshotV1` reconstructible depuis le ledger.

Le snapshot doit contenir exactement :

```text
portfolio_state_id
position_state_ids
open_order_state_ids
pending_intent_state_ids
reservation_ids
cash_total
cash_reserved
cash_available
valuation_time
ledger_watermark
snapshot_sequence
state_hash
```

Tests supplémentaires obligatoires :

- rebuild depuis ledger = snapshot ;
- duplicate event idempotent ;
- watermark incohérent => snapshot invalide ;
- balance ou position inconnue => portefeuille gelé ;
- capital réservé inclus exactement une fois.

## 11. Lot 89 — Cash, Collateral, Margin and Buying Power

Le Lot 89 doit vérifier :

```text
cash_total = cash_available + cash_reserved + unsettled_or_buffered_cash
```

Pour le scope BTC/EUR spot :

```text
leverage=FORBIDDEN
margin=FORBIDDEN
negative_buying_power=FORBIDDEN
```

Une réservation ne peut jamais rendre `cash_available < 0`.

## 12. Lot 90 — Position Lifecycle

Le Lot 90 doit distinguer :

- quantité économique réconciliée ;
- quantité venue ;
- quantité attribuée par stratégie ;
- quantité protégée ;
- quantité encore réservée mais non fillée.

Toute augmentation est un nouvel intent, sauf reliquat d'un ordre partiellement exécuté encore couvert par la même réservation.

## 13. Lot 93 — Exposure, Correlation, Concentration and Portfolio Heat

Le Lot 93 publie l'état autoritatif nécessaire à V7 :

```text
gross_exposure
net_exposure
instrument_weights
HHI
covariance_state
marginal_risk_contributions
portfolio_risk
reserved_risk
portfolio_heat
drawdown
```

Il ne produit pas lui-même une permission de trading.

## 14. Réservations atomiques V7 → V9 → V15

### Phase V7

Un ledger simulé vérifie la sémantique et les races de concurrence.

### Phase V8

Le paper runtime vérifie réservations, expirations, partial fills et libérations.

### Phase V9

Le `PortfolioDomain` devient propriétaire de l'état économique et du ledger de réservations.

### Phase V15

L'OMS/EMS exige un token actif pour tout ordre augmentant le risque.

Aucune phase ne peut redéfinir le cycle :

```text
PROPOSED → RESERVED → CONSUMED | RELEASED | EXPIRED | CANCELLED
```

## 15. Matrice de sorties obligatoire

La matrice du standard parent est normative. Chaque ligne doit devenir un cas de test. En particulier :

```text
régime légèrement dégradé => HOLD ou REDUCE selon policy versionnée
régime incompatible => EXIT
signal expiré => TIME_EXIT
donnée stale => PAUSE_NEW_RISK + protection maintenue si connue
liquidité critique => BLOCK_ADD + sortie contrôlée
drawdown critique => approved_size=0 + PAUSE ou KILL_SWITCH
position non réconciliée => aucune augmentation
```

Aucun pourcentage de réduction ne peut être inventé dans le runtime. Il provient d'une table versionnée, validée en V6 et liée à `ExitPolicyV1`.

## 16. Interdiction de moyenne à la baisse

Toute augmentation dans la même direction exige une nouvelle décision et une nouvelle réservation.

```text
NetLiquidationPnL <= 0
=> ADD forbidden
=> approved_size=0
=> reason_code=AVERAGING_DOWN_FORBIDDEN
```

Les exceptions implicites sont interdites. Le seul cas qui n'est pas un nouvel `ADD` est le reliquat d'un ordre partiellement exécuté encore couvert par le même intent, la même décision et la même réservation valide.

Un pyramiding gagnant reste soumis à tous les caps et ne peut jamais élargir le stop ou augmenter la perte maximale approuvée sans un nouveau budget séparé.

## 17. Gate documentaire

Avant de déclarer un Lot V7 ou V9 `IMPLEMENTATION_READY`, le rapport d'entrée doit confirmer :

```text
canonical_standard_referenced=true
snapshot_schema_validated=true
reservation_schema_validated=true
formula_oracles_defined=true
exit_matrix_test_plan_complete=true
atomic_reservation_test_plan_complete=true
averaging_down_mutation_tests_defined=true
trading_permissions_unchanged=true
```

Toute valeur `false` produit `NO_GO`.
