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
- Next action: Isolated WU08 HEAD 4dd6e1ef8e14d3d56c886a202a810de6e3d14b89 passes 15/15 read-only structural checks, but has ZERO exact-head CI runs and independently approved R2 grant remains unverified. Prefer a separately authorized zero-file-change workflow-ID dispatch test via Actions-write GitHub CLI/API (Bootstrap 364546277, Secrets 364994700); the connected GitHub tool lacks workflow-dispatch POST. Require real SUCCESS runs bound to that exact HEAD and checkout. See issue #68 comment 6081722012 and #69. Do not mutate PR66/PR67/main, workflows, frozen evidence, Lot46 or trading, nor grant WU09 before qualification.

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
