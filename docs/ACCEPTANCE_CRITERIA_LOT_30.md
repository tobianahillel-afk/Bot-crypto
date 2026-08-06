# Acceptance Criteria — Lot 30 V2 Market Analysis Closure

## Required verdict

`GO_LOT30_V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY`

## Functional acceptance

1. The configuration schema is exactly `v2-market-analysis-closure-config-v1`.
2. The version identifier is exactly `V2_MARKET_ANALYSIS`.
3. The runtime ceiling remains `LOCAL_OFFLINE_ANALYSIS_ONLY`.
4. The Lot 29 state checksum is independently recomputed.
5. Lot 29 state, audit and closure manifest remain mutually linked.
6. The Lot 29 upstream lot sequence is exactly `21..28`.
7. Eight upstream artifact paths, checksums and byte sizes are revalidated.
8. Embedded output checksums, when present, match the referenced files.
9. `scripts/validate_lot29.py` runs twice successfully.
10. The two validator stdout checksums are identical.
11. The final covered lot sequence is exactly `21..30`.
12. The final manifest identifies Lot 29 as the direct validated input and Lot 30 as closure.
13. The final state is deterministic across two builds.
14. State, audit and manifest are persisted atomically and validate independently.

## Negative acceptance

All controls must reject the injected invalid state:

- unsupported config schema;
- upstream checksum tampering;
- forbidden permission activation;
- divergent validator replay;
- unauthorized lifecycle unlock.

Any control that does not reject produces `NO_GO`.

## Safety acceptance

The generated state and audit must contain:

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

The future capability lock set must remain exactly:

```text
ContinuousMarketStateV1
MultiHorizonForecastV1
ParticipantBehaviorScenarioV1
TradeIntent
RiskDecisionV1
RiskReservationV1
OrderIntent
```

## Contract acceptance

- JSON schema uses `additionalProperties=false` at state and nested object levels.
- Code commit is a lowercase 40-character Git SHA.
- Every checksum is a lowercase SHA-256.
- Artifact ordering is stable and canonical.
- Reason code ordering is stable and canonical.
- No implicit fallback converts missing or unknown evidence into `PASS`.

## Test and quality acceptance

- compile: `PASS`;
- Ruff: `PASS`;
- mypy: `PASS`;
- targeted line coverage: at least `95%`;
- targeted branch coverage: at least `90%`;
- full repository regression: `PASS`;
- three repeated Lot 30 suites: `PASS`;
- architecture and domain ownership: `PASS`;
- traceability contract: `PASS`;
- roadmap documentation validation: `PASS`;
- Bandit: `PASS`;
- `pip-audit`: `PASS`;
- critical mutation score: at least `80%`;
- repository-wide quality workflow: `PASS`.

## Required artifacts

- `config/closure/v2_market_analysis_closure_v1.json`;
- `contracts/schemas/v2_market_analysis_closure_state_v1.schema.json`;
- `src/crypto_quant_bot/market_analysis/v2_market_analysis_closure.py`;
- `src/crypto_quant_bot/market_analysis/v2_market_analysis_closure_models.py`;
- `scripts/run_lot30_v2_market_analysis_closure.py`;
- `scripts/validate_lot30.py`;
- `scripts/validate_all_until_lot30.py`;
- `scripts/run_required_chain_until_lot30.sh`;
- `scripts/diagnose_exact_chain_until_lot30.py`;
- `tests/test_lot30_v2_market_analysis_closure.py`;
- `tests/test_lot30_mutation_oracles.py`;
- `data/audit/v2_market_analysis_closure_lot30.json`;
- `data/audit/v2_market_analysis_closure_audit_lot30.json`;
- `data/audit/closure_manifest_lot30.json`;
- `reports/lot_30_v2_market_analysis_closure_report.md`.

## Promotion gate

Lot 30 is not promoted merely because one workflow is green. Promotion requires:

- all exact-head checks green;
- generated evidence committed and revalidated;
- no unresolved review thread;
- human review;
- squash merge;
- separate post-merge audit.

Lot 31 remains `PLANNED_LOCKED` until the post-merge audit is merged and a distinct entry
gate explicitly authorizes V3 work.
