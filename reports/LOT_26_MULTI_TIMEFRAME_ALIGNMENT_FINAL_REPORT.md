# Lot 26 — Multi-Timeframe Alignment Final Report

Verdict: **GO_LOT26_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY**

## Deterministic Lot 25 → Lot 26 evidence

- Edge: `timebar-5m → timebar-15m`
- Join: `ASOF_BACKWARD`
- Contexts: `2` (`5m`, `15m`)
- Available components: `6/6`
- Weighted coverage: `1.0`
- Agreement score: `0.65`
- Alignment state: `MTF_DIVERGENT`
- Divergence state: `MTF_MULTI_COMPONENT_MISMATCH`
- Hard mismatches: `regime`, `volatility`
- Output checksum: `c5238d4e3782ab0ae75b6dae84724f061c11917f07ee899d2341ece2e031d556`
- Decision-evidence checksum: `6b633e1f1ff340c751462851101e18f156bd1d4b04347bac519cebd79ec9a1ee`
- Replay: `MATCH`

## Exact-head quality evidence

- Lot 26 tests: `108 PASS`
- Lot 26 line coverage: `98.73%`
- Lot 26 branch coverage: `97.12%`
- Repository assurance: `832 tests PASS`
- Repository line coverage: `94.63%`
- Repository branch coverage: `86.77%`
- Critical mutation score: `82.43%` (`455/552` evaluated)
- Security and dependencies: `Bandit PASS`, `pip-audit PASS`
- Anti-flake: `3/3 PASS`
- Architecture, ownership, roadmap, lifecycle and traceability: `PASS`

The exact certification SHA is recorded by GitHub Actions in the successful PR workflow metadata and uploaded assurance artifacts. This source-controlled report intentionally avoids a self-referential commit hash.

## Interpretation

The score `0.65` describes compatibility between confirmed 5m and 15m contexts. It is not a directional probability, a return forecast, an alpha signal or a trade authorization. Strong volatility and regime mismatches classify the result as `MTF_DIVERGENT` without applying any trading veto because Lot 26 makes no trading decision.

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
live_execution=DISABLED
```

## Promotion decision

Lot 26 is eligible for merge after the final exact-head CI cycle. Forecasting, alpha, paper, sandbox and live capital remain `NO_GO`. Lot 27 remains locked until post-merge validation succeeds.
