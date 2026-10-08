# T2 Domain Validation — ENG-03.5

T2 is conditional domain validation. It consumes **only the impacts left uncovered by T1**.

Supported bounded groups:

- `CONTRACT_TESTS`;
- `DATA_TESTS`;
- `CHANGED_DOMAIN_TESTS`;
- `RISK_EXECUTION_TESTS`;
- `EVIDENCE_TESTS`.

Target discovery is deterministic over explicit `tests/**/test_*.py` files and is capped per
group and globally. A selected group with zero targets fails closed. A target set that exceeds
the cap also fails rather than falling back to the whole test suite.

Crucially, `pytest` is not imported or invoked when no T2 group is selected. Thus governance
or documentation work pays no domain-test startup cost.

Workflow/security/static-analysis/unknown impacts remain uncovered for T3+.

Policy: `config/governance/validation_t2_policy_v1.json`
Runner: `scripts/governance/run_t2.py`
