# Canonical Portfolio Risk, Sizing, Reservation and Exit Standard

Statut : `PLANNED_LOCKED_NORMATIVE_STANDARD`  
Applicabilité : V5–V9, V13–V18 et toute capability future capable de créer, augmenter, réduire ou clôturer une exposition.  
Owners : `RiskDomain` pour le calcul et la décision de risque ; `PortfolioDomain` pour l'état économique et les réservations de capital ; `StrategyDomain` pour l'hypothèse d'entrée/sortie ; `OMS/EMS Domain` pour les ordres et fills.  
Runtime actuel : aucune capability de décision ou d'exécution n'est activée par ce document.

## 1. Finalité

Cette norme rend obligatoires et directement implémentables :

1. le snapshot exact consommé par chaque décision ;
2. les équations canoniques de risque et de sizing ;
3. le calcul du risque déjà engagé et du risque incrémental ;
4. la réservation atomique du capital et du budget de risque ;
5. la matrice complète des sorties et réductions ;
6. l'interdiction explicite de la moyenne à la baisse et de toute augmentation implicite d'une position perdante ;
7. les responsabilités entre stratégie, risque, portefeuille et OMS/EMS ;
8. les tests, reason codes et preuves d'audit nécessaires avant V7 et V9.

Une opportunité de marché ne constitue jamais une autorisation de prendre du risque.

```text
forecast
→ scenario
→ signal
→ TradeIntent
→ PortfolioDecisionSnapshotV1
→ RiskDecisionV1
→ RiskReservationV1
→ OrderIntent
→ order/fill
→ reconciliation
→ PortfolioStateV1
```

## 2. Principes non négociables

```text
unknown_state => no_new_risk
unreconciled_portfolio => no_new_risk
missing_reservation => no_order_submission
veto => approved_size=0
risk_reducing_action may remain allowed when new risk is blocked
raw_kelly => forbidden
autonomous_scale_up => forbidden
implicit_averaging_down => forbidden
silent_stop_widening => forbidden
```

La conséquence finale respecte toujours :

```text
KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE
```

Les politiques et seuils sont versionnés. Le runtime peut recalculer les états à partir du marché, mais ne peut pas modifier silencieusement les équations, seuils, modèles, permissions ou politiques approuvés.

## 3. Snapshot décisionnel canonique

Chaque décision d'ouverture, d'ajout, de réduction ou de clôture consomme exactement un `PortfolioDecisionSnapshotV1` immuable.

### 3.1 Champs obligatoires

```text
schema_version
snapshot_id
snapshot_sequence
ledger_watermark
portfolio_state_id
portfolio_state_hash
position_state_ids[]
open_order_state_ids[]
pending_intent_state_ids[]
reservation_ids[]
account_state_id
risk_limit_set_id
market_state_ids[]
model_state_ids[]
strategy_state_id
valuation_time
decision_time
available_at
generated_at
base_currency
nav
cash_total
cash_reserved
cash_available
gross_exposure
net_exposure
portfolio_risk
reserved_risk
portfolio_heat
drawdown
reconciliation_state
data_quality_state
runtime_mode
validation_state
lineage_id
state_hash
```

Les tableaux d'identifiants sont triés canoniquement, sans doublon. Le `state_hash` couvre l'intégralité du contenu normalisé.

### 3.2 Cohérence temporelle

Les contraintes suivantes sont obligatoires :

```text
valuation_time <= decision_time
available_at <= decision_time
generated_at >= available_at
all consumed states have available_at <= decision_time
snapshot age <= configured_max_snapshot_age
ledger_watermark is identical for cash, positions, orders and reservations
```

Une position, un ordre, un intent ou une réservation provenant d'un watermark différent interdit la création de nouveau risque.

### 3.3 Cohérence économique

Le snapshot doit vérifier, avec tolérances versionnées :

```text
cash_total = cash_available + cash_reserved + unsettled_or_buffered_cash
nav = reconciled_cash_value + reconciled_position_value - liabilities
open_order_reserved_capital is included exactly once
pending_intent_reserved_risk is included exactly once
position risk and protective orders are not double-counted
```

