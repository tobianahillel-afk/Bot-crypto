# Documentation Consistency — ENG-05.2

Current authorization/status authority is **only**
`config/governance/project_state.json`.

`engineering/STATE.json` is retained solely as a migration compatibility bridge. It may be
mentioned in the agent bootstrap only when explicitly labeled as non-authoritative.

## Registered document roles

- `README.md`, `AGENTS.md`, `engineering/CURRENT_STATUS.md`: generated/current views
  governed by ENG-05.1.
- `docs/PROJECT_IDENTITY.md`: normative project identity.
- `docs/ROADMAP_V1_TO_V21.md`: normative lot ordering/content; no duplicated current state.
- `docs/FUNCTIONAL_COVERAGE_REGISTRY.md`: explicit snapshot of the certified Lot 44
  baseline, not current authorization.
- `docs/SYSTEM_EXECUTION_ARCHITECTURE.md`: normative target architecture; no duplicated
  current state.

Historical lot specifications, reports and immutable evidence are deliberately outside this
registry and are not interpreted as current status.

The validator is standard-library, offline, read-only and zero-cost.
