# Repository Truth Classification

ENG-00 separates **what is true now** from **what was certified historically** and from
human-facing summaries.

## Classes

- **IMMUTABLE_HISTORICAL_EVIDENCE** — exact commits/artifacts proving a past certification.
- **CURRENT_OPERATIONAL_STATE** — the permanent machine-readable state authorizing work now.
- **NORMATIVE_POLICY** — stable rules, architecture and safety contracts.
- **CERTIFIED_GATE_STATE** — a certified transition opening a bounded next scope.
- **DERIVED_OR_HUMAN_STATUS_VIEW** — human/status views or migration compatibility state.
- **EXTERNAL_GIT_REALITY** — refs/PR state observed from GitHub.
- **CANDIDATE_OR_PR_CONTEXT** — unmerged candidate state, never merged truth.

The sole current operational state is now
`config/governance/project_state.json`.

`engineering/STATE.json` is retained temporarily as `MIGRATION_BRIDGE` for bootstrap-era
validators. It must remain in parity during migration but cannot authorize fresh-agent work.

## Conflict rule

Apply authority according to the question:

- historical certification → immutable historical evidence;
- current authorization → permanent project state plus freshly verified Git reality;
- system rule/architecture → normative policy;
- human overview → derived view only.

An authorization conflict becomes `STATE_DRIFT` until reconciled.
