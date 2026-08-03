# Lot 8 — Acceptance Criteria

Le Lot 8 est accepté si :

- le contrat `contracts/audit.py` existe ;
- le module `crypto_quant_bot.audit` existe ;
- les scripts d'audit Lot 8 génèrent leurs JSON et rapports Markdown ;
- `validate_lot8.py` valide directement le Lot 8 sans lancer les validations des lots précédents ;
- `missing_from_registry` est vide ;
- `forbidden_feature_names` est vide ;
- `lookahead_violations` est vide ;
- `available_at_violations` est vide ;
- `used_for_decision_violations` est vide ;
- aucun dataset audité ne contient `future_*`, `target`, `label` ou signal LONG/SHORT ;
- `DecisionEngine` retourne toujours `WAIT` ;
- `RiskEngine` bloque toujours par défaut ;
- `trade_allowed` reste `false` ;
- `live_execution` reste `DISABLED` ;
- `leverage` reste `FORBIDDEN` ;
- tous les tests unitaires des Lots 0 à 8 passent.

## Sorties attendues

```text
data/audit/feature_registry_audit_lot8.json
data/audit/no_lookahead_audit_lot8.json
reports/lot_08_feature_registry_audit_report.md
reports/lot_08_no_lookahead_report.md
```

## Limites V1

L'audit V1 se concentre sur la gouvernance, les noms de clés et la cohérence temporelle générique. Il ne modifie pas les calculs déjà validés des Lots 2 à 7.
