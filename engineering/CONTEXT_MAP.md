# Active Agent Context Map

> Generated from canonical project state and the validated active AWU route. Do not edit manually.

## Bootstrap read order

1. AGENTS.md
2. config/governance/project_state.json
3. engineering/CONTEXT_MAP.json

## Active work

- Track: ENGINEERING
- Work item: ENG-07
- Task: ENG-07.6
- AWU: ENG-07.6-WU01
- Risk: R2
- Manifest: engineering/lots/ENG-07.json
- AWU file: engineering/work_units/ENG-07.6-WU01.json

## Execution context — primary

- AGENTS.md
- config/governance/project_state.json
- engineering/lots/ENG-07.json
- engineering/work_units/ENG-07.6-WU01.json
- engineering/HISTORICAL_EVIDENCE_PROTECTION.json
- scripts/governance/validate_historical_evidence_protection.py
- config/governance/historical_audit_findings_policy_v1.json
- config/governance/historical_audit_report_policy_v1.json
- engineering/handoff/CURRENT.json

## Execution context — reference

- engineering/MASTER_PLAN.md
- engineering/AGENT_PROTOCOL.md

## Budget

- Primary: 9 / 12 files
- Reference: 2 / 16 files
- Routed size: 53 / 1024 KiB
- Implicit repository expansion: FORBIDDEN

## Resume hint

- Handoff: engineering/handoff/CURRENT.json
- Objective: ENG-07.6 WU01: bind the historical audit engine to the canonical immutable-evidence protection boundary.
- Next action: Implement only the audit-engine evidence-protection policy and validator with a built-in synthetic self-check; do not modify canonical frozen evidence or add CI until WU02.

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
