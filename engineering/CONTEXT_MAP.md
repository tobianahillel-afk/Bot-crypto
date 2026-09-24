# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-05
- Task: ENG-05.6
- AWU: ENG-05.6-WU05
- Risk: R2
- Manifest: engineering/lots/ENG-05.json
- AWU file: engineering/work_units/ENG-05.6-WU05.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-05.json
- engineering/work_units/ENG-05.6-WU05.json
- config/governance/documentation_tooling_candidates_v1.json
- config/governance/action_pin_registry_v1.json
- config/governance/workflow_security_policy_v1.json
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 8 / 12 files
- Reference: 2 / 16 files
- Routed size: 51 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-05.6 WU05: benchmark exact pinned lychee v0.24.2 offline as the second one-dependency child of the mandatory tooling split.
- Next action: Validate the WU05 transition, then benchmark the exact lychee x86_64 GNU release with SHA-256 verification and --offline using synthetic local-link controls plus representative project Markdown.

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
