# Lot 32 — Instrument, Symbol & Contract Normalization Report

## Scope

Lot 32 implements deterministic, offline instrument identity and venue-alias normalization
inside `MarketDataGovernanceDomain`.

## Certified implementation evidence

```text
status=IMPLEMENTED_VALIDATED_INDEPENDENT_OFFLINE_ONLY
implementation_commit=cd9ffa91a4a64c36a71a40e746cf575fe438d59b
runtime_mode=DATA_GOVERNANCE_ONLY
canonical_instrument=BTC/EUR:SPOT
instrument_count=1
venue_alias_count=3
round_trip_count=6
frozen_instrument_count=0
```

## Implemented controls

- immutable Lot 32 entry-gate checksum;
- exact SourceRegistryV1 and Lot 31 state/audit lineage;
- approved, unauthenticated and disabled source requirement;
- canonical/venue bidirectional mapping;
- exact Decimal arithmetic without binary-float coercion;
- explicit tick, lot, minimum quantity and minimum notional boundaries;
- explicit spot/perpetual/future/option applicability;
- atomic JSON persistence and independent checksums;
- no network/credential import or configuration path;
- fail-closed safety matrix;
- permanent release-evidence assertions.

## Certified values

```text
implementation_commit=cd9ffa91a4a64c36a71a40e746cf575fe438d59b
state_output_checksum=da269de9a3a94f83b3dd437362ae565bd38a098cbe0dc81190887347c7fce240
audit_checksum=b69aa85d72851470f9f807d05ae27127651e6ac8d12623aed8d3f5d96f94659a
config_checksum=92b97faeaca47bab6f03b2f8d880f74796beffdd5db0232f6490f961e8aac59a
source_registry_checksum=d920d24dc5e774e7aa9f221965e88796c6fecdd8bfc61531109b9b4c040c1f29
lot31_state_file_checksum=59d6f01a65cb071a95abe116938709c5112b82462f2b0d1941a01998df2f3955
lot31_audit_file_checksum=3e5b687dc3b76d170e2830c28d8c3a0c20c268ca7c89ebdce30a446f029645f1
tests=57/57 PASS
line_coverage=97.76%
branch_coverage=91.67%
mutation_score=84.13% (175/208 killed)
anti_flake_repetitions=3 PASS
compileall=PASS
forbidden_network_imports=0
```

All mandatory targeted thresholds are satisfied:

- line coverage minimum: 95%;
- branch coverage minimum: 90%;
- mutation minimum: 80%.

## Validation commands

```bash
python scripts/validate_lot32_entry_gate.py
python scripts/run_lot32_instrument_symbol_and_contract_normalization.py --code-commit <sha>
python scripts/validate_lot32.py
python scripts/validate_lot32_no_connectivity.py
pytest -q tests/test_lot32_*.py
```

## Infrastructure exception

GitHub did not create workflow runs for the PR heads during the hosted-runner/event incident.
No failing result was waived. The isolated environment executed compilation, targeted tests,
coverage, mutation, deterministic replay, checksum/lineage verification, no-connectivity and
three anti-flake repetitions.

The tools unavailable in that isolated environment are explicitly recorded rather than
claimed as PASS: `ruff`, `mypy`, `bandit`, `pip-audit`, and the complete repository-wide test
suite. The post-merge audit must execute them whenever GitHub Actions resumes and must keep
Lot 33 locked until the result is recorded.

## Safety boundary

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

`GO_LOT32_SQUASH_MERGE_WITH_DOCUMENTED_GITHUB_ACTIONS_INFRASTRUCTURE_EXCEPTION`

Lot 33 remains `PLANNED_LOCKED` pending the separate Lot 32 post-merge audit.
