# Agent Work Unit Standard V1

An **Agent Work Unit (AWU)** is the smallest machine-readable unit an implementation agent
may execute. It is deliberately smaller than an ENG/BOOT/AUD work-item.

## Hierarchy

```text
Roadmap / business lot
  -> ENG/BOOT/AUD work-item
    -> work-item task
      -> one or more Agent Work Units
```

The parent work-item remains the roadmap/state-machine unit. An AWU never changes that
identity; it only bounds one implementation slice.

## Required execution contract

Every AWU declares:

- one exact parent work-item/task/manifest;
- objective and explicit non-goals;
- AWU dependencies;
- named inputs and outputs;
- exact scope base SHA;
- allowed paths, forbidden paths and forbidden semantics;
- required invariants and acceptance criteria;
- planning fields for risk, complexity, split decision and context budget;
- required validation tiers and target commands;
- done conditions.

## Fail-closed planning placeholders

ENG-02.1 defines structure before the later classification engines exist.

Until ENG-02.3/02.5/02.6 populate them:

- `risk_class = UNCLASSIFIED`;
- `complexity_score = null`;
- `split_required = null`;
- context budget values may be `null`.

Such an AWU may be `PLANNED` or `IN_PROGRESS` only for construction/qualification of the
engine itself. A `DONE` AWU must be fully classified.

## Status

`PLANNED -> READY -> IN_PROGRESS -> DONE`, with `BLOCKED` as a fail-closed interruption
state. Later ENG-02 tasks add dependency/split authorization; ENG-02.1 only defines the
bounded contract.

## Source files

- JSON Schema: `config/governance/agent_work_unit_v1.schema.json`
- executable semantics: `scripts/governance/validate_agent_work_unit.py`
- reference fixture: `engineering/fixtures/agent_work_unit_v1.example.json`

The executable validator uses only Python 3.11 standard library.
