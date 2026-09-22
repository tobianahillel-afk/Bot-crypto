# Agent Operating Protocol — Permanent V1

## Purpose

A context-free agent must be able to resume the repository from machine-readable state
without reconstructing history from chat, README prose or old PR descriptions.

## S0 — Declare actual capability profile

Use the closest profile from `engineering/AGENT_CAPABILITIES.json`:
`GITHUB_CONNECTOR_ONLY`, `LOCAL_REPOSITORY`, `CI_EXECUTION`, or
`READ_ONLY_AUDITOR`.

Unavailable capabilities change the valid route; they never become inferred evidence.

## S1 — Read permanent state first

Read `config/governance/project_state.json`.

Resolve:
- canonical project identity;
- BUSINESS merged baseline, entry gate, candidate and next lock;
- ENGINEERING active lot/task/manifest;
- AUDIT lifecycle;
- safety and mandatory-cost policy;
- unresolved findings and stop conditions;
- recorded external Git observations.

For ordinary development/“continue”, the default work track is ENGINEERING.
Use AUDIT only for explicitly authorized audit work.

`engineering/STATE.json` is a temporary migration bridge and must not override permanent
state.

## S2 — Verify external Git reality

Before any write, verify the external facts that can stale the state:

- default branch/main head;
- active engineering branch;
- current business candidate PR state/head when present;
- repository protection/ruleset facts when the task depends on them.

Compare them with `external_observations`. An unexpected mismatch is `STATE_DRIFT`.
Never silently rewrite state to match surprise Git movement.

## S3 — Resolve exactly one work item

For ENGINEERING:
- `engineering_track.active_lot`;
- `engineering_track.active_task`;
- `engineering_track.active_manifest`.

For AUDIT, use the equivalent active batch/task/manifest only when that track is active.

The manifest must agree with state, dependencies must be satisfied, and the task must be
the single `IN_PROGRESS` task.

## S4 — Load bounded context

Read only:
1. root `AGENTS.md`;
2. permanent state;
3. `engineering/MASTER_PLAN.md`;
4. active manifest;
5. current handoff;
6. task-relevant normative/contracts/evidence.

Do not recursively read the whole repository as a startup ritual.

## S5 — Authorize the intended diff

Before writing:
- intended paths fit `allowed_paths`;
- semantics do not enter `forbidden_scope`;
- no stop condition is true;
- BUSINESS remains isolated while paused;
- historical evidence protection remains intact.

If authorization is ambiguous, stop rather than broadening scope.

## S6 — Execute minimally

Implement only the active task. Do not opportunistically implement later tasks.
Use the cheapest validation tier that proves the current change; deep certification belongs
to later assurance/certification stages.

## S7 — Evidence discipline

Keep distinct:
- summary: handoff, PR text, prose;
- evidence: exact SHA, diff, command output, workflow run, artifact/checksum.

A summary can route work but cannot certify it.

## S8 — Handoff

Record current task, verified refs, completed work, blockers/findings, exact next action and
evidence already obtained. A future agent still re-verifies Git before trusting the handoff.

## STATE_DRIFT conditions

At minimum:
- observed main or candidate head differs unexpectedly;
- active manifest/task disagrees with permanent state;
- a dependency or completed-lot prefix regresses;
- BUSINESS changes while its foundation lock is active;
- Lot46 unlocks without its gate;
- safety or mandatory-cost policy loosens unexpectedly;
- frozen historical evidence drifts;
- a handoff contradicts permanent state.

## Recovery

1. stop implementation;
2. inventory conflicting facts;
3. preserve immutable historical evidence;
4. do not auto-heal permanent state;
5. create a bounded reconciliation transition;
6. resume only after state, Git and validators agree.

## Performance

Cold start must remain O(control-plane files), not O(repository size).
