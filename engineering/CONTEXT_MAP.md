# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: BUSINESS
- Work item: LOT-45
- Task: LOT-45.1
- AWU: LOT-45.1-WU07
- Risk: R2
- Manifest: business/lots/LOT-45.json
- AWU file: business/work_units/LOT-45.1-WU07.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- business/lots/LOT-45.json
- business/work_units/LOT-45.1-WU07.json
- business/plans/LOT45_REMEDIATION_PLAN.json
- business/evidence/LOT45_V1_REQUALIFICATION.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 6 / 12 files
- Reference: 2 / 16 files
- Routed size: 118 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: LOT-45.1-WU07: read-only recovery coordination for separately approved isolated R2 WU08; isolate contains unauthorised cross-scope changes and remains NOT_CERTIFIED.
- Next action: 2026-10-09 LIVE: isolated agent/lot45-pre01a-authorized-work HEAD 5bc05e9c01c5cc7e1b73066686d9ef344241c80a. Owner approval for 4dd6e1ef... recorded in issue #68 comment 6083702769; exact-head Security Secrets run 37956216987 SUCCESS, Engineering Bootstrap run 37956214042 FAILURE at active-AWU diff scope: five extra paths (.github/workflows/engineering-bootstrap.yml; engineering/HISTORICAL_EVIDENCE_PROTECTION.{json,md}; scripts/governance/{validate_historical_evidence_protection.py,selftest_historical_evidence_protection.py}). Preserve nine-commit forensic HEAD. Do not add those paths to WU08. Require separately authorized historical-evidence/CI migration on its own branch, then clean seven-file R2 WU08 activation line and fresh exact-head Bootstrap+Secrets. See issue #68 comment 6084736451 and issue #69. PR66/PR67/main unchanged; WU09, Lot46 and trading LOCKED.

## Non-authoritative sources

- engineering/STATE.json
- chat_history
- model_memory

Chat history and model memory may explain prior work but never authorize it.

## Stop conditions

- STATE_DRIFT
- BUSINESS_SCOPE_TOUCHED_WITHOUT_UNLOCK
- FROZEN_EVIDENCE_MUTATION
- LOT46_UNLOCK_ATTEMPT
- MANDATORY_PAID_DEPENDENCY_INTRODUCED
