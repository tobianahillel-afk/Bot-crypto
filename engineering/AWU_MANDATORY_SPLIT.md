# Mandatory Agent Work Unit Splitting V1

An AWU is executable only if its cognitive score and structural estimate stay inside the
bounded-work budget.

Mandatory split is triggered when any configured limit is exceeded. The current baseline
uses score >10, >15 touched files, >800 executable LOC, or more than one business domain,
public behavior, contract family, independent algorithm, state machine, trust boundary,
new dependency, or cross-domain interface.

The reason codes are calculated, sorted and must exactly match `split_reasons`.
A split-required AWU is non-executable: only `PLANNED` or `BLOCKED` is legal.

Later ENG-02.7 will compare declared scope/size to the actual Git diff; ENG-02.4 establishes
the planning-time fail-closed rule.
