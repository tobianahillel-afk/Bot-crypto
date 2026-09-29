# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-09
- Task: ENG-09.6
- AWU: ENG-09.6-WU03
- Risk: R2
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.6-WU03A.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.6-WU03A.json
- engineering/BUSINESS_DEVELOPMENT_UNLOCK_ELIGIBILITY.json
- config/governance/development_engine_v1_interface_freeze_v1.json
- engineering/AGENT_PROTOCOL.md

## Execution context — reference

- engineering/MASTER_PLAN.md

## Budget

- Primary: 7 / 12 files
- Reference: 1 / 16 files
- Routed size: 41 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Prepare terminal Development Engine cold-start routing so ordinary continue can safely route to BUSINESS after a later explicit activation transition.
- Next action: Extend the existing V1 resolver and context-map path with backward-compatible BUSINESS routing semantics while keeping project_state PAUSED during WU03A.

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
