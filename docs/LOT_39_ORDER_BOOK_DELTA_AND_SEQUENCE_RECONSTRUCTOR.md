# Lot 39 — Order Book Delta & Sequence Reconstructor

## Status and boundary

- Owner: `MicrostructureDomain`
- Runtime: `OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY`
- Entry gate: `GO_LOT39_IMPLEMENTATION_ENTRY`
- Gate merge base: `938a0e9cf92ef5bbda02045486afbd9a32dc67ec`
- Lot 40: `PLANNED_LOCKED`
- Network/live credentials/trading/execution: forbidden

Lot 39 reconstructs an offline L2 book from the certified Lot 38 `OrderBookSnapshotV1` plus a strictly ordered sequence of `OrderBookDeltaV1` records. It never authorizes trading and never publishes an ambiguous book.

## Canonical contracts

Inputs:

- `RunContextV1`
- `LineageEnvelopeV1`
- `OrderBookSnapshotV1`
- `OrderBookDeltaV1`

Outputs:

- `OrderBookDeltaSequenceReconstructorStateV1`
- `OrderBookDeltaSequenceReconstructorAuditV1`
- `ReconstructedOrderBookV1`
- `SequenceGapEventV1`

The canonical roadmap-facing modules are:

- `src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor.py`
- `src/crypto_quant_bot/microstructure/order_book_delta_and_sequence_reconstructor_models.py`

They are thin public facades over the focused implementation modules and contain no duplicated business logic.

## Delta semantics

`OrderBookDeltaV1` uses exact decimal text at the schema boundary and `Decimal` internally. A delta carries absolute quantity updates at a price level:

- quantity `> 0`: insert or replace that price level quantity;
- quantity `== 0`: delete an existing price level;
- quantity `< 0`: rejected by the contract boundary;
- duplicate prices inside one side of one delta: rejected;
- an empty delta: rejected.

The reference sequence is fixture-only and non-decisional.

## Sequence policy

For current sequence `s`, a delta is applicable only if:

- `prev_sequence == s`; and
- `sequence_id == s + 1`.

The engine also enforces non-decreasing event time and exact source/venue/instrument/market identity. It never silently reorders or skips deltas.

## Fail-closed outcomes

A healthy reconstruction has:

- `validation_state=VALIDATED_OFFLINE_DELTA_SEQUENCE_RECONSTRUCTION_ONLY`;
- `synchronization_state=SYNCED`;
- non-null `ReconstructedOrderBookV1`;
- null `SequenceGapEventV1`.

Any ambiguity requiring a full snapshot resynchronization has:

- `validation_state=BLOCKED_RESYNC_REQUIRED`;
- `synchronization_state=RESYNC_REQUIRED`;
- null reconstructed book;
- non-null `SequenceGapEventV1` with deterministic reason codes.

Resync is required for at least:

- sequence gap;
- duplicate/reordered sequence;
- event-time reorder;
- deletion of a missing price level;
- empty side after delta;
- crossed or locked reconstructed book;
- expected-book checksum mismatch.

The engine detects only the integrity conditions necessary to fail closed. It does not implement the broader Lot 40 integrity/desynchronization analytics engine.

## Deterministic reference replay

The certified Lot 38 snapshot starts at sequence `1001`. The reference fixture applies `1002` then `1003`. The second delta deletes bid `50024.8` with quantity zero.

Expected final book:

- bids: `50024.9@0.9`, `50024.7@0.5`;
- asks: `50025.1@0.65`, `50025.2@1.1`, `50025.3@0.4`;
- final sequence: `1003`;
- deltas applied: `2`;
- levels deleted: `1`;
- levels upserted: `4`;
- sequence gap events: `0`.

All output checksums are canonical JSON SHA-256 values. Run1/run2 with the same source head must be byte-equivalent.

## Persistence

State, audit and the mutually exclusive outcome surface are written atomically:

- healthy: state + audit + reconstructed book, no gap artifact;
- blocked: state + audit + gap artifact, no reconstructed-book artifact.

No partial or stale opposite outcome is accepted.

## Safety invariants

The Lot 39 safety object remains exactly fail-closed:

- `analysis_only=true`
- `used_for_decision=false`
- `external_connectivity_allowed=false`
- `network_ingestion_allowed=false`
- `real_credentials_allowed=false`
- `market_event_publication_allowed=false`
- `raw_data_mutation_allowed=false`
- `signal_generation_allowed=false`
- `risk_approval_allowed=false`
- `order_routing_allowed=false`
- `trade_allowed=false`
- `execution_allowed=false`
- `approved_size=0`

A successful reconstruction is not a forecast, signal, risk approval or order permission.

## Quality gates

- target line coverage: `>=95%`
- target branch coverage: `>=90%`
- mutation score: `>=80%`
- anti-flake repetitions: `>=3`
- full repository non-regression: required
- Ruff, mypy, architecture, roadmap, traceability, no-silent-coercion, security and dependency audit: required

## Promotion

Lot 40 remains locked until Lot 39 implementation is green, frozen, merged and independently audited post-merge. A separate Lot 40 entry gate is mandatory.
