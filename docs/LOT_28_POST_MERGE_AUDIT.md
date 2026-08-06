# Lot 28 — Post-merge audit

Status: `AUDIT_IN_PROGRESS_AWAITING_EXACT_COMMIT_CI`

## Audited baseline

- merged `main` commit: `073e0e7b424b456cc409016d273a2ca78b7d698c`;
- release version: `0.28.0`;
- merged implementation PR: `#10`;
- runtime ceiling: `LOCAL_OFFLINE_ANALYSIS_ONLY`.

## Permanent assertions

- independently recompute the canonical state checksum;
- verify state-to-audit checksum linkage and replay `MATCH`;
- verify 14 structured statements and exactly 3 ordered why-not-trade reasons;
- verify dominant reason `WNT_PERMISSIONS_DISABLED`;
- verify release version, report, worklog and lifecycle overlay consistency;
- verify Lot 29 remains `PLANNED_LOCKED`;
- verify no release-finalization scaffolding remains;
- verify all trading, routing and execution permissions remain disabled.

## Safety invariants

```text
analysis_only=true
used_for_decision=false
forecast_generation_allowed=false
probability_claims_allowed=false
signal_generation_allowed=false
risk_approval_allowed=false
order_routing_allowed=false
execution_allowed=false
trade_allowed=false
approved_size=0
```

The audit does not unlock Lot 29 until every permanent workflow passes on the exact audit head and the audit PR is merged.
