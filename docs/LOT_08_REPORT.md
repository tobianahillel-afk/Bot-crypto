# Lot 8 — Feature Registry Hardening & Anti-Lookahead Audit V1

Le Lot 8 ajoute une couche de gouvernance technique et de sécurité de données à **Crypto Quant Bot V3.1-Ops**.

## Ajouts

```text
src/crypto_quant_bot/contracts/audit.py
src/crypto_quant_bot/audit/
scripts/audit_lot8_feature_registry.py
scripts/audit_lot8_no_lookahead.py
scripts/validate_lot8.py
scripts/validate_all_until_lot8.py
scripts/validate_all_until_lot8.sh
```

## Rapports générés

```text
data/audit/feature_registry_audit_lot8.json
data/audit/no_lookahead_audit_lot8.json
reports/lot_08_feature_registry_audit_report.md
reports/lot_08_no_lookahead_report.md
```

## Garanties conservées

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
Risk Engine blocks by default
live_execution = DISABLED
leverage = FORBIDDEN
```

## Non-objectifs

Ce lot ne crée pas de stratégie, pas de backtest, pas de paper trading, pas de WebSocket, pas d'appel API, pas de ML, pas d'IA/news, pas d'exécution live et pas de signal LONG/SHORT exploitable.

## Limites V1

Le vérificateur V1 bloque les fuites structurelles évidentes et documente les règles, mais ne remplace pas une revue algorithmique formelle complète de chaque formule historique.
