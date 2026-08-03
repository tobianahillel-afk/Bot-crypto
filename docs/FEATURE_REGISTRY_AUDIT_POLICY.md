# Lot 8 — Feature Registry Audit Policy

Le Feature Registry est obligatoire parce qu'il constitue la liste explicite des features autorisées dans **Crypto Quant Bot V3.1-Ops**. Une feature absente du registre ne peut pas être considérée comme gouvernée, documentée ou auditée.

## Risque couvert

Une feature non déclarée peut introduire :

- une dépendance cachée à une donnée future ;
- une différence entre documentation et code ;
- un comportement difficile à auditer ;
- une dérive vers un signal de trading non autorisé.

Le Lot 8 vérifie donc que `config/feature_registry.yaml` et `docs/FEATURE_REGISTRY.md` existent, que les entrées possèdent les champs obligatoires et que les datasets audités ne contiennent pas de feature absente du registre.

## Champs obligatoires

Chaque entrée doit contenir :

```text
name
description
inputs
formula
timeframe
available_at_rule
lookahead_safe
status
```

`available_at_rule` explique quand la feature devient observable. `lookahead_safe` indique si la formule est construite sans dépendre d'une donnée future.

## Limites V1

L'audit V1 vérifie la structure et les noms de features observables dans les datasets gold. Il ne prouve pas mathématiquement chaque formule ligne par ligne. Les formules déjà validées des Lots 2 à 7 restent inchangées.
