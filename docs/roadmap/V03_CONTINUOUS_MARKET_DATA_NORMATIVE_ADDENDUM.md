# V3 Normative Addendum — Continuous Market Data and Temporal Projection

Ce document complète V3 Lots 31–36.

## Ownership

V3 possède la transformation d'un ensemble de sources en flux canonique continu, temporellement ordonné et auditable. V3 ne produit ni forecast ni signal.

## Lot mapping

### Lot 31

Le Source Registry déclare les capacités événementielles, cadence, timestamps, licence, révisions et qualité de chaque source.

### Lot 32

La normalisation instrument garantit la comparabilité spot/perp/future et les conventions de prix, quantité et notional.

### Lot 33

Le contrat temporel conserve :

```text
source_time
exchange_time
event_time
receive_time
process_time
available_at
monotonic_time si applicable
sequence_id
revision_id
```

Il implémente les règles de disponibilité communes au flux et aux projections.

### Lot 34

Le Data Quality Engine valide valeurs, séquences, staleness, outliers, duplications et états inconnus. Une erreur ne devient jamais zéro.

### Lot 35

Candle/Trade/Book Reconciliation démontre qu'une barre ou feature agrégée est reconstructible depuis les événements autorisés, dans les tolérances publiées.

### Lot 36

La clôture V3 prouve gaps/outages, replay, qualité et déterminisme avant V4.

## Continuous canonical stream

V3 publie `MarketDataEnvelopeV1` dans l'ordre canonique. Il fournit la base de `ContinuousMarketStateV1` mais ne calcule pas les features microstructure appartenant à V4.

## Temporal projections

Les agrégations utilisent `TemporalScaleRegistryV1`. Chaque barre conserve les IDs des événements sources et une preuve de clôture. Les barres time/volume/dollar/tick/imbalance sont des profiles versionnés distincts.

## Tests

- source/event ordering ;
- late and revised events ;
- duplicate and gap handling ;
- UTC/timezone/DST ;
- reconstruction candles from trades ;
- book/trade/candle consistency ;
- `available_at` anti-lookahead ;
- deterministic replay ;
- outage and recovery ;
- no signal/order fields.

## Gate

V4 reste verrouillée tant que le flux continu et les projections ne sont pas réconciliables, suffisamment complets et temporellement sûrs.
