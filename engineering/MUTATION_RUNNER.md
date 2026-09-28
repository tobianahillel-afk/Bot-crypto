# Generic Mutation Profile Runner — ENG-09.3 WU11

WU11 introduces a reusable mutation runner without migrating any production/main trigger.

## Safety model

The profile registry is data only. The runner first executes the WU10 validator and accepts
only one enabled, validated profile. No profile field can supply a shell command, executable,
argv, or environment variable.

The only mutation subprocesses are fixed in source:

```text
python -m mutmut run
python -m mutmut results
```

The runner rejects non-`CURRENT_CHECKOUT` source bindings during WU11.

## P0.6 parity

For `P06_DECISION_EVIDENCE`, the runner materializes the exact declarative mutation
configuration into `[tool.mutmut]`, using the WU10-bound:

- source path and single mutation target;
- exactly two decision-evidence tests;
- `also_copy` list;
- covered-line, stack-depth and timeout controls;
- do-not-mutate patterns;
- score numerator/denominator and 80% floor.

`pyproject.toml` is restored in a `finally` block and the configured source tree must remain
Git-clean.

## Workflow lifecycle

`.github/workflows/ci-mutation.yml` is **parity-only in WU11**:

- push trigger: engineering branch only;
- manual trigger: one choice, `P06_DECISION_EVIDENCE`;
- no `main` push or pull-request trigger;
- legacy `p06-extended-mutation.yml` remains active and byte-identical.

WU12 may migrate the trigger surface only after exact-head parity evidence is recorded.

## Evidence

The runner writes the profile evidence under the profile-declared
`reports/quality/p06_extended_mutation/` directory. It records exact source head, profile
version, source binding, legacy workflow blob, materialized config hash, fixed tool versions,
mutation counts, score terms, threshold, and PASS/FAIL.
