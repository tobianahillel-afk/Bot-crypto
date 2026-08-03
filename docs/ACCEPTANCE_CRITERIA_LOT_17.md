# Acceptance Criteria — Lot 17

Le Lot 17 est accepté si :

```text
src/crypto_quant_bot/health/__init__.py existe.
src/crypto_quant_bot/health/models.py existe.
src/crypto_quant_bot/health/monitor.py existe.
src/crypto_quant_bot/health/io.py existe.
scripts/run_lot17_health_monitor.py produit les outputs attendus.
scripts/validate_lot17.py valide directement le Lot 17.
scripts/validate_all_until_lot17.py existe.
scripts/run_required_chain_until_lot17.sh existe.
scripts/diagnose_lot17_required_chain_timing.py existe.
scripts/diagnose_exact_chain_until_lot17.py existe.
data/audit/health_monitor_lot17.json existe.
data/audit/health_checks_lot17.jsonl existe.
reports/lot_17_health_monitor_report.md existe.
reports/lot_17_validation_report.md existe.
project_name = Crypto Quant Bot V3.1-Ops.
project_mode = EDUCATIONAL_AUDIT_ONLY.
health_state = HEALTHY_FOR_LOCAL_AUDIT.
integrity_state = VERIFIED.
reproducibility_state = REPRODUCIBLE_LOCALLY.
monitoring_mode = LOCAL_STATIC_ONLY.
external_connectivity_allowed = false.
execution_allowed = false.
trade_allowed = false.
dataset_catalog_readable = true.
lot16_manifest_readable = true.
lot16_artifacts_readable = true.
required_artifacts_present = true.
required_reports_present = true.
required_scripts_present = true.
required_diagnostics_present = true.
critical_counts_valid = true.
checksum_references_valid = true.
health_checksum est présent.
artifact_count > 0.
health_checks est non vide.
dataset_catalog.json contient health_monitor_lot17 et health_checks_lot17 sans doublon.
Le calcul dataset_catalog_checksum reste valide après ajout des entrées audit-only du Lot 18.
LOT 17 ORCHESTRATED VALIDATION: PASS.
LOT 17 REQUIRED CHAIN: PASS.
DIAGNOSE LOT17 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT17: PASS.
EXACT_CHAIN_LOT17_DONE.
rc=0.
```

Le Lot 17 reste un moniteur local non exécutable, sans connectivité externe et sans logique de trading exploitable.
