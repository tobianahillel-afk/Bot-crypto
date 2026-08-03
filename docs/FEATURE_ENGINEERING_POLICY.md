# Feature Engineering Policy — Lot 2

Les features du Lot 2 sont uniquement des transformations mathématiques de base, non stratégiques et sans cible.

Règles :

```text
- Une feature à t ne peut utiliser que des candles dont available_at <= available_at de t.
- Une rolling window utilise uniquement le passé et le présent disponible.
- Aucune feature future_*.
- Aucun target.
- Aucun label.
- Aucun signal LONG/SHORT exploitable.
```

Les features non calculables au début des séries valent `null` en JSON et `None` en Python.
