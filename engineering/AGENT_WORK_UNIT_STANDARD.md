# Agent Work Unit Standard V1

An **Agent Work Unit (AWU)** is the smallest machine-readable unit an implementation agent
may execute, below an ENG/BOOT/AUD work-item task.

## Planning progression

- ENG-02.3: deterministic complexity score.
- ENG-02.4: deterministic mandatory split decision.
- ENG-02.5: risk class R0-R3.
- ENG-02.6: context budget.

### Mandatory split

`planning.size_estimate` declares bounded structural estimates. CI combines those estimates
with the verified complexity score and applies
`config/governance/awu_split_policy_v1.json`.

Current mandatory split triggers include:

- complexity score > 10;
- >1 business domain;
- >15 touched files;
- >800 executable LOC changed;
- >1 new public behavior;
- >1 contract family;
- >1 independent algorithm;
- >1 state machine;
- >1 trust boundary;
- >1 new dependency;
- >1 cross-domain interface.

`split_reasons` must exactly equal the deterministic reason list. If a split is required,
the AWU may only remain `PLANNED` or `BLOCKED`; it cannot be executable or completed.

This turns “massive changes must be separated” into a machine-enforced rule rather than
reviewer discretion.
