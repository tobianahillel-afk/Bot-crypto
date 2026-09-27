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
- AWU: ENG-09.3-WU09
- Risk: R0
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.3-WU09.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.3-WU09.json
- engineering/LOT45_WORKFLOW_REDUNDANCY_EVIDENCE.json
- engineering/ENG09_WU08_COMPLETION_EVIDENCE.json
- .github/workflows/p06-extended-mutation.yml
- .github/workflows/code-quality.yml

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 8 / 8 files
- Reference: 2 / 8 files
- Routed size: 67 / 512 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Produce a read-only, exact-evidence phase-1 reconciliation and a bounded implementation plan for phase-2 mutation consolidation, accounting for the three protected Lot44 exceptions and the fact that the Lot45 mutation workflow exists only on the suspended candidate head.
- Next action: Write the phase-1 reconciliation and phase-2 mutation consolidation plan from WU08 evidence, P0.6 mutation, institutional quality mutation overlap, and read-only Lot45 mutation evidence; do not mutate any workflow or candidate file.

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
