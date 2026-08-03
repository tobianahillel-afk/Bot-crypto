# Multi-Timeframe Policy — Lot 2

Le Lot 2 transforme une fixture OHLCVT 1m en datasets multi-timeframes déterministes 5m et 15m.

Règles d’agrégation :

```text
open = open de la première candle du bucket
high = max(high)
low = min(low)
close = close de la dernière candle du bucket
volume = somme(volume)
trades = somme(trades)
timestamp = début du bucket
closed_at = timestamp + durée du bucket
available_at = closed_at
```

Anti-look-ahead : une candle agrégée n’est utilisable qu’après clôture complète du bucket. Une candle 5m commençant à 00:00 devient disponible à 00:05. Une candle 15m commençant à 00:00 devient disponible à 00:15.

Le Lot 2 ne produit aucun signal de trading.
