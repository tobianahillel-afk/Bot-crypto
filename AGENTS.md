# Agent Bootstrap — Crypto Quant Bot V3.1-Ops

This file is the first entry point for any coding or audit agent working in this repository.

## 1. Canonical identity

- Project: **Crypto Quant Bot V3.1-Ops**.
- This is the same project that has existed since the beginning.
- Do not rename, fork into a new product identity, or infer identity from stale status text.
- Real trading remains disabled unless a future certified governance state explicitly says otherwise.

## 2. Current bootstrap rule

The repository is currently building its permanent Development Engine.

Before any implementation work:

1. Read `engineering/STATE.json`.
2. Read `engineering/MASTER_PLAN.md`.
3. Read `engineering/handoff/CURRENT.yaml`.
4. Read the manifest for the active BOOT/ENG work item.
5. Verify the declared Git/PR state against GitHub before writing.
6. Continue only the declared active task.

Do **not** infer the next task from README text, an old PR description, chat history, or model memory.

## 3. Business-development hold

While `engineering/STATE.json` declares `business_development: PAUSED`:

- do not merge or extend Lot45 as part of engineering-engine work;
- do not start Lot46;
- do not activate networking, exchange connectivity, trading, leverage, withdrawals, risk authority, order authority, or execution authority;
- do not rewrite or delete frozen historical evidence.

Lot44 is the current merged certified business baseline. PR #66 is a separate Lot45 candidate and must remain isolated unless the canonical state explicitly unlocks it.

## 4. Source-of-truth precedence during bootstrap

1. Frozen historical evidence for facts about past certification.
2. `engineering/STATE.json` for current engineering/bootstrap state.
3. Active work-item manifest for allowed current work.
4. Normative project standards in `docs/`.
5. `engineering/MASTER_PLAN.md` for planned engineering sequence.
6. Generated/readme/status summaries.
7. PR descriptions and comments.
8. Chat history or model memory.

If two higher-authority sources conflict, stop implementation and record `STATE_DRIFT`.

## 5. Development principles

The Development Engine must be:

- security-first and fail-closed;
- free-by-construction for the mandatory path;
- independent of paid LLM/API tokens;
- incremental, diff-aware and risk-aware;
- fast on ordinary changes;
- heavy only when the risk or certification stage requires it;
- resumable by a fresh agent with no chat context;
- evidence-driven: summaries are not certification evidence.

## 6. Tool honesty

An agent must never claim a local test was executed if it only has GitHub access.
When only GitHub tools are available, use GitHub Actions or repository evidence and state that boundary accurately.

## 7. Completion and handoff

At the end of a work session:

- update the active manifest/task state when appropriate;
- update `engineering/handoff/CURRENT.yaml`;
- record the last verified commit/ref and blockers;
- do not choose or unlock future business work outside the state machine.

The permanent Development Engine will eventually supersede this minimal bootstrap protocol. Until then, these rules are authoritative for engineering-engine work.
