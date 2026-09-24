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
- AWU: ENG-06.4-WU01
- Risk: R2
- Manifest: engineering/lots/ENG-06.json
- AWU file: engineering/work_units/ENG-06.4-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-06.json
- engineering/work_units/ENG-06.4-WU01.json
- config/governance/certification_candidate_lifecycle_v1.json
- config/governance/certification_exact_head_binding_v1.json
- config/governance/certification_deep_assurance_v1.json
- engineering/AGENT_CAPABILITIES.json
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 9 / 12 files
- Reference: 2 / 16 files
- Routed size: 53 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-06.4 WU01: define the canonical provenance envelope and attestation subject without replacing domain integrity hashes.
- Next action: Implement deterministic provenance-envelope semantics over exact-head input identity plus satisfied assurance and workflow identity; do not issue remote attestations in WU01.

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
