# Agent Operating Protocol — Bootstrap V1

## Purpose

This protocol makes a fresh agent deterministic without requiring previous conversation
context. It is deliberately procedural: agents should spend reasoning on the engineering
problem, not on rediscovering where the project is.

## Startup algorithm

### S0 — Capability declaration

Determine which capabilities actually exist for the session:

| Profile | May read GitHub | May write GitHub | May execute local code | May claim CI evidence |
|---|---:|---:|---:|---:|
| GITHUB_CONNECTOR_ONLY | yes | if authorized | no | only from exact GitHub run |
| LOCAL_REPOSITORY | yes/optional | yes/optional | yes | only if inspected |
| CI_EXECUTION | yes | workflow-defined | workflow only | yes, exact run/head |
| READ_ONLY_AUDITOR | yes | no | optional read-only | only if inspected |

An unavailable capability is not a failure; it changes the valid execution route.

### S1 — Canonical state

Read `engineering/STATE.json`. Do not start with README, roadmap summaries or chat history.

Resolve:
- project identity;
- current phase;
- completed work;
- active lot;
- active task;
- active manifest;
- business hold;
- safety state;
- blockers and findings.

### S2 — External reality check

For GitHub-backed work, verify the facts that can make the state stale:

- default branch still exists;
- declared main baseline has not unexpectedly moved;
- active engineering branch exists;
- the Lot45 candidate remains isolated while business work is paused;
- no declared locked future Lot has been opened by the engine work.

A mismatch is `STATE_DRIFT`. Do not silently update state to whatever GitHub currently says;
first determine whether the movement was authorized.

### S3 — Bounded context

Read:
1. `engineering/MASTER_PLAN.md`;
2. the active manifest;
3. current handoff;
4. only normative documents explicitly relevant to the active task.

Do not recursively read the entire repository as a startup ritual.

### S4 — Work authorization

Before writing, establish:
- dependencies are satisfied;
- active task matches active manifest;
- intended paths fit `allowed_paths`;
- intended semantics do not violate `forbidden_scope`;
- no stop condition is already true.

If authorization cannot be proved, do not write.

### S5 — Execute minimally

Implement the current task only. Avoid opportunistic refactors and future-task work.
Use the cheapest validation tier that can prove the change at the current stage.

### S6 — Evidence

Separate:
- summary: prose, handoff, PR text;
- evidence: exact Git SHA, diff, test output, workflow run, artifact/checksum.

Never promote work solely from summary text.

### S7 — Handoff

Record:
- exact work item/task;
- last verified Git ref;
- what was completed;
- unresolved blockers/findings;
- next exact action;
- validation already performed and its evidence class.

The next agent re-verifies Git before relying on this handoff.

## STATE_DRIFT conditions

At minimum:
- canonical main/reference SHA moved without a recorded transition;
- active branch/ref is missing or unexpectedly diverged;
- state says one work item but active manifest says another;
- handoff refers to a different active item or stale ref;
- dependency previously marked DONE is no longer represented as completed;
- business development moves while engine state says PAUSED;
- Lot46 is unlocked during bootstrap;
- frozen historical evidence is edited.

## Recovery rule

When drift exists:
1. stop feature/engine implementation;
2. inventory the conflicting facts;
3. prefer immutable evidence for historical facts;
4. do not overwrite canonical state merely to make validation pass;
5. create a bounded reconciliation change;
6. resume only after state and Git agree again.

## Performance rule

Startup should be O(number of bootstrap control files), not O(repository size).
The permanent Development Engine may add context routing, but must preserve this property.
