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

The parent work-item remains the roadmap/state-machine unit. An AWU only bounds one
implementation slice.

## Required execution contract

Every AWU declares one parent task, objective/non-goals, dependencies, I/O, exact scope
base, allowed/forbidden scope, invariants, acceptance criteria, planning data, validation
targets and done conditions.

## Planning progression

- ENG-02.1 introduced fail-closed placeholders.
- ENG-02.3 makes `complexity_score` deterministic and non-null.
- `split_required` remains null until ENG-02.4.
- `risk_class` may remain `UNCLASSIFIED` until ENG-02.5.
- context budgets may remain null until ENG-02.6.

### Complexity

`planning.complexity_factors` is a closed 12-factor declaration. The authoritative weights
live in `config/governance/awu_complexity_policy_v1.json`.

The stored `complexity_score` is not trusted: CI recalculates it. Basic under-declaration
checks also bind schema/contract outputs, workflow scope and production scope to their
minimum factors.

ENG-02.3 defines **score only**. Mandatory split thresholds are ENG-02.4.

## Source files

- AWU schema: `config/governance/agent_work_unit_v1.schema.json`
- individual validator: `scripts/governance/validate_agent_work_unit.py`
- complexity policy: `config/governance/awu_complexity_policy_v1.json`
- complexity validator: `scripts/governance/validate_awu_complexity.py`
