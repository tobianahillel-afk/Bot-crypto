# Lot 30 — V2 Market Analysis Closure Report

Verdict: **GO_LOT30_V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY**

- Code commit: `602bc91b2d4c886f654840294fa740474515e0a0`
- Covered lots: `[21, 22, 23, 24, 25, 26, 27, 28, 29, 30]`
- Upstream artifact count: `8`
- Lot 29 validator replays: `2`
- Negative controls: `SCHEMA_MISMATCH_REJECTED, UPSTREAM_CHECKSUM_TAMPER_REJECTED, FORBIDDEN_CAPABILITY_REJECTED, VALIDATOR_DIVERGENCE_REJECTED, LIFECYCLE_UNLOCK_REJECTED`
- Final chain checksum: `2a598990adaec7ebc1368f30295a0130d4d8bd8f89c9610772347f25ba6c17cf`
- Output checksum: `c1cfab56ae33cd0add04af17a375045c631fab780e198f06dce00b5d8dec12ee`
- Critical line coverage: `97.93%`
- Critical branch coverage: `95.27%`
- Critical mutation score: `86.02%` (`991/1152` killed)
- Closure status: `V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY`

The Lot 29 replay state remains the canonical aggregate proof for Lots 21–28.
Lot 30 independently rechecks every referenced artifact checksum, the Lot 29
state/audit/manifest linkage, two identical validator runs, lifecycle locking
and five fail-closed negative controls before closing V2.

No V3 data-governance capability is activated by this closure.
Lot 31 remains `PLANNED_LOCKED` pending the post-merge audit and a separate
exact-commit entry gate.

```text
analysis_only=true
used_for_decision=false
signal_generation_allowed=false
risk_approval_allowed=false
order_routing_allowed=false
trade_allowed=false
execution_allowed=false
approved_size=0
```
