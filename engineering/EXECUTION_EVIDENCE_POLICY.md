# Agent Execution & Evidence Policy V1

The Development Engine separates **capability**, **execution**, and **evidence**.

A tool being able to read GitHub does not imply local execution. A workflow existing does
not imply it passed. A previous successful run does not certify a new HEAD.

Machine policy: `engineering/AGENT_CAPABILITIES.json`.

## Core rules

- GitHub-only agents may report a CI PASS only when they inspected an exact workflow run,
  its conclusion and its exact head SHA.
- GitHub-only agents may never claim `LOCAL_TEST_PASS`.
- Local agents may claim local tests only with actual command execution evidence.
- Read-only auditors may not claim repository mutation.
- A head change invalidates prior exact-head CI claims for the new candidate.
- Missing capability is an explicit limitation, not an inferred PASS.

The validator exposes claim semantics as Python functions so later automation can validate
machine-readable evidence records without an LLM.
