# Lot 26 — Mathematical specification of multi-timeframe alignment

Definition ID: `MTF_ALIGNMENT_V1`  
Status: `PROVISIONAL_UNCALIBRATED_OFFLINE_ONLY`  
Configuration checksum: `cb6ac1d3c392df67b5eb15d4c07a8fc818772025ec05e142190b0b667308bd76`

## 1. Purpose

Comparer le contexte local 5m au dernier contexte supérieur 15m légalement disponible. Le résultat
décrit un accord ou une divergence. Il ne prédit pas un rendement et n’est pas une probabilité.

## 2. Inputs

Pour chaque composante `i` :

```text
L_i = état local 5m
H_i = état supérieur 15m
```

Composantes :

```text
trend, range, momentum, volatility, regime, confluence
```

Domaine : enums fermés définis par les contrats/configs.  
Codomaine d’une compatibilité : `[0,1] ∪ {UNKNOWN}`.

## 3. Temporal admissibility

Les deux états satisfont :

```text
bar_close_time <= available_at <= decision_time
```

Le 15m est choisi par jointure as-of backward. Toute barre ouverte/future est exclue.

## 4. Ordinal components

Pour `trend`, `momentum`, `volatility`, `confluence`, une fonction d’encodage `e_i` est définie dans
la configuration.

```text
a_i = 1 - |e_i(L_i) - e_i(H_i)| / R_i
```

avec :

```text
R_trend = 2
R_momentum = 2
R_volatility = 1
R_confluence = 1
```

Puis `a_i` est borné dans `[0,1]`.

Un état divergent/non ordinal non encodé vaut `UNKNOWN`, pas zéro.

## 5. Categorical components

`range` et `regime` utilisent les matrices complètes `C_i(L_i,H_i)` de la configuration :

```text
a_i = C_i(L_i,H_i)
```

Toutes les valeurs sont dans `[0,1]`. Une paire absente invalide la configuration.

## 6. Weighted coverage

Poids :

```text
trend       0.22
range       0.13
momentum    0.18
volatility  0.14
regime      0.18
confluence  0.15
```

La somme est exactement `1` dans `atol=1e-9`.

Pour `I_i=1` si la composante est disponible, sinon `0` :

```text
weighted_coverage_ratio = Σ(w_i I_i)
available_component_count = Σ(I_i)
```

Condition de calcul :

```text
available_component_count >= 4
weighted_coverage_ratio >= 0.70
```

Sinon le score et les classifications valent `UNKNOWN`.

## 7. Overall score

```text
overall_agreement_score =
    Σ(w_i a_i I_i) / Σ(w_i I_i)
```

Le dénominateur nul donne `UNKNOWN`. Le résultat est arrondi uniquement à la publication à
6 décimales ; les calculs internes gardent la précision binaire complète.

## 8. Classification

```text
ALIGNED    si score >= 0.75 et moins de 2 hard mismatches
PARTIAL    si 0.50 <= score < 0.75
DIVERGENT  si score < 0.50 ou au moins 2 hard mismatches
UNKNOWN    si couverture insuffisante
```

Hard mismatch :

```text
a_i <= 0.25
```

`coherence_state` :

```text
MTF_COHERENT     : ALIGNED sans contradiction directionnelle
MTF_MIXED        : PARTIAL ou une contradiction
MTF_INCOHERENT   : DIVERGENT
MTF_UNKNOWN      : score indisponible
```

`divergence_state` est déterminé par priorité :

```text
MTF_MULTI_COMPONENT_MISMATCH
MTF_DIRECTIONAL_MISMATCH
MTF_REGIME_MISMATCH
MTF_VOLATILITY_MISMATCH
MTF_NO_HARD_DIVERGENCE
MTF_UNKNOWN
```

## 9. Uncertainty

`uncertainty_state` dépend de la couverture :

```text
LOW       si coverage = 1 et aucun UNKNOWN
MODERATE  si 0.85 <= coverage < 1
HIGH      si 0.70 <= coverage < 0.85
UNKNOWN   si coverage < 0.70
```

Ce n’est pas un intervalle statistique de confiance.

## 10. Properties

- bornes exactes `[0,1]` ;
- symétrie des compatibilités : `a(L,H)=a(H,L)` ;
- identité : même état valide → `1` ;
- oppositions directionnelles extrêmes → `0` ;
- permutation de l’ordre des composantes sans effet ;
- ajout d’une composante disponible ne réduit pas `coverage_ratio` ;
- UNKNOWN ne devient jamais accord ;
- 15m divergent n’annule pas automatiquement le contexte 5m ;
- aucune direction BUY/SELL dans la sortie.

## 11. Tolerances

```text
atol = 1e-9
rtol = 1e-9
publication decimals = 6
```

## 12. Invalidation

- contrat incompatible ;
- timezone invalide ;
- barre ouverte/future ;
- état stale ;
- matrice incomplète ;
- poids non positifs ou somme différente de 1 ;
- valeur non finie ;
- couverture insuffisante ;
- replay divergent.

## 13. Required validation

Oracles analytiques, property-based tests, mutation tests des comparateurs temporels, poids,
dénominateur, seuils et classifications. Aucun résultat n’est promotionnable vers paper/live.
