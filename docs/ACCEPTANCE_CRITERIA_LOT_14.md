# Acceptance Criteria — Lot 14

Le Lot 14 est accepté si :

```text
src/crypto_quant_bot/decision/__init__.py existe.
src/crypto_quant_bot/decision/models.py existe.
src/crypto_quant_bot/decision/firewall.py existe.
src/crypto_quant_bot/decision/io.py existe.
scripts/run_lot14_decision_firewall.py produit les outputs attendus.
scripts/validate_lot14.py valide directement le Lot 14.
data/audit/final_decision_firewall_lot14_5m.jsonl contient 36 lignes.
data/audit/final_decision_firewall_lot14_15m.jsonl contient 12 lignes.
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
portfolio_state = FROZEN partout.
portfolio_change_allowed = false partout.
allocation_change_allowed = false partout.
rebalance_allowed = false partout.
order_routing_allowed = false partout.
external_connectivity_allowed = false partout.
human_review_required = true partout.
capital_at_risk = 0 partout.
live_execution = DISABLED partout.
leverage = FORBIDDEN partout.
decision_block_reasons inclut FINAL_DECISION_FIREWALL_ACTIVE, TRADING_DECISION_WAIT, SYSTEM_DECISION_BLOCK_TRADING, RISK_ENGINE_BLOCKS_BY_DEFAULT, EXPOSURE_GUARD_BLOCKS_BY_DEFAULT, PORTFOLIO_FROZEN, NO_ORDER_ROUTER, NO_EXCHANGE_CONNECTOR, LIVE_EXECUTION_DISABLED, LEVERAGE_FORBIDDEN, EDUCATIONAL_MODE_ONLY et HUMAN_REVIEW_REQUIRED.
LOT 14 ORCHESTRATED VALIDATION: PASS.
LOT 14 REQUIRED CHAIN: PASS.
DIAGNOSE LOT14 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT14: PASS.
EXACT_CHAIN_LOT14_DONE.
rc=0.
Le replay de validation Lot 0 reste disponible après contrôle.
La chaîne exacte Lot 14 redémarre depuis un état propre sans dépendre d'un artefact replay volatil supprimé.
```

Le Lot 14 reste éducatif, non connecté à un exchange, sans stratégie exploitable, sans décision exécutable, sans connectivité externe active et sans capital à risque.
