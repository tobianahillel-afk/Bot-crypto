# Lot 32 — Instrument, Symbol & Contract Normalization Report

## Scope

Lot 32 implements deterministic, offline instrument identity and venue-alias normalization
inside `MarketDataGovernanceDomain`.

## Current implementation evidence

```text
status=IMPLEMENTATION_IN_PROGRESS_AWAITING_EXACT_HEAD_VALIDATION
runtime_mode=DATA_GOVERNANCE_ONLY
canonical_instrument=BTC/EUR:SPOT
instrument_count=1
venue_alias_count=3
expected_round_trip_count=6
```

## Implemented controls

- immutable Lot 32 entry-gate checksum;
- strict SourceRegistryV1 lineage;
- approved, unauthenticated and disabled source requirement;
- canonical/venue bidirectional mapping;
- exact Decimal arithmetic without binary float coercion;
- explicit tick, lot, minimum quantity and minimum notional boundaries;
- explicit spot/perpetual/future/option applicability;
- atomic JSON persistence and independent checksums;
- no network/credential import or configuration path;
- fail-closed safety matrix.

## Validation commands

```bash
python scripts/validate_lot32_entry_gate.py
python scripts/run_lot32_instrument_symbol_and_contract_normalization.py --code-commit <sha>
python scripts/validate_lot32.py
python scripts/validate_lot32_no_connectivity.py
pytest -q tests/test_lot32_instrument_symbol_and_contract_normalization.py
pytest -q
```

CI additionally executes Ruff, mypy, line/branch coverage, architecture, ownership,
traceability, no-silent-coercion, Bandit, dependency audit, mutation testing and three
anti-flake repetitions.

## Pending certified values

```text
implementation_commit=PENDING
state_output_checksum=PENDING
audit_checksum=PENDING
config_checksum=PENDING
source_registry_checksum=PENDING
line_coverage=PENDING
branch_coverage=PENDING
mutation_score=PENDING
```

These values will be replaced only after successful validation on the exact implementation
head. This report does not claim completion in advance.

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

## Current verdict

`NO_GO_PROMOTION_IMPLEMENTATION_IN_PROGRESS`

Lot 33 remains `PLANNED_LOCKED`.
