# Acceptance Criteria - Lot 21-bis

Le Lot 21-bis est accepte si :

```text
src/crypto_quant_bot/product_scope/__init__.py existe.
src/crypto_quant_bot/product_scope/models.py existe.
src/crypto_quant_bot/product_scope/registry.py existe.
src/crypto_quant_bot/product_scope/io.py existe.
scripts/validate_v1_archive_frozen.py existe.
scripts/run_lot21_product_scope.py existe et produit les artefacts attendus.
scripts/validate_lot21.py existe et valide le registre.
scripts/validate_all_until_lot21.py existe.
scripts/run_required_chain_until_lot21.sh existe.
scripts/diagnose_lot21_required_chain_timing.py existe.
scripts/diagnose_exact_chain_until_lot21.py existe.
data/audit/product_scope_lot21.json existe.
data/audit/product_scope_capabilities_lot21.jsonl existe.
data/audit/product_scope_roadmap_lot21.jsonl existe.
reports/lot_21_v1_archive_freeze_report.md existe.
reports/lot_21_product_scope_report.md existe.
reports/lot_21_validation_report.md existe.
docs/LOT_21_PRODUCT_SCOPE.md existe.
docs/V2_PRODUCT_ROADMAP.md existe.
docs/FUNCTIONAL_COVERAGE_REGISTRY.md existe.
docs/ACCEPTANCE_CRITERIA_LOT_21.md existe.
project_name = Crypto Quant Bot V3.1-Ops.
project_identity = SAME_PROJECT_NO_V4.
v1_closure_state = V1_DEFENSIVE_AUDIT_CLOSED.
v2_scope_state = OPENED_AS_PLANNING_ONLY.
scope_state = FUNCTIONAL_SCOPE_LOCKED.
source_v1_archive_path = dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz.
source_v1_archive_frozen = true.
source_v1_archive_sha256 est present.
source_v1_archive_size_bytes est present.
execution_allowed = false.
trade_allowed = false.
external_connectivity_allowed = false.
live_execution = DISABLED.
leverage = FORBIDDEN.
scope_checksum est present.
V1 ARCHIVE FROZEN VALIDATION: PASS.
LOT 21 PRODUCT SCOPE: PASS.
LOT 21 VALIDATION: PASS.
LOT 21 ORCHESTRATED VALIDATION: PASS.
LOT 21 REQUIRED CHAIN: PASS.
DIAGNOSE LOT21 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT21: PASS.
EXACT_CHAIN_LOT21_DONE.
rc=0.
```

Acceptance details:
- La V1 defensive/audit reste cloturee et verifiee depuis l'archive locale Lot 20.
- Le gel de l'archive V1 est valide au Lot 21-bis et les chaines V2 ne la regenerent plus.
- La V2 est ouverte uniquement comme planning-only scope lock, sans implementation active.
- Le registre couvre explicitement Market Analysis, Research OS, AI / News / Event Engine, UI / Dashboard, Account Read-Only, Sandbox Demo Trading et Future Personal Live Trading.
- Toutes les capabilities hors V1 sont notees not_yet_implemented avec execution_allowed=false.
- Aucune connectivite externe, aucun connecteur exchange, aucune cle API et aucun WebSocket ne sont autorises.
- La roadmap officielle Lot 22 a Lot 147 est documentee comme forecast-only.
- Le DatasetCatalog contient les entrees Lot 21 sans doublon et reste upsertable idempotent.
- Le scope_checksum est deterministe hors champs runtime-only.
- Toute activation future exige un lot dedie, une validation propre et une revue humaine.

Apres acceptation, le Lot 22 peut uniquement ouvrir une couche Market Analysis locale/offline, sans execution et sans regeneration de l'archive V1.

Le Lot 21-bis reste un registre de cadrage uniquement, sans execution, sans ordre, sans connectivite externe et sans module actif de trading.
