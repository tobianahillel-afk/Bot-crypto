# Lot 26 — Requirement to Test Matrix

| Requirement | Test suites | Mandatory evidence |
|---|---|---|
| AC-26-01 closed confirmed bars | contract, negative | open 5m/15m rejected as confirmed inputs |
| AC-26-02 temporal eligibility | math, anti-lookahead | boundary equality and future rejection |
| AC-26-03 ASOF_BACKWARD | unit, property, integration | exact oracle and tie-break results |
| AC-26-04 initial scale profile | contract, configuration | only 5m→15m enabled |
| AC-26-05 extensibility | property, regression | disabled scales do not change output/checksum |
| AC-26-06 continuous flow | integration, replay | three 5m states may share one 15m |
| AC-26-07 no automatic veto | unit, regression | divergent contexts remain descriptive |
| AC-26-08 no naive voting | architecture, negative | no majority-vote code/config/output |
| AC-26-09 temporal dimensions | contract, static | resolution/lookback/horizon/clock/TTL/holding distinct |
| AC-26-10 exact mathematics | math, property, mutation | formulas, weights, thresholds, tolerances |
| AC-26-11 missing data | negative, property | UNKNOWN propagation, no silent zero |
| AC-26-12 determinism | replay, regression | identical outputs/reason codes/checksums |
| AC-26-13 closed schemas | contract | all schemas pass and extra fields fail |
| AC-26-14 anti-lookahead | failure injection | open/future/revision/timezone/order/gap cases |
| AC-26-15 mathematical properties | property-based | bounds, identity, symmetry, permutation, invariance |
| AC-26-16 decision clock | contract, architecture | only CLOSED_LOCAL_BAR enabled |
| AC-26-17 forecast boundary | static, schema, negative | no forecast/probability/expected-return output |
| AC-26-18 Game Theory boundary | architecture, static | no participant/payoff/zone inference in Lot 26 |
| AC-26-19 protective-order boundary | architecture, static | no stop/TP/trailing/bracket/OCO implementation |
| AC-26-20 quality gates | CI | line/branch coverage and mutation artifacts |
| AC-26-21 forbidden capabilities | security/static | no BUY/SELL/order/size/paper/live fields |
| AC-26-22 audit evidence | audit/replay | manifest, lineage, config/registry checksums |
| AC-26-23 historical immutability | git/static | no Lots 0–25 or src changes |

## Required test metadata

Each implemented test declares:

```text
requirement_id
input_contract_version
expected_result
numeric_tolerance si applicable
failure_consequence
anti_lookahead_relevance
```

## Mandatory suites for implementation

```text
unit
mathematical_oracle
property_based
schema_contract
integration_lot25_to_lot26
anti_lookahead
negative_and_fault_injection
replay_determinism
non_regression
architecture_boundary
security_and_forbidden_capability
performance
mutation
```

## Promotion rule

No requirement can be covered only by a documentation assertion. Each requirement must map to at least one executable test and one auditable evidence artifact before `GO_LOT26`.