`UNKNOWN`, `DIVERGENT`, `FROZEN` ou un checksum invalide produit :

```text
new_risk_allowed=false
approved_size=0
```

Les actions strictement réductrices de risque peuvent rester autorisées uniquement via une politique de secours pré-approuvée et un état de position suffisamment fiable.

## 4. Notation mathématique

Pour une décision prise au temps `t` :

```text
E_t        = NAV réconciliée après haircuts et passifs
C_avail    = cash réellement disponible après réservations et buffers
q          = quantité candidate
P_e        = prix d'entrée stressé
P_s        = prix de stop ou niveau d'invalidation exécutable estimé
m          = multiplicateur de contrat ; m=1 pour BTC/EUR spot
S          = ensemble versionné de scénarios de stress
P          = portefeuille économique actuel
x(q)       = nouvelle exposition candidate de quantité q
R(P)       = mesure de risque canonique du portefeuille
DeltaR(q)  = risque incrémental de x(q)
```

Toutes les valeurs monétaires sont converties dans la devise de base avec un taux frais, versionné et temporellement admissible. Un taux FX stale produit `BLOCK_TRADING`.

## 5. Risque unitaire et risque par trade

### 5.1 Perte stressée unitaire

Pour une position longue :

```text
unit_loss_long(q) =
    max(0, P_e(q) - P_s(q)) * m
    + entry_fee_per_unit(q)
    + exit_fee_per_unit(q)
    + entry_slippage_per_unit(q)
    + exit_slippage_per_unit(q)
    + gap_buffer_per_unit(q)
    + funding_or_carry_per_unit(q)
```

Pour une position courte future, uniquement si son runtime l'autorise :

```text
unit_loss_short(q) =
    max(0, P_s(q) - P_e(q)) * m
    + entry_fee_per_unit(q)
    + exit_fee_per_unit(q)
    + entry_slippage_per_unit(q)
    + exit_slippage_per_unit(q)
    + gap_buffer_per_unit(q)
    + funding_or_carry_per_unit(q)
```

Dans le périmètre initial BTC/EUR spot, `short`, `margin` et `leverage` restent interdits.

### 5.2 Risque du trade

```text
R_trade(q) = q * unit_loss(q)
```

Si les frais, le slippage ou l'impact dépendent de `q`, `R_trade(q)` est résolu numériquement par une méthode déterministe et monotone ; une division linéaire simplifiée est interdite lorsque ses hypothèses ne sont pas démontrées.

### 5.3 Budget de risque effectif

Les limites hiérarchiques sont calculées séparément :

```text
B_base = min(
    B_global,
    B_account,
    B_strategy,
    B_instrument,
    B_order,
    B_time_window
)
```

Puis :

```text
B_effective = B_base
              * m_drawdown
              * m_model_health
              * m_data_quality
              * m_regime
```

avec chaque multiplicateur dans `[0,1]`. Aucun multiplicateur ne peut augmenter le budget au-dessus de `B_base`.

Une donnée ou limite inconnue impose le multiplicateur `0` ou un blocage plus sévère selon la matrice de veto.

## 6. Risque du portefeuille et portfolio heat

### 6.1 Mesure canonique

Le portefeuille économique inclut :

```text
positions réconciliées
+ ordres ouverts pouvant augmenter l'exposition
+ intents approuvés avec réservations actives
- ordres strictement reduce-only correctement liés
```

Pour chaque scénario `s` :

```text
Loss_s(P) = max(0, -DeltaValue_s(P)) + Costs_s(P)
```

La mesure canonique est :

```text
R(P) = max(
    max_{s in S}(Loss_s(P)),
    ExpectedShortfall_alpha(P)
)
```

`ExpectedShortfall_alpha` n'est utilisable que si son estimation est statistiquement validée. Sinon, la composante correspondante reste `UNKNOWN` et le moteur utilise le stress loss conservateur.

### 6.2 Portfolio heat

```text
PortfolioHeat(P) = R(P) / E_t
```

