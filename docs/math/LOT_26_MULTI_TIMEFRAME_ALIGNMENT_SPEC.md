# Lot 26 — Mathematical specification of multi-timeframe alignment

Definition ID: `MTF_ALIGNMENT_V1`  
Status: `PROVISIONAL_UNCALIBRATED_OFFLINE_ONLY`

## 1. Purpose

Définir un calcul d'accord descriptif entre deux contextes temporels confirmés reliés par une arête orientée. Le profil v1 compare le contexte local 5m au dernier contexte supérieur 15m légalement disponible.

Le résultat est un **agreement score**. Il ne prédit pas un rendement et n'est pas une **probability**.

## 2. Scale graph

Soit :

```text
G = (S, E)
```

- `S` : ensemble des échelles enregistrées ;
- `E` : ensemble des relations ordonnées local→supérieur autorisées.

Pour le Lot 26 v1 :

```text
S_v1 = {timebar-5m, timebar-15m}
E_v1 = {(timebar-5m, timebar-15m)}
```

L'algorithme traite une relation `e=(s_l,s_h)` fournie par configuration. Toute autre relation est rejetée dans v1. Les futures relations seront versionnées et ne seront pas fusionnées par vote majoritaire.

## 3. Inputs

Pour chaque composante `i` et relation `e` :

```text
L_i^e = état local de s_l
H_i^e = dernier état supérieur admissible de s_h
```

Composantes :

```text
trend, range, momentum, volatility, regime, confluence
```

Domaine : enums fermés définis par contrats/configuration.  
Codomaine d'une compatibilité : `[0,1] ∪ {UNKNOWN}`.

## 4. Temporal admissibility

```text
bar_close_time <= available_at <= decision_time
```

L'état supérieur est choisi par `ASOF_BACKWARD`. Toute barre ouverte, future, stale ou ambiguë est exclue.

## 5. Ordinal components

Pour `trend`, `momentum`, `volatility`, `confluence`, une fonction d'encodage `q_i` est définie dans la configuration.

```text
a_i^e = 1 - |q_i(L_i^e) - q_i(H_i^e)| / R_i
```

avec :

```text
R_trend = 2
R_momentum = 2
R_volatility = 1
R_confluence = 1
```

Puis `a_i^e` est borné dans `[0,1]`.

Un état divergent/non ordinal non encodé vaut `UNKNOWN`, pas zéro.

## 6. Categorical components

`range` et `regime` utilisent les matrices complètes `C_i` :

```text
a_i^e = C_i(L_i^e, H_i^e)
```

Toutes les valeurs sont dans `[0,1]`. Une paire absente invalide la configuration.

## 7. Weighted coverage

Poids v1 :

```text
trend       0.22
range       0.13
momentum    0.18
volatility  0.14
regime      0.18
confluence  0.15
```

La somme vaut `1` dans `atol=1e-9`.

Pour `I_i^e=1` si la composante est disponible, sinon `0` :

```text
weighted_coverage_ratio_e = Σ(w_i I_i^e)
available_component_count_e = Σ(I_i^e)
```

Condition de calcul :

```text
available_component_count_e >= 4
weighted_coverage_ratio_e >= 0.70
```

Sinon score et classifications valent `UNKNOWN`.

## 8. Overall agreement score

```text
overall_agreement_score_e =
    Σ(w_i a_i^e I_i^e) / Σ(w_i I_i^e)
```

Le dénominateur nul donne `UNKNOWN`. Le résultat est arrondi uniquement à la publication à 6 décimales ; les calculs internes gardent leur précision complète.

```text
agreement score != probability
agreement score != expected return
agreement score != forecast
agreement score != signal
agreement score != trade permission
```

## 9. Classification per edge

```text
ALIGNED    si score >= 0.75 et moins de 2 hard mismatches
PARTIAL    si 0.50 <= score < 0.75
DIVERGENT  si score < 0.50 ou au moins 2 hard mismatches
UNKNOWN    si couverture insuffisante
```

Hard mismatch :

```text
a_i^e <= 0.25
```

`coherence_state` :

```text
MTF_COHERENT     : ALIGNED sans contradiction directionnelle
MTF_MIXED        : PARTIAL ou une contradiction
MTF_INCOHERENT   : DIVERGENT
MTF_UNKNOWN      : score indisponible
```

`divergence_state` suit la priorité :

```text
MTF_MULTI_COMPONENT_MISMATCH
MTF_DIRECTIONAL_MISMATCH
MTF_REGIME_MISMATCH
MTF_VOLATILITY_MISMATCH
MTF_NO_HARD_DIVERGENCE
MTF_UNKNOWN
```

## 10. Future multiple-edge aggregation

Le Lot 26 v1 ne calcule qu'une arête. Pour une future version où `|E|>1` :

- chaque `overall_agreement_score_e` est conservé ;
- aucune moyenne globale n'est normative sans modèle séparé ;
- aucun vote de majorité directionnelle n'est autorisé ;
- la covariance des erreurs et l'emboîtement des horizons doivent être modélisés ;
- l'horizon de stratégie détermine la pertinence d'une arête ;
- toute agrégation constitue un nouveau contrat/version.

## 11. Separation from forecasting

L'alignement compare des états contemporains disponibles. Une prévision multi-horizon estime une distribution future conditionnelle. Ces problèmes sont distincts :

```text
alignment_state(t) != forecast_distribution(t+h | information_t)
```

Les futurs horizons 30s, 5m, 15m et 1h appartiennent à `MultiHorizonForecastV1`, pas au Lot 26.

## 12. Uncertainty

L'incertitude descriptive dépend de la couverture :

```text
LOW       si coverage = 1 et aucun UNKNOWN
MODERATE  si 0.85 <= coverage < 1
HIGH      si 0.70 <= coverage < 0.85
UNKNOWN   si coverage < 0.70
```

Ce n'est pas un intervalle statistique de confiance.

## 13. Properties

- bornes `[0,1]` ;
- symétrie des compatibilités par composante lorsque définie ;
- identité : même état valide → `1` ;
- oppositions directionnelles extrêmes → `0` ;
- permutation des composantes sans effet ;
- ajout d'une composante disponible ne réduit pas la couverture ;
- UNKNOWN ne devient jamais accord ;
- 15m divergent n'annule pas automatiquement le contexte 5m ;
- aucune direction BUY/SELL ;
- une relation non enregistrée est rejetée ;
- ajouter une échelle désactivée ne modifie pas le résultat v1 ;
- aucun vote naïf entre relations.

## 14. Tolerances

```text
atol = 1e-9
rtol = 1e-9
publication decimals = 6
```

## 15. Invalidation

- contrat incompatible ;
- relation d'échelle non autorisée ;
- timezone invalide ;
- barre ouverte/future ;
- état stale ;
- matrice incomplète ;
- poids non positifs ou somme différente de 1 ;
- valeur non finie ;
- couverture insuffisante ;
- champ forecast/probability interdit ;
- replay divergent.

## 16. Required validation

Oracles analytiques, property-based tests, mutation tests des comparateurs temporels, relation d'échelle, poids, dénominateur, seuils et classifications.

Aucun résultat n'est promotionnable vers paper/live et aucune probability ne peut être déduite du score.
