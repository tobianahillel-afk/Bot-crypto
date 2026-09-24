# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-08
- Task: ENG-08.7
- AWU: ENG-08.7-WU01
- Risk: R2
- Manifest: engineering/lots/ENG-08.json
- AWU file: engineering/work_units/ENG-08.7-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-08.json
- engineering/work_units/ENG-08.7-WU01.json
- scripts/governance/select_t3_t4.py
- config/governance/validation_t3_t4_policy_v1.json
- scripts/governance/selftest_t3_t4_selector.py
- scripts/governance/validate_certification_deep_assurance.py
- config/governance/certification_deep_assurance_v1.json
- scripts/governance/validate_certification_exact_head_binding.py
- config/governance/certification_exact_head_binding_v1.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 11 / 12 files
- Reference: 2 / 16 files
- Routed size: 93 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-08.7: prove critical R3 work cannot bypass T3 risk/execution assurance or T4 exact-head/full-chain certification.
- Next action: Harden the existing selector, deep-assurance and exact-head validators against R3 floor removal; qualify policy-mutation bypass attempts without changing business code, runtime permissions or workflow topology.

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
