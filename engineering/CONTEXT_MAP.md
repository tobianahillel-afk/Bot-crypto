# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-07
- Task: ENG-07.4
- AWU: ENG-07.4-WU01
- Risk: R2
- Manifest: engineering/lots/ENG-07.json
- AWU file: engineering/work_units/ENG-07.4-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-07.json
- engineering/work_units/ENG-07.4-WU01.json
- scripts/governance/validate_historical_audit_mapping.py
- config/governance/historical_audit_mapping_policy_v1.json
- scripts/governance/validate_historical_audit_manifest.py
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 8 / 12 files
- Reference: 2 / 16 files
- Routed size: 79 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-07.4 WU01: define the source-bound read-only historical audit findings registry contract.
- Next action: Implement only findings schema/policy/validator with built-in deterministic self-check, bound to validated manifest and mapping identities; defer adversarial test module and CI integration to ENG-07.4-WU02.

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
