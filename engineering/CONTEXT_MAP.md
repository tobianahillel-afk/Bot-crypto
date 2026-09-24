# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-07
- Task: ENG-07.1
- AWU: ENG-07.1-WU01
- Risk: R1
- Manifest: engineering/lots/ENG-07.json
- AWU file: engineering/work_units/ENG-07.1-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-07.json
- engineering/work_units/ENG-07.1-WU01.json
- engineering/HISTORICAL_EVIDENCE_PROTECTION.json
- docs/ROADMAP_V1_TO_V21.md
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 7 / 10 files
- Reference: 2 / 12 files
- Routed size: 61 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-07.1 WU01: define pure complexity-aware historical audit batching for certified Lots 0-44 without executing audits or mutating historical evidence.
- Next action: Implement historical_audit_batching_v1 policy plus a pure planner/selftests that cover Lots 0-44 exactly once, split by explicit complexity budget, isolate oversized lots, and never mutate or execute historical audit content. CI integration is a separate WU.

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
