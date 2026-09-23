# ENG-04 Security Engine Verification

Final engineering verdict: **PASS_ENGINEERING_SECURITY**.

Business unlock remains **BUSINESS_UNLOCK_BLOCKED_EXTERNAL_PROTECTION** because the current
repository-protection observation reports `main` as unprotected, zero repository rulesets,
and no verifiable PR/status/force-push/deletion enforcement. This external administration
blocker is intentionally not treated as an engineering failure and is not bypassed.

## Cost and proportionality

- Mandatory controls require no paid API, SaaS, LLM, or larger runner.
- Dependency, SAST, workflow-security, and supply-chain workflows are path-scoped.
- Secret scanning remains universal on pushes and pull requests.
- Routine secret runs scan only the introduced Git range plus the runtime positive control.
- A missing/unusable range falls back to full-history scanning.
- Current-tree plus full-history secret assurance remains available weekly and by manual dispatch.
- The final verifier is offline and does not re-run heavy scanners.

## Security invariants retained

- Exact registered SHA pins for every remote action in the five security workflows.
- Existing least-privilege workflow permission policy passes all five security workflows.
- Gitleaks remains redacted, exact-source-pinned, and protected by its positive control.
- Dependency Review and pip-audit remain fail-closed.
- CodeQL security-extended remains local-SARIF fail-closed.
- actionlint/zizmor and action supply-chain/permission gates remain bounded to relevant workflow changes.
- `BOOT-FINDING-001` remains the explicit business-unlock blocker until repository protection is positively verified.
