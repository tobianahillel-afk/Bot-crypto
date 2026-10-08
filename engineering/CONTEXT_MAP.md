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
- AWU: LOT-45.1-WU02
- Risk: R0
- Manifest: business/lots/LOT-45.json
- AWU file: business/work_units/LOT-45.1-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- business/lots/LOT-45.json
- business/work_units/LOT-45.1-WU02.json
- business/evidence/LOT45_V1_REQUALIFICATION.json
- business/plans/LOT45_REMEDIATION_PLAN.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 6 / 8 files
- Reference: 2 / 8 files
- Routed size: 75 / 512 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: LOT-45.1-WU02: isolated two-parent integration 2275d478cb69446c9ad3a7f2f4923f671c4d6e95 created; draft PR #67 exposes five blocking integration findings; PR66 untouched.
- Next action: LOT-45.1-WU02: resolve LOT45-INT-001..005 through separately authorized bounded preactivation work (pins, ShellCheck, urllib3 lock, dependency-graph assurance, expired deviations), then qualify exact integrated head and activation scope before LOT-45.2-WU01. Never weaken gates or mutate PR66.

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
