# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-09
- Task: ENG-09.5
- AWU: ENG-09.5-WU01
- Risk: R2
- Manifest: engineering/lots/ENG-09.json
- AWU file: engineering/work_units/ENG-09.5-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-09.json
- engineering/work_units/ENG-09.5-WU01.json
- engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json
- engineering/AGENT_PROTOCOL.md
- engineering/AGENT_CAPABILITIES.json
- config/governance/context_map_policy_v1.json
- config/governance/generated_status_policy_v1.json
- scripts/governance/resolve_active_awu.py
- scripts/governance/verify_external_git_state.py
- scripts/governance/render_context_map.py

## Execution context — reference

- engineering/MASTER_PLAN.md

## Budget

- Primary: 12 / 12 files
- Reference: 1 / 16 files
- Routed size: 83 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: Freeze the certified Development Engine V1 bootstrap interfaces and permanent agent entry points without freezing dynamic state values or changing business/runtime authority.
- Next action: Define the machine-readable V1 interface freeze policy plus fail-closed validator/selftests for stable authority paths, JSON identities and CLI contracts.

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
