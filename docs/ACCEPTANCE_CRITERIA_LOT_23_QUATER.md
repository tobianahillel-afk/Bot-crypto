# Acceptance Criteria Lot 23-quater

Lot 23-quater exists because `scripts/diagnose_exact_chain_return_shell.py` could still fail on `source_catalog_checksum mismatch` during `validate_lot16.py` even though the wider Lot 23 exact chain was green.

The corrective objective is a single source of truth for the Lot 16 historical checksum:

- `src/crypto_quant_bot/lineage/manifest.py` exposes one canonical function for the Lot 16 checksum scope.
- `scripts/run_lot16_reproducibility_manifest.py` uses that canonical function.
- `scripts/validate_lot16.py` uses that same canonical function.
- the dedicated diagnostic `scripts/diagnose_lot16_source_catalog_checksum.py` recalculates the checksum with that same canonical function.
- the Lot 16 checksum tests use that same canonical function.

The canonical Lot 16 checksum scope is:

- historical dataset catalog source entries up to Lot 15 only;
- Lot 16 self-produced entries excluded;
- Lot 17, Lot 18, Lot 19, Lot 20, Lot 21, Lot 22, Lot 23 and future entries excluded;
- duplicate `dataset_id` entries normalized deterministically with the same last-write-wins rule as the dataset catalog writer;
- runtime-only fields such as generated ids and timestamps excluded from the hashed payload.

Acceptance requires:

- `python scripts/run_lot16_reproducibility_manifest.py` prints `LOT 16 REPRODUCIBILITY MANIFEST: PASS`;
- `python scripts/validate_lot16.py` prints `LOT 16 VALIDATION: PASS`;
- `python scripts/diagnose_lot16_source_catalog_checksum.py` prints `DIAGNOSE LOT16 SOURCE CATALOG CHECKSUM: PASS`;
- `python scripts/diagnose_exact_chain_return_shell.py` prints `DIAGNOSE EXACT CHAIN RETURN SHELL: PASS`;
- `python scripts/diagnose_exact_chain_until_lot23.py` prints `DIAGNOSE EXACT CHAIN LOT23: PASS`;
- `python -m pytest -q` returns naturally;
- the frozen V1 archive SHA remains unchanged;
- no Lot 24 artifact is created;
- `run_lot20_v1_closure.py` is not called by Lot 21, Lot 22 or Lot 23 chains.
