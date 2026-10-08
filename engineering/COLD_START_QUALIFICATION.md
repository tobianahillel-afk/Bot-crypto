# Context-Free Cold-Start Qualification — ENG-08.5

ENG-08.5 proves that a fresh agent can resume **without chat history or model memory** from
repository authority alone.

The qualification reuses the permanent resolver and active-AWU machinery; it does not create a
second bootstrap engine and does not change workflow topology.

## What is proven

A `GITHUB_CONNECTOR_ONLY` agent resolves:

- canonical project: `Crypto Quant Bot V3.1-Ops`;
- authority: `config/governance/project_state.json`;
- active work: `ENG-08 / ENG-08.5 / ENG-08.5-WU01`;
- exact AWU primary + reference read route;
- business hold: `PAUSED`, Lot46 `LOCKED`;
- trading/execution disabled;
- no local execution or local-test PASS capability.

The generated route must:

- start with `AGENTS.md` then permanent state;
- exclude `engineering/STATE.json`, `chat_history` and `model_memory`;
- forbid implicit repository expansion;
- remain within 10 primary files, 12 reference files and 768 KiB.

## Adversarial qualification

The same executable rejects stale handoff, Lot46 unlock, mandatory paid LLM, inactive audit
routing, ambiguous active AWU, stale context-map AWU, implicit repository expansion,
chat-history injection, context byte-budget overflow and a GitHub-only profile falsely
claiming local execution.

The CI budget is deliberately generous at 1000 ms so ordinary runner variance does not create
noise. The measured elapsed time is emitted in the PASS record and is evidence for ENG-08.5,
not a benchmark of GitHub API latency.

No business code, execution capability, mandatory workflow, dependency or paid service is
changed by this qualification.
