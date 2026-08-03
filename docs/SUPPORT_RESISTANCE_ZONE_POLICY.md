# Support / Resistance Zone Policy — Lot 3

Lot 3 creates simple price zones from confirmed fractal pivots.

Rules:

```text
pivot low  -> support
pivot high -> resistance
```

Zone width:

```text
zone_width_pct = 0.001
lower_bound = price * (1 - zone_width_pct)
upper_bound = price * (1 + zone_width_pct)
center_price = price
```

The zone inherits its `usable_from` from the source pivot. Zones are analytical objects only and always have:

```text
used_for_decision = false
```

Lot 3 does not merge nearby zones intelligently. Advanced zone clustering is out of scope.
