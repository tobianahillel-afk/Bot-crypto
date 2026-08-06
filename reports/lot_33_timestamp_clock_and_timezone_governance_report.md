# Lot 33 — Timestamp, Clock & Timezone Governance Report

## Scope

Deterministic offline governance of timestamp identity, timezone, precision, ordering, drift,
latency, availability and clock health.

## Certified implementation

```text
status=IMPLEMENTED_VALIDATED_INDEPENDENT_OFFLINE_ONLY
implementation_commit=f4762cb7d68fd11a42962f8016f8af22e2bc1c5a
runtime_mode=DATA_GOVERNANCE_ONLY
instrument=BTC/EUR:SPOT
records=3
source_timezones=Europe/Paris,UTC
precision=MICROSECONDS
same_event_time_records=2
late_record_count=1
```

## Exact observations

```text
max_clock_drift_us=1000
max_out_of_order_delay_us=201000
max_total_latency_us=420000
clock_health_status=HEALTHY
state_output_checksum=4bb5f8df3b49a8a54b6a932a37d35a4575edc63f897c55e88df90dfaf000f450
audit_checksum=73afe6a1d7dc73565d76f7e6d5f7c96cbc4fdecc6dadce88c2e88edb1ca365ad
config_file_checksum=b3bca4910aaeb0151824ac0525a8aae64e9f6d837896798d3b5fae74dbea7516
```

## Quality evidence

```text
line_coverage=98.43% (minimum 95%)
branch_coverage=91.53% (minimum 90%)
mutation_score=90.57% / 96 of 106 killed (minimum 80%)
anti_flake_repetitions=3 PASS
```

The mutation result comes from an independent operator/constant AST campaign over the three
covered temporal modules. The permanent GitHub workflow also defines a full isolated `mutmut`
gate and must be used whenever hosted runners execute.

## Implemented safeguards

- timezone-naive rejection;
- IANA timezone/offset verification;
- exact seconds/milliseconds/microseconds precision enforcement;
- raw timestamp, timezone and precision preservation;
- UTC canonicalization;
- anti-lookahead causal order;
- sequence/revision tie-break;
- deterministic DST fold handling;
- non-negative exact integer-microsecond latency;
- input-order out-of-order delay measurement;
- versioned health thresholds;
- atomic persistence and canonical checksums;
- exact Lot 32 file lineage;
- no network, credentials, market-event publication or trading permission.

## Lineage

```text
instrument_registry_file_checksum=5d514b9a7242d119495e85bc1b56b368e74610f699083007e26c95fddfc83e24
lot32_state_file_checksum=54c721735281161912854b3567e1b6e9e30fb7683bf6f00fc721590ca6037871
lot32_audit_file_checksum=3d71d44a77829dacb8f6477334814205594ba83c958ce1c8cd54d6210f2f4deb
```

## GitHub Actions condition

Permanent exact-head validation and mutation workflows are committed. If the ongoing
hosted-runner/event incident prevents their execution, the PR must record a bounded
infrastructure exception. Unexecuted Ruff, mypy, Bandit, pip-audit and complete repository
regression checks are not represented as PASS.

## Safety

```text
analysis_only=true
used_for_decision=false
external_connectivity_allowed=false
network_ingestion_allowed=false
real_credentials_allowed=false
signal_generation_allowed=false
risk_approval_allowed=false
order_routing_allowed=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

## Verdict

`GO_LOT33_DRAFT_PR_EXACT_HEAD_VALIDATION`

Lot 34 remains locked until Lot 33 is squash-merged and independently audited.
