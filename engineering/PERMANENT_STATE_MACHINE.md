# Permanent Project-State Transition Policy V1

ENG-01.3 turns the permanent state into a state machine rather than a mutable status file.

## Enforcement model

CI validates two things:

1. current-state invariants;
2. the actual Git transition from `HEAD^:config/governance/project_state.json` to
   `HEAD:config/governance/project_state.json`.

This means a writer cannot skip from `ENG-01.2` to `ENG-01.4` merely by editing JSON.

## Foundation locks

Until later engine lots explicitly change the policy:

- BUSINESS is immutable and remains paused;
- safety is immutable and fail-closed;
- mandatory-cost policy is immutable and zero-cost;
- ENGINEERING tasks advance by current manifest order only;
- ENGINEERING lots advance through `next_lot` only and append the previous lot to
  `completed`;
- findings cannot silently disappear;
- AUDIT may remain NOT_STARTED or later enter BUILDING according to its own track.

Policy: `config/governance/project_state_transitions_v1.json`.
