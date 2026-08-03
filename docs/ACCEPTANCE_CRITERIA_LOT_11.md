# Acceptance Criteria — Lot 11

Le Lot 11 est accepté si :

```text
src/crypto_quant_bot/risk/__init__.py existe.
src/crypto_quant_bot/risk/models.py existe.
src/crypto_quant_bot/risk/engine.py existe.
src/crypto_quant_bot/risk/io.py existe.
scripts/run_lot11_risk_engine.py produit les outputs attendus.
scripts/validate_lot11.py valide directement le Lot 11.
data/audit/risk_engine_lot11_5m.jsonl contient 36 lignes.
data/audit/risk_engine_lot11_15m.jsonl contient 12 lignes.
total = 48.
TradingDecision = WAIT partout.
SystemDecision = BLOCK_TRADING partout.
trade_allowed = false partout.
used_for_decision = false partout.
live_execution = DISABLED partout.
leverage = FORBIDDEN partout.
risk_block_reasons inclut LIVE_EXECUTION_DISABLED, LEVERAGE_FORBIDDEN, NO_ORDER_ROUTER, NO_EXCHANGE_CONNECTOR, EDUCATIONAL_MODE_ONLY et RISK_ENGINE_BLOCKS_BY_DEFAULT.
aucun champ interdit de trading exploitable n'est présent.
LOT 11 ORCHESTRATED VALIDATION: PASS.
LOT 11 REQUIRED CHAIN: PASS.
DIAGNOSE LOT11 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT11: PASS.
EXACT_CHAIN_LOT11_DONE.
rc=0.
```

Le Lot 11 reste éducatif, non connecté à un exchange, sans stratégie, sans ordre réel, sans ordre simulé exploitable, sans PnL exploitable, sans paper trading, sans WebSocket et sans API.

## Addendum Lot 12 on top of Lot 11

Les sorties Lot 11 peuvent être relues par le Lot 12 uniquement comme contexte documentaire d’exposition/capital. Elles ne doivent pas devenir une source de stratégie, d’ordre, de fill, de PnL exploitable ou d’exposition active.

Les invariants Lot 11 doivent rester inchangés après exécution du Lot 12 :

- `trade_allowed=false`
- `used_for_decision=false`
- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

Le Lot 12 ne doit pas transformer ces sorties en allocation capital, en rebalancing ou en exposition active.
