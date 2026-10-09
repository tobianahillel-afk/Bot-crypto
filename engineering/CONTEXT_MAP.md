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
- AWU: LOT-45.1-WU08
- Risk: R2
- Manifest: business/lots/LOT-45.json
- AWU file: business/work_units/LOT-45.1-WU08.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- business/lots/LOT-45.json
- business/work_units/LOT-45.1-WU08.json
- business/plans/LOT45_REMEDIATION_PLAN.json
- business/work_units/LOT-45.1-WU02.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 6 / 12 files
- Reference: 2 / 16 files
- Routed size: 59 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: LOT-45.1-WU08: separately approved administrative R2 activation on isolated branch; exact-head checks pending.
- Next action: Qualify exact WU08 HEAD with T0/T1/T3, Engineering Bootstrap and Security Secrets. WU09 remains DESIGN_ONLY and separately gated; never mutate workflows, PR66, PR67, main, Lot46 or trading permissions.

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
