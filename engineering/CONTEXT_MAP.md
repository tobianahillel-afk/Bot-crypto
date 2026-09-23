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
- AWU: ENG-05.6-WU02
- Risk: R1
- Manifest: engineering/lots/ENG-05.json
- AWU file: engineering/work_units/ENG-05.6-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-05.json
- engineering/work_units/ENG-05.6-WU02.json
- engineering/handoff/CURRENT.json
- scripts/governance/validate_documentation_consistency.py
- config/governance/generated_status_policy_v1.json
- config/governance/context_map_policy_v1.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 8 / 10 files
- Reference: 2 / 12 files
- Routed size: 46 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-05.6 WU02: evaluate DocGuard, Vale and lychee deterministically before any third-party documentation-tool adoption.
- Next action: Encode the externally audited release/commit/license/runtime/network facts, validate bounded verdict rules offline, and record whether a separate benchmark/adoption WU is justified.

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
