# Mutation Profile Control — ENG-09.3-WU10

WU10 extracts mutation semantics from workflow shell into validated **data**, without executing
mutation testing and without modifying any workflow.

## Initial profile

`P06_DECISION_EVIDENCE` preserves the existing P0.6 behavior:

- selector surface is exactly the legacy workflow path filter;
- mutation target is only
  `src/crypto_quant_bot/contracts/decision_evidence.py`;
- tests are exactly the two P0.6 decision-evidence tests;
- score threshold is 80%;
- numerator is `killed + timeout`;
- denominator is `killed + timeout + suspicious + survived`;
- timeout/suspicious are not required to be zero;
- `mutate_only_covered_lines=true`;
- `max_stack_depth=10`;
- `timeout_multiplier=8.0`;
- `timeout_constant=1.0`;
- the existing do-not-mutate patterns and also-copy dependencies are explicit;
- source binding remains `CURRENT_CHECKOUT`;
- source immutability restores `pyproject.toml` and verifies
  `src/crypto_quant_bot`.

The profile is parity-bound to the current legacy workflow blob
`b1653c0c392e74ea7f50b7b922fd8750fa402bb7` until WU12 intentionally migrates that
trigger surface.

## Safety model

Profile JSON is declarative only. Keys capable of introducing arbitrary command/shell
execution are forbidden recursively. Repository paths are validated as relative and
non-escaping.

Selection is deterministic:

1. each changed path is evaluated against explicit EXACT/GLOB selectors;
2. if one path matches more than one profile, selection fails closed;
3. unrelated paths select no profile;
4. selected profile IDs are returned in sorted order;
5. no mutation command is executed by the selector.

Lot45 is deliberately absent from this registry in WU10. Its profile is deferred to WU13 and
its candidate workflow remains untouched.

Files:

- policy: `config/governance/mutation_profile_policy_v1.json`
- registry: `config/governance/mutation_profiles_v1.json`
- validator: `scripts/governance/validate_mutation_profiles.py`
- selector: `scripts/governance/select_mutation_profile.py`
