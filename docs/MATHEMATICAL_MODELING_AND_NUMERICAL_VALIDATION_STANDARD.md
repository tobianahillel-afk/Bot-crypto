# Mathematical Modeling and Numerical Validation Standard

Ce document est normatif pour tout lot produisant une mesure, un score, une probabilité, une estimation, une décision quantitative ou une simulation.

## 1. Spécification mathématique obligatoire

Avant toute implémentation, chaque objet quantitatif doit définir :

- symbole et nom ;
- domaine et codomaine ;
- unité ;
- convention de signe ;
- index temporel ;
- fenêtre d'observation ;
- hypothèses ;
- conditions d'existence ;
- bornes ;
- traitement des valeurs manquantes ;
- comportement aux limites ;
- dépendances et disponibilité temporelle ;
- méthode d'estimation ;
- incertitude ;
- conditions d'invalidation.

Aucun score ad hoc ne peut être accepté sans interprétation, calibration et propriétés attendues.

## 2. Forme normative d'une définition

```text
Definition ID
Inputs X with domains
Parameters theta with admissible set
Function f_theta(X)
Output Y and codomain
Units and normalization
Assumptions A1...An
Invariants I1...In
Numerical method
Error/tolerance model
Failure/UNKNOWN conditions
Reference implementation
Validation tests
```

## 3. Exigences de correction

Chaque formule doit satisfaire les propriétés applicables :

- cohérence dimensionnelle ;
- conservation des quantités ;
- monotonie attendue ;
- symétrie ou antisymétrie ;
- invariance d'échelle ou de translation lorsqu'annoncée ;
- continuité ou discontinuités explicitement documentées ;
- bornes exactes ;
- absence de division par zéro ;
- absence de logarithme/racine hors domaine ;
- traitement explicite des NaN, infinis et données dégénérées.

## 4. Probabilités et scores

Une probabilité doit être dans `[0,1]`, calibrée et accompagnée d'une métrique de calibration. Un score non probabiliste ne doit jamais être nommé `probability`.

Les modèles probabilistes documentent au minimum :

- définition de l'événement ;
- horizon ;
- population de référence ;
- fréquence de base ;
- méthode de calibration ;
- Brier score/log loss ;
- reliability diagram ou équivalent ;
- intervalles d'incertitude ;
- comportement hors distribution.

## 5. Statistique et inférence

- hypothèse nulle et alternative explicites ;
- taille d'échantillon et puissance ;
- correction du multiple testing ;
- intervalles de confiance ;
- séparation exploration/confirmation ;
- données dépendantes traitées comme telles ;
- bootstrap par blocs lorsque nécessaire ;
- aucune conclusion à partir du seul p-value ;
- effet économique et statistique séparés.

## 6. Séries temporelles et anti-lookahead

- index temporel total et déterministe ;
- `event_time`, `available_at`, `decision_time` séparés ;
- fenêtres strictement passées ;
- joins as-of backward ;
- bougies non clôturées exclues sauf contrat dédié ;
- labels disponibles uniquement après leur horizon ;
- purging/embargo pour événements chevauchants ;
- révisions de données versionnées.

## 7. Backtest et Expected Value

L'EV nette doit séparer :

```text
EV_gross
- fees
- spread cost
- slippage
- market impact
- funding/carry
- latency/adverse selection
- rejected/no-fill opportunity effects
= EV_net
```

Doivent être produits : distribution, moyenne, médiane, quantiles, intervalle d'incertitude, downside, tail loss, capacité et sensibilité aux hypothèses.

Aucun coût absent ne vaut zéro par défaut. Il produit `UNKNOWN` ou un fallback conservateur explicite.

## 8. Risk et sizing

Le sizing doit être borné par la plus restrictive des limites applicables. Toute donnée, limite ou état inconnu force une taille nulle.

Propriétés minimales :

- `approved_size >= 0` ;
- `approved_size = 0` sur veto ;
- monotonie non croissante lorsque risque, coût ou incertitude augmentent ;
- limites d'exposition jamais dépassées ;
- rounding instrument appliqué après sizing puis revalidation ;
- risk of ruin et drawdown sous stress évalués ;
- aucun scale-up autonome.

## 9. Microstructure

- conservation du volume : `total = buy + sell + unknown` ;
- book valide : bids triés, asks triés, quantités non négatives ;
- crossed/locked book traité explicitement ;
- séquences et gaps vérifiés ;
- inference de participant toujours étiquetée comme proxy ;
- aucun stop réel prétendu sans observation directe ;
- aucun fill avant ack ou hors profondeur disponible.

## 10. Portfolio, PnL et comptabilité

Les identités comptables doivent être testées :

```text
position_t = position_{t-1} + signed_fills_t
cash_t = cash_{t-1} - trade_notional_t - fees_t + cashflows_t
PnL_total = PnL_realized + PnL_unrealized + income - fees - funding
NAV = cash + marked_positions
```

Devise, FX, precision, rounding et conventions de mark sont versionnés. Toute divergence au-delà de la tolérance déclenche reconciliation failure.

## 11. Stabilité numérique

- précision numérique choisie par domaine ;
- tolérances `atol` et `rtol` documentées ;
- algorithmes stables préférés aux formes naïves ;
- accumulation compensée si nécessaire ;
- Decimal/integer ticks pour montants et prix sensibles ;
- tests sur valeurs extrêmes, très petites et très grandes ;
- aucun arrondi intermédiaire caché.

## 12. Validation indépendante

Chaque algorithme critique possède :

- une spécification indépendante du code ;
- une implémentation de référence lente et simple ou un oracle analytique ;
- une comparaison property-based ;
- des fixtures manuelles vérifiées ;
- une revue mathématique par une personne autre que l'auteur lorsqu'une promotion critique est envisagée.

## 13. Rapport mathématique du lot

Le rapport doit inclure : formules, hypothèses, preuves/propriétés, résultats numériques, tolérances, contre-exemples testés, limites connues, calibration, sensibilité et verdict.

Tout défaut de domaine, d'unité, de temporalité, de calibration ou de stabilité donne `NO_GO_MATHEMATICAL_VALIDATION`.