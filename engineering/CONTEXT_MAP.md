# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-09
- Task: ENG-09.3
- AWU: ENG-09.3-WU04
- Risk: R1
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.3-WU04.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.3-WU04.json
- engineering/LOT45_WORKFLOW_REDUNDANCY_EVIDENCE.json
- engineering/ENG09_WU02_COMPLETION_EVIDENCE.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 6 / 10 files
- Reference: 2 / 12 files
- Routed size: 59 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Remove pull_request triggering from the remaining nine mutable historical mutation workflows while preserving their existing push/manual lifecycle surfaces and all jobs, commands, thresholds and evidence logic; protected Lot44 mutation assurance remains untouched.
- Next action: Remove only pull_request triggers and pull-request-only path filters from the nine WU04 workflows; preserve everything below each trigger block byte-for-byte and do not touch protected Lot44, Lot45, or global workflows.

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
