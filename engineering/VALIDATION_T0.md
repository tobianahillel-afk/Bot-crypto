# T0 Instant Validation — ENG-03.3

T0 is the universal cheap gate. It runs on the **active AWU diff only**.

It performs:

- exact changed-file discovery from the AWU `scope_base_sha`;
- Python syntax compilation via `compile()` without importing project modules;
- JSON parsing with `json`;
- TOML parsing with `tomllib`;
- deterministic diff classification and impact mapping;
- escalation metadata for elevated/critical or unknown impact;
- elapsed-time reporting.

It deliberately does **not** run pytest, mypy, Ruff, mutation, replay, security scanners,
network calls, or certification.

An elevated/critical result is not a failure by itself. T0 reports that deeper validation is
recommended; later ENG-03 stages decide what is actually required.

Policy: `config/governance/validation_t0_policy_v1.json`
Runner: `scripts/governance/run_t0.py`
