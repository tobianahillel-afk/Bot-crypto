# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-08
- Task: ENG-08.5
- AWU: ENG-08.5-WU01
- Risk: R1
- Manifest: engineering/lots/ENG-08.json
- AWU file: engineering/work_units/ENG-08.5-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-08.json
- engineering/work_units/ENG-08.5-WU01.json
- scripts/governance/cold_start_qualification.py
- scripts/governance/resolve_next_work.py
- engineering/AGENT_CAPABILITIES.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 7 / 10 files
- Reference: 2 / 12 files
- Routed size: 57 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-08.5: prove a fresh agent can resume from repository state alone with bounded context and no conversational memory.
- Next action: Strengthen the permanent cold-start qualification to prove context-free authority resolution, bounded read order/context budget, unique active AWU, safety preservation and cold-start timing without chat/model memory.

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
