# Canonical Data and Event Contracts

Tous les contrats sont versionnés, sérialisables en JSON et incluent `schema_version`, `run_id`, `correlation_id`, `generated_at`, `validation_state` et `lineage_id`.

## MarketDataEnvelopeV1

```text
source_id, venue, canonical_instrument_id, market_type
event_time, source_time, receive_time, process_time, available_at
sequence_id, revision_id, payload_type, payload
quality_state_id, raw_content_hash
```

## MarketContextStateV1

```text
instrument_id, timeframe, as_of, available_at
trend_state, range_state, momentum_state, volatility_state, regime_state
component_scores, confidence, uncertainty, conflicts, reason_codes
used_for_decision=false jusqu’aux lots dédiés
```

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

Signal ne contient pas de venue, quantity finale ni ordre.

## TradeIntentV1

```text
trade_intent_id, signal_id, strategy_id/version
instrument_id, side_hypothesis, max_risk_budget, horizon
requested_at, expires_at, context/risk references
```

## RiskDecisionV1

```text
risk_decision_id, trade_intent_hash, decision
approved_size, binding_limits, vetoes, reason_codes
risk_state_id, limit_set_version, created_at, expires_at
```

## OrderIntentV1

```text
order_intent_id, trade_intent_id, risk_decision_id
venue, instrument_id, side, order_type, quantity, limit/stop prices
TIF, post_only/reduce_only, idempotency_key
created_at, expires_at, config/instrument versions
```

## OMSOrderStateV1 / ExecutionEventV1

Contient `client_order_id`, venue IDs, current_state, cumulative_qty, leaves_qty, average_price, fees, attempts et causal events. Tout event est idempotent par `event_id`.

## FillV1 / PositionStateV1 / PnLStateV1

Les fills portent venue_fill_id, order IDs, price, qty, fee, liquidity role et event_time. Position et PnL sont reconstruisibles depuis le ledger, avec séparation realized/unrealized/fees/funding/slippage/FX.

## IncidentRecordV1

```text
incident_id, severity, detected_at, source_component
symptoms, affected_entities, automatic_action
operator_actions, timeline, root_cause, recovery_evidence, status
```
