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
- AWU: ENG-09.3-WU08
- Risk: R1
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.3-WU08.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.3-WU08.json
- engineering/LOT45_WORKFLOW_REDUNDANCY_EVIDENCE.json
- engineering/ENG09_WU07_COMPLETION_EVIDENCE.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 6 / 10 files
- Reference: 2 / 12 files
- Routed size: 54 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Remove pull_request triggering from the final three protected Lot44 historical workflows while preserving workflow_dispatch and every job, command, evidence, provenance, threshold and exact-head check byte-for-byte; this completes phase-1 historical PR fanout removal without mutating frozen evidence artifacts.
- Next action: Remove only pull_request triggering from the three protected Lot44 workflows; preserve workflow_dispatch and everything below each trigger block byte-for-byte. Do not touch Lot45, global workflows, business code, or historical evidence artifacts.

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
