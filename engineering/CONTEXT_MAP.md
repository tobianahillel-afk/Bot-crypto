# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-05
- Task: ENG-05.6
- AWU: ENG-05.6-WU01
- Risk: R1
- Manifest: engineering/lots/ENG-05.json
- AWU file: engineering/work_units/ENG-05.6-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-05.json
- engineering/work_units/ENG-05.6-WU01.json
- engineering/handoff/CURRENT.json
- scripts/governance/resolve_active_awu.py
- scripts/governance/resume_recovery_qualification.py
- scripts/governance/selftest_resume_recovery.py

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 8 / 10 files
- Reference: 2 / 12 files
- Routed size: 55 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-05.6 WU01: remove task-specific assumptions from resume/recovery qualification before evaluating documentation tools.
- Next action: Make resume/recovery assertions derive the active task and AWU dynamically, rerun adversarial recovery tests and cold-start, then open a separate WU02 for DocGuard/Vale/lychee evaluation.

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
