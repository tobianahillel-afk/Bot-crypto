# Lot 32 — Post-Merge Validation Matrix

| Requirement | Independent evidence | Expected result |
|---|---|---|
| Lot 31 historical governance remains valid | `python scripts/validate_lot31.py` | PASS |
| Lot 32 entry gate remains immutable | `python scripts/validate_lot32_entry_gate.py` | PASS |
| State, audit and registry remain linked | `python scripts/validate_lot32.py` | PASS |
| No network or credential path exists | `python scripts/validate_lot32_no_connectivity.py` | PASS |
| State and audit checksums recompute | `tests/test_lot32_post_merge_state.py` | PASS |
| Lot 31 file lineage remains exact | `tests/test_lot32_release_evidence.py` | PASS |
| Canonical/venue round-trips remain exact | 3 aliases / 6 checks | PASS |
| Certified spot applicability remains strict | derivative fields explicit null | PASS |
| Coverage thresholds remain certified | 97.76% lines / 91.67% branches | PASS |
| Mutation threshold remains certified | 84.13% / 175 of 208 killed | PASS |
| Lifecycle identifies Lot 32 as current | `roadmap_lifecycle_overlay_lot32.json` | PASS |
| Lot 33 remains locked | status + implementation flag | PASS |
| Architecture, ownership and coercion gates | permanent repository validators | PASS when runner available |
| Full regression and anti-flake | permanent repository suite | PASS when runner available |
| Ruff, mypy, Bandit and dependency audit | dedicated exact-head workflow | PASS when runner available |

## Safety invariants

```text
runtime_mode=DATA_GOVERNANCE_ONLY
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

## Promotion boundary

```text
lot32_status=IMPLEMENTED_VALIDATED_NORMALIZATION_ONLY
lot33_status=PLANNED_LOCKED
lot33_implementation_started=false
```

A separate exact-head Lot 33 entry-gate PR and explicit human start decision are required
before any Lot 33 implementation branch is created.
