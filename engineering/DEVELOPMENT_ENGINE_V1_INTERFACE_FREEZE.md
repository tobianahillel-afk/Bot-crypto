# Development Engine V1 Interface Freeze

The Development Engine V1 is certified, but certification must not make normal project state
immutable. ENG-09.5 freezes the **compatibility surface** used by fresh agents while leaving
current task/state payloads evolvable.

## Stable V1 surface

A fresh agent starts from exactly three bootstrap files:

1. `AGENTS.md`
2. `config/governance/project_state.json`
3. `engineering/CONTEXT_MAP.json`

The stable authority relationships are:

- `project_state.json` is the sole mutable current-authorization source;
- `CONTEXT_MAP.json` is generated bounded routing, never higher authority;
- the active task is executed through exactly one `IN_PROGRESS` Agent Work Unit;
- `engineering/handoff/CURRENT.json` is a resume hint only;
- `engineering/STATE.json` remains a migration bridge only;
- chat/model memory never authorizes work.

Stable executable entry points include:

- `python scripts/governance/resolve_active_awu.py`
- `python scripts/governance/verify_external_git_state.py --mode github`
- `python scripts/governance/render_context_map.py --check`
- `python scripts/governance/render_current_status.py --check`

## What is not frozen

V1 does **not** freeze bytes or current values of project state, handoff, active AWU routing,
generated status or context-map payloads. These must change as work progresses.

Compatibility is defined by stable paths, schema/kind identities, authority direction and CLI
contracts. An incompatible change must introduce an explicit later interface version rather
than silently changing V1.

## Certification anchor

The interface freeze remains anchored to
`engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json`:

- candidate: `DEV_ENGINE_V1:b9e5ebadbb739e57f2e0023d7498593f0f9a45bde46af24d8a83541351cdd1ed`
- qualified head: `972748579bcb998fc48542c02ed76aacae482fa5`
- input identity: `32829891fa11c4e5905ef01d9f24320a34180e03640d478807fda2edf10565ac`
- bundle identity: `490cf76580b4259a5812e81cc861c63bf9e4c1825591f46a276b1694ad18590b`

This certification grants **no** business-development, Lot45 merge, Lot46, trading or runtime
authority. `BOOT-FINDING-001` remains blocking.

Policy:
`config/governance/development_engine_v1_interface_freeze_v1.json`

Validator:
`scripts/governance/validate_development_engine_v1_interface_freeze.py`
