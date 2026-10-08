# Documentation Tooling Benchmark — ENG-05.6 WU04

## Scope

This work unit benchmarks **Vale v3.22.0 only**. It does not execute lychee or DocGuard and
does not make Vale authoritative over project documentation.

### Exact candidate

- Release: `v3.22.0`
- Source commit: `e109c06297dc58a513f10691a275f3a9465584a1`
- Linux x86_64 asset: `vale_3.22.0_Linux_64-bit.tar.gz`
- Required SHA-256: `52f5cd0314a1b7384cac6aa102a68193977312f6ba9c9f3ae001b5deec8e3a10`
- License: MIT

The workflow verifies the archive digest **before extraction or execution**.

## Offline benchmark design

Vale runs with a temporary `.vale.ini` and temporary project-local rule directory created by
the benchmark runner. No package is declared, no remote style source is used, and `vale sync`
is never executed.

The synthetic fixture contains one deterministic benchmark-only token. The local rule must
detect it. The same local rule is then run against four representative project Markdown files
to measure runtime and false-positive noise without changing any documentation.

Representative set:

- `README.md`
- `AGENTS.md`
- `engineering/MASTER_PLAN.md`
- `engineering/DOCUMENTATION_TOOLING_EVALUATION.md`

## Authority and cost

This benchmark is evidence-only. Canonical state, generated status, documentation-consistency
checks, context maps and handoff remain authoritative.

Mandatory paid API/SaaS/LLM/larger-runner cost: **0**.

## Runtime evidence — Vale

Validated workflow run: `35971610505` on source head
`92b0140e394c9e116bc364168046810d302eddf6`.

Measured Vale execution:

- Vale version: `3.22.0`
- Synthetic finding count: **1** (expected local rule `CQBBenchmark.Placeholder`)
- Synthetic elapsed time: **11.272 ms**
- Representative documents: **4**
- Representative finding count: **0**
- Representative elapsed time: **23.359 ms**
- Total Vale lint time: **34.631 ms**
- Networked style resolution: **false**
- `vale sync` executed: **false**
- Paid dependency: **false**

The archive SHA-256 matched
`52f5cd0314a1b7384cac6aa102a68193977312f6ba9c9f3ae001b5deec8e3a10`
before execution.

### Vale benchmark verdict

**ADOPT_PARTIALLY remains supported.** The pinned binary is fast and produced zero noise on
the bounded representative set, while the synthetic local rule proved that project-owned
rules work offline. A future changed-document integration may be justified, but only with
project-local rules, no package sync, and no authority over canonical/factual state.


---

# lychee Offline Benchmark — ENG-05.6 WU05

## Scope

This child benchmarks **lychee v0.24.2 only**. Vale evidence above remains unchanged. lychee
is evaluated only for local-link integrity and remains non-authoritative.

### Exact candidate

- Release: `lychee-v0.24.2`
- Audited source commit: `2bba271688c1abb1503097a064e6c3bc1d1b6a9b`
- Linux x86_64 GNU asset: `lychee-x86_64-unknown-linux-gnu.tar.gz`
- Required SHA-256:
  `1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a`
- License: MIT OR Apache-2.0
- GitHub release mutability observation: **not immutable**
- Execution trust boundary: the exact asset SHA-256, verified before extraction/execution.

## Offline benchmark design

Every lychee invocation is constructed by the benchmark runner with `--offline`, which
lychee v0.24.2 defines as checking local files only and blocking network requests. Remote URL
and `mailto:` inputs are rejected by the runner itself.

Synthetic controls:

1. an existing local Markdown target must pass;
2. a missing local Markdown target must return lychee's link-failure exit code and at least
   one JSON `errors` count.

The same offline mode then measures local-link findings in:

- `README.md`
- `AGENTS.md`
- `engineering/MASTER_PLAN.md`
- `engineering/DOCUMENTATION_TOOLING_EVALUATION.md`

No GitHub token, external URL health check, cache, paid API, SaaS, LLM, or larger runner is
required.

## Runtime evidence — lychee

Validated workflow run: `35972772349` on source head
`b61e6f3db7e72c66f811f4d2ab089825de364cdc`.

Measured lychee execution:

- lychee version: `0.24.2`
- Synthetic missing local link: **1 error**, exit code **2**, **13.170 ms**
- Synthetic valid local link: **0 errors**, exit code **0**, **13.510 ms**
- Representative documents: **4**
- Representative links checked: **67**
- Representative errors: **0**
- Representative timeouts/unknown/unsupported: **0 / 0 / 0**
- Representative elapsed time: **15.097 ms**
- Total lychee benchmark time: **41.777 ms**
- `--offline`: **required and used**
- External URL health checks: **false**
- GitHub token used by lychee: **false**
- Paid dependency: **false**

The release archive SHA-256 matched
`1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a`
before extraction or execution.

### lychee benchmark verdict

**ADOPT_PARTIALLY is supported.** The pinned binary is fast, correctly distinguishes valid
and missing local links, and found no local-link defects across the bounded representative
documentation set while network access was blocked by `--offline`.

A future integration should therefore be restricted to local-link integrity on changed
documentation (or another bounded local file set). External URL health checking remains
outside the mandatory path because it adds network variability, latency and rate-limit risk.
