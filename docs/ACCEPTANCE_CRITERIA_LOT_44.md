# Acceptance Criteria — Lot 44

Lot 44 is acceptable only when all criteria below are simultaneously satisfied.

## Functional

- Exact reference fixture classifies `UNKNOWN`, `BUY_AGGRESSOR`, `SELL_AGGRESSOR` in source order.
- Quote test has precedence whenever a causally usable quote exists.
- Tick rule is used only when quote data is genuinely unavailable and policy permits it.
- Inside-spread trade remains `UNKNOWN`; it is not forced through tick rule.
- Future, stale or locked quote degrades to `UNKNOWN` and cannot trigger fallback.
- Source trade `side` remains `UNKNOWN`; Lot 44 never trusts a preclassified source side.
- Source/venue/instrument/market mismatch fails closed.
- `event_time <= receive_time`; future state is rejected or degraded, never backfilled.

## Conservation

Reference result must preserve:

- total volume `0.16`;
- buy volume `0.08`;
- sell volume `0.03`;
- unknown volume `0.05`;
- unknown ratio `0.3125`;
- total = buy + sell + unknown.

Unknown volume must never be silently dropped or redistributed.

## Contracts and confidence

- `ClassifiedTradeV1`, `AggressorConfidenceStateV1`, state and audit schemas are closed.
- Confidence semantics are exactly `DESCRIPTIVE_METHOD_CONFIDENCE_NOT_PROBABILITY`.
- Quote-test confidence is `1`, tick-rule confidence `0.5`, unknown confidence `0` under versioned policy `lot44-aggressor-confidence-v1`.
- No Lot 46 model, probability engine, calibration or inference is implemented.

## Determinism and evidence

- Same frozen inputs/config/code commit produce byte-identical state, audit and confidence artifacts on repeated runs.
- State, audit and confidence checksums validate canonically.
- Persisted artifacts must exactly equal a replay when `--require-persisted` is used.
- Input lineage binds gate checksum, frozen Lot 43 evidence, Lot 37 trade fixture checksum and Lot 38 canonical snapshot checksum.

## Quality

- Critical Lot 44 line coverage `>=95%`.
- Critical Lot 44 branch coverage `>=90%`.
- Targeted mutation score `>=80%`.
- Full repository tests PASS.
- Targeted tests PASS three consecutive times.
- Ruff, MyPy, architecture, roadmap, traceability, numeric-coercion, Bandit and dependency audit PASS.

## Safety and lot boundaries

- No external connectivity or credentials.
- `used_for_decision=false`.
- `signal_generation_allowed=false`.
- `risk_approval_allowed=false`.
- `order_routing_allowed=false`.
- `trade_allowed=false`.
- `execution_allowed=false`.
- `approved_size=0`.
- No Lot 45 Order Flow/Delta/CVD implementation path exists.
- No Lot 46 Trade Classification Confidence Engine implementation path exists.
- Participant intent is never asserted as fact.

A technical PASS is not a live-trading authorization.
