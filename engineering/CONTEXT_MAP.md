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
- AWU: ENG-09.3-WU11
- Risk: R2
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.3-WU11.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.3-WU11.json
- config/governance/mutation_profile_policy_v1.json
- config/governance/mutation_profiles_v1.json
- scripts/governance/validate_mutation_profiles.py
- scripts/governance/select_mutation_profile.py
- .github/workflows/p06-extended-mutation.yml
- requirements-dev.lock
- pyproject.toml

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 11 / 12 files
- Reference: 2 / 16 files
- Routed size: 73 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Implement a command-free reusable mutation-profile runner and engineering-branch parity workflow, then prove P0.6 profile execution preserves the legacy mutation semantics before any trigger migration.
- Next action: Implement the fixed internal mutation runner, adversarial runner selftests and engineering-only ci-mutation parity workflow; execute WU10 profile validation before mutation and keep the legacy P0.6 workflow byte-identical.

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
