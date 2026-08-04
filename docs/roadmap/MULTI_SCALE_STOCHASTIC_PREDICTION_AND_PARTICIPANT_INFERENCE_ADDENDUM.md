# Roadmap Addendum — Multi-Scale, Stochastic Prediction and Participant Inference

Statut : `NORMATIVE_ADDENDUM`  
Ce document précise la répartition des responsabilités sans renuméroter les Lots 0–177.

## 1. Principe

Le produit cible est un système unique qui combine :

```text
flux continu
+ états multi-échelles
+ prévisions multi-horizons
+ microstructure et comportements probables
+ stratégie falsifiable
+ coûts, risque et exécution gouvernée
```

Les 5m et 15m forment le premier profil d'alignement, pas la limite finale du système.

## 2. Lot 26 — fondation descriptive

Le Lot 26 doit :

- implémenter une interface d'arête temporelle extensible ;
- activer uniquement `timebar-5m → timebar-15m` dans v1 ;
- produire accord, divergence, cohérence, couverture et reason codes ;
- utiliser uniquement des états confirmés et disponibles ;
- conserver les deux contextes séparément ;
- interdire vote naïf, prévision, probabilité, signal et ordre.

Il ne doit pas implémenter le flux événementiel, les modèles stochastiques ou la théorie des jeux.

## 3. V3 — Market Data Governance, Lots 31–36

V3 doit préciser et implémenter :

- flux canonique continu de `MarketDataEnvelopeV1` ;
- event/source/receive/process/available time ;
- ordre canonique et gestion des révisions ;
- registre des résolutions et agrégations ;
- construction auditable des barres ;
- réconciliation candles/trades/book ;
- fraîcheur, gaps et outages ;
- base de `ContinuousMarketStateV1` côté qualité/disponibilité.

## 4. V4 — Microstructure / Liquidity / Game Theory, Lots 37–52

### Lots 37–40

- contrats tick/trade/L2/L3 autorisés ;
- snapshots, deltas, séquences et santé du carnet ;
- événements continus temporellement ordonnés.

### Lots 41–48

- spread, profondeur, imbalance ;
- murs, vides, résilience et replenishment ;
- aggressor classification ;
- order flow, delta et CVD ;
- absorption, défense et liquidité cachée proxy ;
- clusters de volume et time-at-level.

### Lots 49–51

- zones `STOP_LOSS_CLUSTER` ;
- zones `TAKE_PROFIT_CLUSTER` ;
- zones `BREAK_EVEN_CLUSTER` ;
- trapped positions et forced exits ;
- sweeps, fakeouts, traps et failed auctions ;
- OI, funding, basis, squeeze et liquidations.

### Lot 52

Le Lot 52 doit formaliser :

```text
participant classes
information sets
action sets
constraints
payoff/loss proxies
belief states
best-response candidates
bounded rationality
scenario probabilities uniquement calibrées
```

Il agrège des scénarios concurrents et ne produit aucun signal exécutable.

## 5. V5 — Alpha / Strategy Research, Lots 53–59

V5 doit ajouter :

- `ForecastHorizonRegistryV1` ;
- `MultiHorizonForecastV1` ;
- hypothèses falsifiables par horizon ;
- modèles stochastiques ou baselines sélectionnés par preuve ;
- calibration indépendante par horizon ;
- dépendance et contradictions entre horizons ;
- `ExitPolicyV1` avec invalidation, stop, take-profit, break-even, trailing et time exit ;
- séparation forecast/signal/TradeIntent.

Le Lot 55 ne peut appeler une sortie `probability` sans calibration approuvée.

## 6. V6 — Backtesting / EV / TCA, Lots 60–71

V6 doit valider :

- labels et barrières par horizon ;
- target-hit, stop-hit, time-to-event, MAE et MFE ;
- walk-forward, purging et embargo ;
- calibration et erreurs conjointes entre horizons ;
- placebos et contrôle des tests multiples ;
- bootstrap, Monte Carlo et sensibilité ;
- fill probability, queue proxy, capacité ;
- EV nette des coûts par horizon, régime et taille ;
- réalisme des sorties protectrices.

## 7. V7 — Risk / Sizing, Lots 72–80

V7 possède :

- sizing selon distribution prédictive, volatilité et confiance calibrée ;
- limites par stratégie, horizon et instrument ;
- stop/risk budget obligatoires ;
- risque de ruine et tails ;
- corrélation et concentration ;
- veto sur données, modèles ou forecasts expirés ;
- approbation du hash exact du TradeIntent.

## 8. V8 et V15 — Paper puis OMS/EMS

V8 simule les décisions, fills et ordres protecteurs sans réseau exchange.

V15 doit implémenter :

- `ProtectiveOrderPlanV1` ;
- bracket et OCO natifs/émulés ;
- stop-loss, take-profit, break-even et trailing ;
- partial fills et sorties partielles ;
- cancel/replace idempotent ;
- restart, recovery et reconciliation ;
- interdiction de nouvelle action lorsque l'issue d'une soumission est inconnue.

## 9. V19 — HFT Research, Lots 166–171

V19 peut étudier :

- tick/L2/L3 haute résolution ;
- queue position et matching ;
- processus ponctuels/Hawkes ;
- intensité d'annulation et de trade ;
- latence et toxicité ;
- décision à horloge événementielle très courte.

V19 reste `HFT_RESEARCH_ONLY` et ne crée aucun chemin live.

## 10. Contrats transverses ajoutés

```text
TemporalScaleRegistryV1
DecisionClockPolicyV1
ContinuousMarketStateV1
MultiHorizonForecastV1
ParticipantBehaviorScenarioV1
LiquidityExitZoneV1
ExitPolicyV1
ProtectiveOrderPlanV1
```

Les contrats marqués futurs sont `PLANNED_LOCKED_NOT_IMPLEMENTED`.

## 11. Tests transverses

- distinction résolution/lookback/horizon/clock/TTL/holding ;
- anti-lookahead sur chaque état ;
- absence de vote naïf ;
- calibration par horizon ;
- dépendance des erreurs ;
- replay événementiel ;
- ablation des données ;
- scénario concurrent conservé ;
- zone de participant explicitement inférée ;
- ordres protecteurs réconciliés ;
- aucun bypass Risk→OMS.

## 12. Gate pré-Lot26

Le Lot 26 ne peut démarrer que si :

- le profil 5m→15m est mathématiquement figé ;
- l'interface reste extensible ;
- les notions temporelles sont séparées ;
- les futurs contrats sont enregistrés mais non implémentés ;
- les frontières V3/V4/V5/V6/V7/V15/V19 sont explicites ;
- toutes les permissions de trading restent désactivées.
