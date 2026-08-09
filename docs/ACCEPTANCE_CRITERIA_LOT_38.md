# Acceptance Criteria — Lot 38 Order Book L2 Snapshot Engine

Lot 38 is accepted only if all criteria below pass on the exact implementation source head and are preserved by frozen evidence before merge.

## Contract and lineage

- The implementation starts from gate merge `2120aab94d54fde6e9ad36022499b1f9f284c3f6`.
- The gate checksum is exactly `29fe4a5fd14b3bce95e3016fce67e10f94edcca1c2aad60c9fda382f3eb9d6a0`.
- Lot 37 state, audit, contract-registry and capability-matrix evidence remains checksum-identical.
- The Lot 37 L2 fixture remains byte-identical, noncanonical and unused for decisions.
- `OrderBookSnapshotRawV1` is defined explicitly; the fixture is mapped into it rather than reclassified.

## Numeric normalization

- Prices and quantities use `Decimal`, never binary float arithmetic.
- Prices are finite and strictly positive.
- Quantities are finite and non-negative; negative quantities are rejected.
- Identical price levels are aggregated exactly before depth capping.
- Bids are strictly descending after normalization.
- Asks are strictly ascending after normalization.
- Input level ordering does not change the canonical snapshot/checksum.

## Book validity

- A crossed book (`best_bid > best_ask`) is rejected fail-closed.
- A locked book (`best_bid == best_ask`) is accepted only with explicit `venue_state=LOCKED`.
- `venue_state=LOCKED` is rejected when the normalized book is actually open.
- Empty bid or ask sides are rejected.
- Source, normalized and published depth counters are internally consistent.
- Published depth never exceeds configured depth or normalized depth.

## Sequence and determinism

- A deterministic sequence anchor binds source/venue/instrument/sequence/event/receive identity.
- Changing the sequence id changes the sequence anchor and snapshot checksum.
- Lot 38 performs no delta application, sequence reconstruction, gap repair or resynchronization.
- Two runs with the same code commit/config/input produce byte-semantically identical state and audit artifacts.

## Artifacts

The implementation persists atomically:

- `OrderBookL2SnapshotEngineStateV1`;
- `OrderBookL2SnapshotEngineAuditV1`;
- `OrderBookSnapshotV1`;
- `BookHealthStateV1`.

Each checksum is recomputed independently. State/audit/snapshot/health links must agree exactly.

## Reference fixture expectations

For the certified Lot 37 L2 fixture with `published_depth_limit=2`:

- one record processed;
- source levels = 6;
- normalized levels = 6;
- duplicate levels aggregated = 0;
- published levels = 4;
- source bid depth = 3;
- source ask depth = 3;
- published bid depth = 2;
- published ask depth = 2;
- venue state = `OPEN`;
- health status = `HEALTHY`;
- `crossed=false`;
- validation failures = 0;
- latency remains explicitly unmeasured, not coerced to zero.

## Safety and negative capability tests

The implementation must prove:

- no network-capable import in Lot 38 runtime paths;
- no real credentials;
- no market-event publication;
- no raw-data mutation;
- no signal generation;
- no risk approval;
- no order routing;
- no trading or execution;
- `approved_size=0`;
- Lot 39 remains `PLANNED_LOCKED`.

## Engineering and quality gates

- Ruff PASS.
- mypy PASS.
- architecture/ownership/roadmap/traceability/numeric gates PASS.
- engineering inventory has no unregistered Lot 38 finding.
- Bandit PASS.
- dependency audit PASS.
- full regression PASS.
- line coverage ≥95%.
- branch coverage ≥90%.
- mutation score ≥80% with no threshold reduction or inappropriate exclusion.
- targeted anti-flake repetitions ≥3 PASS.

## Promotion

CI green alone is insufficient. Before merge, evidence must be frozen against the exact green source head and revalidated without production-code drift. After merge, an independent Lot 38 post-merge audit is mandatory before any Lot 39 gate may be created.
