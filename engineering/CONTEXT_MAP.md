# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-09
- Task: ENG-09.1
- AWU: ENG-09.1-WU01
- Risk: R1
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.1-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.1-WU01.json
- engineering/CRITICAL_R3_BYPASS_EVIDENCE.json
- config/governance/diff_classifier_policy_v1.json
- config/governance/diff_impact_policy_v1.json
- config/governance/validation_t3_t4_policy_v1.json
- engineering/AGENT_CAPABILITIES.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 9 / 10 files
- Reference: 2 / 12 files
- Routed size: 50 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-09.1: run the completed Development Engine read-only against suspended Lot45 PR #66 and record exact-head pilot evidence without mutating business code.
- Next action: Verify live main and PR #66 base/head/open/unmerged state, then inventory the candidate diff and exact workflow/check evidence and map them through the current engine; write only engineering/LOT45_ENGINE_PILOT_EVIDENCE.json and engineering/LOT45_ENGINE_PILOT.md.

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
