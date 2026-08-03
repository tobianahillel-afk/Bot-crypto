# Acceptance Criteria — Lot 2

Le Lot 2 est accepté seulement si :

```text
- Lot 0 reste valide.
- Lot 1 reste valide.
- fixture 1m de 60 candles présente.
- resampling 5m produit 12 candles.
- resampling 15m produit 4 candles.
- closed_at et available_at respectent la clôture des buckets.
- datasets silver générés.
- datasets gold générés.
- Feature Registry présent.
- toutes les features calculées sont enregistrées.
- aucune feature future_* ou target.
- rapports Lot 2 générés.
- Decision Engine retourne WAIT.
- Risk Engine bloque.
- trade_allowed reste false.
- live_execution reste DISABLED.
- leverage reste FORBIDDEN.
```
