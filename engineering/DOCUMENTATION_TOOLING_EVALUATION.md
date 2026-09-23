# Documentation Tooling Evaluation — ENG-05.6

> Generated from `config/governance/documentation_tooling_candidates_v1.json`.
> This phase evaluates candidates only; it does not install or execute them.

Observed: **2026-09-24**

## Verdicts

| Tool | Release | License | Runtime | Verdict | Immediate decision |
| --- | --- | --- | --- | --- | --- |
| DocGuard | v0.42.1 | MIT | NODE_CLI | **COPY_PATTERN** | Reuse selected deterministic evidence/guard/lifecycle patterns only; reconsider a pinned runtime integration if Spec Kit artifacts become active. |
| Vale | v3.22.0 | MIT | STATIC_GO_BINARY | **ADOPT_PARTIALLY** | Benchmark a pinned binary with project-local rules on changed Markdown only; no vale sync in the mandatory path and no authority over factual/canonical state. |
| lychee | lychee-v0.24.2 | MIT OR Apache-2.0 | STATIC_RUST_BINARY | **ADOPT_PARTIALLY** | Benchmark a pinned binary with --offline on changed documentation for local links; keep external URL checks scheduled/advisory only. |

## Candidate rationale

### DocGuard

- Repository: `raccioly/docguard`
- Exact source commit: `90684da66d52230b462e92a3f5f0e35e84ead9c5`
- Published: `2026-09-22T16:40:18Z`
- Current-engine overlap: `HIGH`
- Authority: `NON_AUTHORITATIVE`
- Rationale: The current engine already owns canonical state, generated status, context, handoff and drift checks, while no Spec Kit artifacts are present. Installing DocGuard now would duplicate governance and add Node/npm surface before its strongest integration is needed.
- Rollback: No runtime adoption in this phase; copied patterns remain project-owned.

### Vale

- Repository: `vale-cli/vale`
- Exact source commit: `e109c06297dc58a513f10691a275f3a9465584a1`
- Published: `2026-09-17T15:23:38Z`
- Current-engine overlap: `LOW`
- Authority: `NON_AUTHORITATIVE`
- Rationale: Vale fills the currently missing prose-style layer and can run fully offline, but useful behavior depends on carefully designed local rules; remote style-package sync would add avoidable network and drift.
- Rollback: Remove the optional binary/config/rules without changing canonical documentation authority.

### lychee

- Repository: `lycheeverse/lychee`
- Exact source commit: `2bba271688c1abb1503097a064e6c3bc1d1b6a9b`
- Published: `2026-05-01T15:41:38Z`
- Current-engine overlap: `LOW`
- Authority: `NON_AUTHORITATIVE`
- Rationale: lychee fills the missing link-integrity layer. Its --offline mode can make local-link checks deterministic; external URL health is network-dependent and therefore unsuitable as a mandatory per-change gate.
- Rollback: Remove the optional binary/config/workflow step; canonical docs and state remain unaffected.

## Follow-up

- Benchmark AWU required: `true`
- Proposed AWU: `ENG-05.6-WU03`
- Benchmark candidates: `VALE`, `LYCHEE`
- DocGuard revisit condition: `SPEC_KIT_ARTIFACTS_PRESENT`

The mandatory path remains zero-cost, offline, non-LLM and governed by the project's
existing canonical state. External tools may only add bounded lint evidence.
