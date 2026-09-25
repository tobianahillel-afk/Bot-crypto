# ENG-09.1 — Lot45 Development Engine Pilot

## Verdict

**ENGINE_PILOT_PASS_CANDIDATE_BLOCKED**

The Development Engine successfully detects that the suspended Lot45 candidate is **not
currently certifiable or merge-ready**. This is a read-only pilot result, not business
authorization. BUSINESS remains PAUSED and Lot46 remains LOCKED.

## Exact Git state

- main: `390d0779f2be257fa8134faf8f02193a760a09c3`
- PR: #66, open, unmerged
- current PR head: `ec2c4ab16f21b23e062b7fca0bb796c8db4a5133`
- candidate: 228 commits, 48 changed files, +7689/-587
- engineering head used by pilot: `b4c7d459a23ed01d9b850cd3afb6def545a8b266`
- ENG-09 transition Bootstrap: `36123197944` SUCCESS
- ENG-09 transition Security Secrets: `36123198210` SUCCESS

## Why the old certification cannot be reused

The PR body cites frozen head `75e8a82fe7c20717f7351129073d1f47b373d4b9`, and that head genuinely had 49/49 successful
workflows. But Git proves the current PR head has **diverged** from it:

- ahead by 7
- behind by 5
- materially different files: `contracts/schemas/cvd_series_v1.schema.json`, `contracts/schemas/order_flow_state_v1.schema.json`, `src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine.py`, `src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_models.py`, `tests/test_lot45_final_review_contracts.py`, `tests/test_lot45_market_identity_binding.py`, `tests/test_lot45_order_flow_delta_and_cvd_engine.py`

Therefore the old 49/49 result is stale for the current candidate. The engine correctly requires
fresh exact-head evidence.

## Current exact-head state

Current head has 49 distinct workflows:

- SUCCESS: 26
- FAILURE: 23

Four directly relevant/global failures remain:

1. Lot45 entry gate — full regression/anti-flake; 2 Lot45 tests fail with CVD checksum canonical mismatch.
2. Lot45 frozen evidence — trusted pre-launch proof exits 67.
3. Institutional quality — one mypy error in the Lot45 models module.
4. P0.6 — mypy, full pytest and all three flake repetitions fail.

The other 19 failures are historical workflow fan-out, which is a major
signal-to-noise/performance problem for ENG-09.2.

## Unresolved substantive review evidence

There are 2 non-outdated unresolved review threads, both P1:

1. `src/crypto_quant_bot/microstructure/_order_flow_delta_and_cvd_engine_impl.py` line 447: ** Preserve market identity in order-flow artifacts** When two homogeneous trade batches differ only by source, venue, instrument, or market type, this validation accepts each batch but then discards the identity tuple; `OrderFlowStateV1` and `CVDSeriesV1` serialize none of these fields. For example, replacing every frozen trade's `instrument_id` with `ETH-USDT` produces byte-identical order-flow and CVD payloads and the same checksums as `BTC-USDT`, so the published standalone artifacts can be 
2. `src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_models.py` line 175: ** Bind matching identities to the certified input market** When both nested artifacts carry the same wrong identity, this equality check accepts them because it compares only Order Flow with CVD, not either identity with the homogeneous source batch or the fixed Lot 44 lineage. For example, `_build_engine_state` accepts BTC classified trades together with an ETH Order Flow/CVD pair sharing timestamps and produces a checksum-valid state claiming the certified Lot 44 lineage; validate the common 

The engine does **not** treat green historical CI as permission to ignore these findings.

## Engine classification

Aggregate labels:

- BUSINESS_PRODUCTION: 6 file(s)
- CERTIFICATION_EVIDENCE: 7 file(s)
- CI_WORKFLOW: 6 file(s)
- CONFIG_POLICY: 1 file(s)
- CONTRACT_SCHEMA: 4 file(s)
- DOCUMENTATION: 8 file(s)
- TEST_ONLY: 11 file(s)
- UNKNOWN_REQUIRES_REVIEW: 6 file(s)

Sensitivity: **CRITICAL**

Six operational files currently fall into `UNKNOWN_REQUIRES_REVIEW`, which is fail-closed but
too noisy. That is an engine-classifier defect routed to ENG-09.3, not a reason to weaken the
unknown-path gate.

## Mandatory decomposition

Under the current AWU policy this candidate could not be one execution unit:

- 48 files > 15
- conservative observed complexity score >= 15 > 10

The new engine would split this work before implementation/review, which directly addresses the
review churn seen in the historical Lot45 PR.

## Validation selected by the current engine

- T1: DIFF_CHECK, GOVERNANCE_ACTIVE_SCOPE, SELFTEST_ENTRYPOINT_CHECK
- T2: CHANGED_DOMAIN_TESTS, CONTRACT_TESTS, EVIDENCE_TESTS
- T3: MANUAL_DEEP_REVIEW, SECURITY_ASSURANCE, STATIC_ANALYSIS_ASSURANCE, WORKFLOW_ASSURANCE
- T4: EXACT_HEAD_CERTIFICATION, PROVENANCE_CERTIFICATION

T4 exact-head/provenance certification is mandatory because certification evidence itself changed.

## Engine/process findings

- **ENG09-PILOT-001 / CLASSIFIER_COVERAGE_GAP / MEDIUM → ENG-09.3** — Six changed operational files are UNKNOWN_REQUIRES_REVIEW: pyproject.toml, requirements-dev.lock and four Lot45 scripts. Fail-closed behavior is safe, but classification is noisier than necessary.
- **ENG09-PILOT-002 / LEGACY_WORKFLOW_FANOUT / HIGH → ENG-09.2** — Current candidate head has 49 distinct workflows; 23 fail and 19 of those failures are historical/non-Lot45 workflow fan-out.
- **ENG09-PILOT-003 / MANDATORY_LLM_REVIEW_MISMATCH / MEDIUM → ENG-09.2** — PR body still requires a fresh Codex review for merge progression, while Development Engine mandatory progress is explicitly LLM-independent. Substantive review findings must remain addressed, but one specific paid/quota-sensitive reviewer must not be the mandatory transport.
- **ENG09-PILOT-004 / TERMINAL_ENGINE_LIFECYCLE_SENTINEL / MEDIUM → ENG-09.3** — ENG-09 currently requires non-empty next_lot while BUILDING although no ENG-10 exists; ENGINE_COMPLETE is a temporary non-executable sentinel that must be hardened before ENG-09 completion.

## Safety

No Lot45 file, candidate branch, workflow, main branch, runtime permission or business status was
modified by this pilot. BUSINESS remains PAUSED, Lot45 remains suspended, Lot46 remains LOCKED,
and live trading/execution remain disabled.
