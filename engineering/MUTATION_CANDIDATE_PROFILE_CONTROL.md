# Mutation Candidate Profile Control

ENG-09.3-WU13 models the suspended Lot45 mutation campaign without adopting or executing it.

The active P0.6 registry remains `config/governance/mutation_profiles_v1.json`. Lot45 is kept
in the separate `mutation_candidate_profiles_v1.json` registry with lifecycle
`READ_ONLY_QUALIFIED_NOT_ADOPTED`.

Hard gates are explicit:

- `execution_allowed=false`
- `active_registry_adopted=false`
- `production_selector_visible=false`
- `generic_runner_executable=false`

The profile is bound to PR #66 head
`ec2c4ab16f21b23e062b7fca0bb796c8db4a5133`, the mutation workflow blob
`e5a569b79b70e42da7c9ce2cc96b8623a0040f1d`, the mutation summary blob
`26e49b1d1fc450a00ebc346541a69e82059f1119`, and the frozen mutation source head
`c418338da86c49bd4b688d4a64893ee5042adc40`.

The stored evidence is recalculated as 1341 killed / 1665 evaluated = 80.54%, with zero
timeouts and zero suspicious mutants, matching the candidate summary. WU13 does not run
Mutmut again.

The qualification selector may answer whether a candidate path would select Lot45, but its
output always states that the selection is qualification-only and no mutation was executed.

This separation prevents a suspended business candidate from silently becoming an active
engineering control while still allowing deterministic parity review.
