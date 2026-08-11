# Lot 43 — Acceptance Criteria

Lot 43 is accepted only on an exact frozen source head that satisfies every applicable criterion below.

## Gate and scope

1. Implementation descends from merged Lot 43 gate `ed8845e0e56151348fe57c0e9bceaf4646ea49aa`.
2. Gate checksum is exactly `4034c86061234a627dafde6122439c3b697fb2d53a1b95ba4e58f77a71089e6d`.
3. Owner is `MicrostructureDomain`.
4. Runtime remains `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`.
5. Lot 44 remains `PLANNED_LOCKED` and physically absent.
6. No external connectivity or network ingestion exists.
7. No live exchange data or real credentials are consumed.
8. No participant intent is asserted as fact.
9. No forecast, signal, risk approval, routing, trading or execution capability is introduced.
10. Safety remains `trade_allowed=false`, `execution_allowed=false`, `approved_size=0`.

## Predecessor and lineage

11. Lot 42 post-merge release remains `0.42.0` with `GO_LOT42_POST_MERGE`.
12. Lot 42 state checksum is exact and frozen.
13. Lot 42 audit checksum is exact and frozen.
14. Lot 42 zone-set checksum is exact and frozen.
15. Lot 42 state/zone-set linkage is exact.
16. Lot 42 participant-intent boundary remains false/not-inferred.
17. Lot 39 final reconstructed book remains exact.
18. Lot 39 delta fixture checksum remains exact.
19. Lot 38 snapshot checksum remains exact.
20. Reconstructed Lot 43 observation history ends at certified sequence `1003` and matches Lot 42 current identity/mid.
21. Input freshness is explicitly checked against injected decision time.
22. Every output includes versioned lineage and config checksum.

## Numerical and temporal contracts

23. Sensitive calculations use `Decimal` with precision 50.
24. No float is used for price, quantity, ratio, bps or money-like values.
25. Timestamps are UTC `Z` values.
26. Availability cannot exceed decision time.
27. Replenishment time uses receive-time differences in integer microseconds.
28. Replenishment elapsed time must be strictly positive when present.
29. Missing replenishment time is `null`, never zero fallback.
30. Horizons are positive, unique and strictly increasing.
31. Ratio thresholds lie in `[0,1]`.
32. Quiet/stressed volatility thresholds are non-negative and strictly ordered.
33. Adjacent distance and mid-shift thresholds are positive.
34. Negative or non-finite quantities/ratios/bps fail closed.

## Depletion detection

35. Depletion compares exact price quantities across consecutive certified observations.
36. Missing later exact price is treated as observed quantity zero, not missing data.
37. Only positive quantity decreases can become depletion events.
38. Event requires both minimum depleted quantity and minimum depletion ratio.
39. Sub-threshold quantity decrease is not promoted.
40. Depletion ratio equals depleted quantity divided by prior quantity.
41. Depletion event sequence is the later observation sequence.
42. Depletion event available time is the later observation receive time.
43. Identity changes between observations fail closed.
44. Non-increasing sequence history fails closed.

## Replenishment classification

45. Same-price replenishment uses future quantity gain relative to post-depletion baseline at exact depleted price.
46. Adjacent replenishment uses only positive future gains over the same post-depletion baseline.
47. Adjacent match excludes exact depleted price.
48. Adjacent match uses versioned bps distance.
49. Same-price evidence has deterministic precedence over adjacent evidence at the same observation.
50. Quantity recovery qualifies only at or above configured minimum recovery fraction.
51. Recovered fraction is capped at 1 and is not a probability.
52. Mid shift is evaluated only when no qualifying same/adjacent quantity recovery exists at that observation.
53. BID mid shift is downward; ASK mid shift is upward.
54. Mid shift does not fabricate replenished quantity.
55. Mid-shift recovered fraction remains zero.
56. Observations after the maximum horizon cannot count as replenishment.
57. First qualifying future outcome is deterministic.
58. No future observation means no replenishment evidence.
59. Participant intent on every event remains `NOT_INFERRED`.

## Horizon and resilience

