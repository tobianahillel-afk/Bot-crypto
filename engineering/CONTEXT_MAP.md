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
- AWU: ENG-09.6-WU04
- Risk: R2
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.6-WU04.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.6-WU04.json
- engineering/BUSINESS_DEVELOPMENT_UNLOCK_ELIGIBILITY.json
- config/governance/active_work_routing_policy_v1.json
- engineering/LOT45_ENGINE_PILOT_EVIDENCE.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 7 / 12 files
- Reference: 2 / 16 files
- Routed size: 53 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: WU04 staging is qualified; wait for direct exact BUSINESS_DEVELOPMENT_UNLOCK before activating WU05.
- Next action: Do not activate business on generic continue. On a direct current-session BUSINESS_DEVELOPMENT_UNLOCK instruction, live-reverify eligibility, bind WU05 to the qualified WU04 head, then execute the atomic terminal ENGINEERING-to-BUSINESS transition.

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
