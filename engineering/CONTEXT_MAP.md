# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-08
- Task: ENG-08.4
- AWU: ENG-08.4-WU02
- Risk: R1
- Manifest: engineering/lots/ENG-08.json
- AWU file: engineering/work_units/ENG-08.4-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-08.json
- engineering/work_units/ENG-08.4-WU02.json
- config/governance/mandatory_cost_zero_policy_v1.json
- scripts/governance/verify_mandatory_cost_zero.py
- engineering/AGENT_CAPABILITIES.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 7 / 10 files
- Reference: 2 / 12 files
- Routed size: 55 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-08.4 WU02: qualify the mandatory zero-paid-requirement claim against live public-repository and current GitHub Actions pricing evidence.
- Next action: Bind exact public repository evidence and official GitHub Actions billing semantics, then adversarially reject private/paid variants without modifying mandatory workflows.

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
