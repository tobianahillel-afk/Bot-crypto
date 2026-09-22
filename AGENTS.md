# Agent Bootstrap — Crypto Quant Bot V3.1-Ops

This file is the mandatory first entry point for any coding or audit agent.

## Start here

1. Read `engineering/STATE.json`.
2. Select the active track:
   - if `bootstrap_engine.phase = BUILDING`, use `bootstrap_engine.active_*`;
   - if `bootstrap_engine.phase = STABLE`, use `engineering_engine.active_*`.
3. Verify the declared GitHub reality before writing:
   - default branch and declared main SHA;
   - active engineering branch;
   - declared business candidate PR/ref when relevant.
4. If reality disagrees with canonical state, stop with `STATE_DRIFT`.
5. Read only:
   - `engineering/MASTER_PLAN.md`;
   - the selected track's active manifest;
   - `engineering/handoff/CURRENT.json`;
   - additional files explicitly required by the active work item/protocol.
6. Continue only the selected track's `active_task`.
7. Respect `allowed_paths`, `forbidden_scope`, dependencies and stop conditions.
8. Run only validation relevant to the current work stage.
9. Leave an updated handoff before ending work.

Do not reconstruct project state from chat history, model memory, README status text,
old PR descriptions, or comments when a higher-authority source exists.

## Canonical identity

- Project: **Crypto Quant Bot V3.1-Ops**.
- Same project since inception; do not rename or fork its identity.
- Real trading remains disabled unless a future certified governance state explicitly unlocks it.

## Current authority order

1. Frozen historical evidence for facts about past certifications.
2. `engineering/STATE.json` for current bootstrap/engineering state.
3. Active work-item manifest for current allowed work.
4. Normative project standards under `docs/`.
5. `engineering/MASTER_PLAN.md` for planned engineering sequence.
6. Handoff/status summaries.
7. PR descriptions/comments.
8. Chat history/model memory.

Conflicts between higher-authority sources are fail-closed and become `STATE_DRIFT`.

## Business-development hold

While canonical state says `business_development = PAUSED`:

- do not merge, extend, or remediate Lot45 as part of engine work;
- do not start or unlock Lot46;
- do not change frozen historical evidence;
- do not enable network/exchange execution, trading, leverage, withdrawals, signal authority,
  risk authority, order authority or live execution.

## Capability honesty

Identify the actual execution profile before claiming evidence:

- `GITHUB_CONNECTOR_ONLY`: may inspect/write GitHub resources; local commands were not run.
- `LOCAL_REPOSITORY`: may claim local commands only when actually executed.
- `CI_EXECUTION`: may rely on CI only for the exact commit/run proved by GitHub evidence.
- `READ_ONLY_AUDITOR`: must not mutate repository state.

Never convert an unavailable capability into an assumed PASS.

## Mandatory-cost rule

The mandatory path must require zero paid LLM/API tokens, zero paid SaaS dependency,
zero paid GitHub larger runner and zero external paid service.

## Stop immediately on

- `STATE_DRIFT`;
- business scope touched without explicit unlock;
- frozen evidence mutation;
- Lot46 unlock attempt;
- mandatory paid dependency introduction;
- an active task whose dependencies or manifest do not validate.

## Handoff

A handoff accelerates resume but is not evidence. A fresh agent must bind it to Git reality
before trusting it. Update the canonical handoff with current task, blockers and exact next
action before ending a work session.

Deep startup/recovery semantics live in `engineering/AGENT_PROTOCOL.md`.
