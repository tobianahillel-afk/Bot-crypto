# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-08
- Task: ENG-08.3
- AWU: ENG-08.3-WU02
- Risk: R1
- Manifest: engineering/lots/ENG-08.json
- AWU file: engineering/work_units/ENG-08.3-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-08.json
- engineering/work_units/ENG-08.3-WU02.json
- scripts/governance/measure_proof_reuse_effectiveness.py
- scripts/governance/proof_reuse.py
- config/governance/proof_reuse_policy_v1.json
- scripts/governance/run_t1.py
- config/governance/validation_t1_policy_v1.json
- config/governance/proof_reuse_effectiveness_policy_v1.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 10 / 10 files
- Reference: 2 / 12 files
- Routed size: 71 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-08.3 WU02: qualify exact-input proof reuse against the real T1 SELFTEST_ENTRYPOINT_CHECK without integrating a production cache.
- Next action: Bind active state/AWU, changed governance selftests, T1/proof policies and transitive T1 implementation into proof material; execute the real SELFTEST_ENTRYPOINT_CHECK once, reuse the exact PASS proof for the identical second request, add adversarial probes, and run all qualification in bootstrap.

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
