# Permanent Project State — ENG-00.3 Design

This is a design input for ENG-01, not yet the canonical operational state.

The permanent state must keep three independent tracks:

```text
BUSINESS      merged baseline / gate / candidate / next lock
ENGINEERING   engine work currently authorized
AUDIT         historical audit campaign state
```

A single integer such as `current_lot=45` is insufficient because the repository may
simultaneously have Lot44 as the last merged/certified implementation, a merged Lot45 entry
gate, an unmerged Lot45 implementation candidate, and Lot46 locked.

## External observations

GitHub refs and PR state are external reality, not blindly persisted truth. Every fresh agent
must re-check them. A mismatch produces `STATE_DRIFT`; the engine must not silently rewrite
state to match an unexpected ref movement.

## Certification separation

- gate authorization is not implementation certification;
- an open PR is not merged truth;
- historical evidence remains immutable;
- business unlock is independent from engineering progress;
- high security findings may block unlock without blocking unrelated engineering work.

The machine-readable design is `engineering/PERMANENT_STATE_DESIGN.json`.
