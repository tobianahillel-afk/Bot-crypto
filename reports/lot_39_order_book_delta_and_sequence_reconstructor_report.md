# Lot 39 — Order Book Delta & Sequence Reconstructor Report

## Scope

Implementation report for the offline-only Lot 39 sequence reconstructor authorized by gate merge `938a0e9cf92ef5bbda02045486afbd9a32dc67ec`.

No network access, live exchange data, credentials, signal generation, risk approval, order routing, trading or execution is implemented.

## Canonical behavior

The engine starts from the certified Lot 38 `OrderBookSnapshotV1` at sequence `1001` and applies the fixture deltas `1002` and `1003` only when the sequence chain is exact. Quantity zero deletes an existing level. Negative quantity is rejected at the model boundary.

Healthy reference result:

- synchronization: `SYNCED`
- final sequence: `1003`
- applied deltas: `2`
- deleted levels: `1`
- upserted levels: `4`
- sequence gap events: `0`
- bids: `50024.9@0.9`, `50024.7@0.5`
- asks: `50025.1@0.65`, `50025.2@1.1`, `50025.3@0.4`

Fail-closed ambiguity result:

- validation: `BLOCKED_RESYNC_REQUIRED`
- synchronization: `RESYNC_REQUIRED`
- reconstructed book: absent
- `SequenceGapEventV1`: present with deterministic reason codes

## Failure cases exercised

- sequence gap;
- duplicate/reordered sequence;
- reordered event time;
- missing-level deletion;
- empty book side after delete;
- crossed or locked post-delta book;
- expected-book checksum mismatch;
- incompatible identity;
- stale/future input;
- negative quantity;
- empty delta sequence.

## Determinism and persistence

Run1/run2 must produce byte-equivalent state/audit/book artifacts on the same source head. Persistence writes exactly one outcome surface: book for `SYNCED`, gap event for `RESYNC_REQUIRED`.

## Quality gates

The final certification section is intentionally pending until one exact implementation source head is frozen. Required evidence:

- Ruff: pending exact source head
- mypy: pending exact source head
- targeted tests: pending exact source head
- line coverage `>=95%`: pending exact source head
- branch coverage `>=90%`: pending exact source head
- mutation `>=80%`: pending exact source head
- full non-regression: pending exact source head
- anti-flake x3: pending exact source head
- security/dependency audit: pending exact source head
- architecture/roadmap/traceability: pending exact source head

## Safety

`trade_allowed=false`, `execution_allowed=false`, `approved_size=0`, `used_for_decision=false`. `LOT40_REMAINS_LOCKED` is mandatory evidence.

## Current conclusion

`IMPLEMENTATION_CANDIDATE_EVIDENCE_PENDING_EXACT_SOURCE_HEAD`

This report must be replaced with exact CI run IDs, artifact digests, checksums and the frozen source head before the implementation PR can be merged.
