# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-08
- Task: ENG-08.2
- AWU: ENG-08.2-WU02
- Risk: R1
- Manifest: engineering/lots/ENG-08.json
- AWU file: engineering/work_units/ENG-08.2-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-08.json
- engineering/work_units/ENG-08.2-WU02.json
- scripts/governance/detect_unnecessary_checks.py
- scripts/governance/run_incremental_validation.py
- config/governance/unnecessary_check_policy_v1.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 7 / 10 files
- Reference: 2 / 12 files
- Routed size: 53 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-08.2 WU02: qualify unnecessary-validation detection directly on the existing single-pass trace.
- Next action: Expose trace metadata in incremental-validation.json, run the detector on that same file, and add adversarial qualification; do not execute a second validation pass.

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
