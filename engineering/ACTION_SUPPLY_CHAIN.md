# GitHub Actions Supply Chain — ENG-04.5 WU01

This work unit separates legacy inventory from anti-regression enforcement.

The repository contains many historical workflows. Rewriting all of them at once would create
a large, risky change and would slow development. Instead:

1. inventory mode scans every GitHub workflow/action YAML file;
2. every uses clause is classified as pinned SHA, floating remote ref, local, Docker, dynamic, or malformed;
3. legacy floating refs are emitted as machine-readable debt without blocking inventory;
4. changed-workflow mode fails if a workflow being added or modified contains floating, dynamic, or malformed uses;
5. deleted workflows do not cause stale-content failures.

This gives immediate anti-regression protection without forcing a bulk rewrite of 80+ historical workflows.

The gate is zero-dependency: Python standard library plus local Git only. It never executes the
actions it inventories and requires no paid API, SaaS, LLM, or larger runner.

Policy: config/governance/action_supply_chain_policy_v1.json
Auditor: scripts/governance/audit_action_supply_chain.py
Workflow: .github/workflows/security-supply-chain.yml
