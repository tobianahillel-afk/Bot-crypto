# Interruption & Recovery Qualification — ENG-08.6

## Goal

Prove that an interrupted or context-lost agent resumes **only** from permanent repository
authority and the unique active AWU, without relying on prior chat, model memory, or a stale
handoff.

## Authority

Recovery resolves from:

1. `config/governance/project_state.json`;
2. the validated unique active AWU;
3. its bounded `context_route`.

`engineering/handoff/CURRENT.json` and `engineering/CONTEXT_MAP.json` are useful hints, but
they are never authorization sources. `engineering/STATE.json`, chat history and model memory
are excluded from the recovered read order.

## Write gate

A successful recovery is intentionally **read-only**:

- `write_authorized=false`;
- `live_git_reverify_satisfied=false`;
- `required_before_write=["LIVE_GIT_REVERIFY_REQUIRED"]`.

A fresh agent must re-read live GitHub state (main, engineering branch, suspended business
candidate and any relevant protection state) before any resumed write. Recovery never
auto-heals canonical state to match surprise Git movement.

## Adversarial cases

The qualification covers, at minimum:

- valid hints;
- stale handoff;
- missing handoff;
- stale context map;
- missing context map;
- simultaneously stale handoff + context;
- simultaneously missing handoff + context;
- stale safety claims;
- implicit context expansion;
- context-route count/budget drift;
- authoritative-hint escalation attempt;
- Lot46 unlock;
- mandatory paid-LLM introduction;
- ambiguous active AWU.

All recovery routes must resolve the canonical ENG-08.6 AWU or fail closed.

## Safety preservation

Recovery asserts that:

- BUSINESS remains `PAUSED`;
- Lot46 remains `LOCKED`;
- trading and execution remain disabled;
- live execution remains `DISABLED`;
- leverage and withdrawals remain forbidden.

## Performance

The permanent interruption/recovery qualifier and adversarial selftest each use a generous
**1000 ms CI ceiling**. The evidence file records the measured exact-head result once Bootstrap
and Security Secrets both pass on the same commit.