60. Every configured horizon is evaluated independently.
61. Quantity recovery within horizon counts as recovered.
62. Mid shift within horizon counts separately as shifted.
63. Closed horizon without qualifying outcome counts as expired.
64. Open horizon without qualifying outcome counts as pending.
65. Mean recovered fraction counts non-recovered events as zero.
66. Mean recovered fraction is null only when there are no depletion events.
67. Mean replenishment time uses quantity-recovered events only.
68. Mean replenishment time is null when no quantity recovery exists.
69. `NO_EVENTS` is emitted only for a side with zero depletion events.
70. `RESILIENT` requires all events quantity-recovered and mean recovery at/above configured minimum.
71. `FRAGILE` requires all events expired with no recovery or shift.
72. `SHIFTED` represents resolved mid-shift outcomes without quantity recovery/pending.
73. `PENDING` represents only-open unresolved evidence.
74. All other mixtures are `PARTIAL`.
75. Resilience labels are descriptive, not probabilities/signals.

## Volatility conditioning

76. Method is exactly `OBSERVED_BOOK_MID_MAX_ABS_MOVE_BPS`.
77. Measurement uses only consecutive certified observation mids.
78. Each move is absolute mid change divided by prior mid times 10000.
79. Overall measure is maximum observed consecutive move.
80. `QUIET` applies at or below quiet threshold.
81. `STRESSED` applies at or above stressed threshold.
82. Intermediate values are `NORMAL`.
83. The local bucket has no market-regime, strategy or execution authority.

## Reference fixture

84. Reference history is `[1001,1002,1003]`.
85. Reference current sequence is `1003`.
86. Reference current mid is `50025`.
87. Exactly one significant depletion is detected.
88. Reference depletion side is BID.
89. Reference depletion price is `50024.8`.
90. Reference prior quantity is `1.25`.
91. Reference post quantity is `0`.
92. Reference depleted quantity is `1.25`.
93. Reference depletion ratio is `1`.
94. Reference depletion sequence is `1003`.
95. Reference has zero same-price replenishments.
96. Reference has zero adjacent-price replenishments.
97. Reference has zero mid-shift outcomes.
98. Reference maximum-window event is expired without replenishment.
99. Reference volatility measure is `0` bps.
100. Reference volatility bucket is `QUIET`.
101. BID 10ms slice is `FRAGILE`.
102. BID 25ms slice is `FRAGILE`.
103. ASK 10ms slice is `NO_EVENTS`.
104. ASK 25ms slice is `NO_EVENTS`.

## Determinism, persistence and auditability

105. State, audit and resilience state have canonical checksums.
106. Event and resilience-slice records have canonical checksums.
107. Run1/run2 persisted outputs are byte-identical.
108. Atomic persistence is used.
109. Output code commit equals exact frozen source head.
110. Reason codes are stable and closed by validation.
111. State/audit/resilience linkage is exact.
112. Metrics match published event/slice counts.
113. No wall-clock timestamp enters deterministic output.
114. Replay divergence blocks certification.

## Negative and synthetic coverage

115. Synthetic same-price replenishment is classified correctly.
116. Synthetic adjacent-price replenishment is classified correctly.
117. Synthetic mid-shift outcome is classified correctly.
118. Synthetic recovery after horizon expiry is rejected.
119. Synthetic partial recovery produces bounded recovered fraction.
120. Synthetic over-recovery caps recovered fraction at 1 without truncating observed replenished quantity.
121. Synthetic ASK depletion uses correct directional mid-shift sign.
122. Pending-window case is covered.
123. Invalid config shape/version fails closed.
124. Invalid gate/lifecycle/checksum fails closed.
125. Stale predecessor evidence fails closed.
126. Malformed observation/history fails closed.

## Quality gates

127. Targeted Lot 43 tests all pass.
128. Critical line coverage is at least 95%.
129. Critical branch coverage is at least 90%.
130. Critical mutation score is at least 80%.
131. Mutation has zero timeout mutants.
132. Mutation has zero suspicious mutants.
133. Ruff passes.
134. MyPy passes.
135. Closed JSON schemas validate.
136. Domain architecture and ownership pass.
137. Roadmap semantic audit passes.
138. Decision traceability passes.
139. Silent numeric coercion gate passes.
140. Engineering deviation gate passes.
141. No-connectivity validator passes.
142. Bandit passes.
143. Dependency audit passes.
144. Full repository regression passes.
145. Three targeted anti-flake repetitions pass.
146. Institutional quality workflow remains green.

## Promotion

147. Source is frozen only after all exact-head source gates are green.
148. Frozen evidence is committed separately from source changes.
149. Implementation PR merges only from the exact fully green final head with no blocking review/thread.
150. Lot 43 receives an independent post-merge audit after merge.
151. Lot 44 remains locked until a merged `GO_LOT43_POST_MERGE` verdict exists.
