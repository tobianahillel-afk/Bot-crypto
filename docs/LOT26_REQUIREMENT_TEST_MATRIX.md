# Lot 26 — Requirement to Test Matrix

| Requirement | Test suite | Mandatory evidence |
|---|---|---|
| AC-26-01 closed bars | contract, negative | open 5m/15m rejected |
| AC-26-02 temporal eligibility | math, anti-lookahead | boundary equality and future rejection |
| AC-26-03 as-of backward join | unit, property, integration | oracle join results |
| AC-26-04 continuous flow | integration, replay | three 5m states may share one 15m |
| AC-26-05 no automatic veto | unit, regression | divergent contexts remain descriptive |
| AC-26-06 exact mathematics | math, property, mutation | formulas and thresholds |
| AC-26-07 missing data | negative, property | UNKNOWN propagation |
| AC-26-08 determinism | replay, regression | identical checksums |
| AC-26-09 schemas | contract | all schemas pass and extras fail |
| AC-26-10 anti-lookahead | failure injection | open/future/revision/timezone cases |
| AC-26-11 properties | property-based | bounds, symmetry, identity, permutation |
| AC-26-12 quality gates | CI | coverage and mutation artifacts |
| AC-26-13 forbidden capabilities | security/static | no BUY/SELL/order/size |
| AC-26-14 audit evidence | audit/replay | manifest, lineage, checksums |
| AC-26-15 Game Theory boundary | architecture | no microstructure participant inference |

Each implemented test must declare `requirement_id`, expected result, tolerance and failure
consequence in its docstring or metadata.
