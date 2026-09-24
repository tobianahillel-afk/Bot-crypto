# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-07
- Task: ENG-07.3
- AWU: ENG-07.3-WU03
- Risk: R0
- Manifest: engineering/lots/ENG-07.json
- AWU file: engineering/work_units/ENG-07.3-WU03.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-07.json
- engineering/work_units/ENG-07.3-WU03.json
- scripts/governance/validate_historical_audit_mapping.py
- scripts/governance/validate_historical_audit_manifest.py
- scripts/governance/selftest_historical_audit_mapping.py
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 8 / 8 files
- Reference: 2 / 8 files
- Routed size: 80 / 512 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-07.3 WU03: repair only the synthetic mapping qualification fixture compatibility.
- Next action: Update the mapping synthetic bundle to use current planner.synthetic_request()/plan_batches() and manifest build_manifest(); do not alter mapping schema, policy, status semantics or CI topology.

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
