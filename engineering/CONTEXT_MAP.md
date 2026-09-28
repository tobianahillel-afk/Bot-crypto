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
- AWU: ENG-09.3-WU10
- Risk: R1
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.3-WU10.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.3-WU10.json
- engineering/ENG09_PHASE1_MUTATION_CONSOLIDATION_PLAN.json
- .github/workflows/p06-extended-mutation.yml
- pyproject.toml

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 7 / 10 files
- Reference: 2 / 12 files
- Routed size: 46 / 768 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Implement a command-free profile policy, validated P0.6 mutation profile and deterministic changed-path selector that preserve the exact P0.6 mutation semantics without migrating or editing any workflow.
- Next action: Implement and adversarially validate the command-free mutation profile policy/registry plus deterministic P0.6 selector; do not edit any workflow, run generic mutation, or touch the Lot45 candidate.

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
