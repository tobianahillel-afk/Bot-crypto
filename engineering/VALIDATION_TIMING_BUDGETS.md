# Validation Timing Budgets — ENG-08.1

ENG-08.1 makes the "FAST" target explicit without weakening validation semantics.

The budgets apply **only** to the routine incremental path where:

- `routine_path=true`;
- pytest is not invoked;
- no full suite runs;
- no network is used;
- T3 assurance is not executed;
- T4 certification is not executed.

## Budgets

| Stage | Maximum |
|---|---:|
| T0 | 250 ms |
| T1 | 500 ms |
| T2 routine / no pytest | 750 ms |
| Single-pass total | 1500 ms |

The existing incremental-validation ceiling remains 2000 ms and is treated as an upper
bound that ENG-08.1 may tighten but not relax.

Calibration reference: GitHub Actions run `36043856025`, exact head
`fa1623e8bc5c7ea8a30c49970c9b7248cbdf7246`.

Observed routine timings on that run:

- T0: 20.536 ms
- T1: 22.219 ms
- T2: 15.782 ms
- single-pass total: 71.289 ms

The large margin is intentional: the budget should catch architectural/performance
regressions, not ordinary GitHub-hosted-runner jitter.

The validator is pure and zero-dependency. It validates policy and supplied measurement
objects; it never executes T0/T1/T2 itself. Pytest-backed T2 is explicitly
`NOT_APPLICABLE` here rather than being mislabeled as fast or slow.

Policy: `config/governance/validation_timing_budget_v1.json`
Validator: `scripts/governance/validate_validation_timing_budgets.py`
