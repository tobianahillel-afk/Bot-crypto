# Canonical Data and Event Contracts

Tous les contrats sont versionnés, sérialisables en JSON et incluent les identifiants nécessaires au replay et à l'audit. Un contrat documenté peut être `PLANNED_LOCKED_NOT_IMPLEMENTED`; sa présence n'active aucune capability.

## Envelope commun

```text
schema_version
run_id
correlation_id
generated_at
available_at
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

## TemporalScaleRegistryV1

Registre versionné des résolutions et agrégations :

```text
registry_id
scale_id
resolution_type
duration_seconds
aggregation_method
publication_policy
state_kind
enabled_by_lot
```

Le Lot 26 active uniquement `timebar-5m` et `timebar-15m`. Schema : `contracts/schemas/temporal_scale_registry_v1.schema.json`.

## DecisionClockPolicyV1

Sépare le déclenchement d'une réévaluation de la résolution et de l'horizon :

```text
policy_id
trigger_id
causal_event_id
decision_time
required_evidence
idempotency_policy
out_of_order_policy
enabled_by_lot
```

Schema : `contracts/schemas/decision_clock_policy_v1.schema.json`.

## MarketContextStateV1 — historique

Contrat historique utilisé par les Lots 22–25. Il reste normatif pour leurs preuves et n'est pas renommé rétroactivement.

```text
instrument_id, timeframe, as_of, available_at
trend_state, range_state, momentum_state, volatility_state, regime_state
component_scores, confidence, uncertainty, conflicts, reason_codes
used_for_decision=false
```

## TimeframeMarketContextStateV1 — Lot 26+

```text
state_id, instrument_id, timeframe, scale_id
data_resolution, feature_lookback
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

`forecast_horizon`, `signal_ttl` et `holding_horizon` restent distincts. Schema : `contracts/schemas/timeframe_market_context_state_v1.schema.json`.

## ClosedBarAvailabilityV1

```text
availability_id, instrument_id, timeframe, scale_id, source_bar_id
bar_open_time, bar_close_time, available_at, decision_time
is_closed, is_complete, quality_state
revision_id, sequence_id, lineage_id, reason_codes
```

Schema : `contracts/schemas/closed_bar_availability_v1.schema.json`.

## MultiTimeframeAlignmentStateV1

```text
alignment_id, instrument_id
local_scale_id=timebar-5m, higher_scale_id=timebar-15m
decision_trigger=CLOSED_LOCAL_BAR
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
scale_registry_version, decision_clock_policy_version
config_version, config_checksum, lineage_id
analysis_only=true
used_for_decision=false
forecast_generation_allowed=false
signal_generation_allowed=false
order_routing_allowed=false
execution_allowed=false
```

Schema : `contracts/schemas/multi_timeframe_alignment_state_v1.schema.json`.

## ContinuousMarketStateV1 — planned V3/V4

État événementiel provisoire :

```text
state_id, instrument_id, as_of_event_time, available_at
source_event_range, market_quality_state
price_state, volatility_state, liquidity_state
order_flow_state, derivatives_state, latent_regime_state
state_uncertainty, model_ids, config_versions, lineage_id
```

Schema : `contracts/schemas/continuous_market_state_v1.schema.json`. Statut : `PLANNED_LOCKED_NOT_IMPLEMENTED`.

## MultiHorizonForecastV1 — planned V5/V6

Pour chaque horizon enregistré :

```text
forecast_horizon
expected_return, median_return, return_quantiles
volatility_forecast
direction_probability(optional only if calibrated)
target_hit_probability(optional only if calibrated)
stop_hit_probability(optional only if calibrated)
time_to_target_distribution
maximum_adverse_excursion_distribution
maximum_favorable_excursion_distribution
regime_transition_probability(optional only if calibrated)
liquidity_risk, model_uncertainty, data_uncertainty
calibration_id
```

Le contrat inclut `cross_horizon_dependence` et interdit le vote naïf. Schema : `contracts/schemas/multi_horizon_forecast_v1.schema.json`. Statut : `PLANNED_LOCKED_NOT_IMPLEMENTED`.

## ParticipantBehaviorScenarioV1 — planned V4

```text
scenario_id, participant_class, information_set
observable_evidence, counter_evidence, constraints, action_set
payoff_proxy, loss_or_pain_proxy, belief_state
best_response_candidates, bounded_rationality_assumptions
forecast_horizon, invalidation_conditions
confidence_proxy ou calibrated_probability
inference_explicitly_labeled=true
```

Schema : `contracts/schemas/participant_behavior_scenario_v1.schema.json`.

## LiquidityExitZoneV1 — planned V4

Types fermés :

```text
STOP_LOSS_CLUSTER
TAKE_PROFIT_CLUSTER
BREAK_EVEN_CLUSTER
LIQUIDATION_CLUSTER
ENTRY_CONGESTION_ZONE
TRAPPED_POSITION_ZONE
FORCED_EXIT_ZONE
PASSIVE_DEFENSE_ZONE
```

Chaque zone porte bornes de prix, horizons, preuves, contre-preuves, méthode, score/probabilité correctement nommée, incertitude, disponibilité et invalidation. Schema : `contracts/schemas/liquidity_exit_zone_v1.schema.json`.

## ScenarioV1

```text
scenario_id, type, horizon, preconditions
evidence_refs, counter_evidence_refs, invalidation_conditions
score, probability(optional only if calibrated), confidence, status
```

## AlphaHypothesisV1 / StrategyCandidateV1

```text
hypothesis_id/version, mechanism, null_hypothesis, falsification_plan
strategy_id/version, universe, timeframe, forecast_horizon, allowed_regimes
entry_logic_ref, exit_logic_ref, invalidation, holding_horizon
parameter_status(researched/frozen), forbidden_data, expected_cost_model
```

## ExitPolicyV1 — planned V5/V7

```text
exit_policy_id, strategy_id/version
initial_stop_policy, take_profit_policy, break_even_policy
trailing_policy, partial_exit_policy, time_exit_policy
regime_exit_policy, emergency_exit_policy
maximum_holding_horizon
```

## SignalV1

```text
signal_id, strategy_id/version, instrument_id
created_at, expires_at, forecast_horizon, direction_hypothesis, strength
confidence, calibration_id(optional), invalidation_reason
```

Signal ne contient pas de venue, quantité finale ni ordre.

## TradeIntentV1 / RiskDecisionV1 / OrderIntentV1

Ces contrats restent inactifs jusqu'aux versions propriétaires. Aucun état Market Analysis ne peut les créer.

## ProtectiveOrderPlanV1 — planned V15

```text
plan_id, position_or_entry_intent_id, risk_decision_id
stop_order_intent, take_profit_order_intents
oco_group_id, bracket_group_id
activation_rules, quantity_allocation, reduce_only_policy
replacement_policy, expiry_policy, reconciliation_policy
```

## OMSOrderStateV1 / ExecutionEventV1 / FillV1 / PositionStateV1 / PnLStateV1

Contrats futurs versionnés et reconstructibles depuis le ledger.

## IncidentRecordV1

```text
incident_id, severity, detected_at, source_component
symptoms, affected_entities, automatic_action
operator_actions, timeline, root_cause, recovery_evidence, status
```

## Boundary invariants

```text
alignment != forecast
forecast != scenario
scenario != signal
signal != TradeIntent
TradeIntent != RiskDecision
RiskDecision approval != OrderIntent submission
OrderIntent != order
order != fill
fill != reconciled position
```
