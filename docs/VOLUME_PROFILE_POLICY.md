# Volume Profile Policy — Lot 4

Lot 4 ajoute un Volume Profile V1 candle-based. Il produit des objets d'analyse uniquement.

## Méthode V1

- `bin_size = 50.0`.
- Chaque candle est répartie dans les bins couverts par `[low, high]`.
- Si une candle couvre `N` bins, `volume/N` et `trades/N` sont ajoutés à chaque bin.
- Si `high == low`, tout le volume est affecté au bin du prix unique.

## POC / HVN / LVN

- POC : bin avec le plus gros volume.
- HVN : bin dont `volume_share >= moyenne + écart-type`.
- LVN : bin dont `volume_share <= moyenne - écart-type`.
- Si l'écart-type est nul ou le nombre de bins trop faible, HVN/LVN peuvent être vides.
- Le POC doit exister si le profil contient du volume.

## Anti-look-ahead

Un profil couvrant `[start, end]` est disponible seulement après `end`.

```text
available_at = end_timestamp
```

## Limites

Ce Volume Profile est une approximation candle-based. Il ne reconstruit pas la distribution exacte des trades dans la candle.

## Interdictions

- Aucun signal LONG/SHORT.
- Aucun target.
- Aucun label.
- Aucun champ `future_*`.
- Aucun trading.
- Aucun backtest.
