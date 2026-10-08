# ENG-00 Canonical Baseline

This file is the handoff boundary between **Repository Truth Recovery (ENG-00)** and
**Agent Bootstrap & Canonical State (ENG-01)**.

It intentionally records only facts already established by Git/evidence and ENG-00
reconciliation:

- canonical identity: **Crypto Quant Bot V3.1-Ops**;
- last merged/certified implementation baseline: **Lot44 / 0.44.0**;
- Lot45 implementation entry gate: merged and certified;
- Lot45 implementation: PR #66, open/unmerged/suspended candidate;
- Lot46: locked;
- business development: paused;
- runtime: offline microstructure research only;
- trading/execution/leverage/withdrawals: forbidden;
- main branch protection finding remains unresolved and blocks future business unlock.

The baseline is **not** the final permanent state format. ENG-01 consumes it to build
`config/governance/project_state.json` and the permanent state machine.

Machine-readable source: `engineering/CANONICAL_BASELINE.json`.
