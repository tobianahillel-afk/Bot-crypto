# Lot 31 Requirement–Test Matrix

| Requirement | Primary evidence |
|---|---|
| Deterministic state and audit | `test_build_is_deterministic_and_metadata_only` |
| Atomic persistence | `test_atomic_write_replaces_complete_json` |
| Gate-required source fields | `test_serialization_contains_gate_required_source_fields` |
| Source of truth and backups | `test_source_registry_rejects_duplicates_order_truth_unknown_and_cycles` |
| Unknown source rejected | `test_unknown_source_and_active_connection_fail_before_publication` |
| Secrets and authentication rejected | `test_source_contract_is_fail_closed` |
| UTC and anti-future-state | `test_lineage_rejects_wrong_predecessor`, `test_state_rejects_temporal_registry_and_policy_mutations` |
| Capability owner/contract/gate | `test_capability_and_contract_registry_reject_invalid_entries` |
| No connectivity | `scripts/validate_lot31_no_connectivity.py` and dedicated workflow step |
| Safety remains fail-closed | `test_metrics_and_safety_reject_permissive_values` |
| Checksums and artifact links | `test_state_and_audit_serialization_are_exactly_linked`, mutation oracles |
| Lot 32 remains locked | capability-matrix validation and exact-head workflow |
