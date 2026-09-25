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
- AWU: ENG-09.3-WU02
- Risk: R1
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.3-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.3-WU02.json
- engineering/LOT45_WORKFLOW_REDUNDANCY_EVIDENCE.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 5 / 10 files
- Reference: 2 / 12 files
- Routed size: 53 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-09.3-WU02: suppress pull-request fanout for the first bounded batch of nine historical mutation workflows without changing their mutation jobs or lifecycle evidence.
- Next action: Remove only the pull_request trigger blocks from the nine WU02 workflows; preserve existing push main and workflow_dispatch triggers and leave all job bodies byte-for-byte unchanged.

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
