# Acceptance Criteria — Lot 15

Le Lot 15 est accepté si :

```text
Le correctif Lot 14-bis supprime le faux échec replay file missing.
scripts/validate_lot0.py passe directement.
scripts/diagnose_exact_chain_until_lot14.py passe.
scripts/diagnose_exact_chain_return_shell.py passe.
src/crypto_quant_bot/ledger/__init__.py existe.
src/crypto_quant_bot/ledger/models.py existe.
src/crypto_quant_bot/ledger/audit_trail.py existe.
src/crypto_quant_bot/ledger/io.py existe.
scripts/run_lot15_decision_ledger.py produit les outputs attendus.
scripts/validate_lot15.py valide directement le Lot 15.
data/audit/decision_ledger_lot15_5m.jsonl contient 36 lignes.
data/audit/decision_ledger_lot15_15m.jsonl contient 12 lignes.
total = 48.
TradingDecision = WAIT partout.
SystemDecision = BLOCK_TRADING partout.
final_decision = WAIT partout.
final_system_decision = BLOCK_TRADING partout.
decision_firewall_state = ACTIVE partout.
execution_allowed = false partout.
trade_allowed = false partout.
used_for_decision = false partout.
risk_allowed = false partout.
exposure_allowed = false partout.
portfolio_change_allowed = false partout.
allocation_change_allowed = false partout.
rebalance_allowed = false partout.
order_routing_allowed = false partout.
external_connectivity_allowed = false partout.
human_review_required = true partout.
ledger_state = RECORDED partout.
audit_trail_state = ACTIVE partout.
immutability_mode = APPEND_ONLY_SIMULATED partout.
ledger_block_reasons inclut DECISION_RECORDED_FOR_AUDIT_ONLY, FINAL_DECISION_WAIT, SYSTEM_DECISION_BLOCK_TRADING, EXECUTION_NOT_ALLOWED, ORDER_ROUTING_NOT_ALLOWED, EXTERNAL_CONNECTIVITY_DISABLED, RISK_ENGINE_BLOCKS_BY_DEFAULT, EXPOSURE_GUARD_BLOCKS_BY_DEFAULT, PORTFOLIO_FROZEN, EDUCATIONAL_MODE_ONLY et HUMAN_REVIEW_REQUIRED.
Chaque ligne possède entry_checksum.
Le chaînage previous_entry_checksum est cohérent par timeframe.
LOT 15 ORCHESTRATED VALIDATION: PASS.
LOT 15 REQUIRED CHAIN: PASS.
DIAGNOSE LOT15 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT15: PASS.
EXACT_CHAIN_LOT15_DONE.
rc=0.
```

Le Lot 15 reste un journal d’audit local, éducatif et non exécutable.

Le Lot 16 peut consommer les sorties du Lot 15 comme contexte documentaire local, sans modifier les invariants ni autoriser d'exécution.
