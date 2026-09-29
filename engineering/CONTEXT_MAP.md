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
- AWU: ENG-09.6-WU02
- Risk: R2
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.6-WU02.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.6-WU02.json
- engineering/REPOSITORY_PROTECTION_STATUS.json
- config/governance/repository_protection_policy_v1.json
- engineering/SECURITY_ENGINE_VERIFICATION.json
- engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json
- config/governance/development_engine_v1_interface_freeze_v1.json
- engineering/BUSINESS_DEVELOPMENT_UNLOCK_DECISION.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 10 / 12 files
- Reference: 2 / 16 files
- Routed size: 60 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Re-evaluate business-development unlock eligibility against the manually remediated live ruleset without activating business/runtime authority.
- Next action: Validate exact live protection and PR #66 against BUSINESS_DEVELOPMENT_UNLOCK_ELIGIBILITY; if eligible, preserve PAUSED/LOCKED authority and require a separate explicit human unlock transition.

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
