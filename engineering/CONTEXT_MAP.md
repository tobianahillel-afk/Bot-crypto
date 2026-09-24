# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-06
- Task: ENG-06.4
- AWU: ENG-06.4-WU02
- Risk: R2
- Manifest: engineering/lots/ENG-06.json
- AWU file: engineering/work_units/ENG-06.4-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-06.json
- engineering/work_units/ENG-06.4-WU02.json
- config/governance/certification_provenance_v1.json
- scripts/governance/validate_certification_provenance.py
- config/governance/action_pin_registry_v1.json
- config/governance/workflow_permission_policy_v1.json
- config/governance/action_supply_chain_policy_v1.json
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 10 / 12 files
- Reference: 2 / 16 files
- Routed size: 66 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-06.4 WU02: qualify native GitHub attestation transport without redefining provenance or executing business/T4 certification.
- Next action: Register the exact actions/attest v4.2.2 commit and only the two required write scopes, then issue one engineering-only exact-head attestation probe over the canonical WU01 provenance envelope.

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
