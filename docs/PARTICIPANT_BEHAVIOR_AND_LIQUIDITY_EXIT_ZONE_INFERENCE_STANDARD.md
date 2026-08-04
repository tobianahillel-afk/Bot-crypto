# Participant Behavior and Liquidity Exit-Zone Inference Standard

Statut : `PLANNED_LOCKED_STANDARD`  
Owner principal : **V4 — Microstructure / Liquidity / Game Theory, Lots 37–52**

## 1. Principe

Le système peut inférer des comportements probables à partir de données observables, mais ne prétend jamais connaître l'intention réelle d'un participant. Toute sortie est une hypothèse probabiliste avec preuves, contre-preuves, incertitude et condition d'invalidation.

```text
participant_behavior = inference_explicitly_labeled
inferred_order_location != observed_private_order
scenario_score != probability sauf calibration
scenario_score != signal
```

## 2. Catégories de participants

Taxonomie initiale, extensible et versionnée :

- market makers et fournisseurs de liquidité ;
- traders momentum ;
- traders de retour à la moyenne ;
- acheteurs de cassure tardifs ;
- vendeurs de cassure tardifs ;
- positions longues à levier ;
- positions courtes à levier ;
- acheteurs piégés ;
- vendeurs piégés ;
- liquidateurs forcés ;
- grands participants passifs ;
- arbitragistes spot/perp/venue ;
- preneurs de profit ;
- participants défendant un coût moyen ou break-even.

Une observation peut être compatible avec plusieurs catégories. Le moteur conserve des scénarios concurrents.

## 3. Modèle de théorie des jeux

Chaque `ParticipantBehaviorScenarioV1` décrit :

```text
scenario_id
participant_class
information_set
observable_evidence
counter_evidence
constraints
action_set
payoff_proxy
loss_or_pain_proxy
belief_state
best_response_candidates
bounded_rationality_assumptions
forecast_horizon
invalidation_conditions
confidence_proxy ou calibrated_probability
```

Les `payoff_proxy` et `loss_or_pain_proxy` peuvent intégrer :

- profit/perte non réalisé estimé ;
- frais, funding et coût de portage ;
- risque de liquidation ;
- coût de sortie et profondeur ;
- risque d'inventaire ;
- sélection adverse ;
- contrainte de temps ;
- coût d'opportunité.

Aucun équilibre n'est supposé exister sans preuve. Les solutions candidates peuvent inclure best response, équilibre approximatif, jeu séquentiel, jeu bayésien ou comportement borné, mais chaque hypothèse doit être testée contre des baselines plus simples.

## 4. Preuves admissibles

Après les lots dédiés, les scénarios peuvent utiliser :

- carnet L2/L3 et ses deltas ;
- spread, profondeur et imbalance ;
- replenishment et résilience ;
- transactions et aggressor classification ;
- order flow, delta et CVD ;
- absorption et liquidité cachée proxy ;
- volume clusters et time-at-level ;
- sweeps, fakeouts, traps et failed auctions ;
- open interest, funding, basis et liquidations ;
- structures multi-échelles confirmées ;
- historique des réactions aux niveaux.

Une donnée privée non observée ne peut être inventée.

## 5. Taxonomie des zones de sortie et de vulnérabilité

`LiquidityExitZoneV1` possède un `zone_type` fermé :

```text
STOP_LOSS_CLUSTER
TAKE_PROFIT_CLUSTER
BREAK_EVEN_CLUSTER
LIQUIDATION_CLUSTER
ENTRY_CONGESTION_ZONE
TRAPPED_POSITION_ZONE
FORCED_EXIT_ZONE
PASSIVE_DEFENSE_ZONE
```

Chaque zone comporte :

```text
zone_id
instrument_id
price_lower
price_upper
zone_type
participant_classes
forecast_horizons
construction_method
evidence_refs
counter_evidence_refs
probability ou score correctement nommé
uncertainty
first_observed_at
last_updated_at
available_at
invalidation_conditions
```

## 6. Méthodes de construction candidates

### 6.1 Stop-loss clusters

- swings confirmés ;
- égalités de hauts/bas ;
- niveaux ronds ;
- extrêmes de range ;
- cassures suivies de retour ;
- zones où un scénario devient invalide.

### 6.2 Take-profit clusters

- objectifs de range ou measured move ;
- niveaux de liquidité opposés ;
- zones de forte extension ;
- précédents points d'entrée probables ;
- quantiles de maximum favorable excursion ;
- zones où le rendement marginal devient négatif après coûts.

### 6.3 Break-even clusters

- prix moyen pondéré probable d'une cohorte ;
- clusters de volume et temps passé au niveau ;
- coût d'entrée estimé, frais et funding ;
- zones de retest après breakout ;
- coût moyen des positions ouvertes lorsqu'une donnée fiable le permet.

### 6.4 Liquidation et forced-exit zones

- prix de liquidation estimé par type de contrat et levier hypothétique ;
- OI, funding, basis et concentration ;
- profondeur disponible ;
- cascades observées historiques ;
- incertitude explicite sur la distribution du levier.

## 7. Processus d'inférence

1. Construire uniquement des faits mesurés et temporellement admissibles.
2. Générer plusieurs scénarios de participants.
3. Associer preuves et contre-preuves.
4. Calculer score ou probabilité calibrée par scénario.
5. Construire les zones associées.
6. Définir actions probables et réactions alternatives.
7. Tester les scénarios sur horizons distincts.
8. Réviser ou invalider à chaque événement matériel.
9. Conserver l'historique append-only.
10. Ne jamais créer directement Signal ou OrderIntent.

## 8. Interaction multi-horizon

Les acteurs n'ont pas tous le même horizon. Le moteur doit pouvoir représenter :

- market maker à horizon secondes ;
- trader momentum à horizon minutes ;
- détenteur intraday à horizon heures ;
- position à levier sensible à une liquidation immédiate.

Les zones et réponses probables sont donc conditionnées par `forecast_horizon`, pas fusionnées en une seule carte statique.

## 9. Calibration et validation

Pour publier une probabilité :

- labels ex post définis sans leakage ;
- calibration par zone, participant et horizon ;
- Brier/log loss ;
- reliability diagram ;
- validation walk-forward ;
- comparaison à une baseline structurelle ;
- stabilité par régime ;
- ablation de chaque famille de preuves.

Sans calibration, la sortie reste un `score` ou une `confidence_proxy`.

## 10. Tests obligatoires

- zone bornée et prix cohérents ;
- aucune zone issue d'une donnée future ;
- même replay → mêmes scénarios/checksums ;
- preuves retirées → confiance non croissante lorsque la propriété est attendue ;
- scénario contradictoire conservé ;
- absence de carnet → pas de fausse précision ;
- OI/levier non comparables → liquidation `UNKNOWN` ;
- mutation des bornes, seuils et ordre temporel détectée ;
- aucune assertion d'intention réelle ;
- aucun signal ou ordre généré.

## 11. Roadmap

- Lots 38–48 : preuves microstructure ;
- Lot 49 : stop zones et attraction de liquidité ;
- Lot 50 : sweeps, traps et failed auctions ;
- Lot 51 : dérivés et liquidations ;
- Lot 52 : participants, payoffs, beliefs et scénarios agrégés ;
- V5 : transformation éventuelle en hypothèse falsifiable ;
- V6 : validation prédictive et économique.

## 12. Restrictions Lot 26

Le Lot 26 peut fournir un contexte d'alignement multi-échelle comme preuve future, mais il ne calcule aucun participant, stop, take-profit, break-even, liquidation ou payoff.
