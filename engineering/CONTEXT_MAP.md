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
- Routed size: 110 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: LOT-45.1-WU07: establish exact PRE-01A integration-branch authorization preflight without candidate mutation.
- Next action: LOT-45.1-WU07: design-only PRE-01A WU08/WU09 packet is recorded in business/plans/LOT45_REMEDIATION_PLAN.json. Independent R2 authority transition must first permit WU08 creation/activation on isolated branch agent/lot45-pre01a-authorized-work (still exact PR67 integration SHA 2275d478); inherited WU02 R0 and WU07 administrative scope CANNOT grant workflow-write permission. Do not change PR66, PR67, main, Lot46, or Lot45 workflows before separately qualified WU08 and WU09.

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