Si aucun modèle de dépendance validé n'est disponible, le fallback conservateur est :

```text
R_fallback(P) =
    sum(stressed_loss_open_positions)
    + sum(stressed_loss_active_reservations)
```

Le fallback ne doit jamais produire moins de risque qu'une hypothèse d'indépendance non démontrée.

### 6.3 Capacité de risque restante

```text
RiskCapacityRemaining = max(0, HeatLimit * E_t - R(P))
```

Une nouvelle exposition doit satisfaire simultanément :

```text
R_trade(q) <= B_effective
DeltaR(q) <= RiskCapacityRemaining
PortfolioHeat(P union x(q)) <= HeatLimit
```

## 7. Risque incrémental

Le risque incrémental n'est pas égal au risque isolé du nouveau trade.

```text
DeltaR(q) = max(0, R(P union x(q)) - R(P))
```

Cette définition capture :

- le risque déjà pris ;
- les réservations actives ;
- les corrélations ;
- la concentration ;
- les coûts et la liquidité ;
- les scénarios de stress communs.

Toute décision est recalculée sur le snapshot courant. Le résultat d'un ancien snapshot ne peut pas être réutilisé après modification du portefeuille, des ordres ou des réservations.

## 8. Concentration

Pour chaque instrument ou bucket de risque `i` :

```text
notional_i = abs(q_i * mark_i * multiplier_i)
w_i = notional_i / E_t
```

Les mesures obligatoires sont :

```text
MaxWeight = max_i(w_i)
HHI = sum_i(w_i^2)
GrossExposureRatio = gross_exposure / E_t
NetExposureRatio = abs(net_exposure) / E_t
```

Une exposition candidate doit respecter les caps versionnés :

```text
w_i_after <= instrument_weight_cap_i
HHI_after <= hhi_cap
GrossExposureRatio_after <= gross_exposure_cap
NetExposureRatio_after <= net_exposure_cap
```

Pour le périmètre initial BTC/EUR, la limite d'exposition BTC et la réserve minimale en EUR sont obligatoires, même si un seul instrument est actif.

## 9. Corrélation et contribution au risque

Lorsque plusieurs actifs ou facteurs sont actifs, une matrice de covariance robuste, shrinkée et versionnée est utilisée :

```text
sigma_P = sqrt(w^T * Sigma * w)
```

La contribution marginale de l'actif `i` est :

```text
MRC_i = w_i * (Sigma * w)_i / sigma_P
```

Le risque de la nouvelle exposition est contrôlé par :

```text
DeltaSigma(q) = sigma(P union x(q)) - sigma(P)
```

La décision respecte les caps de volatilité portefeuille, de contribution marginale et de bucket corrélé.

Si l'historique est insuffisant, la corrélation est stale ou la matrice n'est pas définie positive :

```text
correlation_state=UNKNOWN
rho_within_risk_bucket=1.0
capacity_multiplier=conservative_cap
```

Le système ne suppose jamais une diversification favorable en l'absence de preuve.

## 10. Drawdown et de-risking

Le drawdown courant est :

```text
PeakNAV_t = max_{u <= t}(E_u)
Drawdown_t = max(0, 1 - E_t / PeakNAV_t)
```

La politique contient des points versionnés :

```text
(d_0=0, m_0=1), (d_1, m_1), ..., (d_K, m_K=0)
```

avec :

```text
0 = d_0 < d_1 < ... < d_K
1 = m_0 >= m_1 >= ... >= m_K = 0
```

`m_drawdown` est obtenu par interpolation linéaire déterministe entre deux points. Au-delà de `d_K` :

```text
m_drawdown=0
new_risk_allowed=false
action >= PAUSE
```

La réactivation après un drawdown critique nécessite une revue humaine et une nouvelle preuve. Un retour automatique au risque normal est interdit.

## 11. Capacité de liquidité

Pour un horizon d'exécution `H` et un taux de participation maximal `pi_max` :

```text
q_participation = pi_max * ExecutableVolumeForecast(H)
```

Depuis le carnet ou un modèle de coût validé :

