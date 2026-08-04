# PRE_LOT26_ENTRY_GATE

Projet : **Crypto Quant Bot V3.1-Ops**  
Nature : gate transversal de readiness, sans numéro de lot.  
Conséquence runtime : aucune.

## 1. Objectif

Autoriser ou refuser le démarrage de l'implémentation du Lot 26 à partir de preuves objectives. Ce gate ne calcule aucun signal, ne crée aucune prévision et n'implémente pas le moteur multi-timeframe.

## 2. Conditions d'entrée

- baseline P0 fusionnée dans `main` ;
- CI institutionnelle verte sur la baseline ;
- Lot 25 toujours validé ;
- Lot 26 toujours `PLANNED_LOCKED` ;
- invariants no-trading inchangés ;
- Lots 0–25 non modifiés.

## 3. Artefacts obligatoires

### Lot 26 immédiat

- ADR temporel ;
- contrats JSON Schema Lot 26 ;
- spécification mathématique ;
- configuration d'alignement versionnée ;
- spécification complète du Lot 26 ;
- critères d'acceptation ;
- matrice exigences → tests ;
- adaptateur historique défini mais non implémenté ;
- validateur automatique et rapport.

### Architecture extensible

- `TemporalScaleRegistryV1` ;
- `DecisionClockPolicyV1` ;
- registre des horizons de prévision ;
- standard multi-échelle ;
- standard stochastique/multi-horizon ;
- standard de comportement des participants et zones de sortie ;
- standard des ordres protecteurs ;
- addendum de roadmap V3/V4/V5/V6/V7/V15/V19 ;
- schémas futurs marqués `PLANNED_LOCKED_NOT_IMPLEMENTED`.

### Gouvernance

- README et règles de contribution ;
- environnement Python et dépendances verrouillés ;
- workflow CI permanent ;
- rapport final et manifeste machine-readable.

## 4. Architecture temporelle

Le système utilise un flux canonique continu, mais distingue :

```text
data_resolution
feature_lookback
forecast_horizon
decision_clock
signal_ttl
holding_horizon
```

Le Lot 26 v1 active uniquement :

```text
timebar-5m → timebar-15m
trigger = CLOSED_LOCAL_BAR
join = ASOF_BACKWARD
```

Une barre est admissible si :

```text
bar_close_time <= available_at <= decision_time
```

Le 5m/15m est un profil initial. L'interface doit rester extensible, mais aucune autre échelle ne doit être activée par le Lot 26.

## 5. Flux continu et open bars

L'ingestion peut être continue. Les `open_bars` sont des observations provisoires et ne peuvent pas créer un état confirmé Lot 26.

`ContinuousMarketStateV1` est enregistré pour V3/V4 mais n'est pas implémenté ni consommé par le Lot 26.

## 6. Frontières de responsabilité

### Lot 26

- compare une relation temporelle enregistrée ;
- expose alignement, divergence, cohérence et couverture ;
- ne produit ni probability, ni forecast, ni alpha, ni signal, ni ordre ;
- ne déduit pas le comportement des participants ;
- n'active aucune décision event-driven hors clôture 5m.

### Versions ultérieures

- V3 : flux canonique continu et qualité temporelle ;
- V4 : carnet, trades, microstructure, Game Theory et zones de sortie ;
- V5 : prévisions stochastiques multi-horizons et stratégies ;
- V6 : preuve statistique, coûts et capacité ;
- V7 : risque et sizing ;
- V15 : ordres protecteurs et lifecycle OMS/EMS ;
- V19 : haute résolution tick/L2/L3 research-only.

## 7. Contrôles obligatoires

`GO` seulement si :

- tous les fichiers obligatoires existent ;
- schemas/configs sont valides et fermés ;
- poids = 1 dans la tolérance ;
- matrices complètes et bornées ;
- le registre active exactement 5m et 15m pour Lot 26 ;
- les autres échelles sont désactivées ;
- seul `CLOSED_LOCAL_BAR` est activé ;
- les horizons sont enregistrés mais non implémentés ;
- vote naïf explicitement interdit ;
- aucune capability future n'est active ;
- tests du validateur PASS ;
- roadmap cohérente ;
- aucune preuve historique Lots 0–25 modifiée ;
- aucune modification de `src/` ;
- CI verte sur le commit exact.

## 8. NO-GO codes

```text
NO_GO_PRE_LOT26_FILES
NO_GO_PRE_LOT26_TEMPORAL_SEMANTICS
NO_GO_PRE_LOT26_SCALE_REGISTRY
NO_GO_PRE_LOT26_DECISION_CLOCK
NO_GO_PRE_LOT26_FORECAST_SCOPE
NO_GO_PRE_LOT26_MATHEMATICS
NO_GO_PRE_LOT26_DOCUMENTATION
NO_GO_PRE_LOT26_HISTORICAL_IMMUTABILITY
NO_GO_PRE_LOT26_TESTS
NO_GO_PRE_LOT26_INVARIANTS
```

## 9. Verdict

`GO` autorise seulement la création d'une branche d'implémentation du Lot 26 depuis le commit exact validé. Il n'autorise ni Lot 27, ni forecast, ni paper, ni live.
