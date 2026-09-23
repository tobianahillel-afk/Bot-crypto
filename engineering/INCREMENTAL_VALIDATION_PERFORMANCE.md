# Incremental Validation Performance — ENG-03.8

Before ENG-03.8, production CI called each tier as a standalone CLI:

- T0 once directly, then again inside T1, T2 and the selector → **4 T0 computations**;
- T1 directly, then again inside T2 and selector → **3 T1 computations**;
- T2 directly and again inside selector → **2 T2 computations**;
- selector once.

That is 10 stage invocations for four logical stages.

The production path is now one in-memory chain:

```text
T0 once
  -> T1(precomputed T0)
  -> T2(precomputed T1)
  -> T3/T4 selector(precomputed T2)
```

This is 4 stage invocations: **6 avoided recomputations, a 60% reduction** in tier-function
invocations before any proof-cache benefit.

Standalone CLIs still work for debugging and targeted use. Tier selftests remain independent
and are intentionally not included in production-chain timing.

The orchestrator records:
- per-stage and total elapsed time;
- selected T1 checks and T2 groups;
- whether pytest/full-suite/network/deep assurance/certification ran;
- T3/T4 requirements selected but not executed.

For routine governance changes, pytest, full-suite, network, T3 execution and T4 execution must
all remain absent.

Policy: `config/governance/incremental_validation_policy_v1.json`
Runner: `scripts/governance/run_incremental_validation.py`
