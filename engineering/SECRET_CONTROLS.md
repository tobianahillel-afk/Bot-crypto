# Secret Controls — ENG-04.1

ENG-04.1 uses the **MIT-licensed Gitleaks CLI**, not the separately licensed
`gitleaks-action`.

Pinned inputs:

- Gitleaks tag: `v8.30.1`
- Gitleaks source commit: `83d9cd684c87d95d656c1458ef04895a7f1cbd8e`
- Go: `1.24.11`
- `actions/checkout`: exact commit for v7.0.1
- `actions/setup-go`: exact commit for v7.0.0

The workflow clones the tag, verifies its exact source commit, and only then builds the CLI.

Every scan uses `--redact=100`. The workflow has only `contents: read`, uses
`persist-credentials: false`, and requires no Gitleaks license key, paid API, paid SaaS,
LLM, or larger runner.

Qualification is fail-closed:

1. a synthetic GitHub-token-shaped fixture is assembled only at runtime from fragments;
2. Gitleaks must reject that fixture;
3. the current repository tree is scanned;
4. the complete Git history is scanned.

No TOML allowlist is present. Real findings are triaged explicitly instead of being broadly
suppressed.

## Vetted historical false positives

The first real scan found two `generic-api-key` findings in the immutable roadmap audit
artifact `data/audit/product_scope_roadmap_lot21.jsonl`, on the Lot 119 and Lot 151 records.
Qualification showed that the captures are adjacent **contract identifiers** in their
`output_contracts` arrays, not credentials.

The exception mechanism is deliberately narrow:

- `.gitleaksignore` contains exactly two global fingerprints and no wildcard;
- their rationale is recorded in
  `config/governance/secret_false_positive_registry_v1.json`;
- the registry is bound to the exact historical Git blob
  `84de51bda788a8d124fb7d344419c4a4b12030b5`;
- the validator recomputes that Git blob SHA and checks the exact Lot identity plus contract
  identifier arrays;
- any byte change to the historical artifact invalidates the exception before scanning.

Policy: `config/governance/secret_control_policy_v1.json`
Workflow: `.github/workflows/security-secrets.yml`
Validator: `scripts/governance/validate_secret_controls.py`
