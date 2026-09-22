# Bootstrap Engineering Engine (BEE)

## Purpose

The Bootstrap Engineering Engine is a deliberately small temporary control layer used to build the permanent Development Engine safely and coherently.

It exists to answer only five questions:

1. What are we building?
2. In what order?
3. Where are we now?
4. What is the exact next allowed action?
5. What must the next context-free agent read to resume safely?

It must **not** grow into a second permanent platform.

## Hard constraints

- Mandatory external paid API cost: **0 EUR**.
- Mandatory LLM/API calls: **0**.
- Business development remains paused until explicitly unlocked.
- Lot46 remains locked.
- No trading/execution/network capability may be enabled.
- Frozen historical evidence is read-only.
- Bootstrap validation must stay cheap and deterministic.
- Heavy assurance belongs to the permanent Development Engine, not BEE.

## Bootstrap lifecycle

```text
BOOT-00 Freeze & Inventory
    ↓
BOOT-01 Engineering Master Plan
    ↓
BOOT-02 Engineering State
    ↓
BOOT-03 Sub-Lot / Work-Item Standard
    ↓
BOOT-04 Agent Bootstrap Protocol
    ↓
BOOT-05 Handoff / Resume
    ↓
BOOT-06 Minimal Validation
    ↓
BOOT-07 Cold-Start Qualification
    ↓
Development Engine construction
```

No recursive meta-engine is allowed. BEE is level 0; the permanent Development Engine is level 1; Crypto Quant Bot business development is level 2.

## Bootstrap completion rule

BEE is complete only when a fresh agent with no prior conversation can be given only:

`@GitHub continue le développement de l'engine`

and can determine, from the repository alone:

- the canonical project identity;
- the current Git/business baseline;
- the active engineering work item;
- the exact next task;
- the allowed and forbidden scope;
- the required context;
- the current blockers;
- how to leave a valid handoff.

After BOOT-07, BEE becomes stable/frozen except for emergency repair.
