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
- AWU: LOT-45.1-WU07
- Risk: R2
- Manifest: business/lots/LOT-45.json
- AWU file: business/work_units/LOT-45.1-WU07.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- business/lots/LOT-45.json
- business/work_units/LOT-45.1-WU07.json
- business/plans/LOT45_REMEDIATION_PLAN.json
- business/evidence/LOT45_V1_REQUALIFICATION.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 6 / 12 files
- Reference: 2 / 16 files
- Routed size: 118 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: LOT-45.1-WU07: reconcile observed isolated WU08 activation without treating it as certification or permission for WU09.
- Next action: Isolated WU08 is at 4dd6e1ef8e14d3d56c886a202a810de6e3d14b89 with 7 scoped administrative paths, but has ZERO exact-head CI runs. GitHub workflow_dispatch is unavailable because both Engineering Bootstrap and Security Secrets are ABSENT from default main. A separately authorized exact-head CI execution route and independently verified R2 grant are required; do not modify workflow files under WU07/WU08, or PR66/PR67/main/frozen evidence/trading/Lot46. WU09 remains DESIGN_ONLY.

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
