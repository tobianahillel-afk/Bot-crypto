# Lot 26 — Temporal and state contracts

Ces contrats sont normatifs pour le futur moteur du Lot 26. Ils ne constituent pas son
implémentation.

## TimeframeMarketContextStateV1

Snapshot analytique d’un instrument et d’un timeframe, construit sur une barre fermée.

Champs obligatoires :

```text
schema_version
state_id
instrument_id
timeframe
bar_open_time
bar_close_time
event_time
available_at
decision_time
generated_at
source_bar_id
revision_id
sequence_id
lineage_id
config_version
code_commit
validation_state
trend_state
range_state
momentum_state
volatility_state
regime_state
confluence_state
component_scores
reason_codes
analysis_only=true
used_for_decision=false
execution_allowed=false
```

Invariants :

```text
bar_open_time < bar_close_time
event_time <= bar_close_time
bar_close_time <= available_at
available_at <= decision_time
revision_id >= 0
sequence_id >= 0
```

## ClosedBarAvailabilityV1

Preuve qu’une barre et son état étaient fermés, validés et disponibles.

```text
schema_version
availability_id
instrument_id
timeframe
source_bar_id
bar_open_time
bar_close_time
available_at
decision_time
is_closed
is_complete
quality_state
revision_id
sequence_id
lineage_id
reason_codes
```

`is_closed=false`, `is_complete=false`, qualité invalide ou disponibilité future rendent l’état
inconsommable.

## MultiTimeframeAlignmentStateV1

```text
schema_version
alignment_id
instrument_id
local_timeframe=5m
higher_timeframe=15m
decision_time
local_state_id
higher_state_id
local_bar_close_time
higher_bar_close_time
join_method=ASOF_BACKWARD
component_alignment_scores
available_component_count
weighted_coverage_ratio
overall_agreement_score
alignment_state
divergence_state
coherence_state
combined_context_state
hard_mismatch_components
reason_codes
uncertainty_state
lineage_id
config_version
config_checksum
analysis_only=true
used_for_decision=false
signal_generation_allowed=false
order_routing_allowed=false
execution_allowed=false
```

Le score est nullable. `UNKNOWN` n’est jamais converti en zéro.

## JSON schemas

- `contracts/schemas/timeframe_market_context_state_v1.schema.json`
- `contracts/schemas/closed_bar_availability_v1.schema.json`
- `contracts/schemas/multi_timeframe_alignment_state_v1.schema.json`