```text
q_depth = sup{q >= 0 : expected_VWAP_slippage(q) <= slippage_cap}
q_impact = sup{q >= 0 : expected_market_impact(q) <= impact_cap}
q_adverse = sup{q >= 0 : adverse_selection_cost(q) <= adverse_cost_cap}
```

La capacité finale est :

```text
q_liquidity = min(
    q_participation,
    q_depth,
    q_impact,
    q_adverse,
    venue_order_cap,
    strategy_capacity_cap
)
```

Les fonctions de coût doivent être monotones dans la taille. Si le carnet est insuffisant, le moteur produit `NO_FILL` ou `PARTIAL_FILL_CAP`, jamais un prix inventé.

## 12. Taille finale approuvée

Les caps obligatoires sont :

```text
q_requested
q_trade_risk
q_incremental_risk
q_portfolio_heat
q_capital
q_concentration
q_correlation
q_liquidity
q_account
q_strategy
q_instrument
q_order
q_runtime_tier
```

La taille brute est :

```text
q_raw = max(0, min(all_defined_caps))
```

La quantité est arrondie uniquement vers le bas selon `InstrumentSpecificationV1` :

```text
q_approved = floor_to_step(q_raw, quantity_step)
```

Après arrondi, toutes les équations sont recalculées. Si le minimum de quantité ou de notional n'est pas atteint, ou si une limite est dépassée :

```text
q_approved=0
```

La décision publie :

```text
requested_size
approved_size
approved_notional
approved_risk
incremental_risk
portfolio_heat_before
portfolio_heat_after
binding_constraints[]
reason_codes[]
snapshot_id
risk_reservation_required=true|false
decision_hash
expiry
```

Le Kelly brut est interdit. Toute expérimentation de Kelly fractionné reste offline, doit être plafonnée, validée hors échantillon et ne peut contourner aucun cap ci-dessus.

## 13. Réservation atomique du capital et du risque

### 13.1 But

Empêcher deux décisions simultanées d'utiliser le même cash, la même capacité de risque ou la même limite d'exposition.

### 13.2 État de réservation

```text
PROPOSED
→ RESERVED
→ CONSUMED | RELEASED | EXPIRED | CANCELLED
```

Une réservation couvre au minimum :

```text
reservation_id
intent_id
intent_hash
snapshot_id
snapshot_sequence
portfolio_state_version_before
portfolio_state_version_after
reserved_capital
reserved_risk
reserved_notional
reserved_quantity
currency
binding_constraints[]
created_at
expires_at
idempotency_key
decision_hash
status
```

### 13.3 Protocole obligatoire

1. Le RiskDomain calcule une décision sur le snapshot de séquence `v`.
2. Il émet une `RiskReservationRequestV1` liée au hash exact de l'intent et de la décision.
3. Le propriétaire du ledger de réservations exécute une transaction sérialisable ou un compare-and-swap avec `expected_snapshot_sequence=v`.
4. Dans la même transaction, il revalide cash, limites, risque, exposition et absence de réservation équivalente.
5. Si l'état courant n'est plus `v`, la réservation échoue avec `SNAPSHOT_CONFLICT`; la décision est entièrement recalculée.
6. Si elle réussit, le ledger écrit atomiquement la réservation et incrémente sa version.
7. L'OMS/EMS ne peut créer un ordre augmentant le risque sans token de réservation actif, non expiré et correspondant au même `intent_hash` et `decision_hash`.
8. Les fills consomment la réservation proportionnellement. Les quantités non utilisées sont libérées après annulation, expiration ou réconciliation.
9. Un retry avec le même `idempotency_key` retourne le même résultat ; il ne crée jamais une deuxième réservation.

### 13.4 Propriété anti-double-dépense

À tout instant :

```text
cash_available = cash_total - active_capital_reservations - other_required_buffers
risk_available = max(0, risk_limit - R(current_portfolio_with_active_reservations))
```

Les invariants sont vérifiés après chaque transition. Un échec de persistance partiel produit `PAUSE` et réconciliation ; aucune autorisation implicite n'est conservée.

