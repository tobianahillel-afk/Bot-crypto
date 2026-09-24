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

## Runtime evidence

Pending the first successful execution of
`.github/workflows/documentation-tooling-benchmark.yml`. The workflow emits a bounded
`VALE_BENCHMARK_SUMMARY` containing only finding counts, elapsed Vale runtime and document
count.
