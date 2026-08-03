# Acceptance Criteria - Lot 23-bis

Le Lot 23-bis est accepte si :

```text
src/crypto_quant_bot/market_state/loader.py lit les JSONL Lot 7 de maniere robuste.
src/crypto_quant_bot/data/data_writer.py ecrit les JSONL par remplacement atomique tmp -> replace.
scripts/build_lot7_market_state.py ne relit plus fragillement la sortie Lot 7 pour l'upsert du catalogue.
scripts/validate_lot7.py detecte proprement un JSONL invalide.
scripts/diagnose_lot7_market_state_jsonl.py existe.
tests/test_lot7_market_state_jsonl_robustness.py existe.
tests/test_lot23_bis_lot7_chain_stability.py existe.
reports/lot_23_bis_lot7_jsonl_robustness_report.md existe.
read_jsonl ignore les lignes strictement vides.
read_jsonl signale le chemin et le numero de ligne sur contenu non JSON.
LOT 7 MARKET STATE BUILD: PASS.
LOT 7 VALIDATION: PASS.
DIAGNOSE LOT7 MARKET STATE JSONL: PASS.
DIAGNOSE EXACT CHAIN LOT23: PASS.
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS.
EXACT_CHAIN_LOT23_DONE.
rc=0.
L'archive V1 gelee conserve le meme SHA256 avant et apres correction.
Aucun artefact Lot 24 n'est cree.
```
