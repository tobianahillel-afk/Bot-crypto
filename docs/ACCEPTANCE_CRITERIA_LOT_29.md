# Acceptance Criteria — Lot 29

Lot 29 is accepted only when every requirement below is satisfied on one exact commit.

## Required implementation

- `src/crypto_quant_bot/market_analysis/v2_deterministic_replay_and_audit.py` exists.
- `src/crypto_quant_bot/market_analysis/v2_replay_audit_models.py` exists.
- `scripts/run_lot29_v2_deterministic_replay_and_audit.py` exists.
- `scripts/validate_lot29.py` exists.
- `config/replay/v2_deterministic_replay_audit_v1.json` exists.
- `contracts/schemas/v2_deterministic_replay_audit_state_v1.schema.json` exists and is closed.
- Lot 29 state, audit, closure and report are generated atomically.

## Canonical replay chain

- exactly eight lots are registered;
- lot sequence is exactly `21,22,23,24,25,26,27,28`;
- every artefact path is unique and under `data/audit/`;
- every lot uses its canonical `scripts/validate_lotNN.py` validator;
- all eight validators return `0` and `PASS`;
- every validator output is bounded and hashed;
- every complete artefact file is hashed with SHA-256;
- chain checksum is deterministic and order-sensitive;
- run 1 and run 2 produce identical state, audit and closure evidence;
- persisted evidence validates independently after re-read.

## Negative and tamper tests

Tests must reject:

- wrong schema or runtime mode;
- wrong lot order, duplicate path or external path;
- missing/non-object artefact;
- changed artefact checksum or byte size;
- malformed embedded checksum;
- validator failure, wrong identity, wrong count or oversized output;
- altered state checksum, chain checksum, audit checksum or replay status;
- altered reason-code order;
- any enabled decision, trade or execution permission.

## Quality gates

- Python `3.11.9` exact toolchain;
- Ruff and mypy `PASS`;
- targeted line coverage at least `95%`;
- targeted branch coverage at least `90%`;
- critical mutation score at least `80%`;
- full repository regression `PASS`;
- targeted anti-flake replay `3/3 PASS`;
- Bandit, pip-audit, architecture, ownership, traceability and engineering-deviation gates `PASS`;
- zero new unregistered engineering deviation;
- zero unresolved review thread.

## Mandatory safety invariants

```text
runtime_mode=LOCAL_OFFLINE_ANALYSIS_ONLY
analysis_only=true
used_for_decision=false
trade_allowed=false
execution_allowed=false
approved_size=0
```

## Promotion gate

Lot 30 remains `PLANNED_LOCKED` until:

1. the Lot 29 implementation PR is certified and merged;
2. a separate post-merge audit independently confirms replay, checksums and safety;
3. the post-merge audit PR is certified and merged.
