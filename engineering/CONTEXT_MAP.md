# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: BUSINESS
- Work item: LOT-45
- Task: LOT-45.1
- AWU: LOT-45.1-WU01
- Risk: R2
- Manifest: business/lots/LOT-45.json
- AWU file: business/work_units/LOT-45.1-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- business/lots/LOT-45.json
- business/work_units/LOT-45.1-WU01.json
- business/work_units/LOT-45.1-WU05.json
- engineering/LOT45_ENGINE_PILOT_EVIDENCE.json
- engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json
- engineering/BUSINESS_DEVELOPMENT_UNLOCK_ACTIVATION.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 8 / 12 files
- Reference: 2 / 16 files
- Routed size: 73 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: LOT-45.1-WU01: read-only exact-head requalification of PR #66 under the fully reconciled Development Engine V1.
- Next action: Live-reverify PR #66 exact head and required checks, then update only the read-only Lot45 requalification evidence/remediation plan; do not mutate or merge the candidate and keep Lot46 locked.

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
