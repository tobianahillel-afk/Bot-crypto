# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-08
- Task: ENG-08.2
- AWU: ENG-08.2-WU01
- Risk: R1
- Manifest: engineering/lots/ENG-08.json
- AWU file: engineering/work_units/ENG-08.2-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-08.json
- engineering/work_units/ENG-08.2-WU01.json
- config/governance/validation_t1_policy_v1.json
- config/governance/validation_t2_policy_v1.json
- config/governance/validation_t3_t4_policy_v1.json
- config/governance/incremental_validation_policy_v1.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 8 / 10 files
- Reference: 2 / 12 files
- Routed size: 38 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-08.2 WU01: define exact deterministic semantics for unnecessary validation and missing required validation.
- Next action: Implement the validation-trace policy and pure detector only; do not change the incremental orchestrator or bootstrap in WU01.

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
