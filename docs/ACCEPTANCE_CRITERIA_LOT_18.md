# Acceptance Criteria - Lot 18

Le Lot 18 est accepte si :

```text
src/crypto_quant_bot/compliance/__init__.py existe.
src/crypto_quant_bot/compliance/models.py existe.
src/crypto_quant_bot/compliance/no_trading_audit.py existe.
src/crypto_quant_bot/compliance/io.py existe.
scripts/run_lot18_no_trading_compliance.py produit les outputs attendus.
scripts/validate_lot18.py valide directement le Lot 18.
scripts/validate_all_until_lot18.py existe.
scripts/run_required_chain_until_lot18.sh existe.
scripts/diagnose_lot18_required_chain_timing.py existe.
scripts/diagnose_exact_chain_until_lot18.py existe.
data/audit/no_trading_compliance_lot18.json existe.
data/audit/no_trading_compliance_checks_lot18.jsonl existe.
reports/lot_18_no_trading_compliance_report.md existe.
reports/lot_18_validation_report.md existe.
project_name = Crypto Quant Bot V3.1-Ops.
project_mode = EDUCATIONAL_AUDIT_ONLY.
compliance_state = COMPLIANT.
no_trading_state = ENFORCED.
execution_state = DISABLED.
connectivity_state = DISABLED.
artifact_integrity_state = VERIFIED.
health_state = HEALTHY_FOR_LOCAL_AUDIT.
reproducibility_state = REPRODUCIBLE_LOCALLY.
live_execution = DISABLED.
leverage = FORBIDDEN.
trading_decision = WAIT.
system_decision = BLOCK_TRADING.
final_decision = WAIT.
final_system_decision = BLOCK_TRADING.
trade_allowed = false.
execution_allowed = false.
external_connectivity_allowed = false.
exchange_connector_present = false.
order_router_present = false.
api_key_present = false.
websocket_present = false.
paper_trading_present = false.
strategy_present = false.
forbidden_semantics_present = false.
critical_counts_valid = true.
health_monitor_valid = true.
reproducibility_manifest_valid = true.
dataset_catalog_valid = true.
required_artifacts_present = true.
required_reports_present = true.
required_scripts_present = true.
compliance_checksum est present.
compliance_checks est non vide.
dataset_catalog.json contient no_trading_compliance_lot18 et no_trading_compliance_checks_lot18 sans doublon.
LOT 18 ORCHESTRATED VALIDATION: PASS.
LOT 18 REQUIRED CHAIN: PASS.
DIAGNOSE LOT18 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT18: PASS.
EXACT_CHAIN_LOT18_DONE.
rc=0.
```

Le Lot 18 reste une certification locale non executable, sans connectivite externe et sans logique de trading exploitable.

Le Lot 19 reutilise ensuite ces artefacts comme contexte documentaire local, sans modifier l'etat `COMPLIANT / ENFORCED` attendu du Lot 18.
