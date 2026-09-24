# Proof-Reuse Effectiveness — ENG-08.3

ENG-03.7 already certified the **safety semantics** of exact-input proof reuse. ENG-08.3
measures whether those semantics can avoid redundant eligible work without weakening them.

## WU01 boundary

WU01 is a measurement harness only. It does **not**:

- modify `scripts/governance/proof_reuse.py`;
- modify `config/governance/proof_reuse_policy_v1.json`;
- create a production cache;
- persist proofs externally;
- reuse T0, T3 or T4;
- infer wall-clock savings that were not directly measured.

The exact-match scenario makes two logically identical requests. Without reuse, the baseline
would execute the subject twice. The harness executes the first request, issues a PASS proof,
then evaluates the second request against the exact same proof material. The second executor
call is suppressed only when the certified engine returns `reusable=true`.

The report distinguishes:

- **baseline executions** — how many executor calls would occur without reuse;
- **actual executions** — directly counted executor calls;
- **avoided executions** — baseline minus actual;
- **reuse hits/misses/rejections**;
- **request hit rate** and **candidate-lookup hit rate**;
- **proof lookup elapsed time** measured with `perf_counter()`;
- **executor elapsed time** actually observed.

`saved_elapsed_ms` is deliberately null. An avoided call is real evidence; converting it
into claimed saved wall-clock time without timing the counterfactual would not be.

## Qualification split

WU01 proves the generic control-flow mechanism with deterministic local fixtures. WU02 will
qualify the same measurement against a real reusable T1 subject
(`SELFTEST_ENTRYPOINT_CHECK`) and wire the qualification into bootstrap without adding a
production proof cache.

Policy: `config/governance/proof_reuse_effectiveness_policy_v1.json`

Harness: `scripts/governance/measure_proof_reuse_effectiveness.py`


## WU02 — real T1 qualification

WU02 qualifies the mechanism against the repository's real
`SELFTEST_ENTRYPOINT_CHECK`, not a synthetic stand-in.

The qualification:

1. resolves the active AWU and its exact `scope_base_sha`;
2. discovers the changed `scripts/governance/selftest_*.py` files from that AWU diff;
3. requires the WU02 effectiveness selftest to be one of those files;
4. builds proof material that binds:
   - canonical project state;
   - the active AWU manifest;
   - every changed governance selftest;
   - T1, proof-reuse, effectiveness, complexity, split, risk and context policies;
   - `run_t1.py`, `run_t0.py`, the active-AWU resolver and its validators;
   - active AWU id, scope base, symbolic check id and the exact changed-selftest path set;
   - the current Python/platform environment;
5. calls the real T1 `SELFTEST_ENTRYPOINT_CHECK` for the first request and verifies its
   inspected path set;
6. evaluates the identical second request through the certified proof engine and requires
   `EXACT_INPUT_MATCH`;
7. proves that the real executor was called exactly once rather than twice.

This remains an **isolated qualification**. The canonical single-pass T1 validation still
runs normally and is not skipped. No proof is persisted across jobs and no production cache is
introduced.
