# Acceptance Criteria — Lot 12

Le Lot 12 est accepté si :

```text
src/crypto_quant_bot/exposure/__init__.py existe.
src/crypto_quant_bot/exposure/models.py existe.
src/crypto_quant_bot/exposure/guard.py existe.
src/crypto_quant_bot/exposure/io.py existe.
scripts/run_lot12_exposure_guard.py produit les outputs attendus.
scripts/validate_lot12.py valide directement le Lot 12.
data/audit/exposure_guard_lot12_5m.jsonl contient 36 lignes.
data/audit/exposure_guard_lot12_15m.jsonl contient 12 lignes.
total = 48.
TradingDecision = WAIT partout.
SystemDecision = BLOCK_TRADING partout.
trade_allowed = false partout.
used_for_decision = false partout.
exposure_allowed = false partout.
allocation_allowed = false partout.
rebalance_allowed = false partout.
current_exposure_units = 0 partout.
max_exposure_units = 0 partout.
capital_at_risk = 0 partout.
live_execution = DISABLED partout.
leverage = FORBIDDEN partout.
exposure_block_reasons inclut NO_CAPITAL_ALLOCATION, NO_ACTIVE_EXPOSURE, NO_ORDER_ROUTER, NO_EXCHANGE_CONNECTOR, RISK_ENGINE_BLOCKS_BY_DEFAULT, EDUCATIONAL_MODE_ONLY, LIVE_EXECUTION_DISABLED et LEVERAGE_FORBIDDEN.
LOT 12 ORCHESTRATED VALIDATION: PASS.
LOT 12 REQUIRED CHAIN: PASS.
DIAGNOSE LOT12 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT12: PASS.
EXACT_CHAIN_LOT12_DONE.
rc=0.
```

Le Lot 12 reste éducatif, non connecté à un exchange, sans stratégie, sans ordre réel, sans ordre simulé exploitable, sans fill, sans PnL exploitable, sans paper trading, sans WebSocket et sans API.

Les artefacts produits par le Lot 12 peuvent être consommés par le Lot 13 comme contexte documentaire uniquement, sans autoriser de variation de portefeuille.
