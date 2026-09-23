# T3/T4 Requirement Selection — ENG-03.6

ENG-03.6 **selects obligations only**. It does not run scanners, deep assurance, mutation,
full regression, or certification.

### T3 assurance IDs
- `WORKFLOW_ASSURANCE`
- `SECURITY_ASSURANCE`
- `STATIC_ANALYSIS_ASSURANCE`
- `RISK_EXECUTION_ASSURANCE`
- `MANUAL_DEEP_REVIEW`

### T4 certification IDs
- `EXACT_HEAD_CERTIFICATION`
- `PROVENANCE_CERTIFICATION`
- `R3_FULL_CERTIFICATION_CHAIN`

Rules are fail-closed:
- residual workflow/security/static/unknown impacts become T3 obligations;
- R3 always requires risk/execution assurance plus exact-head full certification;
- `EVIDENCE_PROVENANCE`, even if T2-tested, requires T4 provenance + exact-head certification;
- low-risk fully covered work selects no T3/T4.

The selector reports `requirements_executed=[]`,
`assurance_executed=false`, and `certification_executed=false`. ENG-04 and later
certification work will satisfy these requirements.

Policy: `config/governance/validation_t3_t4_policy_v1.json`
Selector: `scripts/governance/select_t3_t4.py`
