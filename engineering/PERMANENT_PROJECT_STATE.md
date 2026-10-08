# Permanent Project State — Migration Stage

`config/governance/project_state.json` is now the **permanent-state candidate**.

During ENG-01.2–ENG-01.3, `engineering/STATE.json` remains a compatibility authority so
the existing bootstrap validators can prove parity while the permanent state machine is
built.

Track responsibilities:

- **BUSINESS** — certified merged baseline, merged gate, candidate PR and next lock;
- **ENGINEERING** — active Development Engine lot/task;
- **AUDIT** — independent historical audit campaign lifecycle.

The tracks are intentionally independent. Advancing ENGINEERING must not imply business
promotion, and opening an AUDIT batch must not mutate business certification state.

The authority switch to `config/governance/project_state.json` for fresh agents occurs in
ENG-01.4 after state-machine semantics are enforced.
