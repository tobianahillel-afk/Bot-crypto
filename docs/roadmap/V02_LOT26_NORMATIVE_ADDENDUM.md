# V2 Lot 26 — Normative readiness addendum

Ce document complète et, en cas d’ambiguïté, prévaut sur la section Lot 26 de
`V02_MARKET_ANALYSIS_OFFLINE.md`.

## Clarification centrale

Le flux peut être continu, mais le moteur travaille sur des snapshots issus de barres fermées.
Le timeframe n’est pas une limitation de l’ingestion : il est une vue agrégée avec une cadence et
une disponibilité propres.

```text
5m = contexte local, mise à jour fréquente
15m = contexte supérieur, mise à jour plus lente
```

Le même 15m peut contextualiser plusieurs 5m. Une divergence est informative.

## Documents normatifs

- `docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md`
- `docs/ACCEPTANCE_CRITERIA_LOT_26.md`
- `docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md`
- `docs/adr/ADR_0001_TIME_SEMANTICS_AND_ASOF_JOIN.md`
- `docs/contracts/LOT26_TEMPORAL_CONTRACTS.md`
- `config/math/multi_timeframe_alignment_v1.json`

## Frontière Game Theory

La théorie des jeux et la microstructure restent en V4 Lots 37–52. Lot 26 peut seulement produire
un contexte multi-timeframe consommable ultérieurement par ces domaines. Il ne prétend pas observer
les stops réels ni prédire le comportement d’un participant.

## Gate

Le Lot 26 reste `PLANNED_LOCKED` jusqu’au rapport pré-Lot26 `GO` et à une activation explicite.
