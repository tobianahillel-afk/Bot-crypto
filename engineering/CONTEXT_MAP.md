# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-06
- Task: ENG-06.3
- AWU: ENG-06.3-WU01
- Risk: R2
- Manifest: engineering/lots/ENG-06.json
- AWU file: engineering/work_units/ENG-06.3-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-06.json
- engineering/work_units/ENG-06.3-WU01.json
- config/governance/validation_t3_t4_policy_v1.json
- config/governance/certification_exact_head_binding_v1.json
- config/governance/security_engine_verification_policy_v1.json
- engineering/AGENT_CAPABILITIES.json
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 9 / 12 files
- Reference: 2 / 16 files
- Routed size: 51 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-06.3: satisfy selected T3 assurance using existing ENG-04 controls and exact-head run evidence only.
- Next action: Implement reason-to-control planning and exact-head assurance evidence verification; reuse existing Security Actions, Supply Chain, SAST, Secrets and Bootstrap workflows without duplicating scanners or executing T4.

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
