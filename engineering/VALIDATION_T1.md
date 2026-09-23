# T1 Targeted Validation — ENG-03.4

T1 is the first **impact-targeted** execution tier. It consumes a successful T0 result and
selects only hardcoded symbolic checks.

Current T1 checks:

- `DIFF_CHECK` — `git diff --check` for the active AWU diff;
- `GOVERNANCE_ACTIVE_SCOPE` — active AWU resolution + exact scope enforcement;
- `SELFTEST_ENTRYPOINT_CHECK` — static integrity of changed governance selftests.

The JSON policy maps **impact families to check IDs**, never to shell commands. Unknown check
IDs fail closed.

Impacts that T1 does not yet cover are returned as `uncovered_impacts`; they do not trigger a
blanket full suite. This is intentional. ENG-03.5+ decides domain/deep validation.

A documentation-only diff selects zero executable T1 checks because `DOC_CONSISTENCY` is
already satisfied by T0.

Policy: `config/governance/validation_t1_policy_v1.json`
Runner: `scripts/governance/run_t1.py`