## 14. Augmentation d'une position et interdiction de moyenne à la baisse

### 14.1 Toute augmentation est une nouvelle décision

Une augmentation de quantité n'est jamais une modification silencieuse d'un ordre ou d'une position existante. Elle exige :

```text
new TradeIntent
new PortfolioDecisionSnapshotV1
new RiskDecisionV1
new RiskReservationV1
new expiry
new decision_hash
```

La quantité restante d'un ordre d'entrée partiellement exécuté n'est pas un nouvel `ADD` uniquement si elle reste couverte par le même intent, la même décision et une réservation encore valide.

### 14.2 Moyenne à la baisse interdite

Pour une augmentation dans la même direction, le système calcule le PnL de liquidation net de coûts :

```text
NetLiquidationPnL =
    liquidation_value_at_current_executable_price
    - current_cost_basis
    - estimated_exit_fees
    - estimated_exit_slippage
```

L'ajout est bloqué lorsque :

```text
NetLiquidationPnL <= 0
```

ou lorsqu'au moins une condition suivante est vraie :

```text
current_price moved adversely beyond configured_add_threshold
original_invalidation_condition is closer or already breached
new stop would widen total approved loss
portfolio_heat_after > portfolio_heat_before without a separately approved budget
add is justified only by lower market price
intent omits an explicit add/pyramiding policy
```

Reason code obligatoire :

```text
AVERAGING_DOWN_FORBIDDEN
```

### 14.3 Pyramiding contrôlé

Un ajout à une position gagnante peut être étudié uniquement si :

- `NetLiquidationPnL > 0` ;
- la stratégie possède une politique `PYRAMIDING_ALLOWED` versionnée ;
- le scénario reste valide ;
- la nouvelle perte stressée totale respecte tous les budgets ;
- le stop n'est pas élargi pour financer l'ajout ;
- la taille finale reste issue du minimum de tous les caps ;
- une nouvelle réservation atomique est obtenue.

Un score de confiance plus élevé ne suffit jamais à autoriser un ajout.

## 15. Actions canoniques de position

```text
WAIT
OPEN
HOLD
ADD
REDUCE
EXIT
TIME_EXIT
EMERGENCY_EXIT
BLOCK_NEW_RISK
PAUSE
KILL_SWITCH
```

`REDUCE`, `EXIT`, `TIME_EXIT` et `EMERGENCY_EXIT` doivent être marqués `reduce_only=true` lorsque le venue le permet. Ils ne peuvent jamais retourner la position ni augmenter l'exposition.

## 16. Matrice normative des sorties

La première condition applicable selon la priorité de conséquence gagne. Les pourcentages de réduction sont définis par la politique de stratégie versionnée ; ils ne peuvent pas être improvisés par le runtime.

