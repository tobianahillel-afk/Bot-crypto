# Acceptance Criteria - Lot 19

Le Lot 19 est accepte si :

```text
src/crypto_quant_bot/release/__init__.py existe.
src/crypto_quant_bot/release/models.py existe.
src/crypto_quant_bot/release/candidate.py existe.
src/crypto_quant_bot/release/io.py existe.
scripts/run_lot19_release_candidate.py produit les outputs attendus.
scripts/validate_lot19.py valide directement le Lot 19.
scripts/validate_all_until_lot19.py existe.
scripts/run_required_chain_until_lot19.sh existe.
scripts/diagnose_lot19_required_chain_timing.py existe.
scripts/diagnose_exact_chain_until_lot19.py existe.
data/audit/release_candidate_lot19.json existe.
data/audit/release_candidate_checks_lot19.jsonl existe.
reports/lot_19_release_candidate_report.md existe.
reports/lot_19_validation_report.md existe.
reports/lot_19_acceptance_bundle.md existe.
project_name = Crypto Quant Bot V3.1-Ops.
project_mode = EDUCATIONAL_AUDIT_ONLY.
release_candidate_state = READY_FOR_LOCAL_AUDIT_REVIEW.
acceptance_state = ACCEPTANCE_BUNDLE_GENERATED.
packaging_state = NO_ARCHIVE_CREATED.
archive_created = false.
compliance_state = COMPLIANT.
no_trading_state = ENFORCED.
health_state = HEALTHY_FOR_LOCAL_AUDIT.
integrity_state = VERIFIED.
reproducibility_state = REPRODUCIBLE_LOCALLY.
pytest_state = EXPECTED_GREEN.
exact_chain_state = EXPECTED_GREEN.
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
no_trading_compliance_valid = true.
reproducibility_manifest_valid = true.
dataset_catalog_valid = true.
required_artifacts_present = true.
required_reports_present = true.
required_scripts_present = true.
release_checksum est present.
release_checks est non vide.
dataset_catalog.json contient release_candidate_lot19 et release_candidate_checks_lot19 sans doublon.
LOT 19 ORCHESTRATED VALIDATION: PASS.
LOT 19 REQUIRED CHAIN: PASS.
DIAGNOSE LOT19 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT19: PASS.
EXACT_CHAIN_LOT19_DONE.
rc=0.
```

Le Lot 19 reste une release candidate locale defensive, sans archive, sans connectivite externe et sans logique de trading exploitable.

Le Lot 20, ouvert separement, peut seulement consommer ce resultat pour produire une archive locale finale et son checksum SHA256 sans modifier les invariants defensifs.
