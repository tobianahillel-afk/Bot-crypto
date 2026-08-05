# Lot 27 — Global Market Context Aggregator

Status: `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`

Owner: `MarketAnalysisDomain`  
Runtime maximal: `LOCAL_OFFLINE_ANALYSIS_ONLY`

## Objective

Aggregate the validated descriptive outputs of Lots 22–26 into one auditable global market context without treating heterogeneous scores as probabilities or trading evidence.

## Inputs

- `data/audit/market_analysis_lot22.json`;
- `data/audit/technical_indicators_lot23.json`;
- `data/audit/trend_range_momentum_lot24.json`;
- `data/audit/volatility_regime_confluence_lot25.json`;
- `data/audit/multi_timeframe_alignment_engine_lot26.json`;
- `config/math/global_market_context_aggregator_v1.json`.

Every source preserves its artifact checksum, schema/version, state, semantic category, score, configured weight, event time, age, quality and effective contribution.

## Mathematical contract

For included source `i`:

```text
contribution_i = configured_weight_i × descriptive_score_i
```

For semantic category `c`:

```text
support_c = Σ contribution_i where semantic_category_i = c
```

The aggregate evidence score is:

```text
aggregate_evidence_score = Σ contribution_i
```

Missing, invalid or stale sources contribute exactly zero. Their configured weight is retained in `missing_source_weight`; remaining weights are never renormalized.

The v1 categories are:

- `TRENDING`;
- `RANGE`;
- `MIXED`;
- `CONFLICT`.

The global state is `GLOBAL_CONTEXT_MIXED` when explicit conflict support reaches the configured threshold or when the leading support margin is insufficient. It is `GLOBAL_CONTEXT_UNKNOWN` when minimum source count or weighted coverage is not reached.

## Current deterministic oracle

With the validated Lots 22–26 artifacts:

```text
TRENDING support = 0.166955
RANGE support    = 0.151198
MIXED support    = 0.116448
CONFLICT support = 0.130000
aggregate score  = 0.564600
coverage         = 1.000000
dominant state   = GLOBAL_CONTEXT_MIXED
```

The explicit `MTF_DIVERGENT` source remains visible in `conflict_states`.

## Confidence interval policy

The source scores describe different constructs and are not calibrated samples of one random variable. Lot 27 therefore emits `confidence_interval=null` with reason code `GMC_CONFIDENCE_INTERVAL_UNAVAILABLE_UNCALIBRATED`. No statistical interval is invented.

## Failure behavior

- missing source: retained as `MISSING`, zero contribution, original configured weight preserved;
- invalid safety/check state: `INVALID`, zero contribution;
- stale source: `STALE`, zero contribution and age preserved;
- insufficient coverage/count: `GLOBAL_CONTEXT_UNKNOWN`;
- invalid weights/config: fail closed;
- replay mismatch: `GMC_REPLAY_DIVERGENCE`.

## Outputs

- `GlobalMarketContextAggregatorStateV1`;
- `GlobalMarketContextAggregatorAuditV1`;
- `data/audit/global_market_context_aggregator_lot27.json`;
- `data/audit/global_market_context_aggregator_audit_lot27.json`;
- `reports/lot_27_global_market_context_aggregator_report.md`.

## Non-goals

- no forecast or probability;
- no BUY/SELL direction;
- no signal, strategy, sizing, risk approval, trade intent or order;
- no paper, sandbox or live execution;
- no silent weight renormalization;
- no inference that one source automatically vetoes another.

## Safety invariants

```text
analysis_only=true
used_for_decision=false
forecast_generation_allowed=false
probability_claims_allowed=false
signal_generation_allowed=false
order_routing_allowed=false
execution_allowed=false
trade_allowed=false
approved_size=0
```

## Definition of done

- closed contracts and schema;
- deterministic run1/run2 replay;
- real Lots 22–26 integration oracle;
- source ablation and missing-source tests;
- stale/invalid/config negative tests;
- line coverage ≥95%, branch coverage ≥90%;
- mutation score ≥80% on aggregation/classification logic;
- architecture, traceability, security and full regression PASS;
- final report and post-merge audit before Lot 28.