| Déclencheur | Condition minimale | Nouvelle entrée / ADD | Action position | Protection / OMS | Conséquence minimale |
|---|---|---|---|---|---|
| Kill switch | sécurité, perte extrême ou commande opérateur | interdit | `EMERGENCY_EXIT` ou gel selon runbook | annuler les ordres augmentant le risque, conserver/réconcilier reduce-only | `KILL_SWITCH` |
| Position ou ordre non réconcilié | quantité, fill, cash ou ownership divergent | interdit | aucune augmentation ; réduction seulement via fallback sûr | réconciliation immédiate | `PAUSE` ou `KILL_SWITCH` |
| Stop/hard loss atteint | prix exécutable franchit le niveau approuvé | interdit | `EMERGENCY_EXIT` ou `EXIT` complet | stop/bracket prioritaire, gestion gap | `BLOCK_TRADING` ou plus |
| Invalidation de thèse | condition d'invalidation vraie | interdit | `EXIT` complet | annuler targets incompatibles | `BLOCK_TRADING` pour la stratégie |
| Régime incompatible | régime hors mandat de la stratégie | interdit | `EXIT` ou réduction complète planifiée | protection maintenue jusqu'au fill | `BLOCK_TRADING` |
| Régime légèrement dégradé | baisse de qualité sans invalidation | interdit pour ADD sauf politique explicite | `HOLD` ou `REDUCE` selon table versionnée | ne jamais élargir le stop | `WAIT` ou `BLOCK_NEW_RISK` |
| Signal expiré | `decision_time > signal_expiry` | interdit | `TIME_EXIT` ou réduction selon politique | annuler entrée restante | `WAIT` |
| Horizon maximal dépassé | `holding_time >= maximum_holding_horizon` | interdit | `TIME_EXIT` | reduce-only | `WAIT` |
| Donnée de marché stale | âge supérieur au seuil | interdit | conserver protection si son état est connu ; sinon réconcilier puis fallback | aucune nouvelle soumission risquée | `PAUSE` |
| Donnée critique absente | prix, FX, position ou limite inconnue | interdit | réduction uniquement si quantité fiable | fail-closed | `BLOCK_TRADING` ou `PAUSE` |
| Liquidité dégradée | spread, depth ou impact hors limite | interdit pour OPEN/ADD | `HOLD` protégé ou `REDUCE` par tranches | participation cap et limite de slippage | `WAIT` ou `PAUSE` |
| Liquidité critique | sortie difficile ou carnet discontinu | interdit | sortie contrôlée selon emergency unwind policy | pas de market dump aveugle sauf urgence approuvée | `PAUSE` |
| Slippage réel excessif | coût observé > cap | interdit | réduire cadence/taille ou stopper l'unwind non urgent | cancel/replace gouverné | `PAUSE` |
| Drawdown palier | `Drawdown_t >= d_k` | taille réduite par `m_drawdown` | `HOLD` ou `REDUCE` selon palier | aucune réaugmentation automatique | `WAIT`/`PAUSE` |
| Drawdown critique | `Drawdown_t >= d_K` | interdit | réduction/exit selon runbook | toutes réservations nouvelles libérées | `PAUSE` ou `KILL_SWITCH` |
| Heat ou limite globale dépassée | `PortfolioHeat > HeatLimit` | interdit | réduire le plus grand contributeur marginal selon politique | reduce-only | `BLOCK_TRADING` |
| Concentration dépassée | weight/HHI/gross/net hors cap | interdit | réduire le bucket le plus concentré | reduce-only | `BLOCK_TRADING` |
| Corrélation devenue défavorable | contribution marginale hors cap | interdit | réduire les positions responsables | reduce-only | `WAIT` ou `BLOCK_TRADING` |
| Modèle drifté | drift/calibration/performance hors seuil | interdit | `HOLD`, `REDUCE` ou `EXIT` selon model card | aucune promotion automatique | `PAUSE` |
| Calibration expirée | probabilité non valide | interdit si la stratégie l'exige | sortie selon politique d'expiration | aucun score renommé probability | `BLOCK_TRADING` |
| Exchange/API dégradé | latence, séquence ou permission inconnue | interdit | protection native maintenue ; réconciliation | pas de retry aveugle | `PAUSE` |
| Target atteint | niveau et quantité valides | sans effet sur nouvelle entrée | `REDUCE` partiel ou `EXIT` | OCO/bracket réconcilié | `APPROVE` reduce-only |
| Break-even activé | coûts et buffer couverts | ADD séparé seulement | stop peut être resserré selon politique | inclure frais/slippage | `APPROVE` protection |
| Trailing favorable | référence progresse favorablement | ADD séparé seulement | `HOLD` avec stop resserré | trailing monotone ; jamais desserré | `APPROVE` protection |
| Gap au-delà du stop | stop non exécutable au niveau attendu | interdit | `EMERGENCY_EXIT` au meilleur prix admissible | enregistrer slippage/gap exact | `PAUSE` |
| Incident opérationnel | persistence, checksum ou horloge invalide | interdit | protection maintenue si fiable | recovery/replay | `PAUSE` ou `KILL_SWITCH` |

### 16.1 Sortie sur rendement marginal

Une position peut être réduite ou clôturée lorsque :

