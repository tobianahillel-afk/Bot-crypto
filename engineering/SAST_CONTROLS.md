# SAST Controls — ENG-04.3

ENG-04.3 layers deep CodeQL analysis on top of the repository's existing Bandit gate instead
of adding a second redundant Python-only linter.

## Fast layer already present

The institutional quality workflow already installs the exact `requirements-dev.lock` and
runs:

```text
bandit -q -r src -ll
```

ENG-04.3 validates that this gate remains present and fail-closed.

## Deep layer

The dedicated SAST workflow uses:

- `github/codeql-action` tag `v4`, resolved and pinned to exact commit
  `1c5b675653bb5c22dbe9b12b556ec555138e09fd`;
- the pinned action commit's audited defaults: CodeQL bundle `v2.27.0`, CLI `2.27.0`;
- language: Python;
- query suite: `security-extended`;
- source root: `src/crypto_quant_bot`;
- `upload: never` and only `contents: read` permission.

Because no SARIF is uploaded to GitHub Code Scanning, the workflow performs its own local,
fail-closed SARIF gate. Missing SARIF fails. Any CodeQL result fails. Only zero findings
produces `CODEQL_SECURITY_EXTENDED_PASS`.

The workflow runs only for Python production-code changes or its own control files, plus weekly
and manual qualification. Documentation-only changes do not trigger it.

This provides deeper interprocedural security analysis without requiring a paid API, external
SaaS token, LLM, larger runner, or write permission.
