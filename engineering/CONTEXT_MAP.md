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
- engineering/work_units/ENG-09.3-WU03.json
- engineering/LOT45_WORKFLOW_REDUNDANCY_EVIDENCE.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 6 / 10 files
- Reference: 2 / 12 files
- Routed size: 40 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-09.3-WU02: suppress pull_request fanout for the first eight mutable historical mutation workflows while preserving all jobs, commands, thresholds, artifacts and existing push/manual behavior.
- Next action: Remove only pull_request triggers and pull-request-only path filters from the eight WU02 workflows; preserve everything below each trigger block byte-for-byte and do not touch Lot44 protected or Lot45/global workflows.

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
