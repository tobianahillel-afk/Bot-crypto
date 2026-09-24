# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-07
- Task: ENG-07.2
- AWU: ENG-07.2-WU01
- Risk: R2
- Manifest: engineering/lots/ENG-07.json
- AWU file: engineering/work_units/ENG-07.2-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-07.json
- engineering/work_units/ENG-07.2-WU01.json
- config/governance/historical_audit_batching_v1.json
- engineering/HISTORICAL_EVIDENCE_PROTECTION.json
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 7 / 12 files
- Reference: 2 / 16 files
- Routed size: 44 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-07.2 WU01: define a source-bound tamper-evident read-only historical audit manifest and fail-closed batch lifecycle.
- Next action: Implement the historical audit manifest schema, lifecycle policy, pure validator and adversarial tests; do not execute audits, record findings, remediate code, or mutate historical evidence. CI integration is a separate WU.

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
