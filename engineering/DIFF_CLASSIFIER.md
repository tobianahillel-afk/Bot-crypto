# Deterministic Diff Classifier — ENG-03.1

The classifier is intentionally **classification-only**. It does not choose tests and does
not authorize skipping assurance.

## Semantics

Each changed path can receive multiple labels. Examples:

- documentation;
- governance control;
- CI workflow;
- contract/schema;
- config/policy;
- tests;
- business production;
- data pipeline;
- security;
- risk/execution critical;
- certification evidence.

A path matching no rule receives `UNKNOWN_REQUIRES_REVIEW`.

`DOC_ONLY` is an aggregate label, not a path rule. It appears only when every changed path
has exactly documentation-class semantics. A governance Markdown file is therefore not
`DOC_ONLY`, and a mixed docs + production diff is never docs-only.

Critical/security/unknown labels are fail-closed markers for later ENG-03 selectors. ENG-03.1
does not map labels to validation tiers yet.

Policy: `config/governance/diff_classifier_policy_v1.json`
Executable: `scripts/governance/classify_diff.py`