```text
ExpectedRemainingReturn
- expected_exit_cost
- expected_holding_cost
- incremental_tail_risk_cost
<= 0
```

Cette règle n'est utilisable que si les composantes sont validées et disponibles ; sinon elle ne remplace pas les protections déterministes.

### 16.2 Resserrement seulement

Après l'entrée, toute modification de stop doit vérifier :

```text
new_worst_case_loss <= previous_approved_worst_case_loss
```

Un stop ne peut pas être éloigné pour éviter de constater une perte. Une augmentation du risque exige une nouvelle décision, et reste interdite lorsqu'elle constitue une moyenne à la baisse.

## 17. Adaptation au marché sans auto-modification

Le runtime peut recalculer à chaque événement admissible :

- volatilité et régime ;
- liquidité, spread, profondeur et impact ;
- prévisions et incertitude par horizon ;
- validité du signal et du scénario ;
- coûts attendus ;
- état du portefeuille et risque incrémental ;
- taille autorisée ;
- décision `HOLD`, `REDUCE`, `EXIT` ou `WAIT`.

Le runtime ne peut pas modifier sans nouvelle promotion :

- les poids d'un modèle ;
- les seuils de risque ;
- les équations de sizing ;
- la politique d'entrée ou de sortie ;
- les droits live ;
- les tiers de capital ;
- la possibilité d'ajouter à une position.

## 18. Ownership et intégration par version

### V5 — Strategy Research

Produit :

```text
StrategyContractV1
TradeIntentV1
ExitPolicyV1
AddPolicyV1
InvalidationPolicyV1
```

V5 ne produit ni taille finale, ni réservation, ni ordre.

### V6 — Backtest / EV / TCA

Valide hors échantillon :

- les équations de risque et de sortie ;
- les coûts et la capacité ;
- les paliers de drawdown ;
- la matrice de sorties ;
- les politiques d'ajout ;
- les scénarios de gap, partial fills et données stale.

### V7 — Risk / Sizing

Implémente :

```text
RiskLimitSetV1
SizingDecisionV1
RiskDecisionV1
RiskReservationRequestV1
SimulatedRiskReservationLedgerV1
```

V7 commence en simulation et consomme un snapshot conforme au même contrat que V9.

### V8 — Paper

Vérifie les réservations, expirations, fills partiels, sorties et réconciliation sans capital réel.

### V9 — Portfolio / PnL

`PortfolioDomain` devient la source économique autoritative pour :

```text
cash
positions
open orders
pending intents
capital reservations
portfolio state
PnL
exposure
portfolio heat inputs
```

Il publie `PortfolioDecisionSnapshotV1` mais ne décide pas lui-même d'augmenter le risque.

### V15 — OMS/EMS

Refuse tout ordre augmentant l'exposition sans réservation valide. Les sorties reduce-only restent liées à la position réconciliée et à la politique de protection.

### V17 — Live Governance

Ajoute approbation humaine, tier de capital et expiry. Aucun scale-up autonome.

## 19. Reason codes minimaux

```text
SNAPSHOT_STALE
SNAPSHOT_CONFLICT
PORTFOLIO_UNRECONCILED
POSITION_STATE_UNKNOWN
OPEN_ORDER_STATE_UNKNOWN
PENDING_INTENT_STATE_UNKNOWN
RESERVATION_MISSING
RESERVATION_EXPIRED
RESERVATION_HASH_MISMATCH
INSUFFICIENT_CASH_AVAILABLE
TRADE_RISK_LIMIT
INCREMENTAL_RISK_LIMIT
PORTFOLIO_HEAT_LIMIT
CONCENTRATION_LIMIT
CORRELATION_LIMIT
DRAWDOWN_DE_RISK
LIQUIDITY_CAPACITY_LIMIT
SLIPPAGE_LIMIT
RUNTIME_TIER_LIMIT
AVERAGING_DOWN_FORBIDDEN
ADD_POLICY_MISSING
STOP_WIDENING_FORBIDDEN
SIGNAL_EXPIRED
REGIME_INCOMPATIBLE
DATA_STALE
MODEL_DRIFT
RECONCILIATION_REQUIRED
RISK_REDUCING_ONLY
```

