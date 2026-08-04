# Veto Consequence Matrix

| Veto | Sévérité basse | Sévérité haute/critique |
|---|---|---|
| data_quality_veto | BLOCK_ANALYSIS | BLOCK_TRADING |
| book_health_veto | WAIT | BLOCK_TRADING |
| unknown_volume_veto | WAIT | BLOCK_TRADING |
| spread/slippage/capacity_veto | WAIT | BLOCK_TRADING |
| scenario_uncertainty_veto | WAIT | WAIT |
| uncalibrated_model_veto | WAIT | BLOCK_STRATEGY |
| strategy_promotion_veto | WAIT | BLOCK_STRATEGY |
| portfolio/risk_limit_veto | WAIT | BLOCK_TRADING |
| exchange_health_veto | WAIT | PAUSE |
| order_state_unknown | PAUSE | KILL_SWITCH si exposition inconnue |
| reconciliation_veto | PAUSE | KILL_SWITCH |
| security_veto | PAUSE | KILL_SWITCH |
| incident_unresolved | BLOCK_TRADING | KILL_SWITCH |
| kill_switch_triggered | KILL_SWITCH | KILL_SWITCH |

Résolution finale : `KILL_SWITCH > PAUSE > BLOCK_TRADING > WAIT > APPROVE`.

## Baseline historique des seuils

Les valeurs historiques ci-dessous sont conservées uniquement comme baseline initiale, `NOT_LIVE_APPROVED`, et doivent être recalibrées/versionnées avant tout runtime concerné :

```yaml
book_health_min_trade: 0.80
book_health_min_system: 0.50
max_unknown_volume_ratio: 0.30
max_decision_latency_ms: 500
max_reconnects_per_hour: 3
max_api_errors_per_hour: 5
max_order_rejections_per_day: 2
max_reconciliation_fee_diff_pct: 0.05
```
