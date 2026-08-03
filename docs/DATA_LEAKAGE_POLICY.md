# Lot 8 — Data Leakage Policy

Le Lot 8 interdit les noms de clés qui pourraient matérialiser une cible, un label supervisé ou un signal exploitable avant les phases explicitement prévues pour cela.

## Champs interdits dans les datasets audités

```text
future_
target
label
signal
long_signal
short_signal
trade_signal
entry_signal
exit_signal
buy
sell
```

L'audit porte sur les noms de clés JSONL, pas sur une phrase documentaire. Un texte de documentation peut expliquer le mot `signal`, mais un dataset gold ne doit pas contenir un champ appelé `signal`, `target`, `label`, `future_return`, `buy`, `sell`, etc.

## Pourquoi c'est interdit

Ces champs peuvent transformer un dataset d'analyse en dataset d'apprentissage supervisé ou en moteur de décision implicite. Avant les lots de backtest supervisés, ils créeraient un risque de fuite temporelle, d'optimisation cachée ou de signal LONG/SHORT exploitable.

## Ce que le Lot 8 ne fait pas

Le Lot 8 ne crée aucune stratégie, aucun backtest, aucun paper trading, aucun ML, aucun appel API, aucun WebSocket et aucune exécution live.
