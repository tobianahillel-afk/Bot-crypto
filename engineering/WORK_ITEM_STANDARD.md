# Work-Item Manifest Standard V1

The work-item manifest is the smallest machine-readable unit of development governance.

## Design goals

- one canonical representation: JSON;
- no third-party parser required;
- bounded scope and explicit dependencies;
- exactly one resumable task for an in-progress item;
- reusable for BOOT, ENG, AUD and future business work units;
- no duplication of deep project specifications.

## Required fields

`schema_version`, `kind`, `id`, `title`, `status`, `objective`,
`depends_on`, `allowed_paths`, `forbidden_scope`, `tasks`, and `done_when`.

The JSON Schema representation is `engineering/WORK_ITEM_SCHEMA.json`.
The authoritative executable semantics are also checked by
`scripts/governance/validate_work_item.py` using only Python 3.11 standard library.

## Lifecycle

```text
PLANNED → IN_PROGRESS → DONE
    └────────→ BLOCKED ─→ IN_PROGRESS
```

A `DONE` item is terminal. While an item is `IN_PROGRESS`, exactly one task is
`IN_PROGRESS`; all earlier tasks are `DONE` and later tasks remain `PLANNED`.
A `DONE` work item requires all tasks to be `DONE`.

## Dependencies

- dependencies are explicit work-item IDs;
- self-dependency is forbidden;
- duplicate dependencies are forbidden;
- the bootstrap set must form an acyclic dependency graph;
- an active work item's dependencies must already be completed in canonical state.

## Scope

`allowed_paths` is an allowlist for files the work item may intentionally modify.
`forbidden_scope` records semantic boundaries that must not be crossed even when a
filesystem glob could technically match.

The future Development Engine will compare Git diffs against these declarations.

## Extension rule

New optional machine-readable fields must live under `extensions` until a new schema
version makes them canonical. This prevents accidental format sprawl.

## Non-goals

The manifest does not replace:
- normative project standards;
- a business Lot specification;
- mathematical specifications;
- test evidence;
- certification evidence;
- handoff state.

It routes an agent to those artifacts and bounds the work.
