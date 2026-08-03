# Acceptance Criteria — Lot 13

Le Lot 13 est accepté si :

```text
src/crypto_quant_bot/portfolio/__init__.py existe.
src/crypto_quant_bot/portfolio/models.py existe.
src/crypto_quant_bot/portfolio/freeze.py existe.
src/crypto_quant_bot/portfolio/io.py existe.
scripts/run_lot13_portfolio_freeze.py produit les outputs attendus.
scripts/validate_lot13.py valide directement le Lot 13.
data/audit/portfolio_freeze_lot13_5m.jsonl contient 36 lignes.
data/audit/portfolio_freeze_lot13_15m.jsonl contient 12 lignes.
total = 48.
TradingDecision = WAIT partout.
SystemDecision = BLOCK_TRADING partout.
trade_allowed = false partout.
used_for_decision = false partout.
portfolio_state = FROZEN partout.
allocation_state = DISABLED partout.
rebalance_state = DISABLED partout.
portfolio_change_allowed = false partout.
allocation_change_allowed = false partout.
allocation_allowed = false partout.
rebalance_allowed = false partout.
new_exposure_allowed = false partout.
exposure_allowed = false partout.
current_exposure_units = 0 partout.
max_exposure_units = 0 partout.
capital_at_risk = 0 partout.
live_execution = DISABLED partout.
leverage = FORBIDDEN partout.
portfolio_block_reasons inclut PORTFOLIO_FROZEN, ALLOCATION_DISABLED, REBALANCE_DISABLED, NO_CAPITAL_ALLOCATION, NO_ACTIVE_EXPOSURE, NO_ORDER_ROUTER, NO_EXCHANGE_CONNECTOR, RISK_ENGINE_BLOCKS_BY_DEFAULT, EXPOSURE_GUARD_BLOCKS_BY_DEFAULT, EDUCATIONAL_MODE_ONLY, LIVE_EXECUTION_DISABLED et LEVERAGE_FORBIDDEN.
LOT 13 ORCHESTRATED VALIDATION: PASS.
LOT 13 REQUIRED CHAIN: PASS.
DIAGNOSE LOT13 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT13: PASS.
EXACT_CHAIN_LOT13_DONE.
rc=0.
```

Le Lot 13 reste éducatif, non connecté à un exchange, sans stratégie exploitable, sans variation de portefeuille, sans capital à risque et sans exécution active.

Les artefacts produits par le Lot 13 peuvent être consommés par le Lot 14 comme contexte documentaire uniquement, sans autoriser de décision exécutable.
