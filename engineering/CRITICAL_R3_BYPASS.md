# Critical R3 Bypass Qualification — ENG-08.7

## Verdict

**CRITICAL_R3_BYPASS_PASS**

The final qualified implementation head is:

`d0bf1381298ea81356e469afec4e9f5a90deefda`

Both mandatory evidence workflows passed on that **same exact head**:

- Engineering Bootstrap: run `36121700188` — SUCCESS
- Security Secrets: run `36121700184` — SUCCESS

## R3 assurance floor

The permanent cross-layer qualification proves that R3 work cannot remove:

- T3: `RISK_EXECUTION_ASSURANCE`
- T4: `EXACT_HEAD_CERTIFICATION`
- T4: `R3_FULL_CERTIFICATION_CHAIN`

On the qualified head:

- T3/T4 selector selftest: **16 probes PASS**
- exact-head binding selftest: **12 probes PASS**
- deep-assurance selftest: **16 probes PASS**
- exact-head binding resolved HEAD `d0bf1381...` and tree `d66c3737...`

WU02 did **not** modify the R3 selector policy, deep-assurance policy, exact-head policy, or
Engineering Bootstrap workflow. It only repaired lifecycle-generic recovery/context evidence.

## Interruption / recovery

Permanent recovery now derives the expected task and AWU from canonical project state plus the
unique validated active AWU; it has no ENG-08.6-specific authorization expectation.

Qualified result:

- recovery: **PASS**, 13 scenarios, 236.169 ms / 1000 ms
- recovery adversarial selftest: **17 probes PASS**, 347.015 ms
- cold-start regression: **PASS**, 10 negative probes, 38.066 ms
- bounded route: 8 primary + 2 reference files, 69 KiB
- chat/model-memory required: **false**
- state auto-heal: **false**
- resumed write authorization: **false**
- required before write: `LIVE_GIT_REVERIFY_REQUIRED`

Stale or missing handoff/context may trigger reconciliation, but cannot redirect the active work
away from canonical state/AWU authority.

## Secret and cost assurance

Security Secrets run `36121700184` passed with pinned Gitleaks 8.30.1 and found **0** secrets
in the final introduced Git range.

The mandatory path continues to require no paid LLM/API, paid SaaS, or paid larger runner.

## Safety preservation

The qualification preserves:

- BUSINESS development: `PAUSED`
- Lot46: `LOCKED`
- runtime maximum: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`
- trading: disabled
- execution: disabled
- live execution: `DISABLED`
- leverage and withdrawals: forbidden

This evidence does not unlock Lot45 remediation, Lot46, or any live-trading capability.
