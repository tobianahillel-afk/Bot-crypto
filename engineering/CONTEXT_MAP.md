# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-05
- Task: ENG-05.6
- AWU: ENG-05.6-WU03
- Risk: R2
- Manifest: engineering/lots/ENG-05.json
- AWU file: engineering/work_units/ENG-05.6-WU03.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-05.json
- engineering/work_units/ENG-05.6-WU03.json
- config/governance/documentation_tooling_candidates_v1.json
- config/governance/action_pin_registry_v1.json
- config/governance/workflow_security_policy_v1.json
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 8 / 12 files
- Reference: 2 / 16 files
- Routed size: 50 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-05.6 WU03: benchmark exact pinned Vale and lychee binaries in offline modes without slowing the routine bootstrap.
- Next action: Create an isolated path-scoped benchmark workflow that verifies GitHub release SHA-256 digests, proves synthetic detection, measures representative docs, and records the adoption decision.

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
