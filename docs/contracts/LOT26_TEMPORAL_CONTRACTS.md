# Lot 26 — Temporal and state contracts

Ces contrats sont normatifs pour le futur moteur du Lot 26. Ils ne constituent pas son implémentation.

## 1. TimeframeMarketContextStateV1

Snapshot analytique confirmé d'un instrument et d'une échelle temporelle, construit sur une barre fermée.

```text
schema_version
state_id
instrument_id
timeframe
scale_id
data_resolution
feature_lookback
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

`forecast_horizon`, `signal_ttl` et `holding_horizon` ne sont pas déduits de `timeframe`.

## 2. ClosedBarAvailabilityV1

Preuve qu'une barre et son état étaient fermés, complets, validés et disponibles.

```text
schema_version
availability_id
instrument_id
timeframe
scale_id
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

`is_closed=false`, `is_complete=false`, qualité invalide ou disponibilité future rendent l'état inconsommable.

## 3. TemporalScaleRegistryV1

Registre de toutes les résolutions connues et de leur statut par lot/version.

```text
registry_id
scale_id
resolution_type
duration_seconds
aggregation_method
publication_policy
state_kind
enabled_in_lot26
lot26_role ou planned_owner
```

Le profil v1 active exactement :

```text
timebar-5m = LOCAL_CONTEXT
timebar-15m = HIGHER_CONTEXT
```

Toutes les autres échelles restent désactivées.

## 4. DecisionClockPolicyV1

Définit les événements autorisés à déclencher une réévaluation.

Lot 26 :

```text
enabled_triggers = [CLOSED_LOCAL_BAR]
duplicate_trigger_behavior = IDEMPOTENT_NO_OP
out_of_order_trigger_behavior = BLOCK_AND_AUDIT
```

Les triggers événementiels futurs restent planifiés et désactivés.

## 5. MultiTimeframeAlignmentStateV1

```text
schema_version
alignment_id
instrument_id
local_scale_id=timebar-5m
higher_scale_id=timebar-15m
decision_trigger=CLOSED_LOCAL_BAR
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
scale_registry_version
decision_clock_policy_version
config_version
config_checksum
analysis_only=true
used_for_decision=false
forecast_generation_allowed=false
signal_generation_allowed=false
order_routing_allowed=false
execution_allowed=false
```

Le score est nullable. `UNKNOWN` n'est jamais converti en zéro.

## 6. Planned future contracts

Les contrats suivants sont enregistrés mais non consommés ni produits par le Lot 26 :

### ContinuousMarketStateV1

État événementiel provisoire, futur owner V3/V4.

### MultiHorizonForecastV1

Distribution prédictive par horizon, futur owner V5 avec validation V6.

### ParticipantBehaviorScenarioV1

Inférence probabiliste d'une classe de participant, ses contraintes, beliefs, actions et payoff proxies, owner V4.

### LiquidityExitZoneV1

Zones de stop-loss, take-profit, break-even, liquidation, congestion, piège, forced exit et défense passive, owner V4.

### ExitPolicyV1 / ProtectiveOrderPlanV1

Politique de sortie de stratégie puis plan d'ordres protecteurs gouverné, owners V5/V7/V15.

Tous portent le statut :

```text
PLANNED_LOCKED_NOT_IMPLEMENTED
```

## 7. JSON schemas

### Lot 26

- `contracts/schemas/timeframe_market_context_state_v1.schema.json`
- `contracts/schemas/closed_bar_availability_v1.schema.json`
- `contracts/schemas/multi_timeframe_alignment_state_v1.schema.json`

### Architecture future verrouillée

- `contracts/schemas/temporal_scale_registry_v1.schema.json`
- `contracts/schemas/decision_clock_policy_v1.schema.json`
- `contracts/schemas/continuous_market_state_v1.schema.json`
- `contracts/schemas/multi_horizon_forecast_v1.schema.json`
- `contracts/schemas/participant_behavior_scenario_v1.schema.json`
- `contracts/schemas/liquidity_exit_zone_v1.schema.json`

## 8. Boundary invariants

```text
alignment != forecast
forecast != scenario
scenario != signal
signal != TradeIntent
TradeIntent != OrderIntent
```

Aucun contrat documenté dans ce fichier n'active une capability de trading.
