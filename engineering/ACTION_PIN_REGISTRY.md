# Approved GitHub Action Pin Registry — ENG-04.5 WU02

The repository now separates two concerns:

1. **legacy debt inventory** — existing floating refs are measured but are not bulk-rewritten;
2. **anti-regression** — any remote action reference added or modified must use an exact
   40-hex SHA that is approved for that exact owner/repository in the offline registry.

Registry: `config/governance/action_pin_registry_v1.json`

## Live provenance verified on 2026-09-23

| Repository | Source ref | GitHub ref object | Approved commit | License |
| --- | --- | --- | --- | --- |
| actions/checkout | v4 | commit `11d5960a326750d5838078e36cf38b85af677262` | same | MIT |
| actions/checkout | v7.0.1 | commit `3d3c42e5aac5ba805825da76410c181273ba90b1` | same | MIT |
| actions/setup-python | v5 | commit `a26af69be951a213d495a4c3e4e4022e16d87065` | same | MIT |
| actions/setup-python | v7.0.0 | commit `5fda3b95a4ea91299a34e894583c3862153e4b97` | same | MIT |
| actions/upload-artifact | v4 | commit `ea165f8d65b6e75b540449e92b4886f43607fa02` | same | MIT |
| actions/setup-go | v7.0.0 | commit `b7ad1dad31e06c5925ef5d2fc7ad053ef454303e` | same | MIT |
| actions/dependency-review-action | v5.0.0 | commit `a1d282b36b6f3519aa1f3fc636f609c47dddb294` | same | MIT |
| github/codeql-action | v4.38.1 | annotated tag `c23de5a82f64bb08c6d9f28844551440ca298e76` | `1c5b675653bb5c22dbe9b12b556ec555138e09fd` | MIT |

For the CodeQL action, the tag object is deliberately stored separately from the dereferenced
commit so an annotated tag cannot be confused with an executable commit pin.

The validator is **offline**. GitHub is consulted only when a human/agent deliberately refreshes
the evidence registry; mandatory CI never performs tag or license network lookups.

## Legacy replacement map

Only the floating refs actually present in the legacy inventory receive deterministic
replacements:

- `actions/checkout@v4` → `11d5960a326750d5838078e36cf38b85af677262`
- `actions/setup-python@v5` → `a26af69be951a213d495a4c3e4e4022e16d87065`
- `actions/upload-artifact@v4` → `ea165f8d65b6e75b540449e92b4886f43607fa02`

This does **not** bulk-rewrite the 211 historical floating refs. It provides a verified
replacement when each workflow is touched naturally.

## Fail-closed behavior

A changed workflow fails when it contains:

- a floating remote ref;
- a dynamic or malformed `uses:` value;
- a 40-hex SHA not registered for that exact action repository.

Registry tampering also fails closed: repository set, owner, MIT license, source-ref provenance,
annotated-tag dereference, exact license URL, legacy replacement, and current repository
coverage are all validated.

No paid API, SaaS, LLM, runtime package install, or larger runner is required for the mandatory
registry gate.