Chaque décision contient tous les reason codes applicables et identifie la contrainte dominante.

## 20. Tests obligatoires

### 20.1 Snapshot

- même ledger watermark pour cash, positions, ordres, intents et réservations ;
- état future-dated rejeté ;
- snapshot stale rejeté ;
- mutation d'un ID ou montant change le hash ;
- ordre ou position dupliqué rejeté ;
- reconstruction depuis ledger identique au snapshot.

### 20.2 Mathématiques

- oracles analytiques pour cas linéaires ;
- solveur déterministe pour coûts non linéaires ;
- `approved_size` non croissant lorsque volatilité, coûts, drawdown, corrélation ou concentration augmentent ;
- `approved_size` non croissant lorsque le budget diminue ;
- aucune limite dépassée après arrondi ;
- absence de NaN/Inf et comportement explicite à zéro ;
- fallback corrélation inconnu conservateur ;
- stress et expected shortfall comparés à des oracles indépendants.

### 20.3 Concurrence

- au moins 100 intents simultanés sur le même snapshot ;
- une seule réservation peut consommer la dernière unité de cash ou de risque ;
- tous les perdants reçoivent `SNAPSHOT_CONFLICT` ou une limite explicite ;
- retry idempotent ;
- crash entre décision et réservation ;
- crash entre réservation et ordre ;
- expiration et libération exactes ;
- aucun capital ou risque réservé deux fois.

### 20.4 Sorties

- chaque ligne de la matrice possède au moins un test déterministe ;
- priorité `KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE` ;
- donnée stale conserve une protection connue mais bloque le nouveau risque ;
- régime incompatible produit l'action attendue ;
- signal expiré produit `TIME_EXIT` selon policy ;
- trailing monotone ;
- stop jamais élargi sans nouvelle approbation, et jamais pour moyenner à la baisse ;
- partial fill protège exactement la quantité fillée ;
- réduction ne retourne jamais la position ;
- gap au-delà du stop audité.

### 20.5 Anti-moyenne à la baisse

- position nette perdante + même direction + quantité positive => `approved_size=0` ;
- ajout justifié seulement par un prix plus bas => rejet ;
- mutation d'un ancien intent pour augmenter la quantité => rejet ;
- pyramiding gagnant sans nouvelle réservation => rejet ;
- reliquat d'un partial fill avec réservation valide => autorisé dans la limite initiale ;
- nouvel ajout après expiration => nouvelle décision obligatoire.

### 20.6 Replay et audit

- même snapshot, config, code et seed => mêmes décisions, réservations et checksums ;
- ordre différent des événements mais même ordre canonique => même résultat ;
- divergence de checksum => `NON_DETERMINISTIC_FAIL` ;
- chaque montant est traçable jusqu'au ledger et aux états de marché.

## 21. Gates avant implémentation V7 et V9

Aucun lot V7 ou V9 concerné ne peut être promu sans :

1. schémas `PortfolioDecisionSnapshotV1` et `RiskReservationV1` validés ;
2. configuration de limites et de drawdown versionnée ;
3. équations implémentées avec oracles indépendants ;
4. matrice de sorties couverte par tests ;
5. protocole de réservation atomique testé sous concurrence ;
6. interdiction de moyenne à la baisse testée par mutation ;
7. replay déterministe ;
8. revue humaine et rapport `GO` sur le commit exact ;
9. zéro BLOCKER et zéro MAJOR ;
10. aucune permission de trading ou d'exécution activée par la documentation seule.

## 22. Non-objectifs

Ce document :

- ne choisit aucun seuil numérique de production sans validation empirique ;
- n'active aucun modèle, signal, sizing, paper, sandbox ou live ;
- ne permet pas le levier dans le périmètre initial ;
- ne remplace pas les gates V5/V6/V7/V8/V9/V15/V17 ;
- ne permet pas à une stratégie ou à un modèle de contourner `RiskDecisionV1` ;
- ne transforme jamais une documentation future en capability implémentée.
