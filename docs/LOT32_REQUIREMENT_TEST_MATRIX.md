# Lot 32 — Requirement/Test Matrix

| Requirement | Contract or implementation | Primary evidence |
|---|---|---|
| Immutable entry gate | `data/audit/lot32_v3_entry_gate.json` | `tests/test_lot32_v3_entry_gate.py` |
| Certified Lot 31 source lineage | `Lot32LineageEnvelopeV1` | `test_build_is_deterministic_linked_and_fail_closed` |
| Canonical instrument identity | `InstrumentSpecificationV1` | `test_market_type_applicability_is_explicit` |
| Unique instrument IDs and symbols | `InstrumentRegistryV1` | `test_registry_rejects_duplicate_canonical_and_venue_aliases` |
| Unique venue aliases | `InstrumentRegistryV1` | `test_registry_rejects_duplicate_canonical_and_venue_aliases` |
| Canonical ↔ venue round-trip | registry lookup methods | `test_registry_round_trip_is_exact_for_all_venues` |
| Decimal strings only | `decimal_value` | `test_decimal_and_quantization_contracts_are_exact` |
| Floor quantization | `quantize_to_increment` | `test_decimal_and_quantization_contracts_are_exact` |
| Minimum quantity/notional | `normalize_candidate_amounts` | `test_quantization_rejects_boundary_breaches` |
| Explicit spot applicability | `InstrumentSpecificationV1` | `test_market_type_applicability_is_explicit` |
| Derivative applicability | `InstrumentSpecificationV1` | `test_incomplete_derivative_contracts_fail_closed` |
| Unknown source/revision frozen | `_build_alias` fail-closed checks | `test_build_rejects_unknown_source_revision_enabled_source_and_gate_tampering` |
| Connected/authenticated source forbidden | `_source_entries` | same negative test plus `validate_lot32_no_connectivity.py` |
| Causal availability | state contract | `test_state_lineage_metrics_and_safety_are_strict` |
| Fail-closed permissions | state/audit contracts | same state/safety test |
| Atomic persistence | `persist_lot32_artifacts` | `test_persistence_writes_three_identical_linked_artifacts` |
| Deterministic replay | `build_lot32_artifacts` | `test_build_is_deterministic_linked_and_fail_closed` |
| Strict JSON schemas | four Lot 32 schemas | `test_schemas_are_strict_and_safety_is_constant` |
| No external connectivity | AST/config boundary validator | `scripts/validate_lot32_no_connectivity.py` |
| Full non-regression | repository suite | Lot 32 validation workflow |
| Mutation >= 80% | isolated mutation workflow | Lot 32 mutation workflow |
| Lot 33 locked | gate, state reason code and docs | release and post-merge tests |

## Negative-control expectations

Every injected anomaly must fail before a valid output is persisted. Tests must assert the
specific boundary reached: checksum, source identity, source revision, canonical identity,
contract applicability, decimal syntax, minimum constraint, causal time or safety permission.

## Ownership

All production files in this matrix remain owned by `MarketDataGovernanceDomain`. Lot 32 does
not import or write internal state owned by strategy, risk, portfolio, OMS or execution
domains.
