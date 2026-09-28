# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-09
- Task: ENG-09.4
- AWU: ENG-09.4-WU03
- Risk: R2
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.4-WU03.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.4-WU03.json
- engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_CANDIDATE.json
- config/governance/development_engine_v1_certification_policy_v1.json
- scripts/governance/qualify_development_engine_v1_exact_head.py
- config/governance/certification_exact_head_binding_v1.json
- engineering/work_units/ENG-09.4-WU02.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 9 / 12 files
- Reference: 2 / 16 files
- Routed size: 58 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Persist the successful exact-head Development Engine V1 certification evidence from WU02 and retire the temporary qualification workflow, while preserving the external business-unlock blocker.
- Next action: Capture WU02 qualification material and exact run conclusions into DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json, remove the temporary WU02 workflow, then require permanent cleanup-head controls to pass.

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
