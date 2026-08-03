# Acceptance Criteria - Lot 23-quinquies

Le Lot 23-quinquies est accepte si :

```text
scripts/diagnose_lot10_transaction_cost_writer.py ne relance plus run_lot10_transaction_costs.py par defaut.
Un mode explicite --rerun existe si une regeneration Lot 10 est volontairement demandee.
Le diagnostic Lot 10 lit les artefacts existants, execute validate_lot10.py et verifie les counts 5m=36 et 15m=12.
Le diagnostic Lot 10 verifie que dataset_catalog.json ne change pas par defaut.
Le diagnostic Lot 10 ne modifie pas reproducibility_manifest_lot16.json par defaut.
scripts/diagnose_lot16_source_catalog_checksum.py passe apres scripts/diagnose_lot10_transaction_cost_writer.py.
tests/test_lot10_diagnostic_is_non_mutating.py existe.
tests/test_lot23_quinquies_lot16_after_lot10_diagnostic.py existe.
reports/lot_23_quinquies_lot16_after_lot10_diagnostic_report.md existe.
DIAGNOSE LOT10 TRANSACTION COST WRITER: PASS.
DIAGNOSE LOT16 SOURCE CATALOG CHECKSUM: PASS.
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS.
DIAGNOSE EXACT CHAIN LOT23: PASS.
PYTEST_DONE.
EXACT_CHAIN_LOT23_DONE.
rc=0.
L'archive V1 gelee conserve le meme SHA256 avant et apres correction.
Aucun artefact Lot 24 n'est cree.
```
