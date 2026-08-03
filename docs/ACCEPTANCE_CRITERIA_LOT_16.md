# Acceptance Criteria — Lot 16

Le Lot 16 est accepté si :

```text
src/crypto_quant_bot/lineage/__init__.py existe.
src/crypto_quant_bot/lineage/models.py existe.
src/crypto_quant_bot/lineage/manifest.py existe.
src/crypto_quant_bot/lineage/io.py existe.
scripts/run_lot16_reproducibility_manifest.py produit les outputs attendus.
scripts/validate_lot16.py valide directement le Lot 16.
data/audit/reproducibility_manifest_lot16.json existe.
data/audit/reproducibility_artifacts_lot16.jsonl existe.
reports/lot_16_reproducibility_report.md existe.
manifest_version est présent.
project_name = Crypto Quant Bot V3.1-Ops.
project_mode = EDUCATIONAL_AUDIT_ONLY.
reproducibility_state = REPRODUCIBLE_LOCALLY.
lineage_state = RECORDED.
external_connectivity_allowed = false.
execution_allowed = false.
trade_allowed = false.
source_catalog_checksum est présent.
manifest_checksum est présent.
artifact_count correspond au nombre de lignes JSONL.
Les artifacts requis existent, avec checksum_sha256, size_bytes, line_count et path.
critical_counts contient 36/12/48 pour Lot 12, Lot 13, Lot 14 et Lot 15.
replay_commands contient la chaîne exacte jusqu'au Lot 16.
validation_commands contient validate_lot16.py.
dataset_catalog.json contient reproducibility_manifest_lot16 et reproducibility_artifacts_lot16 sans doublon.
Le calcul source_catalog_checksum reste valide même après ajout des entrées audit-only du Lot 17.
LOT 16 ORCHESTRATED VALIDATION: PASS.
LOT 16 REQUIRED CHAIN: PASS.
DIAGNOSE LOT16 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT16: PASS.
EXACT_CHAIN_LOT16_DONE.
rc=0.
```

Le Lot 16 reste un manifeste local de reproductibilité, non exécutable et sans connectivité externe.
