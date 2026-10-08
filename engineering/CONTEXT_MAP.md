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
- AWU: LOT-45.1-WU02
- Risk: R0
- Manifest: business/lots/LOT-45.json
- AWU file: business/work_units/LOT-45.1-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- business/lots/LOT-45.json
- business/work_units/LOT-45.1-WU02.json
- business/evidence/LOT45_V1_REQUALIFICATION.json
- business/plans/LOT45_REMEDIATION_PLAN.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 6 / 8 files
- Reference: 2 / 8 files
- Routed size: 51 / 512 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: LOT-45.1-WU02: four ordered Lot45 remediation AWUs are staged and exact-head checks are green; preserve candidate immutability until safe branch-bound activation.
- Next action: Before closing WU02/activating LOT-45.2-WU01, define and validate an ancestry-correct candidate-branch execution/scope binding for Development Engine V1. Do not activate WU01 with candidate scope_base_sha on the unrelated engineering branch; do not modify PR66, merge, or unlock Lot46 as part of staging.

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
