# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-08
- Task: ENG-08.7
- AWU: ENG-08.7-WU02
- Risk: R1
- Manifest: engineering/lots/ENG-08.json
- AWU file: engineering/work_units/ENG-08.7-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-08.json
- engineering/work_units/ENG-08.7-WU02.json
- scripts/governance/resume_recovery_qualification.py
- scripts/governance/selftest_resume_recovery.py
- scripts/governance/resolve_next_work.py
- engineering/AGENT_CAPABILITIES.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 8 / 10 files
- Reference: 2 / 12 files
- Routed size: 68 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-08.7 WU02: make permanent interruption/recovery qualification lifecycle-generic and obtain final same-head proof that the hardened R3 assurance chain cannot be bypassed.
- Next action: Replace ENG-08.6 hardcoded recovery expectations with canonical active-task/AWU expectations, retain all safety/write-gate invariants, then require full Bootstrap plus Security Secrets on the exact final head.

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
