# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-09
- Task: ENG-09.6
- AWU: ENG-09.6-WU01
- Risk: R2
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.6-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.6-WU01.json
- engineering/REPOSITORY_PROTECTION_STATUS.json
- config/governance/repository_protection_policy_v1.json
- engineering/SECURITY_ENGINE_VERIFICATION.json
- engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json
- config/governance/development_engine_v1_interface_freeze_v1.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 9 / 12 files
- Reference: 2 / 16 files
- Routed size: 57 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Make the explicit ENG-09.6 business-development unlock decision while preserving fail-closed business/runtime authority.
- Next action: Keep business PAUSED and Lot46 LOCKED. In GitHub repository administration, change main protection so an accepted mechanism is actively enforced: the current ruleset Protect is disabled and only contains deletion/non-fast-forward rules, so it still lacks required pull-request and required-status-check enforcement. After that change, refresh live Git state and explicitly re-evaluate; never auto-unlock.

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
