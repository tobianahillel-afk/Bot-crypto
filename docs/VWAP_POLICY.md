# VWAP Policy — Lot 4

Lot 4 ajoute un VWAP session V1 par timeframe.

## Formule

```text
typical_price = (high + low + close) / 3
price_volume = typical_price * volume
vwap_t = sum(price_volume jusqu'à t) / sum(volume jusqu'à t)
```

## Règles

- Si `cumulative_volume = 0`, `vwap = null`.
- Le VWAP d'une candle a `available_at = available_at` de cette candle.
- Le VWAP ne peut utiliser que les candles disponibles jusqu'à `t`.

## Interdictions

- Aucun signal de trading.
- Aucun backtest.
- Aucun paper trading.
- Aucun champ `target`, `label` ou `future_*`.
