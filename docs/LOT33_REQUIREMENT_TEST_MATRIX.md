# Lot 33 — Requirement / Test Matrix

| Requirement | Primary evidence |
|---|---|
| Gate checksum and prerequisites | `test_lot33_v3_entry_gate.py`, `validate_lot33_entry_gate.py` |
| Deterministic build | `test_lot33_build_is_deterministic_and_healthy` |
| Raw timestamp/timezone/precision preservation | `test_lot33_preserves_raw_timezone_precision_and_canonicalizes_utc` |
| UTC canonicalization | behavioral and boundary suites |
| Equal timestamp sequence tie-break | `test_equal_event_times_use_sequence_id_and_late_event_is_measured` |
| Exact integer microsecond latency | `test_latency_components_are_exact_integer_microseconds` |
| Out-of-order delay | behavioral suite and persisted validator |
| Anti-lookahead causal chain | `test_causal_availability_and_negative_latency_are_rejected` |
| DST fold determinism | `test_dst_fold_offsets_are_explicit_and_deterministic` |
| Naive/offset/precision rejection | behavioral and boundary suites |
| Explicit monotonic clock domain | `test_monotonic_clock_contract_is_explicit` |
| Degraded threshold behavior | threshold tests in both suites |
| Unknown instrument/source rejection | `test_duplicate_unknown_and_tampered_inputs_fail_closed` |
| Atomic persistence | `test_persistence_writes_three_linked_artifacts` |
| Strict schemas | `test_lot33_schemas_are_strict` |
| Independent artifact validation | `scripts/validate_lot33.py` |
| No connectivity or secrets | `scripts/validate_lot33_no_connectivity.py` |
| Fail-closed safety | behavioral, boundary and mutation suites |
| Line/branch coverage | `reports/lot33/coverage_summary.json` |
| Mutation score | `reports/lot33/mutation_summary.json` |
| Lot 34 remains locked | state reason codes, docs and post-merge lifecycle |
