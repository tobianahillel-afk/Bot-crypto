# PRE_LOT26_ENTRY_GATE

Projet : **Crypto Quant Bot V3.1-Ops**  
Nature : gate transversal de readiness, sans numéro de lot.  
Conséquence runtime : aucune.

## Objectif

Autoriser ou refuser le démarrage de l’implémentation du Lot 26 à partir de preuves objectives.
Ce gate ne calcule aucun signal et n’implémente pas le moteur multi-timeframe.

## Conditions d’entrée

- baseline P0 fusionnée dans `main` ;
- CI institutionnelle verte sur la baseline ;
- Lot 25 toujours validé ;
- Lot 26 toujours `PLANNED_LOCKED` ;
- invariants no-trading inchangés.

## Artefacts obligatoires

- ADR temporel ;
- contrats JSON Schema ;
- spécification mathématique ;
- configuration versionnée ;
- spécification complète du Lot 26 ;
- critères d’acceptation ;
- matrice exigences → tests ;
- README et règles de contribution à jour ;
- environnement Python et dépendances verrouillés ;
- validateur automatique et rapport.

## Règles de temps

L’ingestion peut être continue. Les états 5m et 15m sont néanmoins des snapshots construits
uniquement à partir de barres fermées. Le moteur futur sera déclenché par une nouvelle barre locale
5m fermée et cherchera le dernier état 15m admissible par jointure `ASOF_BACKWARD`.

Une barre est admissible si :

```text
bar_close_time <= available_at <= decision_time
```

Une révision n’est admissible que si sa propre date de disponibilité respecte la même règle.

## Séparation de responsabilité

Le Lot 26 :

- compare des contextes temporels ;
- expose alignement, divergence, cohérence et couverture ;
- ne produit ni probabilité, ni alpha, ni signal, ni ordre ;
- ne déduit pas le comportement des participants.

Les inférences sur stops, take-profit, liquidité, sweeps, fakeouts, absorption et théorie des jeux
restent en V4 / Lots 37–52.

## Verdict

`GO` seulement si :

- tous les fichiers obligatoires existent ;
- schemas/configs sont valides ;
- poids = 1 dans la tolérance ;
- matrices complètes et bornées ;
- tests du validateur PASS ;
- roadmap cohérente ;
- aucune capability interdite activée ;
- aucune preuve historique Lots 0–25 modifiée ;
- CI verte sur le commit exact.

Sinon : `NO_GO_PRE_LOT26_READINESS`.
