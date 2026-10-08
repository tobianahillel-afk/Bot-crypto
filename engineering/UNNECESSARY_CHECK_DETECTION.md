# Unnecessary Validation Detection — ENG-08.2

ENG-08.2 defines overvalidation as **work that the canonical impact/risk policies do not
require**, not merely as a slow check.

The detector consumes a symbolic trace containing:

- impact families;
- AWU risk class;
- stage invocation counts;
- selected T1 checks;
- selected T2 groups;
- selected T3/T4 requirements;
- whether pytest, a full suite, network, T3 execution or T4 execution actually ran.

It then recomputes the expected work from the existing T1, T2, T3/T4 and incremental
validation policies.

Verdicts:

- `CLEAN`: actual work exactly equals required work;
- `OVERVALIDATED`: extra/repeated work occurred;
- `UNDERVALIDATED`: required work is missing;
- `MISMATCH`: both conditions exist.

Examples of overvalidation include:

- invoking T0/T1/T2 more than once;
- selecting an unmapped T1 check or T2 group;
- running pytest when no T2 group is selected;
- running a full suite, network operation, T3 assurance or T4 certification inside the
  incremental selection chain.

Examples of undervalidation include missing mapped checks/groups, omitted T3/T4
requirements, or failing to invoke pytest when a T2 group requires it.

This WU defines the pure detector only. The next WU will expose the required trace from the
existing single-pass run and qualify the detector in CI without creating a second validation
pass.

Policy: `config/governance/unnecessary_check_policy_v1.json`
Detector: `scripts/governance/detect_unnecessary_checks.py`


## Bootstrap integration

WU02 reuses the JSON already emitted by the single-pass incremental validator. The runner adds
only three trace fields that are already available in memory: `trace_version`,
`impact_families`, and `risk_class`.

The bootstrap then:

1. runs the single-pass validator once and stores its JSON in `RUNNER_TEMP`;
2. applies the existing timing budget to that same JSON;
3. runs the unnecessary-check detector against that same JSON;
4. runs synthetic adversarial detector tests.

No T0/T1/T2/selector stage is executed a second time for overvalidation detection.
