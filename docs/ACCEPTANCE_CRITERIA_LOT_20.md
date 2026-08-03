# Acceptance Criteria - Lot 20

Le Lot 20 est accepte si :

```text
src/crypto_quant_bot/closure/__init__.py existe.
src/crypto_quant_bot/closure/models.py existe.
src/crypto_quant_bot/closure/archive.py existe.
src/crypto_quant_bot/closure/io.py existe.
scripts/run_lot20_v1_closure.py produit les outputs attendus.
scripts/validate_lot20.py valide directement le Lot 20.
scripts/validate_all_until_lot20.py existe.
scripts/run_required_chain_until_lot20.sh existe.
scripts/diagnose_lot20_required_chain_timing.py existe.
scripts/diagnose_exact_chain_until_lot20.py existe.
data/audit/v1_closure_lot20.json existe.
data/audit/v1_closure_checks_lot20.jsonl existe.
reports/lot_20_v1_closure_report.md existe.
reports/lot_20_archive_manifest.md existe.
reports/lot_20_validation_report.md existe.
dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz existe.
dist/crypto_quant_bot_v1_defensive_audit_lot_20.sha256 existe.
project_name = Crypto Quant Bot V3.1-Ops.
project_mode = EDUCATIONAL_AUDIT_ONLY.
closure_state = V1_DEFENSIVE_AUDIT_CLOSED.
archive_state = ARCHIVE_CREATED.
archive_created = true.
release_candidate_state = READY_FOR_LOCAL_AUDIT_REVIEW.
acceptance_state = ACCEPTANCE_BUNDLE_GENERATED.
compliance_state = COMPLIANT.
no_trading_state = ENFORCED.
health_state = HEALTHY_FOR_LOCAL_AUDIT.
reproducibility_state = REPRODUCIBLE_LOCALLY.
pytest_state = GREEN.
exact_chain_state = GREEN.
live_execution = DISABLED.
leverage = FORBIDDEN.
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
closure_checksum est present.
closure_checks est non vide.
dataset_catalog.json contient v1_closure_lot20 et v1_closure_checks_lot20 sans doublon.
LOT 20 ORCHESTRATED VALIDATION: PASS.
LOT 20 REQUIRED CHAIN: PASS.
DIAGNOSE LOT20 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT20: PASS.
EXACT_CHAIN_LOT20_DONE.
rc=0.
```

Le Lot 20 reste une cloture locale defensive avec archive verifiable, sans connectivite externe et sans logique de trading exploitable.

Le Lot 20-bis ajoute les points d'acceptance suivants :

```text
Le test technique renomme est present dans l'archive finale.
L'ancien nom de test n'apparait plus dans l'archive finale.
python scripts/validate_lot20_archive_extracted.py passe.
L'archive extraite est verifiee localement avant acceptance finale.
```

Apres acceptance Lot 20, toute ouverture de V2 doit rester un lot de cadrage documentaire tant qu'aucun lot dedie d'implementation n'a ete audite.

Depuis le Lot 21, cette ouverture est materialisee par un registre fonctionnel planning-only, sans modification des invariants defensifs de la V1.
