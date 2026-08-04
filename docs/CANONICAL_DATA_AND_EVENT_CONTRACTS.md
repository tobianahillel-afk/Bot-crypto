# Canonical Data and Event Contracts

Tous les contrats sont versionnés, sérialisables en JSON et incluent les identifiants nécessaires
au replay et à l’audit.

## Envelope commun

```text
schema_version
run_id
correlation_id
generated_at
validation_state
lineage_id
config_version
code_commit
reason_codes
```

## MarketDataEnvelopeV1

```text
source_id, venue, canonical_instrument_id, market_type
event_time, source_time, receive_time, process_time, available_at
sequence_id, revision_id, payload_type, payload
quality_state_id, raw_content_hash
```

## MarketContextStateV1 — historique

Contrat historique utilisé par les Lots 22–25. Il reste normatif pour leurs preuves et n’est pas
renommé rétroactivement.

```text
instrument_id, timeframe, as_of, available_at
trend_state, range_state, momentum_state, volatility_state, regime_state
component_scores, confidence, uncertainty, conflicts, reason_codes
used_for_decision=false
```

## TimeframeMarketContextStateV1 — Lot 26+

Adaptateur temporel explicite autour des états historiques :

```text
state_id, instrument_id, timeframe
bar_open_time, bar_close_time, event_time
available_at, decision_time, generated_at
source_bar_id, revision_id, sequence_id
trend_state, range_state, momentum_state
volatility_state, regime_state, confluence_state
component_scores, validation_state
analysis_only=true
used_for_decision=false
execution_allowed=false
```

Schema :
`contracts/schemas/timeframe_market_context_state_v1.schema.json`.

## ClosedBarAvailabilityV1

Preuve qu’une barre était fermée, complète, validée et disponible à l’instant évalué.

```text
availability_id, instrument_id, timeframe, source_bar_id
bar_open_time, bar_close_time, available_at, decision_time
is_closed, is_complete, quality_state
revision_id, sequence_id, lineage_id, reason_codes
```

Schema :
`contracts/schemas/closed_bar_availability_v1.schema.json`.

## MultiTimeframeAlignmentStateV1

```text
alignment_id, instrument_id
local_timeframe=5m, higher_timeframe=15m
decision_time, local_state_id, higher_state_id
local_bar_close_time, higher_bar_close_time
join_method=ASOF_BACKWARD
component_alignment_scores
available_component_count
weighted_coverage_ratio
overall_agreement_score(nullable)
alignment_state, divergence_state, coherence_state
combined_context_state, hard_mismatch_components
uncertainty_state, reason_codes
config_version, config_checksum, lineage_id
analysis_only=true
used_for_decision=false
signal_generation_allowed=false
order_routing_allowed=false
execution_allowed=false
```

Schema :
`contracts/schemas/multi_timeframe_alignment_state_v1.schema.json`.

## ScenarioV1

```text
scenario_id, type, horizon, preconditions
evidence_refs, counter_evidence_refs, invalidation_conditions
score, probability(optional only if calibrated), confidence, status
```

## AlphaHypothesisV1 / StrategyCandidateV1

```text
hypothesis_id/version, mechanism, null_hypothesis, falsification_plan
strategy_id/version, universe, timeframe, allowed_regimes
entry_logic_ref, exit_logic_ref, invalidation, holding_horizon
parameter_status(researched/frozen), forbidden_data, expected_cost_model
```

## SignalV1

```text
signal_id, strategy_id/version, instrument_id
created_at, expires_at, direction_hypothesis, strength
confidence, calibration_id(optional), invalidation_reason
```

Signal ne contient pas de venue, quantité finale ni ordre.

## TradeIntentV1 / RiskDecisionV1 / OrderIntentV1

Ces contrats restent inactifs jusqu’aux versions propriétaires. Aucun état Market Analysis ne peut
les créer.

## OMSOrderStateV1 / ExecutionEventV1 / FillV1 / PositionStateV1 / PnLStateV1

Contrats futurs versionnés et reconstructibles depuis le ledger.

## IncidentRecordV1

```text
incident_id, severity, detected_at, source_component
symptoms, affected_entities, automatic_action
operator_actions, timeline, root_cause, recovery_evidence, status
```
