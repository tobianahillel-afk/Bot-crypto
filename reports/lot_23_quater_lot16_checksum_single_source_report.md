# Lot 23-quater — Lot16 Source Catalog Checksum Single Source of Truth

## Why this lot exists

Lot 23-quater exists because the Lot 24 preparation could still fail in `scripts/diagnose_exact_chain_return_shell.py` with `source_catalog_checksum mismatch` during `validate_lot16.py`.

## Root cause addressed

The Lot 16 checksum was still vulnerable to differences between the raw `dataset_catalog.json` state seen by `run_lot16_reproducibility_manifest.py` and the canonicalized catalog state written back by later `DatasetCatalog.upsert(...)` operations.

Two instability vectors mattered:

- duplicate `dataset_id` rows could be present in the raw catalog before a save/upsert pass;
- runtime-only fields such as generated ids and timestamps could vary while not representing a true change to the historical source scope.

## Corrective rule

The Lot 16 checksum is now computed by one canonical function only:

- `compute_lot16_source_catalog_checksum(...)`

That function:

- accepts the catalog payload as object input;
- extracts supported catalog entries deterministically;
- deduplicates by `dataset_id` with the same last-write-wins rule as the catalog writer;
- filters the historical scope to Lots 0 through 15 only;
- excludes Lot 16 self-produced records and all later lots;
- keeps only stable fields;
- sorts canonically;
- returns a deterministic SHA256.

## Result

`run_lot16_reproducibility_manifest.py`, `validate_lot16.py`, the dedicated diagnostic, and the tests now rely on the same checksum logic. The Lot 16 manifest records the scope string and entry count used for the checksum, the frozen V1 archive remains unchanged, and Lot 24 has not been started.
