# Acceptance Criteria — Lot 41 Spread, Depth & Imbalance Engine

Lot 41 is accepted only when every criterion below passes on the exact certified source head and the frozen evidence is generated from that same source head.

## Contract and lineage

1. Entry-gate checksum is exact and its merge `75822f8ea7c6f67f73649d2f43be6efba840ab67` is an ancestor.
2. Canonical registry Lot 41 identity, owner, runtime, inputs and outputs remain exact.
3. Lot 40 source/evidence/post-merge lineage and all four certified checksums are exact.
4. Reconstructed order-book checksum and sequence are exact.
5. Source, venue, instrument, market type, sequence and causal times agree across book and integrity state.
6. `BookHealthVetoV1` consequence is `NONE`, veto is inactive and Lot 40 health is `HEALTHY` with score `100` for the reference path.
7. Any stale, incompatible, tampered, crossed/locked, non-SYNCED or ambiguous dependency fails closed.

## Mathematics

8. Absolute spread equals `best_ask - best_bid`.
9. Mid equals `(best_ask + best_bid) / 2`.
10. Spread bps equals `spread / mid * 10000` using configured decimal precision.
11. Microprice uses opposite-side queue weighting exactly as specified in the implementation contract.
12. Depth bands are exactly the versioned config values and are strictly positive/increasing.
13. Bid/ask depth sums only observed levels whose mid-distance is inside the band.
14. Cumulative depth is monotonic and equals the exact prefix sum of observed quantities.
15. Symmetric imbalance is in `[-1, 1]` when defined.
16. Zero imbalance denominator yields `null` plus `UNDEFINED_ZERO_DENOMINATOR`; no silent zero/fallback.
17. Price-unit scaling preserves spread bps and imbalance while scaling price-valued features by the same factor.
18. No feature uses data beyond the certified event/receive/decision boundary.
19. No depth is extrapolated beyond observed levels; every band is labeled `OBSERVED_LEVELS_ONLY`.

## Determinism and persistence

20. Run1/run2 with identical input/config/code commit produce byte-identical state, audit and feature artifacts.
21. State, feature and audit checksums are canonical and tamper-evident.
22. Atomic persistence leaves no partial valid state.
23. Round-trip serialization preserves every value and checksum.
24. Output schemas are closed on critical nested objects and reject unknown safety/identity fields.

## Safety and scope

25. Runtime is exactly `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`.
26. External connectivity, live exchange data, network ingestion and real credentials are rejected/absent.
27. `analysis_only=true`, `used_for_decision=false`, `trade_allowed=false`, `execution_allowed=false`, `approved_size=0`.
28. No participant intent fact, forecast, signal, risk approval, routing, trade or execution output exists.
29. Lot 42 `Liquidity Zones, Walls & Voids Engine` remains absent and `PLANNED_LOCKED`.

## Tests and quality

30. Healthy coherent reference book passes all reference-value assertions.
31. Crossed/locked and unilateral/empty books cannot silently publish valid features.
32. Numeric JSON price/quantity coercion is rejected; only finite positive decimal strings are accepted.
33. Schema mismatch and unsupported config versions are rejected.
34. Every configured depth band is tested, including a zero-denominator synthetic case.
35. Previous-lot/gate integration tests pass.
36. Targeted critical coverage: lines `>=95%`, branches `>=90%`.
37. Mutation score `>=80%`; certification requires timeout `0` and suspicious `0`.
38. Full repository regression passes.
39. Anti-flake Lot 41 tests pass three consecutive repetitions.
40. Ruff, mypy, architecture, roadmap semantics, traceability, no-silent-coercion and engineering-deviation gates pass.
41. Bandit and dependency vulnerability scan pass.
42. Frozen evidence validator passes on the exact source head without modifying certified source.
43. Final PR head has all applicable workflows green and no unresolved review thread.
44. Independent post-merge audit is required before any Lot 42 gate may be created.
