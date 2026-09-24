# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-06
- Task: ENG-06.5
- AWU: ENG-06.5-WU01
- Risk: R2
- Manifest: engineering/lots/ENG-06.json
- AWU file: engineering/work_units/ENG-06.5-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-06.json
- engineering/work_units/ENG-06.5-WU01.json
- config/governance/certification_candidate_lifecycle_v1.json
- config/governance/certification_exact_head_binding_v1.json
- config/governance/certification_deep_assurance_v1.json
- config/governance/certification_provenance_v1.json
- config/governance/certification_attestation_transport_v1.json
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 10 / 12 files
- Reference: 2 / 16 files
- Routed size: 53 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-06.5 WU01: define pure fail-closed certification promotion rules without promoting any business candidate.
- Next action: Implement certification_promotion_v1 policy plus validator/selftests that require CERTIFICATION_READY, exact-head PASS evidence, satisfied selected assurance, canonical provenance, matching native attestation and explicit PASS verdict; do not mutate Lot45 or unlock Lot46.

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
