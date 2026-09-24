# Agent Bootstrap — Crypto Quant Bot V3.1-Ops

This file is the mandatory first entry point for any coding or audit agent.

<!-- BEGIN GENERATED CURRENT STATUS -->
## Current project status (generated)

> Generated from `config/governance/project_state.json`. Do not edit this block manually.

- Project: **Crypto Quant Bot V3.1-Ops**
- Business development: **PAUSED**
- Certified business baseline: **Lot 44 / 0.44.0 / GO_LOT44_POST_MERGE**
- Suspended business candidate: **Lot 45 / PR #66 / SUSPENDED_CANDIDATE**
- Next business lot: **Lot 46 / LOCKED**
- Engineering: **ENG-08 / ENG-08.6 / BUILDING**
- Next engineering lot: **ENG-09**
- Runtime maximum: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`
- Trading allowed: `false`
- Execution allowed: `false`
- Live execution: `DISABLED`
- Leverage: `FORBIDDEN`
- Withdrawals: `FORBIDDEN`
- Open blocking findings: `BOOT-FINDING-001` (MAIN_BRANCH_UNPROTECTED; before BUSINESS_DEVELOPMENT_UNLOCK)
<!-- END GENERATED CURRENT STATUS -->

## Start here

1. Read `config/governance/project_state.json`.
2. Read `engineering/CONTEXT_MAP.json` for the generated bounded route; it never overrides canonical state.
3. Resolve the requested track:
   - ordinary `continue` / development work → `engineering_track`;
   - historical audit work → `audit_track`, only when explicitly active/authorized.
4. Read the active manifest declared by that track, then resolve the single active AWU with `python scripts/governance/resolve_active_awu.py`.
5. Verify external Git reality before writing:
   - `main` still matches the recorded observation or an authorized transition;
   - the active engineering branch exists;
   - the recorded business candidate PR/head still matches when relevant.
6. Any unexpected mismatch is `STATE_DRIFT`; do not auto-heal state. When execution is available, `python scripts/governance/verify_external_git_state.py --mode github` is the canonical live check.
7. Read only the bounded context returned by the active AWU route. The context map lists the exact primary and reference files; do not recursively read the repository.
8. Continue only the active AWU; its allowlist is the executable boundary and the parent work-item manifest is only an upper bound.
9. Run the assurance level appropriate to the current work stage.
10. Update the handoff before ending a work session.

`engineering/STATE.json` is now a **migration compatibility bridge**, not the fresh-agent
source of current authorization.

## Canonical identity

- Project: **Crypto Quant Bot V3.1-Ops**.
- Same project since inception; never rename or fork its identity implicitly.
- Trading/execution remain disabled unless a future certified governance transition explicitly unlocks them.

## Authority by question

- Historical certification fact → immutable historical Git/evidence anchors.
- Current work authorization → `config/governance/project_state.json`.
- Current task → active work-item manifest; executable paths/context → active AWU.
- System rules/architecture → normative documents and contracts.
- Human summaries/handoffs → convenience only; never override higher authority.
- Chat history/model memory → never a source of authorization.

Conflicts affecting authorization fail closed as `STATE_DRIFT`.

## Business-development hold

While `business_track.development_status = PAUSED`:

- do not merge, extend or remediate Lot45 as part of engineering work;
- do not start or unlock Lot46;
- do not mutate frozen historical evidence;
- do not enable exchange/network execution, signals, risk approval, orders, leverage,
  withdrawals or live trading.

## Capability honesty

Use only evidence the current session can actually produce or inspect:

- `GITHUB_CONNECTOR_ONLY`: GitHub read/write if authorized; no local execution claim.
- `LOCAL_REPOSITORY`: local command claims only when actually executed.
- `CI_EXECUTION`: evidence only for the exact workflow run/head inspected.
- `READ_ONLY_AUDITOR`: no repository mutation.

Never convert an unavailable capability into an assumed PASS. Machine-readable capability/evidence rules live in `engineering/AGENT_CAPABILITIES.json`.

## Mandatory-cost rule

The mandatory path requires zero paid LLM/API tokens, zero paid SaaS, zero paid larger
runner and zero external paid service.

## Stop immediately on

- `STATE_DRIFT`;
- business scope touched without explicit unlock;
- frozen evidence mutation;
- Lot46 unlock attempt;
- mandatory paid dependency introduction;
- invalid active manifest/dependency/state-machine transition.

Deep startup/recovery semantics live in `engineering/AGENT_PROTOCOL.md`.
