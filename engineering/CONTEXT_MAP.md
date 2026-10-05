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
- AWU: ENG-09.6-WU05
- Risk: R2
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.6-WU05.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.6-WU05.json
- engineering/BUSINESS_DEVELOPMENT_UNLOCK_ACTIVATION_PLAN.json
- engineering/BUSINESS_DEVELOPMENT_UNLOCK_ELIGIBILITY.json
- config/governance/business_unlock_activation_policy_v1.json
- business/lots/LOT-45.json
- business/work_units/LOT-45.1-WU01.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 9 / 12 files
- Reference: 2 / 16 files
- Routed size: 49 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Preflight ENG-09.6-WU05 atomic business-development activation without executing authority writes.
- Next action: Reverify live GitHub eligibility and remain fail-closed until the exact current-session human action BUSINESS_DEVELOPMENT_UNLOCK is supplied; generic continue is not authorization.

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
