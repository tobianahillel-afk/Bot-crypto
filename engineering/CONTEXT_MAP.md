# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-09
- Task: ENG-09.5
- AWU: ENG-09.5-WU02
- Risk: R2
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.5-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.5-WU02.json
- config/governance/development_engine_v1_interface_freeze_v1.json
- scripts/governance/validate_development_engine_v1_interface_freeze.py
- scripts/governance/selftest_development_engine_v1_interface_freeze.py
- .github/workflows/engineering-bootstrap.yml
- engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 9 / 12 files
- Reference: 2 / 16 files
- Routed size: 84 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Enforce the certified Development Engine V1 interface freeze in the permanent Engineering Bootstrap workflow.
- Next action: Add one permanent validator step and one adversarial selftest step to Engineering Bootstrap, then inspect the exact-head run before closing ENG-09.5.

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
