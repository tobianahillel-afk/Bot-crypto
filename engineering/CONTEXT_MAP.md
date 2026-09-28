# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-09
- Task: ENG-09.3
- AWU: ENG-09.3-WU12
- Risk: R1
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.3-WU12.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.3-WU12.json
- engineering/ENG09_PHASE1_MUTATION_CONSOLIDATION_PLAN.json
- engineering/ENG09_WU11_P06_PARITY_EVIDENCE.json
- config/governance/mutation_profiles_v1.json
- scripts/governance/validate_mutation_profiles.py
- .github/workflows/ci-mutation.yml

- scripts/governance/run_mutation_profile.py
## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 10 / 10 files
- Reference: 2 / 12 files
- Routed size: 95 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: After proven WU11 parity, migrate the P0.6 pull-request and main-push trigger surface to ci-mutation, retire the legacy P0.6 workflow, and transition the P0.6 profile from parity-reference lifecycle to generic-control lifecycle without changing mutation score or test semantics.
- Next action: Migrate the P0.6 profile lifecycle and trigger surface to ci-mutation, retire p06-extended-mutation.yml in the same bounded change, and prove same-head workflow/security plus generic mutation execution before WU13.

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
