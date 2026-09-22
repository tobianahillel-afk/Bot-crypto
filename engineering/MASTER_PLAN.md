# Development Engine — Master Plan

## Objective

Build a small, durable development control plane that lets a context-free AI agent safely resume Crypto Quant Bot development from GitHub without relying on previous chats, paid LLM review, or repeated manual reconstruction.

The permanent engine must maximize security while minimizing routine development overhead.

## Non-negotiable design rules

1. **Thin control plane** — reuse mature open-source/GitHub-native tools instead of rebuilding them.
2. **Free mandatory path** — no paid SaaS, paid runner, paid LLM or API token may be required to make progress.
3. **Risk-proportional assurance** — expensive checks run only when relevant.
4. **Incremental first** — ordinary edits use fast targeted validation; deep certification runs only on a stable candidate.
5. **One source of current truth** — current state is machine-readable and status views derive from it.
6. **Bounded agent context** — agents load only task-relevant context.
7. **Bounded work units** — oversized work is split before implementation.
8. **Evidence over summaries** — PR text and handoff accelerate work but never replace proof.
9. **No silent historical rewrite** — audit findings and remediations are separate.
10. **Security stays fail-closed** — especially for data, lineage, risk, permissions, OMS/EMS and any future live boundary.

## Current business freeze

At bootstrap start:

- merged certified baseline: **Lot44**;
- main: `390d0779f2be257fa8134faf8f02193a760a09c3`;
- Lot45 candidate: PR #66, separate from main;
- Lot46: locked;
- business development: paused while the engineering foundation is built.

This section is descriptive. `engineering/STATE.yaml` is the current bootstrap state authority.

# Phase A — Bootstrap Engine

## BOOT-00 — Freeze & Inventory

Goal: establish the exact starting point without changing business code.

Deliverables:
- verified main/base SHA;
- verified Lot45 PR separation;
- inventory of existing normative docs and quality controls;
- confirmation that no previous agent bootstrap exists;
- explicit business-development hold.

Exit: baseline is unambiguous and protected.

## BOOT-01 — Engineering Master Plan

Goal: define the whole Development Engine before implementing it.

Deliverables:
- this master plan;
- ENG-00 → ENG-09 sequence;
- major sub-lots;
- dependency order;
- performance/free/security principles.

Exit: a future agent can see the complete intended route.

## BOOT-02 — Engineering State

Goal: create a tiny canonical bootstrap state and transition model.

Sub-work:
- BOOT-02.1 state fields and authority;
- BOOT-02.2 legal state transitions;
- BOOT-02.3 consistency rules;
- BOOT-02.4 minimal state validator.

Exit: current/next work cannot be ambiguous.

## BOOT-03 — Sub-Lot / Work-Item Standard

Goal: define one small manifest format for BOOT/ENG work.

Sub-work:
- BOOT-03.1 required fields;
- BOOT-03.2 dependencies;
- BOOT-03.3 allowed/forbidden paths;
- BOOT-03.4 task status rules;
- BOOT-03.5 done/blocked semantics.

Exit: every engine task is bounded and machine-checkable.

## BOOT-04 — Agent Bootstrap Protocol

Goal: make context-free startup deterministic.

Sub-work:
- BOOT-04.1 root AGENTS protocol;
- BOOT-04.2 source-of-truth precedence;
- BOOT-04.3 GitHub-only capability rules;
- BOOT-04.4 stop/state-drift conditions.

Exit: agents know exactly what to read first and what not to infer.

## BOOT-05 — Handoff / Resume

Goal: survive chat/context loss without trusting stale summaries.

Sub-work:
- BOOT-05.1 handoff schema;
- BOOT-05.2 last-verified-ref binding;
- BOOT-05.3 stale-handoff detection;
- BOOT-05.4 recovery sequence.

Exit: interrupted work resumes safely.

## BOOT-06 — Minimal Validation

Goal: validate the bootstrap itself cheaply.

Checks:
- YAML/manifest consistency;
- one active work item;
- dependency consistency;
- valid next task;
- no completed item marked active;
- scope/path rules for bootstrap files.

Exit: bootstrap errors fail fast without running the bot's heavy CI.

## BOOT-07 — Cold-Start Qualification

Goal: prove BEE works.

Tests:
- fresh agent: continue engine;
- fresh agent: inspect state;
- fresh agent: recover from stale handoff;
- fresh agent: attempt forbidden Lot46 progression;
- GitHub-only agent: no false claim of local execution.

Exit: BEE = STABLE and permanent engine construction may proceed.

# Phase B — Permanent Development Engine

## ENG-00 — Repository Truth Recovery

Sub-lots:
- ENG-00.1 inventory authoritative sources;
- ENG-00.2 reconcile project identity/version/status drift;
- ENG-00.3 map current Git/PR/certification reality;
- ENG-00.4 protect historical evidence;
- ENG-00.5 define canonical baseline.

