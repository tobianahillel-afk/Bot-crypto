# Work Decomposition & Context Engine — Qualification

ENG-02.8 proves the decomposition layer end to end.

The fresh-agent path is now:

```text
project_state
  -> active ENG task
  -> exactly one active AWU
  -> AWU dependency DAG
  -> deterministic complexity
  -> mandatory split decision
  -> deterministic R0-R3 risk
  -> bounded context route
  -> AWU Git diff boundary
  -> implementation
```

Qualification rejects, before implementation:

- oversized executable work;
- missing or cyclic dependencies;
- incomplete predecessors;
- unclassified executable risk;
- forged/over-budget context;
- duplicate active AWUs;
- out-of-scope Git diffs.

`resolve_next_work.py` exposes the exact AWU and its context route to a context-free agent.
No paid LLM reviewer or external SaaS is required.
