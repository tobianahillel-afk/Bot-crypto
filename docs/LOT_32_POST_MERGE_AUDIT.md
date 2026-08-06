# Lot 32 — Post-Merge Audit

## Scope

This audit independently verifies the squash-merged Lot 32 implementation and advances the
current repository lifecycle to version `0.32.0`.

```text
pull_request=21
merged_commit=7187f2ebfebeb67292c8a521e7e8bdbc653c3086
implementation_evidence_commit=cd9ffa91a4a64c36a71a40e746cf575fe438d59b
runtime_mode=DATA_GOVERNANCE_ONLY
```

## Independently verified artifacts

```text
state=data/audit/instrument_symbol_and_contract_normalization_lot32.json
state_output_checksum=da269de9a3a94f83b3dd437362ae565bd38a098cbe0dc81190887347c7fce240
audit=data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json
audit_checksum=b69aa85d72851470f9f807d05ae27127651e6ac8d12623aed8d3f5d96f94659a
registry=data/audit/instrument_registry_lot32.json
config_checksum=92b97faeaca47bab6f03b2f8d880f74796beffdd5db0232f6490f961e8aac59a
source_registry_checksum=d920d24dc5e774e7aa9f221965e88796c6fecdd8bfc61531109b9b4c040c1f29
lot31_state_file_checksum=59d6f01a65cb071a95abe116938709c5112b82462f2b0d1941a01998df2f3955
lot31_audit_file_checksum=3e5b687dc3b76d170e2830c28d8c3a0c20c268ca7c89ebdce30a446f029645f1
```

The audit recomputes the canonical state and audit checksums, verifies state/audit/registry
linkage, verifies the three Lot 31 lineage file hashes, and verifies that the audit and state
refer to the same valid Git commit.

## Normalization evidence

```text
canonical_symbol=BTC/EUR:SPOT
instrument_count=1
venue_alias_count=3
round_trip_count=6
frozen_instrument_count=0
BITSTAMP=btceur
COINBASE=BTC-EUR
KRAKEN=XBTEUR
```

Every alias remains metadata-only, margin-free for the certified spot contract and linked to
an approved, unauthenticated and connection-disabled Lot 31 source revision.

## Certified quality evidence

```text
tests=57/57 PASS
line_coverage=97.76%
branch_coverage=91.67%
mutation_score=84.13%
killed_mutants=175
evaluated_mutants=208
anti_flake_repetitions=3 PASS
compileall=PASS
forbidden_network_imports=0
```

The permanent release tests require line coverage >= 95%, branch coverage >= 90% and
mutation >= 80%.

## GitHub Actions infrastructure exception

During the Lot 31 post-merge audit, Lot 32 entry gate and Lot 32 implementation, GitHub did
not create or start the expected pull-request workflow runs. No red test was waived and no
unexecuted tool is represented as successful.

The implementation evidence explicitly did not claim the following unavailable checks as
PASS:

- Ruff;
- mypy;
- Bandit;
- pip-audit;
- complete repository-wide regression.

This post-merge audit includes a dedicated workflow that attempts those checks again. If the
hosted-runner incident remains active, the PR must record the same bounded infrastructure
exception. Lot 33 remains locked in either case until this audit is merged.

## Safety invariants

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

## Lifecycle result

```text
project_version=0.32.0
latest_implemented_lot=32
lot32_status=IMPLEMENTED_VALIDATED_NORMALIZATION_ONLY
lot33_status=PLANNED_LOCKED
lot33_implementation_started=false
```

## Verdict

`GO_LOT32_POST_MERGE_AUDIT`

This verdict validates only deterministic offline normalization and its governance evidence.
It does not activate canonical time publication, live metadata, market events, forecasts,
signals, risk approval or execution.
