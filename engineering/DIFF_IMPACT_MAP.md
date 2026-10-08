# Diff Impact Map — ENG-03.2

ENG-03.2 converts **classifier labels** into conservative **impact families** and affected
domains.

It deliberately does **not**:

- execute a command;
- select T0/T1/T2/T3/T4;
- reuse proof;
- decide certification.

This separation prevents the engine from jumping directly from “file changed” to an
expensive full-suite decision.

Examples:

- `DOC_ONLY` → documentation consistency only;
- `CI_WORKFLOW` → workflow syntax + Actions security impact;
- `CONTRACT_SCHEMA` → schema + compatibility impact;
- `BUSINESS_PRODUCTION` → static analysis + unit-behavior impact;
- `RISK_EXECUTION_CRITICAL` → risk invariants + execution safety + security/replay impact;
- `UNKNOWN_REQUIRES_REVIEW` → conservative broad impact + human-review sentinel.

Policy: `config/governance/diff_impact_policy_v1.json`
Mapper: `scripts/governance/map_diff_impact.py`