## ENG-01 — Agent Bootstrap & Canonical State

Sub-lots:
- ENG-01.1 permanent project-state schema;
- ENG-01.2 BUSINESS / ENGINEERING / AUDIT tracks;
- ENG-01.3 permanent state machine;
- ENG-01.4 agent startup protocol;
- ENG-01.5 GitHub-only execution protocol;
- ENG-01.6 state-drift detection.

## ENG-02 — Work Decomposition & Context Engine

Sub-lots:
- ENG-02.1 work-unit schema;
- ENG-02.2 dependency DAG;
- ENG-02.3 complexity scoring;
- ENG-02.4 mandatory split rules;
- ENG-02.5 risk classification R0–R3;
- ENG-02.6 context routing and context budgets;
- ENG-02.7 scope validator;
- ENG-02.8 qualification.

## ENG-03 — Incremental Validation Engine

Sub-lots:
- ENG-03.1 diff classifier;
- ENG-03.2 impact/test dependency map;
- ENG-03.3 T0 instant checks;
- ENG-03.4 T1 targeted checks;
- ENG-03.5 T2 domain checks;
- ENG-03.6 assurance/certification selector;
- ENG-03.7 safe proof reuse/cache;
- ENG-03.8 timing/overhead metrics.

## ENG-04 — Security & Supply Chain Engine

Target integrations, subject to audit before adoption:
- GitHub CodeQL;
- Semgrep Community Edition;
- Bandit;
- Gitleaks;
- actionlint;
- zizmor;
- OSV Scanner / pip-audit;
- GitHub Dependency Review;
- OpenSSF Scorecard;
- import-linter / deptry where useful.

Sub-lots:
- ENG-04.1 secret controls;
- ENG-04.2 dependency controls;
- ENG-04.3 SAST;
- ENG-04.4 Actions security;
- ENG-04.5 supply-chain/pinning;
- ENG-04.6 permission minimization;
- ENG-04.7 zero-cost verification.

No mandatory LLM reviewer.

## ENG-05 — Documentation, Context & Handoff

Sub-lots:
- ENG-05.1 generated current-status blocks;
- ENG-05.2 documentation consistency;
- ENG-05.3 context map/index;
- ENG-05.4 handoff format;
- ENG-05.5 resume/recovery;
- ENG-05.6 documentation tooling evaluation (e.g. DocGuard/Vale/lychee).

## ENG-06 — Certification & Provenance

Sub-lots:
- ENG-06.1 candidate lifecycle;
- ENG-06.2 exact-head binding;
- ENG-06.3 risk-proportional deep assurance;
- ENG-06.4 provenance/attestation;
- ENG-06.5 promotion rules;
- ENG-06.6 post-merge verification without redundant full reruns.

## ENG-07 — Historical Audit Engine

Sub-lots:
- ENG-07.1 complexity-aware audit batching;
- ENG-07.2 historical audit manifest;
- ENG-07.3 requirement/code/test/evidence mapping;
- ENG-07.4 findings registry;
- ENG-07.5 isolated remediation workflow;
- ENG-07.6 immutable historical evidence protection.

## ENG-08 — Performance & Cold-Start Qualification

Sub-lots:
- ENG-08.1 T0/T1/T2 timing budgets;
- ENG-08.2 unnecessary-check detector;
- ENG-08.3 proof-reuse effectiveness;
- ENG-08.4 mandatory-cost = 0 verification;
- ENG-08.5 context-free cold-start tests;
- ENG-08.6 interruption/recovery tests;
- ENG-08.7 critical R3 bypass tests.

The engine must pass both **SAFE** and **FAST** verdicts.

## ENG-09 — Productionization / Lot45 Pilot

Sub-lots:
- ENG-09.1 run engine against the suspended Lot45 candidate;
- ENG-09.2 identify workflow/review redundancies;
- ENG-09.3 repair engine defects;
- ENG-09.4 certify Development Engine V1;
- ENG-09.5 freeze V1 bootstrap interfaces;
- ENG-09.6 explicitly decide business-development unlock.

Only after ENG-09 may normal business roadmap progression be unlocked.

# Runtime validation tiers target

```text
T0 INSTANT
  every meaningful change
  cheap state/scope/lint/basic static checks

T1 TARGETED
  affected unit/contract/property tests

T2 DOMAIN
  work unit nearing completion

T3 ASSURANCE
  only for sensitive/high-risk changes

T4 CERTIFICATION
  one stable candidate, exact-head proof
```

A documentation-only change must not trigger an execution-domain certification.
A risk/execution boundary change must not be able to bypass strengthened assurance.

# Cost policy target

Mandatory path:
- paid external API: forbidden;
- paid LLM tokens: forbidden;
- paid SaaS dependency: forbidden;
- paid GitHub larger runners: forbidden.

Optional experiments may use other services only if project progress never depends on them.
